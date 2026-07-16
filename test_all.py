#!/usr/bin/env python3
import re, sys
from app import create_app, db

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECRET_KEY'] = 'test-secret'

passed = []
failed = []

def check(name, ok, detail=""):
    if ok:
        passed.append(name)
    else:
        s = f"FAIL {name}"
        if detail:
            s += f" -- {detail}"
        failed.append(s)

# Re-seed manually
with app.app_context():
    db.drop_all()
    db.create_all()
    from models import User, Room, Booking, Payment, Expense, Vendor, MaintenanceRequest, Notification
    from datetime import date, timedelta
    import random

    admin = User(username='admin', email='admin@kos.com', role='admin', nama_lengkap='Admin Kos', no_telepon='08123456789')
    admin.set_password('admin123')
    db.session.add(admin)

    clients_data = [
        ('budi', 'Budi Santoso', '08111111111'),
        ('siti', 'Siti Rahayu', '08222222222'),
        ('agus', 'Agus Wijaya', '08333333333'),
        ('dewi', 'Dwi Putri', '08444444444'),
        ('eko', 'Eko Prasetyo', '08555555555'),
    ]
    clients = []
    for u, n, t in clients_data:
        c = User(username=u, email=f'{u}@email.com', role='client', nama_lengkap=n, no_telepon=t, alamat=f'Alamat {n}')
        c.set_password('client123')
        db.session.add(c)
        clients.append(c)

    rooms_data = [
        ('101', 1, 'Reguler', 1500000, '12m2', 'AC, Kasur, Lemari, Meja'),
        ('102', 1, 'Reguler', 1500000, '12m2', 'AC, Kasur, Lemari, Meja'),
        ('103', 1, 'Deluxe', 2000000, '16m2', 'AC, Kasur, Lemari, Meja, TV, Kamar Mandi Dalam'),
        ('201', 2, 'Reguler', 1500000, '12m2', 'AC, Kasur, Lemari, Meja'),
        ('202', 2, 'Deluxe', 2000000, '16m2', 'AC, Kasur, Lemari, Meja, TV, Kamar Mandi Dalam'),
        ('203', 2, 'VIP', 3000000, '24m2', 'AC, Kasur, Lemari, Meja, TV, Kulkas, Kamar Mandi Dalam, Balkon'),
    ]
    rooms = []
    for no, lt, tp, hr, uk, fs in rooms_data:
        r = Room(nomor_kamar=no, lantai=lt, tipe=tp, harga_per_bulan=hr, ukuran=uk, fasilitas=fs, status='tersedia', deskripsi=f'Kamar {tp} nyaman di lantai {lt}')
        db.session.add(r)
        rooms.append(r)
    db.session.commit()

    today = date.today()
    room_assignments = [
        (clients[0], rooms[0], today - timedelta(days=60)),
        (clients[1], rooms[2], today - timedelta(days=30)),
        (clients[3], rooms[4], today - timedelta(days=90)),
    ]
    for client, room, tgl_masuk in room_assignments:
        tgl_keluar = tgl_masuk + timedelta(days=365)
        booking = Booking(user_id=client.id, room_id=room.id, tanggal_masuk=tgl_masuk, tanggal_keluar=tgl_keluar, status='aktif', deposit=room.harga_per_bulan, catatan='Deposit sudah dibayar')
        db.session.add(booking)
        room.status = 'terisi'
        db.session.commit()
        months_back = 1
        while today - tgl_masuk > timedelta(days=months_back * 30):
            bulan = (tgl_masuk + timedelta(days=months_back * 30)).strftime('%Y-%m')
            Payment(booking_id=booking.id, jumlah=room.harga_per_bulan, tanggal_bayar=today - timedelta(days=random.randint(1,5)), bulan_dibayar_untuk=bulan, metode_bayar='transfer', status='lunas')
            months_back += 1
        db.session.commit()

    for n, t, k in [('Teknisi AC', '08666666666', 'maintenance'), ('Tukang Listrik', '08777777777', 'listrik'), ('Cleaning Service', '08888888888', 'kebersihan')]:
        db.session.add(Vendor(nama=n, no_telepon=t, kategori=k))
    db.session.commit()

    for kat, jml, dsc in [('listrik', 1200000, 'Listrik bulan ini'), ('air', 500000, 'PDAM bulan ini'), ('kebersihan', 300000, 'Cleaning service'), ('gaji', 2500000, 'Gaji satpam')]:
        db.session.add(Expense(kategori=kat, jumlah=jml, tanggal=today - timedelta(days=random.randint(1,15)), deskripsi=dsc))
    db.session.commit()

    mr = MaintenanceRequest(room_id=rooms[1].id, vendor_id=1, deskripsi='AC tidak dingin', prioritas='normal', status='diproses', catatan='Sudah dihubungi teknisi')
    db.session.add(mr)
    db.session.commit()

