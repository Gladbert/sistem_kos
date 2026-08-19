from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, flash, url_for, request, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, Room, Booking, Payment, Expense, Notification, MaintenanceRequest, Complaint, Kos
from helpers import log_activity, admin_or_management, get_or_404, kos_room_ids, create_notification, kos_expense_query, safe_commit, notify_pengelola
from sqlalchemy.orm import joinedload, subqueryload

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
@login_required
def index():
    # Check per-kos role first, fall back to global role
    kos_role = None
    kos_id = session.get("kos_id")
    if kos_id:
        from models import UserKos
        uk = UserKos.query.filter_by(user_id=current_user.id, kos_id=kos_id).first()
        if uk:
            kos_role = uk.role
    
    effective_role = kos_role or current_user.role
    
    if effective_role in ("admin", "management"):
        return redirect(url_for("dashboard.admin"))
    return redirect(url_for("dashboard.client"))

@dashboard_bp.route("/admin")
@admin_or_management
def admin():
    kos_id = session.get("kos_id")
    room_ids = kos_room_ids(kos_id) if kos_id else [r.id for r in db.session.query(Room.id).all()]

    total_kamar = len(room_ids)
    room_q = Room.query.filter(Room.id.in_(room_ids)) if room_ids else Room.query.filter(False)
    kamar_terisi_count = room_q.filter_by(status="terisi").count()
    kamar_tersedia = room_q.filter_by(status="tersedia").count()
    kamar_maintenance = room_q.filter_by(status="maintenance").count()

    # Eager load relationships to avoid N+1 in template loops
    active_bookings = Booking.query.options(
        joinedload(Booking.room), joinedload(Booking.client), subqueryload(Booking.audits)
    ).filter(Booking.room_id.in_(room_ids), Booking.status == "aktif").all() if room_ids else []
    kamar_pending = Booking.query.filter(Booking.room_id.in_(room_ids), Booking.status == "pending").count() if room_ids else 0
    total_penghuni = len(set(b.user_id for b in active_bookings))

    # Precompute penghuni from already-loaded relationships
    penghuni = [{
        "id": b.client.id, "nama_lengkap": b.client.nama_lengkap, "username": b.client.username,
        "no_telepon": b.client.no_telepon, "is_active": b.client.is_active,
        "nomor_kamar": b.room.nomor_kamar, "kamar_id": b.room_id,
    } for b in active_bookings]

    booking_ids = [b.id for b in active_bookings]
    bulan_ini = date.today().strftime("%Y-%m")

    pemasukan_bulan_ini = db.session.query(db.func.sum(Payment.jumlah)).filter(
        Payment.status == "lunas",
        Payment.booking_id.in_(booking_ids) if booking_ids else False,
        db.func.to_char(Payment.tanggal_bayar, 'YYYY-MM') == bulan_ini,
    ).scalar() or 0

    pengeluaran_bulan_ini = kos_expense_query(
        db.session.query(db.func.sum(Expense.jumlah)).filter(
            db.func.to_char(Expense.tanggal, 'YYYY-MM') == bulan_ini,
        )
    ).scalar() or 0

    # Batch: check all unpaid bookings at once
    tagihan_belum_dibayar = 0
    unpaid_bookings = []
    if booking_ids:
        paid_this_month = set(
            r[0] for r in db.session.query(Payment.booking_id).filter(
                Payment.booking_id.in_(booking_ids),
                Payment.bulan_dibayar_untuk == bulan_ini,
                Payment.status == "lunas"
            ).all()
        )
        for b in active_bookings:
            if b.id not in paid_this_month:
                tagihan_belum_dibayar += 1
                unpaid_bookings.append(b)

    booking_pending = Booking.query.options(
        joinedload(Booking.room), joinedload(Booking.client)
    ).filter(Booking.room_id.in_(room_ids), Booking.status == "pending").order_by(Booking.created_at.asc()).all() if room_ids else []

    total_tagihan = len(active_bookings)
    # Collection rate: paid / (paid + unpaid) per-booking, capped at 100
    if total_tagihan > 0:
        paid_count = total_tagihan - tagihan_belum_dibayar
        collection_rate = min(round((paid_count / total_tagihan * 100)), 100)
    else:
        collection_rate = 0
    occupancy_rate = round((kamar_terisi_count / total_kamar * 100) if total_kamar > 0 else 0)

    tipe_kamar = db.session.query(Room.tipe, db.func.count(Room.id)).filter(Room.id.in_(room_ids)).group_by(Room.tipe).all() if room_ids else []

    # Batch: 6-month income in one query
    today = date.today()
    six_months_ago = (today.replace(day=1) - timedelta(days=155)).replace(day=1)
    pemasukan_6bulan = []
    if booking_ids:
        rows = db.session.query(
            db.func.to_char(Payment.tanggal_bayar, 'YYYY-MM').label('bulan'),
            db.func.sum(Payment.jumlah).label('total')
        ).filter(
            Payment.status == "lunas",
            Payment.booking_id.in_(booking_ids),
            Payment.tanggal_bayar >= six_months_ago,
        ).group_by('bulan').all()
        row_map = {r.bulan: float(r.total) for r in rows}
    else:
        row_map = {}

    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        bulan_str = f"{y:04d}-{m:02d}"
        pemasukan_6bulan.append({"bulan": bulan_str, "total": row_map.get(bulan_str, 0)})

    pembayaran_terbaru = Payment.query.options(
        joinedload(Payment.booking).joinedload(Booking.client)
    ).filter(Payment.booking_id.in_(booking_ids)).order_by(Payment.created_at.desc()).limit(5).all() if booking_ids else []
    pengeluaran_terbaru = kos_expense_query(Expense.query).order_by(Expense.created_at.desc()).limit(5).all()

    permintaan_maintenance = MaintenanceRequest.query.options(
        joinedload(MaintenanceRequest.room)
    ).filter(
        MaintenanceRequest.room_id.in_(room_ids),
        MaintenanceRequest.status.in_(["diajukan", "diproses"]),
    ).order_by(MaintenanceRequest.created_at.desc()).limit(5).all() if room_ids else []

    komplain_baru_q = Complaint.query.filter(Complaint.status == "diajukan")
    if kos_id:
        komplain_baru_q = komplain_baru_q.filter(Complaint.kos_id == kos_id)
    komplain_baru = komplain_baru_q.count()

    # Bookings awaiting check-out audit before the room can be reused
    pending_checkout = [
        b for b in Booking.query.options(
            joinedload(Booking.room), joinedload(Booking.client)
        ).filter_by(status="menunggu_checkout").all()
        if b.room and b.client
    ]
    if room_ids:
        pending_checkout = [b for b in pending_checkout if b.room_id in room_ids]

    return render_template("dashboard/admin.html",
        total_kamar=total_kamar, kamar_terisi=kamar_terisi_count,
        kamar_tersedia=kamar_tersedia, total_penghuni=total_penghuni,
        penghuni=penghuni, pemasukan_bulan_ini=pemasukan_bulan_ini,
        pengeluaran_bulan_ini=pengeluaran_bulan_ini,
        tagihan_belum_dibayar=tagihan_belum_dibayar,
        pembayaran_terbaru=pembayaran_terbaru, pengeluaran_terbaru=pengeluaran_terbaru,
        permintaan_maintenance=permintaan_maintenance, komplain_baru=komplain_baru,
        kamar_pending=kamar_pending, kamar_maintenance=kamar_maintenance,
        booking_pending=booking_pending, unpaid_bookings=unpaid_bookings,
        collection_rate=collection_rate, occupancy_rate=occupancy_rate,
        tipe_kamar=tipe_kamar, pemasukan_6bulan=pemasukan_6bulan,
        booking_audit=active_bookings[:5], pending_checkout=pending_checkout)

