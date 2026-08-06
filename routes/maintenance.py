import urllib.parse
from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from extensions import db
from models import MaintenanceRequest, Vendor, Room, Notification

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")


def _kos_rooms():
    """Return rooms filtered by current kos, or all rooms if no kos selected."""
    kos_id = session.get("kos_id")
    return Room.query.filter_by(kos_id=kos_id).all() if kos_id else Room.query.all()


@maintenance_bp.route("/")
@login_required
def index():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    kos_id = session.get("kos_id")
    status = request.args.get("status")
    query = MaintenanceRequest.query

    if kos_id:
        kos_room_ids = [r.id for r in db.session.query(Room.id).filter_by(kos_id=kos_id).all()]
        query = query.filter(MaintenanceRequest.room_id.in_(kos_room_ids)) if kos_room_ids else query.filter(False)
    if status:
        query = query.filter_by(status=status)

    requests = query.order_by(MaintenanceRequest.created_at.desc()).all()
    return render_template("maintenance/index.html", requests=requests)


@maintenance_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        room_id = request.form.get("room_id", type=int)
        deskripsi = request.form.get("deskripsi", "").strip()

        if not deskripsi:
            flash("Deskripsi wajib diisi.", "danger")
            return render_template("maintenance/form.html", rooms=_kos_rooms(), vendors=Vendor.query.order_by(Vendor.nama).all())

        mr = MaintenanceRequest(
            room_id=room_id,
            vendor_id=request.form.get("vendor_id", type=int) or None,
            deskripsi=deskripsi,
            prioritas=request.form.get("prioritas", "normal"),
            status="diajukan",
            catatan=request.form.get("catatan"),
        )
        db.session.add(mr)
        db.session.commit()

        if room_id:
            room = Room.query.get(room_id)
            if room and room.booking_aktif:
                client = room.booking_aktif.client
                notif = Notification(
                    user_id=client.id,
                    pesan=f"Ada maintenance untuk kamar {room.nomor_kamar}: {deskripsi[:50]}...",
                    jenis="maintenance",
                )
                db.session.add(notif)
                db.session.commit()

        flash("Permintaan maintenance berhasil diajukan.", "success")
        return redirect(url_for("maintenance.index"))

    return render_template("maintenance/form.html", rooms=_kos_rooms(), vendors=Vendor.query.order_by(Vendor.nama).all())


@maintenance_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    mr = MaintenanceRequest.query.get_or_404(id)

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

        db.session.commit()
        flash("Permintaan maintenance berhasil diperbarui.", "success")
        return redirect(url_for("maintenance.index"))

    return render_template("maintenance/form.html", mr=mr, rooms=_kos_rooms(), vendors=Vendor.query.order_by(Vendor.nama).all())


@maintenance_bp.route("/hapus/<int:id>", methods=["POST"])
@login_required
def hapus(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    mr = MaintenanceRequest.query.get_or_404(id)
    db.session.delete(mr)
    db.session.commit()
    flash("Permintaan maintenance berhasil dihapus.", "success")
    return redirect(url_for("maintenance.index"))


@maintenance_bp.route("/vendor")
@login_required
def vendor_index():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    vendors = Vendor.query.order_by(Vendor.nama).all()
    return render_template("maintenance/vendor_index.html", vendors=vendors)


@maintenance_bp.route("/vendor/tambah", methods=["GET", "POST"])
@login_required
def vendor_tambah():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama vendor wajib diisi.", "danger")
            return render_template("maintenance/vendor_form.html")

        vendor = Vendor(
            nama=nama,
            no_telepon=request.form.get("no_telepon"),
            kategori=request.form.get("kategori", "lainnya"),
            alamat=request.form.get("alamat"),
            catatan=request.form.get("catatan"),
        )
        db.session.add(vendor)
        db.session.commit()
        flash(f"Vendor {nama} berhasil ditambahkan.", "success")
        return redirect(url_for("maintenance.vendor_index"))

    return render_template("maintenance/vendor_form.html")


@maintenance_bp.route("/vendor/edit/<int:id>", methods=["GET", "POST"])
@login_required
def vendor_edit(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    vendor = Vendor.query.get_or_404(id)

    if request.method == "POST":
        vendor.nama = request.form.get("nama", vendor.nama)
        vendor.no_telepon = request.form.get("no_telepon")
        vendor.kategori = request.form.get("kategori", "lainnya")
        vendor.alamat = request.form.get("alamat")
        vendor.catatan = request.form.get("catatan")
        db.session.commit()
        flash(f"Vendor {vendor.nama} berhasil diperbarui.", "success")
        return redirect(url_for("maintenance.vendor_index"))

    return render_template("maintenance/vendor_form.html", vendor=vendor)


@maintenance_bp.route("/vendor/hapus/<int:id>", methods=["POST"])
@login_required
def vendor_hapus(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    vendor = Vendor.query.get_or_404(id)
    db.session.delete(vendor)
    db.session.commit()
    flash("Vendor berhasil dihapus.", "success")
    return redirect(url_for("maintenance.vendor_index"))


@maintenance_bp.route("/vendor/wa/<int:id>")
@login_required
def vendor_wa(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    vendor = Vendor.query.get_or_404(id)
    pesan = f"Halo {vendor.nama}, kami dari pengelola kos ingin menghubungi Anda terkait pekerjaan maintenance."
    return redirect(f"https://wa.me/{vendor.no_telepon}?text={urllib.parse.quote(pesan)}")


@maintenance_bp.route("/vendor/hubungi/<int:mr_id>")
@login_required
def vendor_hubungi(mr_id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    mr = MaintenanceRequest.query.get_or_404(mr_id)
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

    return redirect(f"https://wa.me/{mr.vendor.no_telepon}?text={urllib.parse.quote(pesan)}")


@maintenance_bp.route("/notif-penghuni/<int:mr_id>")
@login_required
def notif_penghuni(mr_id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    mr = MaintenanceRequest.query.get_or_404(mr_id)
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

    notif = Notification(
        user_id=booking.client.id,
        pesan=f"Notifikasi maintenance selesai dikirim ke {booking.client.nama_lengkap} (Kamar {mr.room.nomor_kamar})",
        jenis="maintenance",
        wa_sent=True,
    )
    db.session.add(notif)
    db.session.commit()

    return redirect(f"https://wa.me/{booking.client.no_telepon}?text={urllib.parse.quote(pesan)}")
