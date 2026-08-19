from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, g
from flask_login import login_required, current_user
from extensions import db
from models import Room, Booking, MaintenanceRequest, Kos, User, UserKos, Notification, compute_keluar, DEFAULT_STAY_UNITS
from helpers import admin_or_management, get_or_404, parse_amount, safe_commit, require_module_perm, log_activity, create_notification, wa_redirect, notify_pengelola
from sqlalchemy.orm import joinedload
from datetime import date, datetime

VALID_ROOM_STATUSES = ("tersedia", "terisi", "maintenance")
VALID_ROOM_TYPES = ("Reguler", "Deluxe", "VIP")

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")


@rooms_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    kos_id = session.get("kos_id")
    if current_user.role in ("admin", "management"):
        lantai = request.args.get("lantai", type=int)
        status = request.args.get("status")
        q = request.args.get("q", "").strip()
        query = Room.query
        if kos_id:
            query = query.filter_by(kos_id=kos_id)
        if lantai:
            query = query.filter_by(lantai=lantai)
        if status:
            query = query.filter_by(status=status)
        if q:
            query = query.filter(Room.nomor_kamar.ilike(f"%{q}%"))
        pagination = query.order_by(Room.lantai, Room.nomor_kamar).paginate(page=page, per_page=per_page, error_out=False)
        rooms = pagination.items
        # Preload active bookings — avoids N+1 for room.booking_aktif in template
        if rooms:
            active = Booking.query.filter(
                Booking.room_id.in_([r.id for r in rooms]),
                Booking.status.in_(("aktif", "menunggu_checkout")),
            ).options(joinedload(Booking.client)).all()
            g._booking_aktif_cache = {b.room_id: b for b in active}
        # data for the manual fill modal
        kos = db.session.get(Kos, kos_id) if kos_id else None
        return render_template("rooms/index.html", pagination=pagination, rooms=rooms, search=q,
                               modal_clients=User.query.filter_by(role="client").order_by(User.nama_lengkap).all(),
                               modal_kos=kos,
                               modal_active_map={b.user_id: b.room.nomor_kamar for b in Booking.query.filter_by(status="aktif").options(joinedload(Booking.room)).all() if b.room})
    query = Room.query.filter_by(status="tersedia")
    if kos_id:
        query = query.filter_by(kos_id=kos_id)
    pagination = query.order_by(Room.lantai, Room.nomor_kamar).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("rooms/public.html", pagination=pagination, rooms=pagination.items)


@rooms_bp.route("/tambah", methods=["GET", "POST"])
@admin_or_management
def tambah():
    if not require_module_perm("rooms", "create"):
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        nomor = request.form.get("nomor_kamar", "").strip()
        submitted = request.form
        if not nomor:
            flash("Nomor kamar wajib diisi.", "danger")
            return render_template("rooms/form.html", submitted=submitted)

        kos_id = session.get("kos_id")
        existing = Room.query.filter_by(nomor_kamar=nomor, kos_id=kos_id).first()
        if existing:
            flash("Nomor kamar sudah ada di kos ini.", "danger")
            return render_template("rooms/form.html", submitted=submitted)

        harga, err = parse_amount(request.form.get("harga_per_bulan"), label="Harga")
        if err:
            flash(err, "danger")
            return render_template("rooms/form.html", submitted=submitted)

        try:
            lantai = int(request.form.get("lantai", 1))
        except (ValueError, TypeError):
            flash("Lantai harus berupa angka.", "danger")
            return render_template("rooms/form.html", submitted=submitted)
        if lantai < 1:
            flash("Lantai harus minimal 1.", "danger")
            return render_template("rooms/form.html", submitted=submitted)

        status = request.form.get("status", "tersedia")
        if status not in VALID_ROOM_STATUSES:
            status = "tersedia"
        tipe = request.form.get("tipe", "Reguler")
        if tipe not in VALID_ROOM_TYPES:
            tipe = "Reguler"

        room = Room(
            kos_id=kos_id,
            nomor_kamar=nomor,
            lantai=lantai,
            tipe=tipe,
            harga_per_bulan=harga,
            ukuran=request.form.get("ukuran"),
            fasilitas=request.form.get("fasilitas"),
            status=status,
            deskripsi=request.form.get("deskripsi"),
        )
        db.session.add(room)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash(f"Kamar {nomor} berhasil ditambahkan.", "success")
        return redirect(url_for("rooms.index"))

    return render_template("rooms/form.html", room=None)


