import pytest
from datetime import date, datetime, timedelta
from app import create_app
from extensions import db
from models import (Kos, User, UserKos, KosInvite, Room, Booking, Payment,
                    Expense, Vendor, MaintenanceRequest, Notification,
                    Announcement, Complaint, ActivityLog, RoomItem, RoomAudit,
                    AuditItemResult, FasilitasUmum, FasilitasKategori)
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seed(app):
    """Seed minimal test data."""
    with app.app_context():
        kos1 = Kos(id=1, nama='Kos Mawar', alamat='Jl. Mawar 1', is_active=True)
        kos2 = Kos(id=2, nama='Kos Melati', alamat='Jl. Melati 2', is_active=True)
        db.session.add_all([kos1, kos2])
        db.session.flush()

        admin = User(id=1, username='admin', email='admin@test.com',
                     password_hash=generate_password_hash('admin123'),
                     role='admin', nama_lengkap='Admin User', no_telepon='0811111111')
        mgmt = User(id=2, username='management', email='mgmt@test.com',
                    password_hash=generate_password_hash('mgmt123'),
                    role='management', nama_lengkap='Management User', no_telepon='0822222222')
        client_user = User(id=3, username='budi', email='budi@test.com',
                          password_hash=generate_password_hash('client123'),
                          role='client', nama_lengkap='Budi Santoso', no_telepon='0833333333')
        client2 = User(id=4, username='siti', email='siti@test.com',
                       password_hash=generate_password_hash('client123'),
                       role='client', nama_lengkap='Siti Rahayu', no_telepon='0844444444')
        db.session.add_all([admin, mgmt, client_user, client2])
        db.session.flush()

        db.session.add_all([
            UserKos(user_id=1, kos_id=1, role='admin'),
            UserKos(user_id=1, kos_id=2, role='admin'),
            UserKos(user_id=2, kos_id=1, role='management'),
            UserKos(user_id=3, kos_id=1, role='client'),
            UserKos(user_id=4, kos_id=1, role='client'),
        ])

        room1 = Room(id=1, kos_id=1, nomor_kamar='A-01', lantai=1, tipe='Reguler',
                     harga_per_bulan=1500000, status='tersedia', fasilitas='AC, WiFi')
        room2 = Room(id=2, kos_id=1, nomor_kamar='A-02', lantai=1, tipe='VIP',
                     harga_per_bulan=2500000, status='terisi', fasilitas='AC, WiFi, TV')
        room3 = Room(id=3, kos_id=2, nomor_kamar='B-01', lantai=1, tipe='Reguler',
                     harga_per_bulan=1200000, status='tersedia')
        db.session.add_all([room1, room2, room3])
        db.session.flush()

        item1 = RoomItem(id=1, room_id=2, nama='AC', jumlah=1, kondisi='baik')
        item2 = RoomItem(id=2, room_id=2, nama='Lemari', jumlah=1, kondisi='baik')
        db.session.add_all([item1, item2])

        booking1 = Booking(id=1, user_id=3, room_id=2, status='aktif',
                          tanggal_masuk=date(2025, 8, 1), tanggal_keluar=date(2025, 12, 1))
        booking2 = Booking(id=2, user_id=4, room_id=1, status='pending',
                          tanggal_masuk=date(2025, 9, 1))
        db.session.add_all([booking1, booking2])
        db.session.flush()

        payment1 = Payment(id=1, booking_id=1, jumlah=2500000,
                          tanggal_bayar=date(2025, 8, 5), bulan_dibayar_untuk='2025-08',
                          metode_bayar='transfer', status='lunas')
        db.session.add(payment1)

        vendor = Vendor(id=1, nama='AC Service', no_telepon='0855555555', kategori='maintenance')
        db.session.add(vendor)

        mr = MaintenanceRequest(id=1, room_id=2, vendor_id=1, deskripsi='AC tidak dingin',
                               prioritas='normal', status='diajukan')
        db.session.add(mr)

        notif = Notification(id=1, user_id=3, pesan='Selamat datang!', jenis='umum', dibaca=False)
        db.session.add(notif)

        ann = Announcement(id=1, judul='Pengumuman Test', isi='Isi test',
                          prioritas='normal', ditampilkan=True, created_by=1)
        db.session.add(ann)

        comp = Complaint(id=1, user_id=3, kos_id=1, judul='AC Rusak',
                        deskripsi='AC tidak dingin', kategori='fasilitas', status='diajukan')
        db.session.add(comp)

        log = ActivityLog(id=1, user_id=1, tindakan='Test action',
                         deskripsi='Test description', model='Test')
        db.session.add(log)

        expense = Expense(id=1, kos_id=1, kategori='listrik', jumlah=500000,
                         tanggal=date(2025, 8, 1), deskripsi='Bayar listrik')
        db.session.add(expense)

        kat = FasilitasKategori(id=1, nama='toilet', icon='bi-toilet')
        fas = FasilitasUmum(id=1, kos_id=1, nama='Toilet Lantai 1', kategori='toilet',
                           lokasi='Lantai 1', kondisi='baik')
        db.session.add_all([kat, fas])

        audit = RoomAudit(id=1, booking_id=1, tipe='check_in', created_by=1)
        db.session.add(audit)
        db.session.flush()

        air = AuditItemResult(id=1, audit_id=1, item_id=1, kondisi='baik')
        db.session.add(air)

        invite = KosInvite(id=1, kos_id=1, code='TESTCODE', role='client', created_by=1)
        db.session.add(invite)

        db.session.commit()
        return {'kos1': kos1, 'kos2': kos2, 'admin': admin, 'mgmt': mgmt,
                'client': client_user, 'client2': client2,
                'room1': room1, 'room2': room2, 'room3': room3,
                'booking1': booking1, 'booking2': booking2,
                'payment': payment1, 'vendor': vendor, 'mr': mr,
                'notif': notif, 'ann': ann, 'comp': comp, 'log': log,
                'expense': expense, 'fas': fas, 'kat': kat,
                'audit': audit, 'invite': invite}


