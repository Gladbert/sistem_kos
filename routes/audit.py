from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models import RoomAudit, AuditItemResult, RoomItem, Booking, Notification
from helpers import admin_or_management, get_or_404, safe_commit

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


def _save_audit_items(audit, items):
    """Upsert AuditItemResult rows from form data."""
    for item in items:
        kondisi = request.form.get(f"kondisi_{item.id}", "baik")
        if kondisi not in ("baik", "rusak"):
            kondisi = "baik"
        db.session.add(AuditItemResult(
            audit_id=audit.id, item_id=item.id,
            kondisi=kondisi,
            catatan=request.form.get(f"catatan_{item.id}", "").strip(),
        ))


@audit_bp.route("/check-in/<int:booking_id>", methods=["GET", "POST"])
@login_required
def check_in(booking_id):
    booking = get_or_404(Booking, booking_id)
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

        _save_audit_items(audit, items)

        if not existing:
            db.session.add(Notification(user_id=booking.user_id, pesan=f"Audit check-in kamar {booking.room.nomor_kamar} selesai.", jenis="umum"))
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Audit check-in berhasil disimpan.", "success")
        return redirect(url_for("audit.detail", booking_id=booking_id))

    return render_template("audit/check_in.html", booking=booking, items=items, existing=existing)


@audit_bp.route("/check-out/<int:booking_id>", methods=["GET", "POST"])
@admin_or_management
def check_out(booking_id):
    booking = get_or_404(Booking, booking_id)
    existing = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_out").first()
    if existing:
        flash("Audit check-out sudah dilakukan.", "info")
        return redirect(url_for("audit.detail", booking_id=booking_id))

    check_in = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_in").first()
    if not check_in:
        flash("Audit check-in harus dilakukan terlebih dahulu sebelum check-out.", "warning")
        return redirect(url_for("audit.detail", booking_id=booking_id))
    items = RoomItem.query.filter_by(room_id=booking.room_id).order_by(RoomItem.nama).all()

    if request.method == "POST":
        audit = RoomAudit(booking_id=booking_id, tipe="check_out", created_by=current_user.id, catatan=request.form.get("catatan"))
        db.session.add(audit)
        db.session.flush()

        _save_audit_items(audit, items)

        db.session.add(Notification(user_id=booking.user_id, pesan=f"Audit check-out kamar {booking.room.nomor_kamar} selesai.", jenis="umum"))
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Audit check-out berhasil disimpan.", "success")
        return redirect(url_for("audit.detail", booking_id=booking_id))

    return render_template("audit/check_out.html", booking=booking, items=items, check_in=check_in)


@audit_bp.route("/<int:booking_id>")
@login_required
def detail(booking_id):
    booking = get_or_404(Booking, booking_id)
    if booking.user_id != current_user.id and current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    check_in = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_in").first()
    check_out = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_out").first()
    items = RoomItem.query.filter_by(room_id=booking.room_id).order_by(RoomItem.nama).all()
    return render_template("audit/detail.html", booking=booking, items=items, check_in=check_in, check_out=check_out)


@audit_bp.route("/edit/<int:audit_id>", methods=["GET", "POST"])
@admin_or_management
def edit(audit_id):
    audit = get_or_404(RoomAudit, audit_id)
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
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Audit berhasil diperbarui.", "success")
        return redirect(url_for("audit.detail", booking_id=booking.id))

    results = {r.item_id: r for r in AuditItemResult.query.filter_by(audit_id=audit.id).all()}
    return render_template("audit/edit.html", audit=audit, booking=booking, items=items, results=results)


@audit_bp.route("/export/<int:booking_id>")
@admin_or_management
def export(booking_id):
    booking = get_or_404(Booking, booking_id)
    check_in = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_in").first()
    check_out = RoomAudit.query.filter_by(booking_id=booking_id, tipe="check_out").first()

    format_type = request.args.get("format", "csv")

    if format_type == "json":
        ci_items = [
            {"item_id": r.item_id, "item_nama": r.item.nama, "kondisi": r.kondisi, "catatan": r.catatan}
            for r in check_in.items
        ] if check_in else []
        co_items = [
            {"item_id": r.item_id, "item_nama": r.item.nama, "kondisi": r.kondisi, "catatan": r.catatan}
            for r in check_out.items
        ] if check_out else []

        return jsonify({
            "booking_id": booking_id,
            "room": booking.room.nomor_kamar,
            "check_in": {
                "created_at": check_in.created_at.isoformat() if check_in else None,
                "created_by": check_in.created_by if check_in else None,
                "catatan": check_in.catatan if check_in else None,
                "items": ci_items,
            },
            "check_out": {
                "created_at": check_out.created_at.isoformat() if check_out else None,
                "created_by": check_out.created_by if check_out else None,
                "catatan": check_out.catatan if check_out else None,
                "items": co_items,
            },
        })

    lines = [f"Booking ID: {booking_id}", f"Kamar: {booking.room.nomor_kamar}", ""]
    for label, audit in (("CHECK_IN", check_in), ("CHECK_OUT", check_out)):
        lines.append(f"=== {label} ===")
        if audit:
            lines += [f"Tanggal: {audit.created_at}", f"Oleh: {audit.created_by}", f"Catatan: {audit.catatan or ''}", "ID Item,Nama Item,Kondisi,Catatan"]
            for item in audit.items:
                lines.append(f"{item.item_id},{item.item.nama},{item.kondisi},{item.catatan or ''}")
        else:
            lines.append("Tidak ada audit.")
        lines.append("")

    response = make_response("\n".join(lines))
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=audit_{booking_id}.csv"
    return response


@audit_bp.route("/delete/<int:audit_id>", methods=["GET", "POST"])
@admin_or_management
def delete(audit_id):
    audit = get_or_404(RoomAudit, audit_id)
    booking_id = audit.booking_id

    if request.method == "POST":
        AuditItemResult.query.filter_by(audit_id=audit_id).delete()
        db.session.delete(audit)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Audit berhasil dihapus.", "success")
        return redirect(url_for("audit.detail", booking_id=booking_id))

    return render_template(
        "audit/delete.html",
        audit=audit,
        booking=audit.booking,
        items=AuditItemResult.query.filter_by(audit_id=audit_id).all(),
    )