c = app.test_client()

# ====================== 1. AUTH ======================
print("\n=== 1. AUTH ===")
resp = c.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
check('1.1 Admin login 200', resp.status_code == 200)
check('1.1b Admin dashboard', b'Dashboard' in resp.data or b'Kamar' in resp.data or 'dashboard' in resp.request.path)

c.get('/auth/logout', follow_redirects=True)
resp = c.post('/auth/login', data={'username': 'admin', 'password': 'wrong'}, follow_redirects=True)
check('1.2 Invalid login rejected', b'salah' in resp.data or b'error' in resp.data or b'Salah' in resp.data)

c.get('/auth/logout', follow_redirects=True)
resp = c.post('/auth/login', data={'username': '', 'password': ''}, follow_redirects=True)
check('1.3 Empty login rejected', b'wajib' in resp.data or b'Wajib' in resp.data)

resp = c.get('/auth/register', follow_redirects=True)
check('1.4 Register page loads', resp.status_code == 200 and b'Daftar' in resp.data)

resp = c.post('/auth/register', data={
    'username': 'testuser99', 'email': 'test99@test.com', 'password': 'test123',
    'confirm_password': 'test123', 'nama_lengkap': 'Test User 99',
    'no_telepon': '08999999999', 'alamat': 'Test Address',
}, follow_redirects=True)
check('1.5 Register success', b'berhasil' in resp.data or 'login' in resp.request.path)

resp = c.post('/auth/register', data={
    'username': 'testuser99', 'email': 'test99b@test.com', 'password': 'test123',
    'confirm_password': 'test123', 'nama_lengkap': 'Test Dupe',
}, follow_redirects=True)
check('1.6 Register duplicate user blocked', b'sudah' in resp.data)

resp = c.post('/auth/register', data={
    'username': 'testuser98', 'email': 'test98@test.com', 'password': 'test123',
    'confirm_password': 'different', 'nama_lengkap': 'Test Mismatch',
}, follow_redirects=True)
check('1.7 Register password mismatch blocked', b'tidak cocok' in resp.data)

resp = c.get('/auth/logout', follow_redirects=True)
check('1.8 Logout -> login page', b'Masuk' in resp.data or 'login' in resp.request.path)

resp = c.get('/dashboard/admin', follow_redirects=True)
check('1.9 Guest blocked from dashboard', b'Masuk' in resp.data or 'login' in resp.request.path)

# ====================== 2. ONBOARDING & APPROVAL ======================
print("\n=== 2. ONBOARDING & APPROVAL ===")
resp = c.get('/onboarding/', follow_redirects=True)
check('2.1 Public room listing 200', resp.status_code == 200 and b'Kamar' in resp.data)

resp = c.get('/onboarding/kamar', follow_redirects=True)
check('2.2 Public kamar page', resp.status_code == 200)

resp = c.get('/onboarding/kamar/1', follow_redirects=True)
check('2.3 Room detail', resp.status_code == 200)

resp = c.get('/onboarding/kamar/999', follow_redirects=True)
check('2.4 Nonexistent room 404', resp.status_code == 404)

