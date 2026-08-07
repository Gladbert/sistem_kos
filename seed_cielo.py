"""Seed Cielo House -- raw SQL (avoids ORM sequence cache issues)."""
import os, sys
from datetime import date
from dotenv import load_dotenv
load_dotenv()

from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text

DB = os.getenv("DATABASE_URL")
engine = create_engine(DB, connect_args={"connect_timeout": 30})

BULAN_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Mei": 5, "Jun": 6, "Jul": 7, "Agu": 8,
    "Sep": 9, "Okt": 10, "Nov": 11, "Des": 12,
}

def parse_date(s):
    if not s:
        return None
    parts = s.strip().split()
    day, mon = int(parts[0]), BULAN_MAP[parts[1]]
    return f"2026-{mon:02d}-{day:02d}"

ROOMS_DATA = [
    # No, Nama, Kamar, Simbol, Tipe, Tanggal, Harga, Bayar, Blok
    (1,  "susanti",      "b01", "Standard (Murni)",       "05 May",  850000,  "bca",     "B"),
    (2,  "devita",       "b02", "Standard Lebih Besar",   "26 Apr", 1100000,  "mandiri", "B"),
    (3,  "shenny",       "b03", "Standard (Murni)",       "08 May",  850000,  "bca",     "B"),
    (4,  "halizah",      "b05", "VIP Luas Kecil",         "11 May", 1350000,  "bca",     "B"),
    (5,  "cherryn",      "b06", "Standard (Murni)",       "02 May",  850000,  "bca",     "B"),
    (6,  "sefiana",      "b07", "Standard (Murni)",       "03 May",  850000,  "bca",     "B"),
    (7,  "evy",          "b08", "VIP Luas Kecil",         "04 May", 1350000,  "bca",     "B"),
    (8,  "ghaidah",      "b09", "Standard Lebih Besar",   "08 May", 1100000,  "bca",     "B"),
    (9,  "yumicho",      "b10", "Standard (Murni)",       "16 May",  850000,  "bca",     "B"),
    (10, "pandaraman",   "b11", "Standard (Murni)",       "11 May",  850000,  "bca",     "B"),
    (11, "daria",        "b12", "Standard (Murni)",       "04 May",  850000,  "bca",     "B"),
    (12, "gioshelyn",    "b15", "Standard (Murni)",       "03 May",  850000,  "bca",     "B"),
    (13, "puji",         "b16", "Standard Lebih Besar",   "02 May", 1100000,  "bca",     "B"),
    (None, None,         "b17", "Standard Lebih Besar",   None,            0,  "kosong", "B"),
    (14, "lawdia",       "b18", "VIP (Murni)",            "01 May", 1500000,  "bca",     "B"),
    (15, "michelle ame", "b19", "VIP (Murni)",            "10 May", 1500000,  "bca",     "B"),
    (None, None,         "b20", "VIP (Murni)",            None,            0,  "kosong", "B"),
    (None, None,         "b21", "VIP (Murni)",            None,            0,  "kosong", "B"),
    (16, "sulfa",        "b22", "VIP (Murni)",            "08 May", 1500000,  "bca",     "B"),
    (None, None,         "b23", "VIP (Murni)",            None,            0,  "kosong", "B"),

    (17, "nova",         "a01", "Standard (Murni)",       "10 May",  850000,  "bca",     "A"),
    (18, "joane",        "a02", "Standard Lebih Besar",   "03 May", 1100000,  "bca",     "A"),
    (19, "therecia",     "a03", "Standard Lebih Besar",   "04 May",  600000,  "bca",     "A"),
    (20, "cania",        "a05", "Standard Lebih Besar",   "02 Jun", 1100000,  "bca",     "A"),
    (None, None,         "a06", "VIP Luas Kecil",         None,            0,  "kosong", "A"),
    (21, "melinda",      "a07", "Standard (Murni)",       "07 May",  850000,  "bca",     "A"),
    (22, "dhira",        "a08", "Standard (Murni)",       "08 May",  850000,  "bca",     "A"),
    (None, None,         "a09", "VIP Luas Kecil",         None,            0,  "kosong", "A"),
    (23, "eva cristiana","a10", "Standard Lebih Besar",   "04 May", 1100000,  "bca",     "A"),
    (24, "amelia",       "a11", "Standard (Murni)",       "01 May",  850000,  "bca",     "A"),
    (25, "amel",         "a12", "Standard (Murni)",       "02 May",  850000,  "bca",     "A"),
    (26, "kezia",        "a15", "Standard (Murni)",       "10 May",  850000,  "bca",     "A"),
    (27, "fernanda",     "a16", "Standard (Murni)",       "04 May",  850000,  "bca",     "A"),
    (None, None,         "a17", "Standard Lebih Besar",   None,            0,  "kosong", "A"),
    (None, None,         "a18", "Standard Lebih Besar",   None,            0,  "kosong", "A"),
    (28, "vidya",        "a19", "VIP (Murni)",            "10 May", 1500000,  "bca",     "A"),
    (None, None,         "a20", "VIP (Murni)",            None,            0,  "kosong", "A"),
    (None, None,         "a21", "VIP (Murni)",            None,            0,  "kosong", "A"),
    (29, "wulan",        "a22", "VIP (Murni)",            "03 May", 1500000,  "bca",     "A"),
    (30, "giovannya",    "a23", "VIP (Murni)",            "10 May", 1500000,  "mandiri", "A"),
    (31, "yurisa",       "a25", "VIP (Murni)",            "10 May", 1500000,  "bca",     "A"),
]

