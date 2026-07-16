from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Payment, Booking, Notification

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/")
@login_required
def index():
    if current_user.role in ("admin", "management"):
        booking_id = request.args.get("booking_id", type=int)
        status = request.args.get("status")
        query = Payment.query

        if booking_id:
            query = query.filter_by(booking_id=booking_id)
        if status:
            query = query.filter_by(status=status)

        payments = query.order_by(Payment.created_at.desc()).all()
        bookings = Booking.query.filter_by(status="aktif").all()
        return render_template("payments/index.html", payments=payments, bookings=bookings)

    booking = Booking.query.filter_by(user_id=current_user.id, status="aktif").first()
    if not booking:
        flash("Anda belum memiliki kamar.", "warning")
        return redirect(url_for("dashboard.client"))
    payments = Payment.query.filter_by(booking_id=booking.id).order_by(Payment.created_at.desc()).all()
    return render_template("payments/index.html", payments=payments, booking=booking)


@payments_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        booking_id = request.form.get("booking_id", type=int)
        try:
            jumlah = float(request.form.get("jumlah", 0))
        except ValueError:
            flash("Jumlah harus angka.", "danger")
            bookings = Booking.query.filter_by(status="aktif").all()
            return render_template("payments/form.html", bookings=bookings)

        if jumlah <= 0:
            flash("Jumlah harus lebih dari 0.", "danger")
            bookings = Booking.query.filter_by(status="aktif").all()
            return render_template("payments/form.html", bookings=bookings)

        booking = Booking.query.get(booking_id)
        if not booking:
            flash("Booking tidak ditemukan.", "danger")
            return redirect(url_for("payments.index"))

        payment = Payment(
            booking_id=booking_id,
            jumlah=jumlah,
            tanggal_bayar=date.today(),
            bulan_dibayar_untuk=request.form.get("bulan_dibayar_untuk", date.today().strftime("%Y-%m")),
            metode_bayar=request.form.get("metode_bayar", "transfer"),
            status="lunas",
            catatan=request.form.get("catatan"),
        )
        db.session.add(payment)
        db.session.commit()

        notif = Notification(
            user_id=booking.user_id,
            pesan=f"Pembayaran Rp{jumlah:,.0f} untuk bulan {payment.bulan_dibayar_untuk} telah diterima.",
            jenis="pembayaran",
        )
        db.session.add(notif)
        db.session.commit()

        flash("Pembayaran berhasil dicatat.", "success")
        return redirect(url_for("payments.index"))

    bookings = Booking.query.filter_by(status="aktif").all()
    return render_template("payments/form.html", bookings=bookings)


@payments_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    payment = Payment.query.get_or_404(id)

    if request.method == "POST":
        try:
            payment.jumlah = float(request.form.get("jumlah", 0))
        except ValueError:
            flash("Jumlah harus angka.", "danger")
            return render_template("payments/form.html", payment=payment, bookings=[])

        payment.tanggal_bayar = datetime.strptime(request.form["tanggal_bayar"], "%Y-%m-%d").date() if request.form.get("tanggal_bayar") else date.today()
        payment.bulan_dibayar_untuk = request.form.get("bulan_dibayar_untuk")
        payment.metode_bayar = request.form.get("metode_bayar", "transfer")
        payment.status = request.form.get("status", "lunas")
        payment.catatan = request.form.get("catatan")
        db.session.commit()
        flash("Pembayaran berhasil diperbarui.", "success")
        return redirect(url_for("payments.index"))

    return render_template("payments/form.html", payment=payment)


@payments_bp.route("/hapus/<int:id>", methods=["POST"])
@login_required
def hapus(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    payment = Payment.query.get_or_404(id)
    db.session.delete(payment)
    db.session.commit()
    flash("Pembayaran berhasil dihapus.", "success")
    return redirect(url_for("payments.index"))


@payments_bp.route("/resi/<int:payment_id>")
@login_required
def kirim_resi(payment_id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking
    if not booking.client.no_telepon:
        flash("Nomor telepon penghuni tidak tersedia.", "warning")
        return redirect(url_for("payments.index"))

    import urllib.parse
    pesan = f"Halo {booking.client.nama_lengkap}!"
    pesan += f"\n\nTerima kasih atas pembayaran kos Anda."
    pesan += f"\n\n*── RESI PEMBAYARAN ──*"
    pesan += f"\nKamar: {booking.room.nomor_kamar}"
    pesan += f"\nJumlah: Rp{payment.jumlah:,.0f}"
    pesan += f"\nBulan: {payment.bulan_dibayar_untuk}"
    pesan += f"\nTanggal Bayar: {payment.tanggal_bayar.strftime('%d/%m/%Y')}"
    pesan += f"\nMetode: {payment.metode_bayar.title()}"
    pesan += f"\nStatus: LUNAS"
    if payment.catatan:
        pesan += f"\nCatatan: {payment.catatan}"
    harga = booking.room.harga_per_bulan
    if payment.jumlah < harga:
        sisa = harga - payment.jumlah
        pesan += f"\n\n*Sisa tagihan bulan ini: Rp{sisa:,.0f}*"
    pesan += "\n\nTerima kasih telah membayar tepat waktu."

    notif = Notification(
        user_id=payment.booking.user_id,
        pesan=f"Resi pembayaran Rp{payment.jumlah:,.0f} ({payment.bulan_dibayar_untuk}) dikirim via WA.",
        jenis="pembayaran",
        wa_sent=True,
    )
    db.session.add(notif)
    db.session.commit()

    wa_url = f"https://wa.me/{booking.client.no_telepon}?text={urllib.parse.quote(pesan)}"
    return redirect(wa_url)


@payments_bp.route("/notifikasi/<int:booking_id>")
@login_required
def notifikasi_wa(booking_id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    booking = Booking.query.get_or_404(booking_id)
    tagihan = booking.tagihan_bulan_ini

    pesan = f"Halo {booking.client.nama_lengkap}!"
    pesan += f"\n\nIni adalah pengingat pembayaran kos untuk kamar {booking.room.nomor_kamar}."
    pesan += f"\n\nTagihan bulan ini: Rp{booking.room.harga_per_bulan:,.0f}"
    pesan += f"\n\nSilakan transfer ke:\nBank BCA - 1234567890\nA/N: Pengelola Kos"
    pesan += f"\n\n*Jangan lupa kirim bukti transfer ya!*"

    notif = Notification(
        user_id=booking.user_id,
        pesan=f"Pengingat pembayaran dikirim via WA untuk kamar {booking.room.nomor_kamar}",
        jenis="pembayaran",
        wa_sent=True,
    )
    db.session.add(notif)
    db.session.commit()

    import urllib.parse
    wa_url = f"https://wa.me/{booking.client.no_telepon}?text={urllib.parse.quote(pesan)}"
    return redirect(wa_url)
