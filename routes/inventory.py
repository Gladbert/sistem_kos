from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Room, RoomItem, ActivityLog

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventaris")


def log(user_id, tindakan, deskripsi):
    db.session.add(ActivityLog(user_id=user_id, tindakan=tindakan, deskripsi=deskripsi, model="RoomItem"))
    db.session.commit()


@inventory_bp.route("/")
@login_required
def index():
    if current_user.role not in ("admin", "management"):
        return redirect(url_for("dashboard.index"))
    rooms = Room.query.order_by(Room.nomor_kamar).all()
    return render_template("inventory/index.html", rooms=rooms)


@inventory_bp.route("/kamar/<int:room_id>")
@login_required
def room_items(room_id):
    if current_user.role not in ("admin", "management"):
        return redirect(url_for("dashboard.index"))
    room = Room.query.get_or_404(room_id)
    items = RoomItem.query.filter_by(room_id=room_id).order_by(RoomItem.nama).all()
    return render_template("inventory/items.html", room=room, items=items)


@inventory_bp.route("/tambah/<int:room_id>", methods=["GET", "POST"])
@login_required
def add_item(room_id):
    if current_user.role not in ("admin", "management"):
        return redirect(url_for("dashboard.index"))
    room = Room.query.get_or_404(room_id)
    if request.method == "POST":
        i = RoomItem(
            room_id=room_id, nama=request.form["nama"],
            jumlah=int(request.form.get("jumlah", 1)),
            kondisi=request.form.get("kondisi", "baik"),
            catatan=request.form.get("catatan", "")
        )
        db.session.add(i)
        log(current_user.id, "Tambah barang", f"{request.form['nama']} di {room.nomor_kamar}")
        db.session.commit()
        flash("Barang ditambahkan.", "success")
        return redirect(url_for("inventory.room_items", room_id=room_id))
    return render_template("inventory/form.html", room=room)


@inventory_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_item(id):
    if current_user.role not in ("admin", "management"):
        return redirect(url_for("dashboard.index"))
    i = RoomItem.query.get_or_404(id)
    if request.method == "POST":
        i.nama = request.form["nama"]
        i.jumlah = int(request.form.get("jumlah", 1))
        i.kondisi = request.form.get("kondisi", "baik")
        i.catatan = request.form.get("catatan", "")
        log(current_user.id, "Edit barang", f"{i.nama} di {i.room.nomor_kamar}")
        db.session.commit()
        flash("Barang diperbarui.", "success")
        return redirect(url_for("inventory.room_items", room_id=i.room_id))
    return render_template("inventory/form.html", item=i, room=i.room)


@inventory_bp.route("/hapus/<int:id>")
@login_required
def delete_item(id):
    if current_user.role not in ("admin", "management"):
        return redirect(url_for("dashboard.index"))
    i = RoomItem.query.get_or_404(id)
    room_id = i.room_id
    log(current_user.id, "Hapus barang", f"{i.nama} dari {i.room.nomor_kamar}")
    db.session.delete(i)
    db.session.commit()
    flash("Barang dihapus.", "success")
    return redirect(url_for("inventory.room_items", room_id=room_id))