@dashboard_bp.route("/client")
@login_required
def client():
    booking_aktif = Booking.query.filter_by(user_id=current_user.id, status="aktif").first()
    booking_pending = Booking.query.filter_by(user_id=current_user.id, status="pending").first()
    booking = booking_aktif or booking_pending
    riwayat = Booking.query.options(joinedload(Booking.room)).filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    pembayaran = Payment.query.join(Booking).filter(Booking.user_id == current_user.id).order_by(Payment.created_at.desc()).all()
    notifikasi = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    notif_belum_dibaca = Notification.query.filter_by(user_id=current_user.id, dibaca=False).count()

    # Check if check-in audit is required (only if the guest performs it)
    needs_checkin_audit = False
    has_checkin_audit = False
    guest_can_audit = False
    if booking_aktif:
        from models import RoomAudit
        kos = booking_aktif.room.kos
        guest_can_audit = (kos.audit_role if kos else "client") == "client"
        has_checkin_audit = RoomAudit.query.filter_by(
            booking_id=booking_aktif.id, tipe="check_in"
        ).first() is not None
        needs_checkin_audit = guest_can_audit and not has_checkin_audit

    return render_template("dashboard/client.html",
        booking=booking, booking_aktif=booking_aktif, booking_pending=booking_pending,
        riwayat=riwayat, pembayaran=pembayaran,
        notifikasi=notifikasi, notif_belum_dibaca=notif_belum_dibaca,
        needs_checkin_audit=needs_checkin_audit, has_checkin_audit=has_checkin_audit,
        guest_can_audit=guest_can_audit,
        date_today=date.today())

