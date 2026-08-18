from datetime import datetime, date, timedelta
from calendar import monthrange
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
import secrets


# Allowed default-stay units, shared by kos preset + booking request forms
DEFAULT_STAY_UNITS = ("hari", "minggu", "bulan", "tahun")


def compute_keluar(tgl_masuk, value, unit):
    """Compute a stay end date from a duration value+unit.
    unit: hari | minggu | bulan | tahun. Reused by Kos preset and booking forms."""
    v = value or 1
    if unit == "hari":
        return tgl_masuk + timedelta(days=v)
    if unit == "minggu":
        return tgl_masuk + timedelta(weeks=v)
    if unit == "tahun":
        try:
            return tgl_masuk.replace(year=tgl_masuk.year + v)
        except ValueError:  # 29 Feb -> 28 Feb
            return tgl_masuk.replace(year=tgl_masuk.year + v, day=28)
    # bulan — calendar months (rolling month-end)
    bulan = tgl_masuk.month + v
    tahun = tgl_masuk.year + (bulan - 1) // 12
    bulan = ((bulan - 1) % 12) + 1
    max_day = monthrange(tahun, bulan)[1]
    return date(tahun, bulan, min(tgl_masuk.day, max_day))

class Kos(db.Model):
    __tablename__ = "kos"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150), nullable=False)
    alamat = db.Column(db.Text)
    deskripsi = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Default stay duration preset (admin/management editable) so admins don't
    # re-type it for every new guest. unit: hari | minggu | bulan | tahun
    default_stay_value = db.Column(db.Integer, default=1)
    default_stay_unit = db.Column(db.String(10), default="bulan")

    rooms = db.relationship("Room", backref="kos", lazy="dynamic")
    user_roles = db.relationship("UserKos", backref="kos", lazy="dynamic")

    def default_keluar_date(self, tgl_masuk):
        """Compute the stay end date from this kos's default stay preset."""
        return compute_keluar(tgl_masuk, self.default_stay_value or 1, self.default_stay_unit or "bulan")

    @property
    def total_kamar(self):
        return self.rooms.count()

    @property
    def kamar_terisi(self):
        return self.rooms.filter_by(status="terisi").count()

class UserKos(db.Model):
    """Junction table: user-role per kos (multi-tenancy)."""
    __tablename__ = "user_kos"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_userkos_user"), nullable=False, index=True)
    kos_id = db.Column(db.Integer, db.ForeignKey("kos.id", name="fk_userkos_kos"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="client")  # admin, management, client
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'kos_id', name='uq_user_kos'),)