@rooms_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit(id):
    if not require_module_perm("rooms", "edit"):
        return redirect(url_for("dashboard.index"))
    room = get_or_404(Room, id)
    booking = Booking.query.filter_by(room_id=id, status="aktif").first()
    clients = User.query.filter_by(role="client").order_by(User.nama_lengkap).all()
    # JSON snapshot for the penghuni dropdown -> refill textboxes on change
    clients_json = [
        {"id": c.id, "nama_lengkap": c.nama_lengkap, "no_telepon": c.no_telepon or "", "email": c.email}
        for c in clients
    ]
    # room number per client's active booking (for the reassign select), excluding this room
    active_map = {}
    for b in Booking.query.filter_by(status="aktif").options(joinedload(Booking.room)).all():
        if b.room_id != id and b.room:
            active_map[b.user_id] = b.room.nomor_kamar

    def render_form():
        return render_template("rooms/form.html", room=room, booking=booking, clients=clients, clients_json=clients_json, active_map=active_map)

    if request.method == "POST":
        nomor = request.form.get("nomor_kamar", "").strip()
        if not nomor:
            flash("Nomor kamar wajib diisi.", "danger")
            return render_form()

        kos_id = session.get("kos_id")
        dup = Room.query.filter_by(nomor_kamar=nomor, kos_id=kos_id).first()
        if dup and dup.id != id:
            flash("Nomor kamar sudah ada di kos ini.", "danger")
            return render_form()

        harga, err = parse_amount(request.form.get("harga_per_bulan"), label="Harga")
        if err:
            flash(err, "danger")
            return render_form()

        try:
            lantai = int(request.form.get("lantai", 1))
        except (ValueError, TypeError):
            flash("Lantai harus berupa angka.", "danger")
            return render_form()
        if lantai < 1:
            flash("Lantai harus minimal 1.", "danger")
            return render_form()

        room.nomor_kamar = nomor
        room.lantai = lantai
        room.tipe = request.form.get("tipe", "Reguler")
        if room.tipe not in VALID_ROOM_TYPES:
            room.tipe = "Reguler"
        room.harga_per_bulan = harga
        room.ukuran = request.form.get("ukuran")
        room.fasilitas = request.form.get("fasilitas")
        room.status = request.form.get("status", "tersedia")
        if room.status not in VALID_ROOM_STATUSES:
            room.status = "tersedia"
        room.deskripsi = request.form.get("deskripsi")

        # Resident: change penghuni (swap) and/or edit profile — same commit as room = atomic
        swapped = False
        if booking:
            target = booking.client
            new_id = request.form.get("penghuni_id", type=int)
            if new_id and new_id != booking.client.id:
                new_client = db.session.get(User, new_id)
                if not new_client or new_client.role != "client":
                    flash("Penghuni tujuan tidak valid.", "danger")
                    return render_form()
                other = Booking.query.filter(
                    Booking.user_id == new_client.id, Booking.status == "aktif",
                    Booking.id != booking.id).first()
                if other:
                    flash(f"{new_client.nama_lengkap} masih menempati kamar {other.room.nomor_kamar}. Pilih penghuni lain.", "danger")
                    return render_form()
                # end current stay (history preserved), open new booking for target
                booking.status = "selesai"
                booking.tanggal_keluar = date.today()
                # notify the outgoing resident + remind pengelola to return their deposit
                if booking.client:
                    db.session.add(Notification(user_id=booking.client.id,
                        pesan=f"Kamar {room.nomor_kamar} telah dialihkan ke penghuni lain. Masa sewa Anda berakhir {date.today().strftime('%d/%m/%Y')}.",
                        jenis="umum"))
                if booking.deposit and booking.deposit > 0 and booking.client:
                    notify_pengelola(room.kos_id,
                        f"Kembalikan deposit Rp{booking.deposit:,.0f} ke {booking.client.nama_lengkap} (kamar {room.nomor_kamar}).", "deposit")
                db.session.add(Booking(
                    user_id=new_client.id, room_id=room.id, tanggal_masuk=date.today(),
                    tanggal_keluar=room.kos.default_keluar_date(date.today()) if room.kos else None,
                    deposit=room.kos.default_deposit(room) if room.kos else 0,
                    status="aktif",
                    catatan="Dipindahkan dari penghuni sebelumnya via edit kamar"))
                target = new_client
                room.status = "terisi"
                swapped = True

            nama = request.form.get("penghuni_nama", "").strip()
            if nama:
                target.nama_lengkap = nama
                target.no_telepon = request.form.get("penghuni_telepon") or target.no_telepon
                email = request.form.get("penghuni_email", "").strip()
                if email and email != target.email:
                    dup_email = User.query.filter(User.email == email, User.id != target.id).first()
                    if dup_email:
                        flash("Email sudah digunakan penghuni lain.", "danger")
                        return render_form()
                    target.email = email

        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        log_activity(current_user.id, "Perbarui kamar", f"Kamar {nomor}", "Room")
        flash(f"Kamar {nomor} berhasil diperbarui." + (" Penghuni diganti." if swapped else ""), "success")
        return redirect(url_for("rooms.index"))

    return render_form()