resp = c.post('/onboarding/daftar/2', data={'tanggal_masuk': '2026-08-01', 'durasi': 3}, follow_redirects=True)
check('2.5 Register w/o login -> login page', b'Masuk' in resp.data or 'login' in resp.request.path)

c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'agus', 'password': 'client123'}, follow_redirects=True)
resp = c.post('/onboarding/daftar/2', data={'tanggal_masuk': '2026-08-01', 'durasi': 3}, follow_redirects=True)
check('2.6 Client booking creates pending', b'persetujuan' in resp.data or b'menunggu' in resp.data)

resp = c.get('/dashboard/client', follow_redirects=True)
check('2.7 Client sees pending booking', b'menunggu' in resp.data)

c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
resp = c.get('/dashboard/admin', follow_redirects=True)
check('2.8 Admin sees pending alert', b'persetujuan' in resp.data or b'menunggu' in resp.data)

with app.app_context():
    from models import Booking
    pending = Booking.query.filter_by(status='pending').first()
if pending:
    resp = c.post(f'/dashboard/booking/{pending.id}/approve', follow_redirects=True)
    check('2.9 Approve booking', b'berhasil' in resp.data or b'disetujui' in resp.data)
else:
    check('2.9 Approve booking - no pending to test', False, "No pending booking found")

c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'agus', 'password': 'client123'}, follow_redirects=True)
resp = c.get('/dashboard/client', follow_redirects=True)
check('2.10 Client sees approved booking', b'Kamar' in resp.data or b'102' in resp.data)

# ====================== 3. ADMIN DASHBOARD ======================
print("\n=== 3. ADMIN DASHBOARD ===")
c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
resp = c.get('/dashboard/admin', follow_redirects=True)
check('3.1 Admin dashboard 200', resp.status_code == 200)
check('3.2 Stats present', b'Kamar' in resp.data or b'Penghuni' in resp.data or b'pemasukan' in resp.data)

# ====================== 4. ROOMS ======================
print("\n=== 4. ROOMS ===")
resp = c.get('/rooms/', follow_redirects=True)
check('4.1 Room list', resp.status_code == 200 and b'101' in resp.data)

resp = c.get('/rooms/1', follow_redirects=True)
check('4.2 Room detail', resp.status_code == 200)

resp = c.get('/rooms/tambah', follow_redirects=True)
check('4.3 Create form GET', resp.status_code == 200 and b'Tambah' in resp.data)

resp = c.post('/rooms/tambah', data={
    'nomor_kamar': '301', 'lantai': 3, 'tipe': 'VIP',
    'harga_per_bulan': '5000000', 'ukuran': '24m2',
    'fasilitas': 'AC, TV, Kulkas', 'status': 'tersedia',
    'deskripsi': 'Kamar VIP lantai 3',
}, follow_redirects=True)
check('4.4 Create room', b'berhasil' in resp.data)

resp = c.post('/rooms/tambah', data={
    'nomor_kamar': '301', 'lantai': 3, 'tipe': 'Reguler', 'harga_per_bulan': '1000000',
}, follow_redirects=True)
check('4.5 Create duplicate room blocked', b'sudah' in resp.data)

resp = c.post('/rooms/tambah', data={
    'nomor_kamar': '', 'lantai': 1, 'tipe': 'Reguler', 'harga_per_bulan': '1000000',
}, follow_redirects=True)
check('4.6 Empty room name blocked', b'wajib' in resp.data or b'Wajib' in resp.data)

resp = c.get('/rooms/edit/1', follow_redirects=True)
check('4.7 Edit form GET', resp.status_code == 200)

resp = c.post('/rooms/edit/1', data={
    'nomor_kamar': '101', 'lantai': 1, 'tipe': 'Reguler',
    'harga_per_bulan': '2000000', 'fasilitas': 'AC, Kasur Baru', 'status': 'terisi',
}, follow_redirects=True)
check('4.8 Edit room', b'berhasil' in resp.data)

resp = c.post('/rooms/hapus/1', follow_redirects=True)
check('4.9 Delete occupied room blocked', b'tidak bisa' in resp.data or b'terisi' in resp.data)