class KosInvite(db.Model):
    """Invite codes for joining a kos with a specific role."""
    __tablename__ = "kos_invites"

    id = db.Column(db.Integer, primary_key=True)
    kos_id = db.Column(db.Integer, db.ForeignKey("kos.id", name="fk_invite_kos"), nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default="client")  # role granted when used
    max_uses = db.Column(db.Integer, default=0)  # 0 = unlimited
    used_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_invite_creator"), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    kos = db.relationship("Kos", backref="invites")
    creator = db.relationship("User", backref="invites_created")

    @staticmethod
    def generate_code():
        """Generate unique 8-char invite code."""
        return secrets.token_urlsafe(6).upper()

    @property
    def is_valid(self):
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        return True

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="client")  # legacy global role
    nama_lengkap = db.Column(db.String(150), nullable=False)
    no_telepon = db.Column(db.String(20))
    alamat = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="client", lazy="dynamic")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")
    kos_roles = db.relationship("UserKos", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_role_for_kos(self, kos_id):
        """Return user role for specific kos, or None."""
        uk = UserKos.query.filter_by(user_id=self.id, kos_id=kos_id).first()
        return uk.role if uk else None

    def has_kos_access(self, kos_id, required_role=None):
        """Check if user has access to kos (optionally with specific role)."""
        if self.role == "admin":  # global admin bypass
            return True
        uk = UserKos.query.filter_by(user_id=self.id, kos_id=kos_id).first()
        if not uk:
            return False
        if required_role:
            if isinstance(required_role, str):
                return uk.role == required_role
            return uk.role in required_role
        return True

    def get_accessible_kos_ids(self):
        """Return list of kos IDs user can access."""
        if self.role == "admin":
            return [k.id for k in Kos.query.filter_by(is_active=True).all()]
        return [uk.kos_id for uk in UserKos.query.filter_by(user_id=self.id).all()]

    def get_managed_kos(self):
        """Return Kos objects where user is admin or management."""
        if self.role == "admin":
            return Kos.query.filter_by(is_active=True).all()
        kos_ids = [uk.kos_id for uk in UserKos.query.filter(
            UserKos.user_id == self.id, UserKos.role.in_(["admin", "management"])
        ).all()]
        return Kos.query.filter(Kos.id.in_(kos_ids), Kos.is_active == True).all()

class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    kos_id = db.Column(db.Integer, db.ForeignKey("kos.id", name="fk_room_kos"), nullable=True, index=True)
    nomor_kamar = db.Column(db.String(10), nullable=False)
    __table_args__ = (db.UniqueConstraint('kos_id', 'nomor_kamar', name='uq_kos_kamar'),)
    lantai = db.Column(db.Integer, default=1)
    tipe = db.Column(db.String(50), default="Reguler")
    harga_per_bulan = db.Column(db.Numeric(12, 2), nullable=False)
    ukuran = db.Column(db.String(50))
    fasilitas = db.Column(db.Text)
    status = db.Column(db.String(20), default="tersedia")
    deskripsi = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="room", lazy="dynamic")
    maintenance_requests = db.relationship("MaintenanceRequest", backref="room", lazy="dynamic")

    @property
    def booking_aktif(self):
        from flask import g
        cache = g.get("_booking_aktif_cache")
        if cache is not None:
            return cache.get(self.id)
        return Booking.query.filter_by(room_id=self.id, status="aktif").first()

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_booking_user"), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", name="fk_booking_room"), nullable=False, index=True)
    tanggal_masuk = db.Column(db.Date, nullable=False)
    tanggal_keluar = db.Column(db.Date)
    status = db.Column(db.String(20), default="aktif")
    deposit = db.Column(db.Numeric(12, 2), default=0)
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
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", name="fk_payment_booking"), nullable=False, index=True)
    jumlah = db.Column(db.Numeric(12, 2), nullable=False)
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
    kos_id = db.Column(db.Integer, db.ForeignKey("kos.id", name="fk_expense_kos"), nullable=True, index=True)
    kategori = db.Column(db.String(50), nullable=False)
    jumlah = db.Column(db.Numeric(12, 2), nullable=False)
    tanggal = db.Column(db.Date, default=date.today)
    deskripsi = db.Column(db.Text)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id", name="fk_expense_vendor"), nullable=True, index=True)
    fasilitas_id = db.Column(db.Integer, db.ForeignKey("fasilitas_umum.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vendor = db.relationship("Vendor", backref="expenses")
    fasilitas = db.relationship("FasilitasUmum", backref="expenses")
    kos = db.relationship("Kos", backref="expenses")

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
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", name="fk_maintenance_room"), nullable=False, index=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id", name="fk_maintenance_vendor"), nullable=True, index=True)
    deskripsi = db.Column(db.Text, nullable=False)
    prioritas = db.Column(db.String(20), default="normal")
    tanggal_masuk = db.Column(db.Date, default=date.today)
    tanggal_selesai = db.Column(db.Date)
    status = db.Column(db.String(20), default="diajukan")
    biaya = db.Column(db.Numeric(12, 2), default=0)
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_notification_user"), nullable=True, index=True)
    pesan = db.Column(db.Text, nullable=False)
    jenis = db.Column(db.String(50), default="umum")
    wa_sent = db.Column(db.Boolean, default=False)
    dibaca = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(200), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    prioritas = db.Column(db.String(20), default="normal")
    ditampilkan = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_announcement_creator"), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", backref="announcements")