@rooms_bp.route("/isi-penghuni", methods=["POST"])
@admin_or_management
def isi_penghuni():
    """Manual booking: admin/management assigns a guest to a room. No guest self-serve needed."""
    if not require_module_perm("rooms", "edit"):
        return redirect(url_for("dashboard.index"))
    room = get_or_404(Room, request.form.get("room_id", type=int))
    if room.kos_id and not current_user.has_kos_access(room.kos_id, ["admin", "management"]):
        flash("Akses ditolak untuk kos ini.", "danger")
        return redirect(url_for("rooms.index"))
    if room.status != "tersedia":
        flash("Kamar tidak tersedia.", "warning")
        return redirect(url_for("rooms.index"))
    # Don't override an existing pending request on this room from another guest.
    pending_for_room = Booking.query.filter(
        Booking.room_id == room.id, Booking.status == "pending",
    ).first()
    if pending_for_room and pending_for_room.user_id != request.form.get("guest_id", type=int):
        flash(f"Kamar ini punya permintaan pending dari {pending_for_room.client.nama_lengkap}. Tolak permintaan tersebut dulu.", "warning")
        return redirect(url_for("rooms.index"))

    guest = db.session.get(User, request.form.get("guest_id", type=int))
    if not guest or guest.role != "client":
        flash("Pilih penghuni yang valid.", "danger")
        return redirect(url_for("rooms.index"))
    other = Booking.query.filter(
        Booking.user_id == guest.id,
        Booking.status.in_(("aktif", "pending", "menunggu_checkout")),
    ).first()
    if other:
        flash(f"{guest.nama_lengkap} masih menempati kamar {other.room.nomor_kamar}.", "danger")
        return redirect(url_for("rooms.index"))

    masuk_str = request.form.get("tanggal_masuk", "")
    try:
        masuk = datetime.strptime(masuk_str, "%Y-%m-%d").date() if masuk_str else date.today()
    except ValueError:
        flash("Format tanggal masuk salah.", "danger")
        return redirect(url_for("rooms.index"))

    durasi_value = request.form.get("durasi_value", type=int) or 1
    durasi_unit = request.form.get("durasi_unit", "bulan")
    if durasi_unit not in DEFAULT_STAY_UNITS:
        durasi_unit = "bulan"
    keluar = compute_keluar(masuk, durasi_value, durasi_unit)

    try:
        deposit = float(request.form.get("deposit") or 0)
    except (ValueError, TypeError):
        deposit = 0
    deposit = max(0, deposit)

    kos = room.kos
    if kos and not UserKos.query.filter_by(user_id=guest.id, kos_id=kos.id).first():
        db.session.add(UserKos(user_id=guest.id, kos_id=kos.id, role="client"))

    db.session.add(Booking(
        user_id=guest.id, room_id=room.id, tanggal_masuk=masuk, tanggal_keluar=keluar,
        status="aktif", deposit=deposit, catatan="Dimasukkan manual oleh pengelola",
    ))
    room.status = "terisi"
    db.session.add(Notification(user_id=guest.id,
        pesan=f"Anda ditempatkan di kamar {room.nomor_kamar} (masuk {masuk.strftime('%d/%m/%Y')}). Selamat datang!", jenis="umum"))
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed to fill room")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("rooms.index"))
    log_activity(current_user.id, "Isi kamar", f"Kamar {room.nomor_kamar} - {guest.nama_lengkap}", "Booking")
    flash(f"Kamar {room.nomor_kamar} berhasil diisi {guest.nama_lengkap}.", "success")
    return redirect(url_for("rooms.index"))