@dashboard_bp.route("/booking/<int:id>/approve", methods=["POST"])
@admin_or_management
def approve_booking(id):
    booking = get_or_404(Booking, id)
    if booking.status != "pending":
        flash("Booking sudah diproses.", "warning")
        return redirect(url_for("dashboard.admin"))
    # Guard against double-occupancy: the room may have been filled meanwhile.
    if not booking.room or booking.room.status != "tersedia":
        flash("Kamar sudah terisi oleh penghuni lain. Tolak permintaan ini.", "warning")
        return redirect(url_for("dashboard.admin"))
    booking.status = "aktif"
    booking.room.status = "terisi"
    if not booking.tanggal_keluar and booking.room.kos:
        booking.tanggal_keluar = booking.room.kos.default_keluar_date(booking.tanggal_masuk or date.today())
    log_activity(current_user.id, "Setujui booking", f"Kamar {booking.room.nomor_kamar} - {booking.client.nama_lengkap}", "Booking")
    create_notification(
        booking.user_id,
        f"Permintaan sewa kamar {booking.room.nomor_kamar} telah DISETUJUI! Silakan check-in.",
    )
    flash(f"Booking kamar {booking.room.nomor_kamar} oleh {booking.client.nama_lengkap} disetujui.", "success")
    return redirect(url_for("dashboard.admin"))

@dashboard_bp.route("/booking/<int:id>/tolak", methods=["POST"])
@admin_or_management
def tolak_booking(id):
    booking = get_or_404(Booking, id)
    if booking.status != "pending":
        flash("Booking sudah diproses.", "warning")
        return redirect(url_for("dashboard.admin"))
    room_no = booking.room.nomor_kamar
    client_name = booking.client.nama_lengkap
    log_activity(current_user.id, "Tolak booking", f"Kamar {room_no} - {client_name}", "Booking")
    create_notification(
        booking.user_id,
        f"Permintaan sewa kamar {room_no} telah DITOLAK. Silakan hubungi pengelola untuk detail.",
    )
    db.session.delete(booking)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed to reject booking %s", id)
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash(f"Booking kamar {room_no} oleh {client_name} ditolak.", "info")
    return redirect(url_for("dashboard.admin"))

@dashboard_bp.route("/auto-proses", methods=["POST"])
@admin_or_management
def auto_proses():
    today = date.today()
    count_selesai = 0
    count_menunggu = 0
    count_notif = 0
    from models import RoomAudit

    # Lease ended: only finalize if a check-out audit exists (audit-before-reuse).
    # Otherwise hold the room until the audit is done so condition is recorded.
    for b in Booking.query.filter(Booking.status == "aktif", Booking.tanggal_keluar < today).all():
        has_co = RoomAudit.query.filter_by(booking_id=b.id, tipe="check_out").first() is not None
        if has_co:
            b.status = "selesai"
            # free the room only if no other active booking occupies it (protects legacy double-booking data)
            if b.room and b.room.status == "terisi":
                other = Booking.query.filter(
                    Booking.room_id == b.room_id, Booking.status == "aktif",
                    Booking.id != b.id).first()
                if not other:
                    b.room.status = "tersedia"
            db.session.add(Notification(user_id=b.user_id,
                pesan=f"Masa sewa kamar {b.room.nomor_kamar} telah berakhir per {b.tanggal_keluar.strftime('%d/%m/%Y')}.",
                jenis="umum"))
            if b.deposit and b.deposit > 0 and b.client and b.room:
                notify_pengelola(b.room.kos_id,
                    f"Kembalikan deposit Rp{b.deposit:,.0f} ke {b.client.nama_lengkap} (kamar {b.room.nomor_kamar}).", "deposit")
            count_selesai += 1
        else:
            b.status = "menunggu_checkout"
            notify_pengelola(b.room.kos_id if b.room else None,
                f"Kamar {b.room.nomor_kamar} ({b.client.nama_lengkap}) menunggu AUDIT CHECK-OUT sebelum kamar dipakai ulang.", "audit")
            count_menunggu += 1

    for b in Booking.query.filter(Booking.status == "aktif", Booking.tanggal_keluar >= today,
                                   Booking.tanggal_keluar <= date(today.year, today.month, today.day + 7)).all():
        db.session.add(Notification(user_id=b.user_id,
            pesan=f"Pengingat: masa sewa kamar {b.room.nomor_kamar} akan berakhir {b.tanggal_keluar.strftime('%d/%m/%Y')}. Segera perpanjang jika ingin lanjut.",
            jenis="umum"))
        count_notif += 1

    log_activity(current_user.id, "Auto-proses", f"{count_selesai} selesai, {count_menunggu} menunggu audit, {count_notif} pengingat dikirim", "System")
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed auto-proses")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash(f"Proses otomatis selesai: {count_selesai} booking diakhiri, {count_menunggu} menunggu audit check-out, {count_notif} pengingat dikirim.", "success")
    return redirect(url_for("dashboard.admin"))

@dashboard_bp.route("/notifikasi/baca/<int:id>", methods=["POST"])
@login_required
def baca_notifikasi(id):
    n = get_or_404(Notification, id)
    if n.user_id != current_user.id:
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))
    n.dibaca = True
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed to mark notification read")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    return redirect(url_for("dashboard.client"))

@dashboard_bp.route("/notifikasi/baca-semua", methods=["POST"])
@login_required
def baca_semua_notif():
    Notification.query.filter_by(user_id=current_user.id, dibaca=False).update({"dibaca": True})
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed to mark all notifications read")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash("Semua notifikasi ditandai sudah dibaca.", "success")
    return redirect(url_for("dashboard.client"))
