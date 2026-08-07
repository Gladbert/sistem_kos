from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from extensions import db
from models import MaintenanceRequest, Vendor, Room
from helpers import admin_or_management, get_or_404, kos_rooms, kos_room_ids, create_notification, wa_redirect, safe_commit, sanitize

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")


@maintenance_bp.route("/")
@admin_or_management
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    status = request.args.get("status")
    query = MaintenanceRequest.query

    room_ids = kos_room_ids()
    if room_ids:
        query = query.filter(MaintenanceRequest.room_id.in_(room_ids))
    elif room_ids == []:
        query = query.filter(False)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(MaintenanceRequest.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("maintenance/index.html", pagination=pagination, requests=pagination.items)


@maintenance_bp.route("/tambah", methods=["GET", "POST"])
@admin_or_management
def tambah():
    if request.method == "POST":
        room_id = request.form.get("room_id", type=int)
        deskripsi = request.form.get("deskripsi", "").strip()

        if not deskripsi:
            flash("Deskripsi wajib diisi.", "danger")
            return render_template("maintenance/form.html", rooms=kos_rooms(), vendors=Vendor.query.order_by(Vendor.nama).all())

        mr = MaintenanceRequest(
            room_id=room_id,
            vendor_id=request.form.get("vendor_id", type=int) or None,
            deskripsi=deskripsi,
            prioritas=request.form.get("prioritas", "normal"),
            status="diajukan",
            catatan=request.form.get("catatan"),
        )
        db.session.add(mr)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))

        if room_id:
            room = db.session.get(Room, room_id)
            if room and room.booking_aktif:
                client = room.booking_aktif.client
                create_notification(
                    client.id,
                    f"Ada maintenance untuk kamar {room.nomor_kamar}: {deskripsi[:50]}...",
                    jenis="maintenance",
                )

        flash("Permintaan maintenance berhasil diajukan.", "success")
        return redirect(url_for("maintenance.index"))

    return render_template("maintenance/form.html", rooms=kos_rooms(), vendors=Vendor.query.order_by(Vendor.nama).all())


@maintenance_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit(id):
    mr = get_or_404(MaintenanceRequest, id)

    if request.method == "POST":
        mr.room_id = request.form.get("room_id", type=int)
        mr.vendor_id = request.form.get("vendor_id", type=int) or None
        mr.deskripsi = request.form.get("deskripsi", "")
        mr.prioritas = request.form.get("prioritas", "normal")
        mr.status = request.form.get("status", mr.status)
        mr.catatan = request.form.get("catatan")

        if mr.status == "selesai" and not mr.tanggal_selesai:
            mr.tanggal_selesai = date.today()

        try:
            mr.biaya = float(request.form.get("biaya", 0))
        except ValueError:
            mr.biaya = 0

        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Permintaan maintenance berhasil diperbarui.", "success")
        return redirect(url_for("maintenance.index"))

    return render_template("maintenance/form.html", mr=mr, rooms=kos_rooms(), vendors=Vendor.query.order_by(Vendor.nama).all())


@maintenance_bp.route("/hapus/<int:id>", methods=["POST"])
@admin_or_management
def hapus(id):
    mr = get_or_404(MaintenanceRequest, id)
    db.session.delete(mr)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash("Permintaan maintenance berhasil dihapus.", "success")
    return redirect(url_for("maintenance.index"))


@maintenance_bp.route("/vendor")
@admin_or_management
def vendor_index():
    vendors = Vendor.query.order_by(Vendor.nama).all()
    return render_template("maintenance/vendor_index.html", vendors=vendors)