def login(client, username, password):
    return client.post('/auth/login', data={'username': username, 'password': password})


# ═══════════════════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════════════════

class TestUserModel:
    def test_set_password(self, app):
        with app.app_context():
            u = User(username='test', email='test@test.com', nama_lengkap='Test')
            u.set_password('mypassword')
            assert u.check_password('mypassword') is True
            assert u.check_password('wrong') is False

    def test_user_repr(self, app, seed):
        with app.app_context():
            user = User.query.get(1)
            assert 'admin' in repr(user).lower()

    def test_get_role_for_kos(self, app, seed):
        with app.app_context():
            user = User.query.get(3)
            assert user.get_role_for_kos(1) == 'client'
            assert user.get_role_for_kos(2) is None

    def test_admin_global_fallback(self, app, seed):
        with app.app_context():
            admin = User.query.get(1)
            assert admin.has_kos_access(999) is True

    def test_has_kos_access(self, app, seed):
        with app.app_context():
            user = User.query.get(3)
            assert user.has_kos_access(1) is True
            assert user.has_kos_access(1, 'client') is True
            assert user.has_kos_access(1, 'admin') is False
            assert user.has_kos_access(2) is False

    def test_get_accessible_kos_ids(self, app, seed):
        with app.app_context():
            admin = User.query.get(1)
            client = User.query.get(3)
            assert set(admin.get_accessible_kos_ids()) == {1, 2}
            assert client.get_accessible_kos_ids() == [1]

    def test_get_managed_kos(self, app, seed):
        with app.app_context():
            admin = User.query.get(1)
            mgmt = User.query.get(2)
            client = User.query.get(3)
            assert len(admin.get_managed_kos()) == 2
            assert len(mgmt.get_managed_kos()) == 1
            assert len(client.get_managed_kos()) == 0


class TestUserKosModel:
    def test_unique_constraint(self, app, seed):
        with app.app_context():
            db.session.add(UserKos(user_id=3, kos_id=1, role='management'))
            with pytest.raises(Exception):
                db.session.commit()

    def test_cascade_delete(self, app, seed):
        with app.app_context():
            user = User.query.get(4)
            db.session.delete(user)
            db.session.commit()
            assert UserKos.query.filter_by(user_id=4).count() == 0


