import urllib.parse
from datetime import date
from flask import Blueprint, render_template, redirect, flash, url_for, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Room, Booking, Payment, Expense, Notification, MaintenanceRequest, Complaint
from helpers import log_activity

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    if current_user.role in ("admin", "management"):
        return redirect(url_for("dashboard.admin"))
    return redirect(url_for("dashboard.client"))


@dashboard_bp.route("/admin")
@login_required
def admin():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.client"))

    total_kamar = Room.query.count()
    kamar_terisi = Booking.query.filter_by(status="aktif").count()
    kamar_tersedia = Room.query.filter_by(status="tersedia").count()
    kamar_pending = Booking.query.filter_by(status="pending").count()
    kamar_maintenance = Room.query.filter(Room.status == "maintenance").count()

    total_penghuni = db.session.query(Booking.user_id).filter(
        Booking.status == "aktif"
    ).distinct().count()

    penghuni_raw = User.query.join(Booking).filter(
        Booking.status == "aktif", User.role == "client"
    ).all()

    penghuni = []
    for u in penghuni_raw:
        b = Booking.query.filter_by(user_id=u.id, status="aktif").first()
        penghuni.append({
            "id": u.id,
            "nama_lengkap": u.nama_lengkap,
            "username": u.username,
            "no_telepon": u.no_telepon,
            "is_active": u.is_active,
            "nomor_kamar": b.room.nomor_kamar if b else "-",
            "kamar_id": b.room_id if b else None,
        })

    pemasukan_bulan_ini = db.session.query(db.func.sum(Payment.jumlah)).filter(
        Payment.status == "lunas",
        db.func.strftime("%Y-%m", Payment.tanggal_bayar) == date.today().strftime("%Y-%m")
    ).scalar() or 0

    pengeluaran_bulan_ini = db.session.query(db.func.sum(Expense.jumlah)).filter(
        db.func.strftime("%Y-%m", Expense.tanggal) == date.today().strftime("%Y-%m")
    ).scalar() or 0

    tagihan_belum_dibayar = 0
    unpaid_bookings = []
    for b in Booking.query.filter_by(status="aktif").all():
        if b.tagihan_bulan_ini:
            tagihan_belum_dibayar += 1
            unpaid_bookings.append(b)

    booking_pending = Booking.query.filter_by(status="pending").order_by(Booking.created_at.asc()).all()

    bulan_ini = date.today().strftime("%Y-%m")
    pembayaran_bulan_ini = Payment.query.filter(
        Payment.status == "lunas",
        db.func.strftime("%Y-%m", Payment.tanggal_bayar) == bulan_ini
    ).count()

    total_tagihan = Booking.query.filter_by(status="aktif").count()
    collection_rate = round((pembayaran_bulan_ini / total_tagihan * 100) if total_tagihan > 0 else 0)
    occupancy_rate = round((kamar_terisi / total_kamar * 100) if total_kamar > 0 else 0)

    tipe_kamar = db.session.query(Room.tipe, db.func.count(Room.id)).group_by(Room.tipe).all()

    pemasukan_6bulan = []
    for i in range(5, -1, -1):
        m = date.today().month - i
        y = date.today().year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        bulan_str = f"{y:04d}-{m:02d}"
        total = db.session.query(db.func.sum(Payment.jumlah)).filter(
            Payment.status == "lunas",
            db.func.strftime("%Y-%m", Payment.tanggal_bayar) == bulan_str
        ).scalar() or 0
        pemasukan_6bulan.append({"bulan": bulan_str, "total": total})

    pembayaran_terbaru = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    pengeluaran_terbaru = Expense.query.order_by(Expense.created_at.desc()).limit(5).all()
    permintaan_maintenance = MaintenanceRequest.query.filter(
        MaintenanceRequest.status.in_(["diajukan", "diproses"])
    ).order_by(MaintenanceRequest.created_at.desc()).limit(5).all()

    komplain_baru = Complaint.query.filter_by(status="diajukan").count()

    booking_audit = Booking.query.filter_by(status="aktif").order_by(Booking.tanggal_masuk.desc()).limit(5).all()

    return render_template("dashboard/admin.html",
        total_kamar=total_kamar, kamar_terisi=kamar_terisi,
        kamar_tersedia=kamar_tersedia, total_penghuni=total_penghuni,
        penghuni=penghuni, pemasukan_bulan_ini=pemasukan_bulan_ini,
        pengeluaran_bulan_ini=pengeluaran_bulan_ini,
        tagihan_belum_dibayar=tagihan_belum_dibayar,
        pembayaran_terbaru=pembayaran_terbaru,
        pengeluaran_terbaru=pengeluaran_terbaru,
        permintaan_maintenance=permintaan_maintenance,
        komplain_baru=komplain_baru,
        kamar_pending=kamar_pending,
        kamar_maintenance=kamar_maintenance,
        booking_pending=booking_pending,
        unpaid_bookings=unpaid_bookings,
        collection_rate=collection_rate,
        occupancy_rate=occupancy_rate,
        tipe_kamar=tipe_kamar,
        pemasukan_6bulan=pemasukan_6bulan,
        booking_audit=booking_audit)