# ====================== 5. CLIENTS ======================
print("\n=== 5. CLIENTS ===")
resp = c.get('/clients/', follow_redirects=True)
check('5.1 Client list 200', resp.status_code == 200 and b'Budi' in resp.data)

resp = c.get('/clients/2', follow_redirects=True)
check('5.2 Client detail 200', resp.status_code == 200)

resp = c.get('/clients/edit/2', follow_redirects=True)
check('5.3 Edit client form GET', resp.status_code == 200)

resp = c.post('/clients/edit/2', data={
    'nama_lengkap': 'Budi Santoso Update', 'email': 'budi@email.com',
    'no_telepon': '08111111111',
}, follow_redirects=True)
check('5.4 Edit client', b'berhasil' in resp.data)

resp = c.post('/clients/nonaktifkan/2', follow_redirects=True)
check('5.5 Toggle active', (b'dinonaktifkan' in resp.data or b'berhasil' in resp.data))

resp = c.post('/clients/nonaktifkan/2', follow_redirects=True)
check('5.5b Toggle back active', (b'diaktifkan' in resp.data or b'berhasil' in resp.data))

# ====================== 6. PAYMENTS ======================
print("\n=== 6. PAYMENTS ===")
resp = c.get('/payments/', follow_redirects=True)
check('6.1 Payment list 200', resp.status_code == 200)

resp = c.get('/payments/tambah', follow_redirects=True)
check('6.2 Create payment form GET', resp.status_code == 200)

resp = c.post('/payments/tambah', data={
    'booking_id': 1, 'jumlah': '1500000',
    'bulan_dibayar_untuk': '2026-07', 'metode_bayar': 'transfer',
    'status': 'lunas', 'catatan': 'Test payment',
}, follow_redirects=True)
check('6.3 Create payment', b'berhasil' in resp.data)

resp = c.post('/payments/tambah', data={
    'booking_id': 1, 'jumlah': '0', 'metode_bayar': 'transfer',
}, follow_redirects=True)
check('6.4 Zero payment rejected', b'lebih' in resp.data)

resp = c.get('/payments/edit/1', follow_redirects=True)
check('6.5 Edit form GET', resp.status_code == 200)

resp = c.post('/payments/edit/1', data={
    'jumlah': '2000000', 'tanggal_bayar': '2026-07-16',
    'bulan_dibayar_untuk': '2026-07', 'metode_bayar': 'tunai',
    'status': 'lunas', 'catatan': 'Updated',
}, follow_redirects=True)
check('6.6 Edit payment', b'berhasil' in resp.data)

resp = c.post('/payments/hapus/1', follow_redirects=True)
check('6.7 Delete payment', b'berhasil' in resp.data)

resp = c.get('/payments/notifikasi/1', follow_redirects=False)
check('6.8 WA notification redirect', resp.status_code in (302, 303))

# ====================== 7. ACCOUNTING ======================
print("\n=== 7. ACCOUNTING ===")
resp = c.get('/accounting/?tahun=2026&bulan=7', follow_redirects=True)
check('7.1 Accounting page 200', resp.status_code == 200)

resp = c.get('/accounting/pengeluaran/tambah', follow_redirects=True)
check('7.2 Expense form GET', resp.status_code == 200)

resp = c.post('/accounting/pengeluaran/tambah', data={
    'kategori': 'listrik', 'jumlah': '750000',
    'tanggal': '2026-07-15', 'deskripsi': 'Test expense',
}, follow_redirects=True)
check('7.3 Create expense', b'berhasil' in resp.data)

resp = c.post('/accounting/pengeluaran/tambah', data={
    'kategori': 'listrik', 'jumlah': '0', 'tanggal': '2026-07-15',
}, follow_redirects=True)
check('7.4 Zero expense rejected', b'lebih' in resp.data)

resp = c.get('/accounting/pengeluaran/edit/1', follow_redirects=True)
check('7.5 Edit expense form GET', resp.status_code == 200)