@rooms_bp.route("/<int:id>/remind-deposit", methods=["POST"])
@admin_or_management
def remind_deposit(id):
    """Send a deposit payment reminder to the current resident (notification + WhatsApp)."""
    room = get_or_404(Room, id)
    if room.kos_id and not current_user.has_kos_access(room.kos_id, ["admin", "management"]):
        flash("Akses ditolak untuk kos ini.", "danger")
        return redirect(url_for("rooms.detail", id=id))
    booking = room.booking_aktif
    if not booking or not booking.client:
        flash("Tidak ada penghuni aktif.", "warning")
        return redirect(url_for("rooms.detail", id=id))
    guest = booking.client
    deposit = booking.deposit or 0
    if deposit <= 0:
        flash("Tidak ada deposit yang tercatat untuk penghuni ini.", "info")
        return redirect(url_for("rooms.detail", id=id))
    create_notification(guest.id,
        f"Mohon segera bayar deposit kamar {room.nomor_kamar} sebesar Rp{deposit:,.0f}.", "pembayaran")
    phone = getattr(guest, "no_telepon", None)
    if phone:
        msg = f"Halo {guest.nama_lengkap}, mohon selesaikan deposit kamar {room.nomor_kamar} sebesar Rp{deposit:,.0f}. Terima kasih."
        return wa_redirect(phone, msg)
    flash("Pengingat deposit terkirim ke penghuni.", "success")
    return redirect(url_for("rooms.detail", id=id))


@rooms_bp.route("/hapus/<int:id>", methods=["POST"])
@admin_or_management
def hapus(id):
    if not require_module_perm("rooms", "delete"):
        return redirect(url_for("dashboard.index"))
    room = get_or_404(Room, id)
    if room.status == "terisi":
        flash("Kamar sedang terisi, tidak bisa dihapus.", "danger")
        return redirect(url_for("rooms.index"))

    db.session.delete(room)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash(f"Kamar {room.nomor_kamar} berhasil dihapus.", "success")
    return redirect(url_for("rooms.index"))


@rooms_bp.route("/<int:id>")
@login_required
def detail(id):
    room = get_or_404(Room, id)
    booking = room.booking_aktif
    maintenance = MaintenanceRequest.query.options(joinedload(MaintenanceRequest.vendor)).filter_by(room_id=id).order_by(MaintenanceRequest.created_at.desc()).all()
    history = Booking.query.options(joinedload(Booking.client)).filter_by(room_id=id).order_by(Booking.created_at.desc()).all()
    return render_template("rooms/detail.html", room=room, booking=booking, maintenance=maintenance, history=history)