PW_HASH = generate_password_hash("password123")
KOS_ID = 1  # Cielo House
BULAN_INI = "2026-08"

with engine.connect() as c:
    created_rooms = 0
    created_users = 0
    created_bookings = 0
    created_payments = 0

    for idx, nama, kamar, tipe, tgl_str, harga, bayar, blok in ROOMS_DATA:
        fasilitas = "AC, Lemari, Kasur, Meja" if "VIP" in tipe else "Kasur, Lemari, Kipas"
        ukuran = "4x6" if "VIP" in tipe else ("4x5" if "Besar" in tipe else "3x4")
        lantai = 1 if blok == "A" else 2
        status = "terisi" if nama else "tersedia"

        # Upsert room
        r = c.execute(text("SELECT id FROM rooms WHERE kos_id = :k AND nomor_kamar = :n"),
                       {"k": KOS_ID, "n": kamar}).fetchone()
        if r:
            room_id = r[0]
            c.execute(text("UPDATE rooms SET tipe=:t, harga_per_bulan=:h, lantai=:l, fasilitas=:f, ukuran=:u, status=:s WHERE id=:id"),
                       {"t": tipe, "h": harga, "l": lantai, "f": fasilitas, "u": ukuran, "s": status, "id": room_id})
        else:
            r = c.execute(text("""INSERT INTO rooms (kos_id, nomor_kamar, lantai, tipe, harga_per_bulan, fasilitas, ukuran, status)
                VALUES (:k, :n, :l, :t, :h, :f, :u, :s) RETURNING id"""),
                {"k": KOS_ID, "n": kamar, "l": lantai, "t": tipe, "h": harga, "f": fasilitas, "u": ukuran, "s": status})
            room_id = r.fetchone()[0]
            created_rooms += 1

        if not nama:
            continue

        # User
        username = nama.lower().replace(" ", "")
        r = c.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username}).fetchone()
        if r:
            user_id = r[0]
        else:
            r = c.execute(text("""INSERT INTO users (username, email, password_hash, role, nama_lengkap, no_telepon, is_active)
                VALUES (:u, :e, :p, 'client', :n, :t, true) RETURNING id"""),
                {"u": username, "e": f"{username}@cielo.test", "p": PW_HASH, "n": nama.title(), "t": f"08{10000000 + idx:08d}"})
            user_id = r.fetchone()[0]
            created_users += 1

        # UserKos
        c.execute(text("""INSERT INTO user_kos (user_id, kos_id, role)
            VALUES (:u, :k, 'client') ON CONFLICT (user_id, kos_id) DO NOTHING"""),
            {"u": user_id, "k": KOS_ID})

        # Booking
        tgl_masuk = parse_date(tgl_str)
        r = c.execute(text("SELECT id FROM bookings WHERE room_id = :r AND status = 'aktif'"),
                       {"r": room_id}).fetchone()
        if not r:
            r = c.execute(text("""INSERT INTO bookings (user_id, room_id, tanggal_masuk, tanggal_keluar, status, deposit, catatan)
                VALUES (:u, :r, :tm, :tk, 'aktif', :d, :c) RETURNING id"""),
                {"u": user_id, "r": room_id, "tm": tgl_masuk,
                 "tk": f"2027-{tgl_masuk[5:7]}-{tgl_masuk[8:10]}",
                 "d": harga, "c": f"Metode bayar: {bayar}"})
            booking_id = r.fetchone()[0]
            created_bookings += 1
        else:
            booking_id = r[0]

        # Payment for August 2026
        r = c.execute(text("SELECT id FROM payments WHERE booking_id = :b AND bulan_dibayar_untuk = :bu AND status = 'lunas'"),
                       {"b": booking_id, "bu": BULAN_INI}).fetchone()
        if not r:
            c.execute(text("""INSERT INTO payments (booking_id, jumlah, tanggal_bayar, bulan_dibayar_untuk, metode_bayar, status, catatan)
                VALUES (:b, :j, '2026-08-01', :bu, :m, 'lunas', :c)"""),
                {"b": booking_id, "j": harga, "bu": BULAN_INI,
                 "m": bayar if bayar in ("bca","mandiri","transfer") else "transfer",
                 "c": f"Auto-seed: {nama} - {kamar}"})
            created_payments += 1

    c.commit()

    # Verify
    cnt = c.execute(text("SELECT count(*) FROM rooms WHERE kos_id = 1")).scalar()
    occ = c.execute(text("SELECT count(*) FROM rooms WHERE kos_id = 1 AND status = 'terisi'")).scalar()
    print(f"\n=== Done ===")
    print(f"Rooms created/updated: {created_rooms}")
    print(f"Users created: {created_users}")
    print(f"Bookings created: {created_bookings}")
    print(f"Payments created (Aug 2026): {created_payments}")
    print(f"Total rooms: {cnt}, Occupied: {occ}")
