from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import RoomAudit, AuditItemResult, RoomItem, Booking, Notification

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/check-in/<int:booking_id>", methods=["GET", "POST"])
@login_required
def check_in(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    existing = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_in").first()
    if existing and current_user.role not in ("admin", "management"):
        flash("Audit check-in sudah dilakukan.", "info")
        return redirect(url_for("audit.detail", booking_id=booking_id))

    items = RoomItem.query.filter_by(room_id=booking.room_id).order_by(RoomItem.nama).all()

    if request.method == "POST":
        audit = existing or RoomAudit(booking_id=booking_id, tipe="check_in", created_by=current_user.id)
        if not existing:
            db.session.add(audit)
            db.session.flush()

        AuditItemResult.query.filter_by(audit_id=audit.id).delete()
        for item in items:
            kondisi = request.form.get(f"kondisi_{item.id}", "baik")
            catatan = request.form.get(f"catatan_{item.id}", "").strip()
            db.session.add(AuditItemResult(audit_id=audit.id, item_id=item.id, kondisi=kondisi, catatan=catatan))

        if not existing:
            notif = Notification(user_id=booking.user_id, pesan=f"Audit check-in kamar {booking.room.nomor_kamar} selesai.", jenis="umum")
            db.session.add(notif)
        db.session.commit()
        flash("Audit check-in berhasil disimpan.", "success")
        return redirect(url_for("audit.detail", booking_id=booking_id))

    return render_template("audit/check_in.html", booking=booking, items=items, existing=existing)


@audit_bp.route("/check-out/<int:booking_id>", methods=["GET", "POST"])
@login_required
def check_out(booking_id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    booking = Booking.query.get_or_404(booking_id)
    existing = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_out").first()
    if existing:
        flash("Audit check-out sudah dilakukan.", "info")
        return redirect(url_for("audit.detail", booking_id=booking_id))

    check_in = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_in").first()
    items = RoomItem.query.filter_by(room_id=booking.room_id).order_by(RoomItem.nama).all()

    if request.method == "POST":
        audit = RoomAudit(booking_id=booking_id, tipe="check_out", created_by=current_user.id, catatan=request.form.get("catatan"))
        db.session.add(audit)
        db.session.flush()

        for item in items:
            kondisi = request.form.get(f"kondisi_{item.id}", "baik")
            catatan = request.form.get(f"catatan_{item.id}", "").strip()
            db.session.add(AuditItemResult(audit_id=audit.id, item_id=item.id, kondisi=kondisi, catatan=catatan))

        notif = Notification(user_id=booking.user_id, pesan=f"Audit check-out kamar {booking.room.nomor_kamar} selesai.", jenis="umum")
        db.session.add(notif)
        db.session.commit()
        flash("Audit check-out berhasil disimpan.", "success")
        return redirect(url_for("audit.detail", booking_id=booking_id))

    return render_template("audit/check_out.html", booking=booking, items=items, check_in=check_in)


@audit_bp.route("/<int:booking_id>")
@login_required
def detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    check_in = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_in").first()
    check_out = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_out").first()
    items = RoomItem.query.filter_by(room_id=booking.room_id).order_by(RoomItem.nama).all()
    return render_template("audit/detail.html", booking=booking, items=items, check_in=check_in, check_out=check_out)


@audit_bp.route("/edit/<int:audit_id>", methods=["GET", "POST"])
@login_required
def edit(audit_id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    audit = RoomAudit.query.get_or_404(audit_id)
    booking = audit.booking
    items = RoomItem.query.filter_by(room_id=booking.room_id).order_by(RoomItem.nama).all()

    if request.method == "POST":
        audit.catatan = request.form.get("catatan", "")
        existing_ids = {r.item_id: r for r in AuditItemResult.query.filter_by(audit_id=audit.id).all()}
        for item in items:
            kondisi = request.form.get(f"kondisi_{item.id}", "baik")
            catatan = request.form.get(f"catatan_{item.id}", "").strip()
            if item.id in existing_ids:
                r = existing_ids[item.id]
                r.kondisi = kondisi
                r.catatan = catatan
            else:
                db.session.add(AuditItemResult(audit_id=audit.id, item_id=item.id, kondisi=kondisi, catatan=catatan))
        db.session.commit()
        flash("Audit berhasil diperbarui.", "success")
        return redirect(url_for("audit.detail", booking_id=booking.id))

    results = {r.item_id: r for r in AuditItemResult.query.filter_by(audit_id=audit.id).all()}
    return render_template("audit/edit.html", audit=audit, booking=booking, items=items, results=results)