resp = c.post('/accounting/pengeluaran/edit/1', data={
    'kategori': 'air', 'jumlah': '600000',
    'tanggal': '2026-07-10', 'deskripsi': 'Updated',
}, follow_redirects=True)
check('7.6 Edit expense', b'berhasil' in resp.data)

resp = c.get('/accounting/laporan?tahun=2026', follow_redirects=True)
check('7.7 Annual report 200', resp.status_code == 200)

# ====================== 8. MAINTENANCE ======================
print("\n=== 8. MAINTENANCE ===")
resp = c.get('/maintenance/', follow_redirects=True)
check('8.1 Maintenance list 200', resp.status_code == 200)

resp = c.get('/maintenance/tambah', follow_redirects=True)
check('8.2 Create maintenance form GET', resp.status_code == 200)

resp = c.post('/maintenance/tambah', data={
    'room_id': 2, 'vendor_id': 1, 'deskripsi': 'Test AC maintenance',
    'prioritas': 'tinggi', 'catatan': 'Segera diperbaiki',
}, follow_redirects=True)
check('8.3 Create maintenance', b'berhasil' in resp.data)

resp = c.post('/maintenance/tambah', data={
    'room_id': 2, 'deskripsi': '',
}, follow_redirects=True)
check('8.4 Empty desc rejected', b'wajib' in resp.data)

resp = c.get('/maintenance/edit/1', follow_redirects=True)
check('8.5 Edit maintenance form GET', resp.status_code == 200)

resp = c.post('/maintenance/edit/1', data={
    'room_id': 2, 'vendor_id': 1, 'deskripsi': 'AC sudah diperbaiki',
    'prioritas': 'normal', 'status': 'selesai', 'biaya': '500000',
}, follow_redirects=True)
check('8.6 Edit maintenance', b'berhasil' in resp.data)

resp = c.post('/maintenance/hapus/1', follow_redirects=True)
check('8.7 Delete maintenance', b'berhasil' in resp.data)

# ====================== 9. VENDORS ======================
print("\n=== 9. VENDORS ===")
resp = c.get('/maintenance/vendor', follow_redirects=True)
check('9.1 Vendor list 200', resp.status_code == 200 and b'Teknisi AC' in resp.data or b'Vendor' in resp.data)

resp = c.get('/maintenance/vendor/tambah', follow_redirects=True)
check('9.2 Vendor form GET', resp.status_code == 200)

resp = c.post('/maintenance/vendor/tambah', data={
    'nama': 'Tukang Ledeng', 'no_telepon': '08999999999',
    'kategori': 'air', 'alamat': 'Jakarta', 'catatan': 'Handal',
}, follow_redirects=True)
check('9.3 Create vendor', b'berhasil' in resp.data)

resp = c.post('/maintenance/vendor/tambah', data={'nama': ''}, follow_redirects=True)
check('9.4 Empty vendor name blocked', b'wajib' in resp.data)

resp = c.get('/maintenance/vendor/edit/1', follow_redirects=True)
check('9.5 Edit vendor form GET', resp.status_code == 200)

resp = c.post('/maintenance/vendor/edit/1', data={
    'nama': 'Teknisi AC Update', 'no_telepon': '08666666666', 'kategori': 'maintenance',
}, follow_redirects=True)
check('9.6 Edit vendor', b'berhasil' in resp.data)

resp = c.get('/maintenance/vendor/wa/1', follow_redirects=False)
check('9.7 Vendor WA link redirect', resp.status_code in (302, 303))

resp = c.post('/maintenance/vendor/hapus/1', follow_redirects=True)
check('9.8 Delete vendor', b'berhasil' in resp.data)

# ====================== 10. NEW FEATURES ======================
print("\n=== 10. NEW FEATURES ===")
c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

# Auto-proses
resp = c.post('/dashboard/auto-proses', follow_redirects=True)
check('10.1 Auto-proses runs', resp.status_code == 200)