@dashboard_bp.route("/client")
@login_required
def client():
    booking_aktif = Booking.query.filter_by(user_id=current_user.id, status="aktif").first()
    booking_pending = Booking.query.filter_by(user_id=current_user.id, status="pending").first()
    booking = booking_aktif or booking_pending
    riwayat = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    pembayaran = Payment.query.join(Booking).filter(Booking.user_id == current_user.id).order_by(Payment.created_at.desc()).all()
    notifikasi = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    notif_belum_dibaca = Notification.query.filter_by(user_id=current_user.id, dibaca=False).count()

    return render_template("dashboard/client.html",
        booking=booking, booking_aktif=booking_aktif, booking_pending=booking_pending,
        riwayat=riwayat, pembayaran=pembayaran,
        notifikasi=notifikasi, notif_belum_dibaca=notif_belum_dibaca,
        date_today=date.today())


@dashboard_bp.route("/booking/<int:id>/approve", methods=["POST"])
@login_required
def approve_booking(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))
    booking = Booking.query.get_or_404(id)
    if booking.status != "pending":
        flash("Booking sudah diproses.", "warning")
        return redirect(url_for("dashboard.admin"))
    booking.status = "aktif"
    booking.room.status = "terisi"
    notif = Notification(
        user_id=booking.user_id,
        pesan=f"Permintaan sewa kamar {booking.room.nomor_kamar} telah DISETUJUI! Silakan check-in.",
        jenis="umum",
    )
    db.session.add(notif)
    log_activity(current_user.id, "Setujui booking", f"Kamar {booking.room.nomor_kamar} - {booking.client.nama_lengkap}", "Booking")
    db.session.commit()
    flash(f"Booking kamar {booking.room.nomor_kamar} oleh {booking.client.nama_lengkap} disetujui.", "success")
    return redirect(url_for("dashboard.admin"))


@dashboard_bp.route("/booking/<int:id>/tolak", methods=["POST"])
@login_required
def tolak_booking(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))
    booking = Booking.query.get_or_404(id)
    if booking.status != "pending":
        flash("Booking sudah diproses.", "warning")
        return redirect(url_for("dashboard.admin"))
    notif = Notification(
        user_id=booking.user_id,
        pesan=f"Permintaan sewa kamar {booking.room.nomor_kamar} telah DITOLAK. Silakan hubungi pengelola untuk detail.",
        jenis="umum",
    )
    db.session.add(notif)
    db.session.delete(booking)
    log_activity(current_user.id, "Tolak booking", f"Kamar {booking.room.nomor_kamar} - {booking.client.nama_lengkap}", "Booking")
    db.session.commit()
    flash(f"Booking kamar {booking.room.nomor_kamar} oleh {booking.client.nama_lengkap} ditolak.", "info")
    return redirect(url_for("dashboard.admin"))


@dashboard_bp.route("/auto-proses", methods=["POST"])
@login_required
def auto_proses():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))
    today = date.today()
    count_selesai = 0
    count_notif = 0

    bookings_selesai = Booking.query.filter(
        Booking.status == "aktif",
        Booking.tanggal_keluar < today
    ).all()
    for b in bookings_selesai:
        b.status = "selesai"
        b.room.status = "tersedia"
        notif = Notification(user_id=b.user_id,
            pesan=f"Masa sewa kamar {b.room.nomor_kamar} telah berakhir per {b.tanggal_keluar.strftime('%d/%m/%Y')}.",
            jenis="umum")
        db.session.add(notif)
        count_selesai += 1

    bookings_7hari = Booking.query.filter(
        Booking.status == "aktif",
        Booking.tanggal_keluar >= today,
        Booking.tanggal_keluar <= date(today.year, today.month, today.day + 7)
    ).all()
    for b in bookings_7hari:
        notif = Notification(user_id=b.user_id,
            pesan=f"Pengingat: masa sewa kamar {b.room.nomor_kamar} akan berakhir {b.tanggal_keluar.strftime('%d/%m/%Y')}. Segera perpanjang jika ingin lanjut.",
            jenis="umum")
        db.session.add(notif)
        count_notif += 1

    log_activity(current_user.id, "Auto-proses", f"{count_selesai} booking selesai, {count_notif} pengingat dikirim", "System")
    db.session.commit()
    flash(f"Proses otomatis selesai: {count_selesai} booking diakhiri, {count_notif} pengingat dikirim.", "success")
    return redirect(url_for("dashboard.admin"))


@dashboard_bp.route("/notifikasi/baca/<int:id>", methods=["POST"])
@login_required
def baca_notifikasi(id):
    n = Notification.query.get_or_404(id)
    if n.user_id != current_user.id:
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))
    n.dibaca = True
    db.session.commit()
    return redirect(url_for("dashboard.client"))


@dashboard_bp.route("/notifikasi/baca-semua", methods=["POST"])
@login_required
def baca_semua_notif():
    Notification.query.filter_by(user_id=current_user.id, dibaca=False).update({"dibaca": True})
    db.session.commit()
    flash("Semua notifikasi ditandai sudah dibaca.", "success")
    return redirect(url_for("dashboard.client"))