@maintenance_bp.route("/vendor/tambah", methods=["GET", "POST"])
@admin_or_management
def vendor_tambah():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama vendor wajib diisi.", "danger")
            return render_template("maintenance/vendor_form.html")

        vendor = Vendor(
            nama=sanitize(nama),
            no_telepon=sanitize(request.form.get("no_telepon")),
            kategori=request.form.get("kategori", "lainnya"),
            alamat=sanitize(request.form.get("alamat")),
            catatan=sanitize(request.form.get("catatan")),
        )
        db.session.add(vendor)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash(f"Vendor {nama} berhasil ditambahkan.", "success")
        return redirect(url_for("maintenance.vendor_index"))

    return render_template("maintenance/vendor_form.html")


@maintenance_bp.route("/vendor/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def vendor_edit(id):
    vendor = get_or_404(Vendor, id)

    if request.method == "POST":
        vendor.nama = sanitize(request.form.get("nama", vendor.nama))
        vendor.no_telepon = sanitize(request.form.get("no_telepon"))
        vendor.kategori = request.form.get("kategori", "lainnya")
        vendor.alamat = sanitize(request.form.get("alamat"))
        vendor.catatan = sanitize(request.form.get("catatan"))
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash(f"Vendor {vendor.nama} berhasil diperbarui.", "success")
        return redirect(url_for("maintenance.vendor_index"))

    return render_template("maintenance/vendor_form.html", vendor=vendor)


@maintenance_bp.route("/vendor/hapus/<int:id>", methods=["POST"])
@admin_or_management
def vendor_hapus(id):
    vendor = get_or_404(Vendor, id)
    db.session.delete(vendor)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash("Vendor berhasil dihapus.", "success")
    return redirect(url_for("maintenance.vendor_index"))


@maintenance_bp.route("/vendor/wa/<int:id>")
@admin_or_management
def vendor_wa(id):
    vendor = get_or_404(Vendor, id)
    pesan = f"Halo {vendor.nama}, kami dari pengelola kos ingin menghubungi Anda terkait pekerjaan maintenance."
    return wa_redirect(vendor.no_telepon, pesan)


@maintenance_bp.route("/vendor/hubungi/<int:mr_id>")
@admin_or_management
def vendor_hubungi(mr_id):
    mr = get_or_404(MaintenanceRequest, mr_id)
    if not mr.vendor:
        flash("Tidak ada vendor yang ditugaskan.", "warning")
        return redirect(url_for("maintenance.edit", id=mr_id))

    pesan = f"Halo {mr.vendor.nama}!"
    pesan += f"\n\nAda permintaan maintenance untuk kamar {mr.room.nomor_kamar}:"
    pesan += f"\n{mr.deskripsi}"
    pesan += f"\nPrioritas: {mr.prioritas.upper()}"
    if mr.biaya > 0:
        pesan += f"\nBiaya: Rp{mr.biaya:,.0f}"
    pesan += f"\n\nMohon segera ditindaklanjuti. Terima kasih."

    return wa_redirect(mr.vendor.no_telepon, pesan)


@maintenance_bp.route("/notif-penghuni/<int:mr_id>")
@admin_or_management
def notif_penghuni(mr_id):
    mr = get_or_404(MaintenanceRequest, mr_id)
    booking = mr.room.booking_aktif
    if not booking or not booking.client.no_telepon:
        flash("Tidak ada penghuni aktif di kamar ini.", "warning")
        return redirect(url_for("maintenance.index"))

    pesan = f"Halo {booking.client.nama_lengkap}!"
    pesan += f"\n\nMaintenance untuk kamar {mr.room.nomor_kamar} telah selesai."
    pesan += f"\nDeskripsi: {mr.deskripsi}"
    if mr.biaya and mr.biaya > 0:
        pesan += f"\nBiaya: Rp{mr.biaya:,.0f}"
    pesan += f"\n\nTerima kasih."

    create_notification(
        booking.client.id,
        f"Notifikasi maintenance selesai dikirim ke {booking.client.nama_lengkap} (Kamar {mr.room.nomor_kamar})",
        jenis="maintenance",
        wa_sent=True,
    )

    return wa_redirect(booking.client.no_telepon, pesan)
