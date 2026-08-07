from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from extensions import db
from models import Payment, Booking, Room
from helpers import admin_or_management, get_or_404, kos_room_ids, parse_amount, create_notification, wa_redirect, safe_commit

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/")
@login_required
def index():
    if current_user.role in ("admin", "management"):
        kos_id = session.get("kos_id")
        booking_id = request.args.get("booking_id", type=int)
        status = request.args.get("status")
        query = Payment.query

        if kos_id:
            room_ids = kos_room_ids(kos_id)
            booking_ids = [b.id for b in db.session.query(Booking.id).filter(Booking.room_id.in_(room_ids)).all()] if room_ids else []
            query = query.filter(Payment.booking_id.in_(booking_ids)) if booking_ids else query.filter(False)
        if booking_id:
            query = query.filter_by(booking_id=booking_id)
        if status:
            query = query.filter_by(status=status)

        payments = query.order_by(Payment.created_at.desc()).all()
        bookings_q = Booking.query.filter_by(status="aktif")
        if kos_id:
            room_ids = kos_room_ids(kos_id)
            bookings_q = bookings_q.filter(Booking.room_id.in_(room_ids)) if room_ids else bookings_q.filter(False)
        bookings = bookings_q.all()
        return render_template("payments/index.html", payments=payments, bookings=bookings)

    booking = Booking.query.filter_by(user_id=current_user.id, status="aktif").first()
    if not booking:
        flash("Anda belum memiliki kamar.", "warning")
        return redirect(url_for("dashboard.client"))
    payments = Payment.query.filter_by(booking_id=booking.id).order_by(Payment.created_at.desc()).all()
    return render_template("payments/index.html", payments=payments, booking=booking)


@payments_bp.route("/tambah", methods=["GET", "POST"])
@admin_or_management
def tambah():
    if request.method == "POST":
        booking_id = request.form.get("booking_id", type=int)
        jumlah, err = parse_amount(request.form.get("jumlah"))
        if err:
            flash(err, "danger")
            return render_template("payments/form.html", bookings=Booking.query.filter_by(status="aktif").all())

        booking = db.session.get(Booking, booking_id)
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
        try:
            safe_commit()
        except Exception:
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))

        create_notification(
            booking.user_id,
            f"Pembayaran Rp{jumlah:,.0f} untuk bulan {payment.bulan_dibayar_untuk} telah diterima.",
            jenis="pembayaran",
        )

        flash("Pembayaran berhasil dicatat.", "success")
        return redirect(url_for("payments.index"))

    return render_template("payments/form.html", bookings=Booking.query.filter_by(status="aktif").all())


@payments_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit(id):
    payment = get_or_404(Payment, id)

    if request.method == "POST":
        jumlah_val, err = parse_amount(request.form.get("jumlah"))
        if err:
            flash(err, "danger")
            return render_template("payments/form.html", payment=payment, bookings=[])
        payment.jumlah = jumlah_val

        payment.tanggal_bayar = datetime.strptime(request.form["tanggal_bayar"], "%Y-%m-%d").date() if request.form.get("tanggal_bayar") else date.today()
        payment.bulan_dibayar_untuk = request.form.get("bulan_dibayar_untuk")
        payment.metode_bayar = request.form.get("metode_bayar", "transfer")
        payment.status = request.form.get("status", "lunas")
        payment.catatan = request.form.get("catatan")
        try:
            safe_commit()
        except Exception:
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Pembayaran berhasil diperbarui.", "success")
        return redirect(url_for("payments.index"))

    return render_template("payments/form.html", payment=payment)


@payments_bp.route("/hapus/<int:id>", methods=["POST"])
@admin_or_management
def hapus(id):
    payment = get_or_404(Payment, id)
    db.session.delete(payment)
    try:
        safe_commit()
    except Exception:
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash("Pembayaran berhasil dihapus.", "success")
    return redirect(url_for("payments.index"))


@payments_bp.route("/resi/<int:payment_id>")
@admin_or_management
def kirim_resi(payment_id):
    payment = get_or_404(Payment, payment_id)
    booking = payment.booking
    if not booking.client.no_telepon:
        flash("Nomor telepon penghuni tidak tersedia.", "warning")
        return redirect(url_for("payments.index"))

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

    create_notification(
        payment.booking.user_id,
        f"Resi pembayaran Rp{payment.jumlah:,.0f} ({payment.bulan_dibayar_untuk}) dikirim via WA.",
        jenis="pembayaran",
        wa_sent=True,
    )

    return wa_redirect(booking.client.no_telepon, pesan)


@payments_bp.route("/notifikasi/<int:booking_id>")
@admin_or_management
def notifikasi_wa(booking_id):
    booking = get_or_404(Booking, booking_id)
    tagihan = booking.tagihan_bulan_ini

    pesan = f"Halo {booking.client.nama_lengkap}!"
    pesan += f"\n\nIni adalah pengingat pembayaran kos untuk kamar {booking.room.nomor_kamar}."
    pesan += f"\n\nTagihan bulan ini: Rp{booking.room.harga_per_bulan:,.0f}"
    pesan += f"\n\nSilakan transfer ke:\nBank BCA - 1234567890\nA/N: Pengelola Kos"
    pesan += f"\n\n*Jangan lupa kirim bukti transfer ya!*"

    create_notification(
        booking.user_id,
        f"Pengingat pembayaran dikirim via WA untuk kamar {booking.room.nomor_kamar}",
        jenis="pembayaran",
        wa_sent=True,
    )

    return wa_redirect(booking.client.no_telepon, pesan)