class TestKosInviteModel:
    def test_generate_code(self, app):
        with app.app_context():
            code1 = KosInvite.generate_code()
            code2 = KosInvite.generate_code()
            assert len(code1) >= 6
            assert code1 != code2

    def test_is_valid(self, app, seed):
        with app.app_context():
            invite = KosInvite.query.get(1)
            assert invite.is_valid is True

    def test_is_valid_expired(self, app, seed):
        with app.app_context():
            invite = KosInvite(kos_id=1, code='EXPIRED', role='client',
                              expires_at=datetime.utcnow() - timedelta(days=1))
            assert invite.is_valid is False

    def test_is_valid_max_uses(self, app, seed):
        with app.app_context():
            invite = KosInvite(kos_id=1, code='MAXED', role='client',
                              max_uses=5, used_count=5)
            assert invite.is_valid is False


class TestKosModel:
    def test_total_kamar(self, app, seed):
        with app.app_context():
            assert Kos.query.get(1).total_kamar == 2
            assert Kos.query.get(2).total_kamar == 1

    def test_kamar_terisi(self, app, seed):
        with app.app_context():
            assert Kos.query.get(1).kamar_terisi == 1
            assert Kos.query.get(2).kamar_terisi == 0

    def test_kos_repr(self, app, seed):
        with app.app_context():
            kos = Kos.query.get(1)
            assert 'Kos Mawar' in repr(kos)


class TestRoomModel:
    def test_booking_aktif(self, app, seed):
        with app.app_context():
            room = Room.query.get(2)
            assert room.booking_aktif is not None
            assert room.booking_aktif.id == 1

    def test_booking_aktif_empty(self, app, seed):
        with app.app_context():
            room = Room.query.get(1)
            assert room.booking_aktif is None

    def test_room_repr(self, app, seed):
        with app.app_context():
            room = Room.query.get(1)
            assert 'A-01' in repr(room)


class TestBookingModel:
    def test_durasi_bulan(self, app, seed):
        with app.app_context():
            booking = Booking.query.get(1)
            assert booking.durasi_bulan == 4

    def test_tagihan_bulan_ini(self, app, seed):
        with app.app_context():
            booking = Booking.query.get(1)
            assert booking.tagihan_bulan_ini is False


class TestPaymentModel:
    def test_payment_lunas(self, app, seed):
        with app.app_context():
            payment = Payment.query.get(1)
            assert payment.status == 'lunas'
            assert payment.jumlah == 2500000


class TestNotificationModel:
    def test_notification_unread(self, app, seed):
        with app.app_context():
            notif = Notification.query.get(1)
            assert notif.dibaca is False
            assert notif.pesan == 'Selamat datang!'


class TestComplaintModel:
    def test_complaint_status(self, app, seed):
        with app.app_context():
            comp = Complaint.query.get(1)
            assert comp.status == 'diajukan'
            assert comp.kategori == 'fasilitas'


class TestFasilitasUmumModel:
    def test_is_usable(self, app, seed):
        with app.app_context():
            fas = FasilitasUmum.query.get(1)
            assert fas.is_usable is True
            fas.kondisi = 'rusak_ringan'
            assert fas.is_usable is False
            fas.kondisi = 'rusak_berat'
            assert fas.is_usable is False
            fas.kondisi = 'maintenance'
            assert fas.is_usable is False


class TestActivityLogModel:
    def test_activity_log(self, app, seed):
        with app.app_context():
            log = ActivityLog.query.get(1)
            assert log.tindakan == 'Test action'
            assert log.user_id == 1


class TestRoomAuditModel:
    def test_room_audit(self, app, seed):
        with app.app_context():
            audit = RoomAudit.query.get(1)
            assert audit.tipe == 'check_in'
            assert audit.booking_id == 1
            assert len(audit.hasil) == 1


class TestAuditItemResultModel:
    def test_audit_item_result(self, app, seed):
        with app.app_context():
            air = AuditItemResult.query.get(1)
            assert air.kondisi == 'baik'
            assert air.audit_id == 1


