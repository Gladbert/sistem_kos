from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Payment, Booking, Room
from helpers import admin_or_management, get_or_404, kos_room_ids, parse_amount, create_notification, wa_redirect, safe_commit
from sqlalchemy.orm import joinedload
from sqlalchemy import select

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20

    if current_user.role in ("admin", "management"):
        kos_id = session.get("kos_id")
        booking_id = request.args.get("booking_id", type=int)
        status = request.args.get("status")
        query = Payment.query

        if kos_id:
            room_ids = kos_room_ids(kos_id)
            if not room_ids:
                query = query.filter(False)
            else:
                # Use subquery instead of collecting IDs — single round trip
                sub = select(Booking.id).where(Booking.room_id.in_(room_ids)).subquery()
                query = query.filter(Payment.booking_id.in_(sub))
        if booking_id:
            query = query.filter_by(booking_id=booking_id)
        if status:
            query = query.filter_by(status=status)

        pagination = query.options(
            joinedload(Payment.booking).joinedload(Booking.client),
            joinedload(Payment.booking).joinedload(Booking.room),
        ).order_by(Payment.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        bookings_q = Booking.query.options(
            joinedload(Booking.client), joinedload(Booking.room)
        ).filter_by(status="aktif")
        if kos_id:
            room_ids = kos_room_ids(kos_id)
            bookings_q = bookings_q.filter(Booking.room_id.in_(room_ids)) if room_ids else bookings_q.filter(False)
        bookings = bookings_q.all()
        return render_template("payments/index.html", pagination=pagination, payments=pagination.items, bookings=bookings)

    booking = Booking.query.filter_by(user_id=current_user.id).filter(Booking.status.in_(["aktif", "pending"])).first()
    if not booking:
        flash("Anda belum memiliki kamar.", "warning")
        return redirect(url_for("dashboard.client"))
    pagination = Payment.query.filter_by(booking_id=booking.id).order_by(Payment.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("payments/index.html", pagination=pagination, payments=pagination.items, booking=booking)


@payments_bp.route("/tambah", methods=["GET", "POST"])
@admin_or_management
def tambah():
    if request.method == "POST":
        booking_id = request.form.get("booking_id", type=int)
        jumlah, err = parse_amount(request.form.get("jumlah"))
        if err:
            flash(err, "danger")
            return render_template("payments/form.html", bookings=_scoped_bookings())

        booking = db.session.get(Booking, booking_id)
        if not booking:
            flash("Booking tidak ditemukan.", "danger")
            return redirect(url_for("payments.index"))

        bulan = request.form.get("bulan_dibayar_untuk", "").strip()
        if not bulan:
            bulan = date.today().strftime("%Y-%m")

        payment = Payment(
            booking_id=booking_id,
            jumlah=jumlah,
            tanggal_bayar=date.today(),
            bulan_dibayar_untuk=bulan,
            metode_bayar=request.form.get("metode_bayar", "transfer"),
            status="lunas",
            catatan=request.form.get("catatan"),
        )
        db.session.add(payment)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))

        create_notification(
            booking.user_id,
            f"Pembayaran Rp{jumlah:,.0f} untuk bulan {bulan} telah diterima.",
            jenis="pembayaran",
        )

        flash("Pembayaran berhasil dicatat.", "success")
        return redirect(url_for("payments.index"))

    return render_template("payments/form.html", bookings=_scoped_bookings())


def _scoped_bookings():
    """Active bookings filtered by current kos, with client+room eager loaded."""
    kos_id = session.get("kos_id")
    q = Booking.query.options(
        joinedload(Booking.client), joinedload(Booking.room)
    ).filter_by(status="aktif")
    if kos_id:
        room_ids = kos_room_ids(kos_id)
        q = q.filter(Booking.room_id.in_(room_ids)) if room_ids else q.filter(False)
    return q.all()


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
            current_app.logger.exception("Database operation failed")
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
        current_app.logger.exception("Database operation failed")
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
