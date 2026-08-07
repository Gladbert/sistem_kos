"""Production seed script for Cielo House demo data."""
import os
import sys
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

import psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL")

def seed():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # ── KOS ──
    cur.execute("""
        INSERT INTO kos (nama, alamat, deskripsi, is_active)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT DO NOTHING
        RETURNING id
    """, ("Cielo House", "Jl. Melati No. 25, Kemang, Jakarta Selatan", 
          "Kos premium untuk mahasiswa dan karyawan profesional. Lokasi strategis dekat MRT dan mall."))
    kos_id = cur.fetchone()
    if kos_id is None:
        cur.execute("SELECT id FROM kos WHERE nama = %s", ("Cielo House",))
        kos_id = cur.fetchone()
    kos_id = kos_id[0]

    # ── USERS ──
    users_data = [
        # (username, email, role, nama_lengkap, no_telepon, alamat)
        ("admin", "admin@cielohouse.com", "admin", "Admin Cielo", "081211112222", "Kantor Cielo House"),
        ("management", "mgmt@cielohouse.com", "management", "Rina Wijaya", "081211113333", "Kantor Cielo House"),
        ("budi", "budi.santoso@email.com", "client", "Budi Santoso", "08123456001", "Jl. Sudirman 10, Jakarta"),
        ("siti", "siti.rahayu@email.com", "client", "Siti Rahayu", "08123456002", "Jl. Gatot Subroto 15, Jakarta"),
        ("agus", "agus.wijaya@email.com", "client", "Agus Wijaya", "08123456003", "Jl. Thamrin 20, Jakarta"),
        ("dewi", "dewi.lestari@email.com", "client", "Dewi Lestari", "08123456004", "Jl. Kuningan 5, Jakarta"),
        ("eko", "eko.prasetyo@email.com", "client", "Eko Prasetyo", "08123456005", "Jl. Senopati 8, Jakarta"),
        ("maya", "maya.anggraini@email.com", "client", "Maya Anggraini", "08123456006", "Jl. SCBD 12, Jakarta"),
        ("rudi", "rudi.hermawan@email.com", "client", "Rudi Hermawan", "08123456007", "Jl. Rasuna Said 3, Jakarta"),
        ("lisa", "lisa.putri@email.com", "client", "Lisa Putri", "08123456008", "Jl. Sudirman 45, Jakarta"),
    ]

    user_ids = {}
    for u in users_data:
        cur.execute("""
            INSERT INTO users (username, email, password_hash, role, nama_lengkap, no_telepon, alamat)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            RETURNING id
        """, (u[0], u[1], generate_password_hash("admin123" if u[2] == "admin" else 
              "mgmt123" if u[2] == "management" else "client123"), u[2], u[3], u[4], u[5]))
        row = cur.fetchone()
        if row:
            user_ids[u[0]] = row[0]
        else:
            cur.execute("SELECT id FROM users WHERE username = %s", (u[0],))
            user_ids[u[0]] = cur.fetchone()[0]

    # ── ROOMS ──
    rooms_data = [
        # (nomor_kamar, lantai, tipe, harga_per_bulan, ukuran, fasilitas, status)
        ("A-01", 1, "Reguler", 1500000, "3x4m", "AC, WiFi, Kasur, Lemari", "terisi"),
        ("A-02", 1, "Reguler", 1500000, "3x4m", "AC, WiFi, Kasur, Lemari", "terisi"),
        ("A-03", 1, "Reguler", 1500000, "3x4m", "AC, WiFi, Kasur, Lemari", "tersedia"),
        ("B-01", 2, "VIP", 2500000, "4x5m", "AC, WiFi, Kasur, Lemari, TV, Kulkas, Meja Kerja", "terisi"),
        ("B-02", 2, "VIP", 2500000, "4x5m", "AC, WiFi, Kasur, Lemari, TV, Kulkas, Meja Kerja", "terisi"),
        ("B-03", 2, "VIP", 2500000, "4x5m", "AC, WiFi, Kasur, Lemari, TV, Kulkas, Meja Kerja", "tersedia"),
        ("C-01", 3, "Suite", 3500000, "5x6m", "AC, WiFi, Queen Bed, Lemari, TV, Kulkas, Meja Kerja, Kamar Mandi Dalam", "terisi"),
        ("C-02", 3, "Suite", 3500000, "5x6m", "AC, WiFi, Queen Bed, Lemari, TV, Kulkas, Meja Kerja, Kamar Mandi Dalam", "maintenance"),
        ("C-03", 3, "Suite", 3500000, "5x6m", "AC, WiFi, Queen Bed, Lemari, TV, Kulkas, Meja Kerja, Kamar Mandi Dalam", "tersedia"),
    ]

    room_ids = {}
    for r in rooms_data:
        cur.execute("""
            INSERT INTO rooms (kos_id, nomor_kamar, lantai, tipe, harga_per_bulan, ukuran, fasilitas, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (kos_id, nomor_kamar) DO NOTHING
            RETURNING id
        """, (kos_id, *r))
        row = cur.fetchone()
        if row:
            room_ids[r[0]] = row[0]
        else:
            cur.execute("SELECT id FROM rooms WHERE kos_id = %s AND nomor_kamar = %s", (kos_id, r[0]))
            room_ids[r[0]] = cur.fetchone()[0]

    # ── VENDORS ──
    vendors_data = [
        ("PT Bersih Sejahtera", "081111222333", "kebersihan", "Jl. Pahlawan 10, Jakarta", "Vendor kebersihan mingguan"),
        ("Toko Bangunan Jaya", "081111222444", "perbaikan", "Jl. Industri 5, Jakarta", "Material bangunan dan perbaikan"),
        ("Toko Elektronik Cahaya", "081111222555", "elektronik", "Jl. Mangga Dua 8, Jakarta", "AC, TV, kulkas dan servis"),
        ("Laundry Express", "081111222666", "laundry", "Jl. Kemang Raya 12, Jakarta", "Laundry kilat 3 jam"),
        ("Tukang Pipa Bandung", "081111222777", "perbaikan", "Jl. Ciputat Raya 20, Jakarta", "Perbaikan pipa dan saluran air"),
    ]

    vendor_ids = {}
    for v in vendors_data:
        cur.execute("""
            INSERT INTO vendors (nama, no_telepon, kategori, alamat, catatan)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, v)
        row = cur.fetchone()
        if row:
            vendor_ids[v[0]] = row[0]
        else:
            cur.execute("SELECT id FROM vendors WHERE nama = %s", (v[0],))
            vendor_ids[v[0]] = cur.fetchone()[0]

    # ── BOOKINGS (active, pending, completed) ──
    today = date.today()
    bookings_data = [
        # Active bookings
        (user_ids["budi"], room_ids["A-01"], today - timedelta(days=90), today + timedelta(days=275), "aktif", 1500000),
        (user_ids["siti"], room_ids["A-02"], today - timedelta(days=60), today + timedelta(days=305), "aktif", 1500000),
        (user_ids["agus"], room_ids["B-01"], today - timedelta(days=45), today + timedelta(days=320), "aktif", 2500000),
        (user_ids["dewi"], room_ids["B-02"], today - timedelta(days=30), today + timedelta(days=335), "aktif", 2500000),
        (user_ids["eko"], room_ids["C-01"], today - timedelta(days=15), today + timedelta(days=350), "aktif", 3500000),
        # Pending bookings
        (user_ids["maya"], room_ids["A-03"], today + timedelta(days=7), today + timedelta(days=372), "pending", 1500000),
        (user_ids["rudi"], room_ids["B-03"], today + timedelta(days=14), today + timedelta(days=379), "pending", 2500000),
    ]

    booking_ids = []
    for b in bookings_data:
        cur.execute("""
            INSERT INTO bookings (user_id, room_id, tanggal_masuk, tanggal_keluar, status, deposit, catatan)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (*b, "Booking via demo"))
        row = cur.fetchone()
        if row:
            booking_ids.append(row[0])
        else:
            cur.execute("SELECT id FROM bookings WHERE user_id = %s AND room_id = %s", (b[0], b[1]))
            row = cur.fetchone()
            if row:
                booking_ids.append(row[0])

    # ── PAYMENTS (multiple months for active bookings) ──
    metode = ["transfer", "tunai", "e_wallet", "transfer", "tunai"]
    for i, b_id in enumerate(booking_ids[:5]):  # Only active bookings
        for months_ago in range(3, -1, -1):
            pay_date = today - timedelta(days=months_ago * 30)
            bulan = pay_date.strftime("%Y-%m")
            cur.execute("""
                INSERT INTO payments (booking_id, jumlah, tanggal_bayar, bulan_dibayar_untuk, metode_bayar, status, catatan)
                VALUES (%s, %s, %s, %s, %s, 'lunas', %s)
                ON CONFLICT DO NOTHING
            """, (b_id, [1500000, 1500000, 2500000, 2500000, 3500000][i], pay_date, bulan, 
                  metode[i % len(metode)], f"Pembayaran bulan {bulan}"))

    # ── EXPENSES ──
    expenses_data = [
        ("kebersihan", 500000, today - timedelta(days=5), "Pembersihan AC semua kamar", vendor_ids["PT Bersih Sejahtera"]),
        ("perbaikan", 250000, today - timedelta(days=10), "Perbaikan keran kamar mandi B-01", vendor_ids["Tukang Pipa Bandung"]),
        ("utilitas", 3500000, today - timedelta(days=15), "Tagihan listrik bulan ini", None),
        ("utilitas", 800000, today - timedelta(days=15), "Tagihan air bulan ini", None),
        ("utilitas", 500000, today - timedelta(days=15), "Tagihan internet WiFi", None),
        ("elektronik", 1500000, today - timedelta(days=20), "Servis AC kamar C-02", vendor_ids["Toko Elektronik Cahaya"]),
        ("kebersihan", 300000, today - timedelta(days=25), "Cuci karpet dan gordyn", vendor_ids["PT Bersih Sejahtera"]),
        ("lainnya", 200000, today - timedelta(days=30), "Beli alat kebersihan", None),
        ("perbaikan", 750000, today - timedelta(days=35), "Cat ulang kamar A-03", vendor_ids["Toko Bangunan Jaya"]),
        ("keamanan", 1000000, today - timedelta(days=1), "Bayar satpam bulanan", None),
    ]

    for e in expenses_data:
        cur.execute("""
            INSERT INTO expenses (kos_id, kategori, jumlah, tanggal, deskripsi, vendor_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (kos_id, *e))

    # ── ROOM ITEMS ──
    items_data = [
        (room_ids["A-01"], [("AC Split 1PK", 1, "baik"), ("Kasur Single", 1, "baik"), ("Lemari 2 Pintu", 1, "baik")]),
        (room_ids["A-02"], [("AC Split 1PK", 1, "baik"), ("Kasur Single", 1, "baik"), ("Lemari 2 Pintu", 1, "baik")]),
        (room_ids["B-01"], [("AC Split 1.5PK", 1, "baik"), ("Kasur Queen", 1, "baik"), ("TV 32 inch", 1, "baik"), ("Kulkas Mini", 1, "baik")]),
        (room_ids["B-02"], [("AC Split 1.5PK", 1, "baik"), ("Kasur Queen", 1, "baik"), ("TV 32 inch", 1, "rusak"), ("Kulkas Mini", 1, "baik")]),
        (room_ids["C-01"], [("AC Split 2PK", 1, "baik"), ("Kasur King", 1, "baik"), ("TV 43 inch", 1, "baik"), ("Kulkas", 1, "baik"), ("Shower", 1, "baik")]),
    ]

    item_ids = {}
    for r_id, items in items_data:
        for item in items:
            cur.execute("""
                INSERT INTO room_items (room_id, nama, jumlah, kondisi)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (r_id, *item))
            row = cur.fetchone()
            if row:
                item_ids[(r_id, item[0])] = row[0]

    # ── MAINTENANCE REQUESTS ──
    maint_data = [
        (room_ids["B-02"], vendor_ids["Toko Elektronik Cahaya"], "TV tidak menyala, layar gelap", "tinggi",
         today - timedelta(days=3), "diproses", 350000),
        (room_ids["C-02"], vendor_ids["Tukang Pipa Bandung"], "Kamar mandi bocor, air rembes ke tembok", "kritis",
         today - timedelta(days=1), "diajukan", 0),
        (room_ids["A-01"], None, "Ganti bohlam lampu kamar mandi", "rendah",
         today - timedelta(days=7), "selesai", 50000),
        (room_ids["B-01"], vendor_ids["Toko Elektronik Cahaya"], "AC tidak dingin, perlu isi freon", "normal",
         today - timedelta(days=5), "diajukan", 0),
    ]

    for m in maint_data:
        cur.execute("""
            INSERT INTO maintenance_requests (room_id, vendor_id, deskripsi, prioritas, tanggal_masuk, status, biaya)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, m)

    # ── NOTIFICATIONS ──
    notifs = [
        (user_ids["budi"], "Selamat datang di Cielo House! Silakan cek jadwal pembayaran Anda.", "umum"),
        (user_ids["budi"], "Pembayaran bulan Juli 2025 telah diterima. Terima kasih!", "pembayaran"),
        (user_ids["siti"], "Pengingat: Pembayaran bulan Agustus jatuh tempo tanggal 5.", "pengingat"),
        (user_ids["agus"], "Permintaan perbaikan AC Anda sedang diproses.", "maintenance"),
        (user_ids["dewi"], "Selamat datang di Cielo House! Nikmati fasilitas premium kami.", "umum"),
        (user_ids["maya"], "Permintaan sewa kamar A-03 sedang menunggu persetujuan.", "booking"),
        (user_ids["admin"], "Ada 2 permintaan booking baru yang menunggu persetujuan.", "sistem"),
        (user_ids["admin"], "Maintenance request baru untuk kamar C-02 (prioritas kritis).", "sistem"),
    ]

    for n in notifs:
        cur.execute("""
            INSERT INTO notifications (user_id, pesan, jenis, dibaca)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (*n, n[1].startswith("Selamat")))  # Mark welcome as read

    # ── ANNOUNCEMENTS ──
    announcements = [
        ("Selamat Datang di Cielo House!", 
         "Selamat datang para penghuni Cielo House. Kami berkomitmen memberikan hunian yang nyaman dan aman. "
         "Jangan ragu menghubungi pengelola jika ada kebutuhan.", "normal", user_ids["admin"]),
        ("Jadwal Pembersihan AC Bulanan", 
         "Pembersihan AC rutin akan dilakukan setiap hari Sabtu minggu kedua. "
         "Pastikan kamar dapat diakses oleh teknisi.", "normal", user_ids["management"]),
        ("Perubahan Jam Malam", 
         "Mulai 1 September 2025, gerbang utama akan dikunci pukul 23:00. "
         "Harap hubungi satpam jika pulang terlambat.", "penting", user_ids["admin"]),
    ]

    for a in announcements:
        cur.execute("""
            INSERT INTO announcements (judul, isi, prioritas, created_by, ditampilkan)
            VALUES (%s, %s, %s, %s, TRUE)
            ON CONFLICT DO NOTHING
        """, a)

    # ── COMPLAINTS ──
    complaints = [
        (user_ids["budi"], kos_id, "Air Keran Lemah", "Air di kamar A-01 mengalir sangat lemah sejak 3 hari lalu.", "air", "diajukan"),
        (user_ids["siti"], kos_id, "WiFi Lambat", "Koneksi WiFi di lantai 1 sangat lambat saat malam hari.", "internet", "diproses"),
        (user_ids["agus"], kos_id, "Kebisingan Malam", "Ada penghuni yang sering berisik setelah jam 11 malam.", "keamanan", "selesai"),
        (user_ids["dewi"], kos_id, "Lampu Koridor Mati", "Lampu koridor lantai 2 mati, sangat gelap malam hari.", "fasilitas", "diajukan"),
    ]

    for c in complaints:
        cur.execute("""
            INSERT INTO complaints (user_id, kos_id, judul, deskripsi, kategori, status, tanggapan)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (*c, "Sedang ditindaklanjuti oleh teknisi." if c[5] in ("diproses", "selesai") else None))

    # ── ACTIVITY LOGS ──
    activities = [
        (user_ids["admin"], "Approve booking", "Kamar B-01 - Agus Wijaya", "Booking"),
        (user_ids["admin"], "Approve booking", "Kamar C-01 - Eko Prasetyo", "Booking"),
        (user_ids["management"], "Tambah pengeluaran", "Servis AC kamar C-02", "Expense"),
        (user_ids["admin"], "Buat pengumuman", "Jadwal Pembersihan AC Bulanan", "Announcement"),
        (user_ids["admin"], "Approve booking", "Kamar A-01 - Budi Santoso", "Booking"),
        (user_ids["management"], "Maintenance selesai", "Ganti bohlam kamar A-01", "Maintenance"),
    ]

    for a in activities:
        cur.execute("""
            INSERT INTO activity_logs (user_id, tindakan, deskripsi, model)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, a)

    conn.commit()

    # ── VERIFY ──
    tables = ["users", "kos", "rooms", "vendors", "bookings", "payments", 
              "expenses", "maintenance_requests", "notifications", "announcements",
              "complaints", "activity_logs", "room_items"]
    
    print("=== Cielo House Seed Complete ===\n")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        print(f"  {t}: {count}")

    print(f"\nLogin credentials:")
    print(f"  Admin:      admin / admin123")
    print(f"  Management: management / mgmt123")
    print(f"  Clients:    budi, siti, agus, dewi, eko, maya, rudi, lisa / client123")

    cur.close()
    conn.close()

if __name__ == "__main__":
    seed()
