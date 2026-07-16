from datetime import date
from flask import Blueprint, render_template, redirect, flash
from flask_login import login_required, current_user
from app import db
from models import User, Room, Booking, Payment, Expense, Notification, MaintenanceRequest

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

    total_penghuni = db.session.query(Booking.user_id).filter(
        Booking.status == "aktif"
    ).distinct().count()

    penghuni = User.query.join(Booking).filter(
        Booking.status == "aktif", User.role == "client"
    ).all()

    pemasukan_bulan_ini = db.session.query(db.func.sum(Payment.jumlah)).filter(
        Payment.status == "lunas",
        db.func.strftime("%Y-%m", Payment.tanggal_bayar) == date.today().strftime("%Y-%m")
    ).scalar() or 0

    pengeluaran_bulan_ini = db.session.query(db.func.sum(Expense.jumlah)).filter(
        db.func.strftime("%Y-%m", Expense.tanggal) == date.today().strftime("%Y-%m")
    ).scalar() or 0

    tagihan_belum_dibayar = 0
    for b in Booking.query.filter_by(status="aktif").all():
        if b.tagihan_bulan_ini:
            tagihan_belum_dibayar += 1

    pembayaran_terbaru = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    pengeluaran_terbaru = Expense.query.order_by(Expense.created_at.desc()).limit(5).all()
    permintaan_maintenance = MaintenanceRequest.query.filter(
        MaintenanceRequest.status.in_(["diajukan", "diproses"])
    ).order_by(MaintenanceRequest.created_at.desc()).limit(5).all()

    return render_template("dashboard/admin.html",
        total_kamar=total_kamar, kamar_terisi=kamar_terisi,
        kamar_tersedia=kamar_tersedia, total_penghuni=total_penghuni,
        penghuni=penghuni, pemasukan_bulan_ini=pemasukan_bulan_ini,
        pengeluaran_bulan_ini=pengeluaran_bulan_ini,
        tagihan_belum_dibayar=tagihan_belum_dibayar,
        pembayaran_terbaru=pembayaran_terbaru,
        pengeluaran_terbaru=pengeluaran_terbaru,
        permintaan_maintenance=permintaan_maintenance)


@dashboard_bp.route("/client")
@login_required
def client():
    booking = Booking.query.filter_by(user_id=current_user.id, status="aktif").first()
    riwayat = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    pembayaran = Payment.query.join(Booking).filter(Booking.user_id == current_user.id).order_by(Payment.created_at.desc()).all()
    notifikasi = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()

    return render_template("dashboard/client.html",
        booking=booking, riwayat=riwayat,
        pembayaran=pembayaran, notifikasi=notifikasi)
