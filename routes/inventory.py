from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import current_user
from extensions import db
from models import Room, RoomItem
from helpers import log_activity, admin_or_management, get_or_404, kos_rooms, safe_commit

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventaris")


@inventory_bp.route("/")
@admin_or_management
def index():
    rooms = kos_rooms()
    # Sort by nomor_kamar
    rooms.sort(key=lambda r: r.nomor_kamar)
    return render_template("inventory/index.html", rooms=rooms)


@inventory_bp.route("/kamar/<int:room_id>")
@admin_or_management
def room_items(room_id):
    room = get_or_404(Room, room_id)
    items = RoomItem.query.filter_by(room_id=room_id).order_by(RoomItem.nama).all()
    return render_template("inventory/items.html", room=room, items=items)


@inventory_bp.route("/tambah/<int:room_id>", methods=["GET", "POST"])
@admin_or_management
def add_item(room_id):
    room = get_or_404(Room, room_id)
    if request.method == "POST":
        i = RoomItem(
            room_id=room_id,
            nama=request.form["nama"],
            jumlah=int(request.form.get("jumlah", 1)),
            kondisi=request.form.get("kondisi", "baik"),
            catatan=request.form.get("catatan", ""),
        )
        db.session.add(i)
        log_activity(current_user.id, "Tambah barang", f"{request.form['nama']} di {room.nomor_kamar}", "RoomItem")
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Barang ditambahkan.", "success")
        return redirect(url_for("inventory.room_items", room_id=room_id))
    return render_template("inventory/form.html", room=room)


@inventory_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit_item(id):
    i = get_or_404(RoomItem, id)
    if request.method == "POST":
        i.nama = request.form["nama"]
        i.jumlah = int(request.form.get("jumlah", 1))
        i.kondisi = request.form.get("kondisi", "baik")
        i.catatan = request.form.get("catatan", "")
        log_activity(current_user.id, "Edit barang", f"{i.nama} di {i.room.nomor_kamar}", "RoomItem")
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Barang diperbarui.", "success")
        return redirect(url_for("inventory.room_items", room_id=i.room_id))
    return render_template("inventory/form.html", item=i, room=i.room)


@inventory_bp.route("/hapus/<int:id>", methods=["POST"])
@admin_or_management
def delete_item(id):
    i = get_or_404(RoomItem, id)
    room_id = i.room_id
    log_activity(current_user.id, "Hapus barang", f"{i.nama} dari {i.room.nomor_kamar}", "RoomItem")
    db.session.delete(i)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash("Barang dihapus.", "success")
    return redirect(url_for("inventory.room_items", room_id=room_id))