class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_complaint_user"), nullable=False, index=True)
    kos_id = db.Column(db.Integer, db.ForeignKey("kos.id", name="fk_complaint_kos"), nullable=True, index=True)
    judul = db.Column(db.String(200), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    kategori = db.Column(db.String(50), default="umum")
    status = db.Column(db.String(20), default="diajukan")
    tanggapan = db.Column(db.Text)
    ditanggapi_oleh = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_complaint_responder"), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], backref="complaints")
    responder = db.relationship("User", foreign_keys=[ditanggapi_oleh])
    kos = db.relationship("Kos", backref="complaints")

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_activitylog_user"), nullable=True, index=True)
    tindakan = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text)
    model = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="activity_logs")

class RoomItem(db.Model):
    __tablename__ = "room_items"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", name="fk_roomitem_room"), nullable=False, index=True)
    nama = db.Column(db.String(150), nullable=False)
    jumlah = db.Column(db.Integer, default=1)
    kondisi = db.Column(db.String(50), default="baik")
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship("Room", backref="items")

class RoomAudit(db.Model):
    __tablename__ = "room_audits"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", name="fk_roomaudit_booking"), nullable=False, index=True)
    tipe = db.Column(db.String(20), nullable=False)  # check_in / check_out
    catatan = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", name="fk_roomaudit_creator"), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship("Booking", backref="audits")
    auditor = db.relationship("User", backref="audits_created")

class AuditItemResult(db.Model):
    __tablename__ = "audit_item_results"

    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey("room_audits.id", name="fk_auditresult_audit"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("room_items.id", name="fk_auditresult_item"), nullable=False, index=True)
    kondisi = db.Column(db.String(20), nullable=False)  # baik / rusak
    catatan = db.Column(db.Text)

    audit = db.relationship("RoomAudit", backref="items")
    item = db.relationship("RoomItem", backref="audit_results")

class FasilitasUmum(db.Model):
    __tablename__ = "fasilitas_umum"

    id = db.Column(db.Integer, primary_key=True)
    kos_id = db.Column(db.Integer, db.ForeignKey("kos.id", name="fk_fasilitas_kos"), nullable=False, index=True)
    nama = db.Column(db.String(150), nullable=False)
    kategori = db.Column(db.String(50), default="toilet")
    lokasi = db.Column(db.String(100))
    kondisi = db.Column(db.String(20), default="baik")
    deskripsi = db.Column(db.Text)
    catatan = db.Column(db.Text)
    is_recurring = db.Column(db.Boolean, default=False)
    biaya_per_bulan = db.Column(db.Numeric(12, 2))
    frekuensi = db.Column(db.String(20), default="bulanan")  # bulanan, 3_bulan, 6_bulan, tahunan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kos = db.relationship("Kos", backref="fasilitas_umum")

    @property
    def is_usable(self):
        return self.kondisi == "baik"

class FasilitasKategori(db.Model):
    __tablename__ = "fasilitas_kategori"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(30), default="bi-box")
    deskripsi = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RolePermission(db.Model):
    """Per-module permission for a role. Admin page can toggle these."""
    __tablename__ = "role_permissions"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # admin, management, client
    module = db.Column(db.String(50), nullable=False)  # rooms, payments, etc.
    can_view = db.Column(db.Boolean, default=False)
    can_create = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)

    __table_args__ = (db.UniqueConstraint('role', 'module', name='uq_role_module'),)

    @staticmethod
    def get_perm(role, module):
        """Return RolePermission row or None."""
        return RolePermission.query.filter_by(role=role, module=module).first()

    @staticmethod
    def can(role, module, action='view'):
        """Check permission. Admin always True."""
        if role == 'admin':
            return True
        p = RolePermission.get_perm(role, module)
        if not p:
            return False
        return getattr(p, f'can_{action}', False)

    @staticmethod
    def get_all_for_role(role):
        """Return dict of {module: {view, create, edit, delete}} for role."""
        perms = RolePermission.query.filter_by(role=role).all()
        return {p.module: {'view': p.can_view, 'create': p.can_create,
                           'edit': p.can_edit, 'delete': p.can_delete} for p in perms}