# Create pending booking for tolak test
c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'eko', 'password': 'client123'}, follow_redirects=True)
resp = c.post('/onboarding/daftar/6', data={'tanggal_masuk': '2026-09-01', 'durasi': 3}, follow_redirects=True)
c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

with app.app_context():
    from models import Booking, Notification
    pending = Booking.query.filter_by(status='pending').first()
if pending:
    resp = c.post(f'/dashboard/booking/{pending.id}/tolak', follow_redirects=True)
    check('10.2 Tolak booking', b'ditolak' in resp.data)
else:
    check('10.2 Tolak booking - no pending to test', False, "No pending booking found")

# Notification mark as read
c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
with app.app_context():
    from models import Notification
    n = Notification.query.first()
if n:
    resp = c.post(f'/dashboard/notifikasi/baca/{n.id}', follow_redirects=True)
    check('10.3 Mark notif read', resp.status_code == 200)

    resp = c.post('/dashboard/notifikasi/baca-semua', follow_redirects=True)
    check('10.4 Mark all notif read', b'dibaca' in resp.data or resp.status_code == 200)

# Client dashboard notif count
c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'budi', 'password': 'client123'}, follow_redirects=True)
resp = c.get('/dashboard/client', follow_redirects=True)
check('10.5 Client dashboard loads', resp.status_code == 200)
check('10.6 Notif badge present', b'Notifikasi' in resp.data)

# ====================== 11. WA AUTOMATION ======================
print("\n=== 11. WA AUTOMATION ===")
c.get('/auth/logout', follow_redirects=True)
c.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

# Payment receipt
with app.app_context():
    from models import Payment, Booking
    bok = Booking.query.filter_by(status='aktif').first()
    pay = Payment(booking_id=bok.id, jumlah=1500000, tanggal_bayar=date.today(), bulan_dibayar_untuk='2026-08', metode_bayar='transfer', status='lunas')
    db.session.add(pay)
    db.session.commit()
    pid = pay.id
resp = c.get(f'/payments/resi/{pid}', follow_redirects=False)
check('11.1 Payment receipt redirects WA', resp.status_code in (302, 303))

# Maintenance notif penghuni
with app.app_context():
    from models import MaintenanceRequest
    mr = MaintenanceRequest(room_id=1, vendor_id=1, deskripsi='Test client notif', prioritas='tinggi', status='selesai', biaya=100000)
    db.session.add(mr)
    db.session.commit()
    mr_id = mr.id
resp = c.get(f'/maintenance/notif-penghuni/{mr_id}', follow_redirects=False)
check('11.2 Maintenance notif redirects WA', resp.status_code in (302, 303))

# Edge: no vendor assigned
with app.app_context():
    mr2 = MaintenanceRequest(room_id=1, vendor_id=None, deskripsi='No vendor test', prioritas='normal', status='selesai')
    db.session.add(mr2)
    db.session.commit()
    mr2_id = mr2.id
resp = c.get(f'/maintenance/notif-penghuni/{mr2_id}', follow_redirects=False)
check('11.3 Notif without vendor redirects WA', resp.status_code in (302, 303))

# Edge: receipt with unpaid balance
with app.app_context():
    from models import Booking
    bok = Booking.query.filter_by(status='aktif').first()
    p2 = Payment(booking_id=bok.id, jumlah=500000, tanggal_bayar=date.today(), bulan_dibayar_untuk='2026-09', metode_bayar='transfer', status='lunas')
    db.session.add(p2)
    db.session.commit()
    p2_id = p2.id
resp = c.get(f'/payments/resi/{p2_id}', follow_redirects=False)
check('11.4 Receipt with partial balance redirects WA', resp.status_code in (302, 303))

# ====================== SUMMARY ======================
print(f"\n{'='*60}")
print(f"RESULTS: {len(passed)} passed, {len(failed)} failed, {len(passed)+len(failed)} total")
print(f"{'='*60}")
for f in failed:
    print(f"  {f}")
print()
for p in passed:
    print(f"  OK {p}")

sys.exit(len(failed))