# ═══════════════════════════════════════════════════════════════════
# ROUTE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestAuthRoutes:
    def test_login_page(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 200

    def test_login_success(self, client, seed):
        resp = login(client, 'admin', 'admin123')
        assert resp.status_code == 302

    def test_login_wrong_password(self, client, seed):
        resp = login(client, 'admin', 'wrong'), client.get('/dashboard/', follow_redirects=True)
        # Should redirect back to login

    def test_register_page(self, client):
        resp = client.get('/auth/register')
        assert resp.status_code == 200

    def test_register_success(self, client, seed):
        resp = client.post('/auth/register', data={
            'username': 'newuser', 'email': 'new@test.com',
            'password': 'pass123', 'confirm_password': 'pass123',
            'nama_lengkap': 'New User'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert User.query.filter_by(username='newuser').first() is not None

    def test_register_duplicate_username(self, client, seed):
        resp = client.post('/auth/register', data={
            'username': 'admin', 'email': 'dup@test.com',
            'password': 'pass123', 'confirm_password': 'pass123',
            'nama_lengkap': 'Dup User'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_register_password_mismatch(self, client, seed):
        resp = client.post('/auth/register', data={
            'username': 'newuser2', 'email': 'new2@test.com',
            'password': 'pass123', 'confirm_password': 'pass456',
            'nama_lengkap': 'Mismatch User'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_logout(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/auth/logout', follow_redirects=False)
        assert resp.status_code == 302


class TestDashboardRoutes:
    def test_requires_auth(self, client):
        resp = client.get('/dashboard/admin', follow_redirects=False)
        assert resp.status_code == 302

    def test_admin_dashboard(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/admin')
        assert resp.status_code == 200

    def test_management_dashboard(self, client, seed):
        login(client, 'management', 'mgmt123')
        resp = client.get('/dashboard/admin')
        assert resp.status_code == 200

    def test_client_dashboard(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/dashboard/client')
        assert resp.status_code == 200

    def test_index_redirect_admin(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/admin' in resp.headers['Location']

    def test_index_redirect_client(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/dashboard/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/client' in resp.headers['Location']


class TestKosRoutes:
    def test_index_requires_auth(self, client):
        resp = client.get('/kos/', follow_redirects=False)
        assert resp.status_code == 302

    def test_index_admin(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/kos/')
        assert resp.status_code == 200
        assert b'Kos Mawar' in resp.data

    def test_pilih_success(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/kos/pilih/2', follow_redirects=False)
        assert resp.status_code == 302

    def test_pilih_no_access(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.post('/kos/pilih/2', follow_redirects=True)
        assert resp.status_code == 200

    def test_tambah(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/kos/tambah', data={
            'nama': 'Kos Baru', 'alamat': 'Jl. Baru', 'deskripsi': 'Test kos'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert Kos.query.filter_by(nama='Kos Baru').first() is not None

    def test_edit(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/kos/1/edit', data={
            'nama': 'Kos Mawar Updated', 'alamat': 'Jl. Mawar 1 Baru'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_hapus(self, client, seed):
        login(client, 'admin', 'admin123')
        # Create a new kos to delete (empty one)
        resp = client.post('/kos/tambah', data={
            'nama': 'Kos Temp', 'alamat': 'Temp'
        }, follow_redirects=True)
        new_kos = Kos.query.filter_by(nama='Kos Temp').first()
        if new_kos:
            resp = client.post(f'/kos/{new_kos.id}/hapus', follow_redirects=True)
            assert resp.status_code == 200

    def test_unduran_page(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/kos/1/unduran')
        assert resp.status_code == 200

    def test_buat_undangan(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/kos/1/unduran', data={
            'role': 'client', 'max_uses': '5', 'expires_at': '2025-12-31'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_join_via_invite(self, client, seed):
        login(client, 'siti', 'client123')
        invite = KosInvite.query.filter_by(kos_id=1).first()
        if invite:
            resp = client.post(f'/kos/join/{invite.code}', follow_redirects=True)
            assert resp.status_code == 200


class TestRoomRoutes:
    def test_index_admin(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/rooms/')
        assert resp.status_code == 200

    def test_index_client(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/rooms/')
        assert resp.status_code == 200

    def test_detail(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/rooms/1')
        assert resp.status_code == 200

    def test_tambah(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/rooms/tambah', data={
            'nomor_kamar': 'A-03', 'lantai': 2, 'tipe': 'Reguler',
            'harga_per_bulan': '1800000', 'status': 'tersedia'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert Room.query.filter_by(nomor_kamar='A-03').first() is not None

    def test_tambah_duplicate(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/rooms/tambah', data={
            'nomor_kamar': 'A-01', 'lantai': 1, 'tipe': 'Reguler',
            'harga_per_bulan': '1500000'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_edit(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/rooms/1/edit', data={
            'nomor_kamar': 'A-01', 'lantai': 1, 'tipe': 'Deluxe',
            'harga_per_bulan': '2000000', 'status': 'tersedia'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_hapus(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/rooms/1/hapus', follow_redirects=True)
        assert resp.status_code == 200

    def test_client_cannot_add(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/rooms/tambah', follow_redirects=True)
        assert resp.status_code == 200


class TestBookingRoutes:
    def test_booking_list(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/rooms/booking')
        assert resp.status_code == 200

    def test_approve_booking(self, client, seed):
        login(client, 'admin', 'admin123')
        booking = Booking.query.get(2)  # pending booking
        resp = client.post(f'/rooms/booking/{booking.id}/setujui', follow_redirects=True)
        assert resp.status_code == 200

    def test_reject_booking(self, client, seed):
        login(client, 'admin', 'admin123')
        booking = Booking.query.get(2)
        resp = client.post(f'/rooms/booking/{booking.id}/tolak', follow_redirects=True)
        assert resp.status_code == 200


class TestPaymentRoutes:
    def test_list_admin(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/payments/')
        assert resp.status_code == 200

    def test_list_client(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/payments/')
        assert resp.status_code == 200

    def test_tambah(self, client, seed):
        login(client, 'admin', 'admin123')
        booking = Booking.query.get(1)
        resp = client.post('/payments/tambah', data={
            'booking_id': str(booking.id), 'jumlah': '2500000',
            'tanggal_bayar': '2025-09-05', 'bulan_dibayar_untuk': '2025-09',
            'metode_bayar': 'transfer', 'status': 'lunas'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_edit(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/payments/1/edit', data={
            'jumlah': '2600000', 'tanggal_bayar': '2025-08-05',
            'bulan_dibayar_untuk': '2025-08', 'metode_bayar': 'cash',
            'status': 'lunas'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_hapus(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/payments/1/hapus', follow_redirects=True)
        assert resp.status_code == 200

    def test_resi(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/payments/1/resi')
        assert resp.status_code == 200

    def test_reminder(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/payments/reminders')
        assert resp.status_code == 200


class TestAccountingRoutes:
    def test_index(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/accounting/')
        assert resp.status_code == 200

    def test_index_with_year(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/accounting/?tahun=2025')
        assert resp.status_code == 200

    def test_expense_list(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/accounting/pengeluaran')
        assert resp.status_code == 200

    def test_tambah_expense(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/accounting/pengeluaran/tambah', data={
            'kategori': 'air', 'jumlah': '300000',
            'tanggal': '2025-08-10', 'deskripsi': 'Bayar air'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_edit_expense(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/accounting/pengeluaran/1/edit', data={
            'kategori': 'listrik', 'jumlah': '550000',
            'tanggal': '2025-08-01', 'deskripsi': 'Bayar listrik updated'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_hapus_expense(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/accounting/pengeluaran/1/hapus', follow_redirects=True)
        assert resp.status_code == 200

    def test_export_csv(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/accounting/export')
        assert resp.status_code == 200
        assert resp.content_type == 'text/csv'


class TestMaintenanceRoutes:
    def test_list(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/maintenance/')
        assert resp.status_code == 200

    def test_detail(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/maintenance/1')
        assert resp.status_code == 200

    def test_tambah(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/maintenance/tambah', data={
            'room_id': '1', 'deskripsi': 'Lampu rusak', 'prioritas': 'normal'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_update_status(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/maintenance/1/update', data={
            'status': 'diproses', 'vendor_id': '1'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_vendor_list(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/maintenance/vendor')
        assert resp.status_code == 200

    def test_vendor_tambah(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/maintenance/vendor/tambah', data={
            'nama': 'Plumber Pro', 'no_telepon': '0866666666', 'kategori': 'maintenance'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_vendor_edit(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/maintenance/vendor/1/edit', data={
            'nama': 'AC Service Updated', 'no_telepon': '0855555555', 'kategori': 'maintenance'
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestOnboardingRoutes:
    def test_index(self, client):
        resp = client.get('/onboarding/')
        assert resp.status_code == 200

    def test_kamar_list(self, client):
        resp = client.get('/onboarding/kamar')
        assert resp.status_code == 200

    def test_detail_kamar(self, client):
        resp = client.get('/onboarding/kamar/1')
        assert resp.status_code == 200

    def test_booking_requires_login(self, client):
        resp = client.post('/onboarding/booking/1', data={
            'tanggal_masuk': '2025-10-01'
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_booking_submit(self, client, seed):
        login(client, 'siti', 'client123')
        resp = client.post('/onboarding/booking/1', data={
            'tanggal_masuk': '2025-10-01'
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestAnnouncementRoutes:
    def test_list(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/pengumuman/')
        assert resp.status_code == 200

    def test_tambah_requires_admin(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/pengumuman/tambah', data={
            'judul': 'Test Baru', 'isi': 'Isi test', 'prioritas': 'normal'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_edit(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/pengumuman/1/edit', data={
            'judul': 'Updated', 'isi': 'Updated isi', 'prioritas': 'penting'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_hapus(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/pengumuman/1/hapus', follow_redirects=True)
        assert resp.status_code == 200


class TestComplaintRoutes:
    def test_list_admin(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/komplain/')
        assert resp.status_code == 200

    def test_list_client(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/komplain/')
        assert resp.status_code == 200

    def test_tambah(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.post('/komplain/tambah', data={
            'judul': 'Kamar Bocor', 'deskripsi': 'Atap bocor saat hujan', 'kategori': 'umum'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_tanggapi(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/komplain/1/tanggapi', data={
            'status': 'ditindaklanjuti', 'tanggapan': 'Sedang ditangani'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_detail(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/komplain/1')
        assert resp.status_code == 200


class TestFasilitasRoutes:
    def test_index_requires_auth(self, client):
        resp = client.get('/fasilitas/', follow_redirects=False)
        assert resp.status_code == 302

    def test_index_admin(self, client, seed):
        login(client, 'admin', 'admin123')
        client.post('/kos/pilih/1')
        resp = client.get('/fasilitas/')
        assert resp.status_code == 200

    def test_kategori_index(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/fasilitas/kategori')
        assert resp.status_code == 200

    def test_tambah(self, client, seed):
        login(client, 'admin', 'admin123')
        client.post('/kos/pilih/1')
        resp = client.post('/fasilitas/tambah', data={
            'nama': 'Shower Lantai 2', 'kategori': 'shower',
            'lokasi': 'Lantai 2', 'kondisi': 'baik'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_edit(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/fasilitas/1/edit', data={
            'nama': 'Toilet Lantai 1 Updated', 'kategori': 'toilet',
            'lokasi': 'Lantai 1', 'kondisi': 'rusak_ringan'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_hapus(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/fasilitas/1/hapus', follow_redirects=True)
        assert resp.status_code == 200

    def test_kategori_tambah(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/fasilitas/kategori/tambah', data={
            'nama': 'parkir', 'icon': 'bi-p-circle', 'deskripsi': 'Area parkir'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_kategori_edit(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/fasilitas/kategori/1/edit', data={
            'nama': 'toilet', 'icon': 'bi-droplet', 'deskripsi': 'Toilet updated'
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestInventoryRoutes:
    def test_index(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/inventaris/')
        assert resp.status_code == 200

    def test_room_items(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/inventaris/kamar/2')
        assert resp.status_code == 200

    def test_tambah_item(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/inventaris/kamar/2/tambah', data={
            'nama': 'Meja', 'jumlah': '1', 'kondisi': 'baik'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_edit_item(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/inventaris/item/1/edit', data={
            'nama': 'AC', 'jumlah': '1', 'kondisi': 'rusak'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_hapus_item(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/inventaris/item/1/hapus', follow_redirects=True)
        assert resp.status_code == 200


class TestActivityLogRoutes:
    def test_index(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/aktivitas/')
        assert resp.status_code == 200

    def test_index_with_filter(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/aktivitas/?model=Test')
        assert resp.status_code == 200


class TestAuditRoutes:
    def test_check_in(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.post('/audit/check-in', data={
            'booking_id': '1', 'catatan': 'Kamar bersih'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_check_out(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.post('/audit/check-out', data={
            'booking_id': '1', 'catatan': 'Kamar dalam kondisi baik'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_history(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/audit/history')
        assert resp.status_code == 200

    def test_detail(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/audit/1')
        assert resp.status_code == 200


class TestNotificationRoutes:
    def test_list(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/notifikasi/')
        assert resp.status_code == 200

    def test_mark_read(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.post('/notifikasi/1/baca', follow_redirects=True)
        assert resp.status_code == 200

    def test_mark_all_read(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.post('/notifikasi/baca-semua', follow_redirects=True)
        assert resp.status_code == 200


class TestWhatsAppRoutes:
    def test_kirim_resi(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/payments/1/resi')
        assert resp.status_code == 200

    def test_reminder_page(self, client, seed):
        login(client, 'admin', 'admin123')
        resp = client.get('/payments/reminders')
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# HELPERS TESTS
# ═══════════════════════════════════════════════════════════════════

class TestHelpers:
    def test_get_current_kos_role(self, app, seed):
        with app.app_context():
            from helpers import get_current_kos_role
            from flask_login import login_user
            user = User.query.get(3)
            with app.test_request_context():
                from flask import session
                session['kos_id'] = 1
                login_user(user)
                role = get_current_kos_role()
                assert role == 'client'

    def test_format_rupiah(self, app):
        with app.app_context():
            from helpers import format_rupiah
            assert format_rupiah(1500000) == 'Rp 1.500.000'
            assert format_rupiah(0) == 'Rp 0'
            assert format_rupiah(100000) == 'Rp 100.000'


# ═══════════════════════════════════════════════════════════════════
# ACCESS CONTROL TESTS
# ═══════════════════════════════════════════════════════════════════

class TestAccessControl:
    def test_client_cannot_access_admin_dashboard(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/dashboard/admin', follow_redirects=False)
        assert resp.status_code == 302

    def test_client_cannot_access_rooms_tambah(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/rooms/tambah', follow_redirects=True)
        assert resp.status_code == 200

    def test_client_cannot_access_accounting(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/accounting/', follow_redirects=False)
        assert resp.status_code in [302, 403]

    def test_client_cannot_access_activity_log(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/aktivitas/', follow_redirects=False)
        assert resp.status_code in [302, 403]

    def test_client_cannot_manage_fasilitas(self, client, seed):
        login(client, 'budi', 'client123')
        resp = client.get('/fasilitas/tambah', follow_redirects=False)
        assert resp.status_code in [302, 403]

    def test_management_can_access_rooms(self, client, seed):
        login(client, 'management', 'mgmt123')
        resp = client.get('/rooms/')
        assert resp.status_code == 200

    def test_management_can_access_accounting(self, client, seed):
        login(client, 'management', 'mgmt123')
        resp = client.get('/accounting/')
        assert resp.status_code == 200

    def test_unauthenticated_redirect(self, client):
        protected = ['/dashboard/', '/rooms/', '/payments/', '/accounting/',
                     '/maintenance/', '/komplain/', '/fasilitas/', '/inventaris/',
                     '/aktivitas/', '/audit/']
        for route in protected:
            resp = client.get(route, follow_redirects=False)
            assert resp.status_code == 302, f"Expected redirect for {route}"

    def test_onboarding_public(self, client):
        resp = client.get('/onboarding/')
        assert resp.status_code == 200
        resp = client.get('/onboarding/kamar')
        assert resp.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
