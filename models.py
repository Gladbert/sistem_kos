from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="client")
    nama_lengkap = db.Column(db.String(150), nullable=False)
    no_telepon = db.Column(db.String(20))
    alamat = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="client", lazy="dynamic")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    nomor_kamar = db.Column(db.String(10), unique=True, nullable=False)
    lantai = db.Column(db.Integer, default=1)
    tipe = db.Column(db.String(50), default="Reguler")
    harga_per_bulan = db.Column(db.Float, nullable=False)
    ukuran = db.Column(db.String(50))
    fasilitas = db.Column(db.Text)
    status = db.Column(db.String(20), default="tersedia")
    deskripsi = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="room", lazy="dynamic")
    maintenance_requests = db.relationship("MaintenanceRequest", backref="room", lazy="dynamic")

    @property
    def booking_aktif(self):
        return Booking.query.filter_by(room_id=self.id, status="aktif").first()


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    tanggal_masuk = db.Column(db.Date, nullable=False)
    tanggal_keluar = db.Column(db.Date)
    status = db.Column(db.String(20), default="aktif")
    deposit = db.Column(db.Float, default=0)
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship("Payment", backref="booking", lazy="dynamic")

    @property
    def durasi_bulan(self):
        if self.tanggal_masuk and self.tanggal_keluar:
            delta = (self.tanggal_keluar - self.tanggal_masuk).days
            return max(1, round(delta / 30))
        return 1

    @property
    def tagihan_bulan_ini(self):
        bulan_ini = date.today().strftime("%Y-%m")
        sudah_bayar = Payment.query.filter(
            Payment.booking_id == self.id,
            Payment.bulan_dibayar_untuk == bulan_ini,
            Payment.status == "lunas"
        ).first()
        return sudah_bayar is None


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    tanggal_bayar = db.Column(db.Date, default=date.today)
    bulan_dibayar_untuk = db.Column(db.String(20))
    metode_bayar = db.Column(db.String(20), default="transfer")
    status = db.Column(db.String(20), default="lunas")
    bukti_pembayaran = db.Column(db.String(255))
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    kategori = db.Column(db.String(50), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    tanggal = db.Column(db.Date, default=date.today)
    deskripsi = db.Column(db.Text)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vendor = db.relationship("Vendor", backref="expenses")


class Vendor(db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150), nullable=False)
    no_telepon = db.Column(db.String(20))
    kategori = db.Column(db.String(50), default="lainnya")
    alamat = db.Column(db.Text)
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    maintenance_requests = db.relationship("MaintenanceRequest", backref="vendor", lazy="dynamic")


class MaintenanceRequest(db.Model):
    __tablename__ = "maintenance_requests"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=True)
    deskripsi = db.Column(db.Text, nullable=False)
    prioritas = db.Column(db.String(20), default="normal")
    tanggal_masuk = db.Column(db.Date, default=date.today)
    tanggal_selesai = db.Column(db.Date)
    status = db.Column(db.String(20), default="diajukan")
    biaya = db.Column(db.Float, default=0)
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    pesan = db.Column(db.Text, nullable=False)
    jenis = db.Column(db.String(50), default="umum")
    wa_sent = db.Column(db.Boolean, default=False)
    dibaca = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
