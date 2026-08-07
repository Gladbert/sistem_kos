from app import create_app
from extensions import db
from models import User, Room, Booking, Payment, Expense, Vendor, MaintenanceRequest, Notification, Announcement, Complaint, RoomItem, ActivityLog, Kos
from datetime import date, timedelta, datetime
import random


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Admin
        admin = User(username="admin", email="admin@kos.com", role="admin",
                     nama_lengkap="Admin Kos", no_telepon="08123456789")
        admin.set_password("admin123")
        db.session.add(admin)

        # Management
        mgmt = User(username="management", email="management@kos.com", role="management",
                     nama_lengkap="Manajer Kos", no_telepon="08123456780")
        mgmt.set_password("mgmt123")
        db.session.add(mgmt)

        # Kos
        kos1 = Kos(nama="Kos Melati", alamat="Jl. Melati No. 10", deskripsi="Kos putra/putri strategis dekat kampus")
        kos2 = Kos(nama="Kos Anggrek", alamat="Jl. Anggrek No. 25", deskripsi="Kos eksklusif dengan fasilitas lengkap")
        db.session.add_all([kos1, kos2])
        db.session.commit()

        # Test clients
        clients_data = [
            ("budi", "Budi Santoso", "08111111111"),
            ("siti", "Siti Rahayu", "08222222222"),
            ("agus", "Agus Wijaya", "08333333333"),
            ("dewi", "Dwi Putri", "08444444444"),
            ("eko", "Eko Prasetyo", "08555555555"),
        ]
        clients = []
        for i, (u, n, t) in enumerate(clients_data):
            c = User(username=u, email=f"{u}@email.com", role="client",
                     nama_lengkap=n, no_telepon=t, alamat=f"Alamat {n}")
            c.set_password("client123")
            db.session.add(c)
            clients.append(c)

        # Rooms
        rooms_data = [
            (kos1.id, "101", 1, "Reguler", 1500000, "12m2", "AC, Kasur, Lemari, Meja"),
            (kos1.id, "102", 1, "Reguler", 1500000, "12m2", "AC, Kasur, Lemari, Meja"),
            (kos1.id, "103", 1, "Deluxe", 2000000, "16m2", "AC, Kasur, Lemari, Meja, TV, Kamar Mandi Dalam"),
            (kos2.id, "101", 1, "Reguler", 1500000, "12m2", "AC, Kasur, Lemari, Meja"),
            (kos2.id, "102", 1, "Deluxe", 2000000, "16m2", "AC, Kasur, Lemari, Meja, TV, Kamar Mandi Dalam"),
            (kos2.id, "103", 1, "VIP", 3000000, "24m2", "AC, Kasur, Lemari, Meja, TV, Kulkas, Kamar Mandi Dalam, Balkon"),
        ]
        rooms = []
        for kid, no, lt, tp, hr, uk, fs in rooms_data:
            r = Room(kos_id=kid, nomor_kamar=no, lantai=lt, tipe=tp, harga_per_bulan=hr,
                     ukuran=uk, fasilitas=fs, status="tersedia",
                     deskripsi=f"Kamar {tp} nyaman di lantai {lt}")
            db.session.add(r)
            rooms.append(r)

        db.session.commit()

        # Assign rooms to clients (first 3 rooms get clients)
        today = date.today()
        room_assignments = [
            (clients[0], rooms[0], today - timedelta(days=60)),
            (clients[1], rooms[2], today - timedelta(days=30)),
            (clients[3], rooms[4], today - timedelta(days=90)),
        ]
        for client, room, tgl_masuk in room_assignments:
            tgl_keluar = tgl_masuk + timedelta(days=365)
            booking = Booking(
                user_id=client.id, room_id=room.id,
                tanggal_masuk=tgl_masuk, tanggal_keluar=tgl_keluar,
                status="aktif", deposit=room.harga_per_bulan,
                catatan="Deposit sudah dibayar"
            )
            db.session.add(booking)
            room.status = "terisi"
            db.session.commit()

            # Create some payment history
            months_back = 1
            while today - tgl_masuk > timedelta(days=months_back * 30):
                bulan = (tgl_masuk + timedelta(days=months_back * 30)).strftime("%Y-%m")
                db.session.add(Payment(
                    booking_id=booking.id, jumlah=room.harga_per_bulan,
                    tanggal_bayar=date.today() - timedelta(days=random.randint(1, 5)),
                    bulan_dibayar_untuk=bulan, metode_bayar="transfer",
                    status="lunas"
                ))
                months_back += 1
            db.session.commit()

        # Vendors
        vendors_data = [
            ("Teknisi AC", "08666666666", "maintenance"),
            ("Tukang Listrik", "08777777777", "listrik"),
            ("Cleaning Service", "08888888888", "kebersihan"),
        ]
        for n, t, k in vendors_data:
            db.session.add(Vendor(nama=n, no_telepon=t, kategori=k))
        db.session.commit()

        # Expenses
        expenses_data = [
            ("listrik", 1200000, "Listrik bulan ini"),
            ("air", 500000, "PDAM bulan ini"),
            ("kebersihan", 300000, "Cleaning service"),
            ("gaji", 2500000, "Gaji satpam"),
        ]
        for kat, jml, dsc in expenses_data:
            db.session.add(Expense(
                kos_id=kos1.id,
                kategori=kat, jumlah=jml,
                tanggal=date.today() - timedelta(days=random.randint(1, 15)),
                deskripsi=dsc
            ))
        db.session.commit()

        # Maintenance request
        mr = MaintenanceRequest(
            room_id=rooms[1].id, vendor_id=1,
            deskripsi="AC tidak dingin",
            prioritas="normal", status="diproses",
            catatan="Sudah dihubungi teknisi"
        )
        db.session.add(mr)
        db.session.commit()

        # Announcements
        ann = Announcement(
            judul="Pembersihan Lingkungan", isi="Akan diadakan pembersihan lingkungan bersama pada hari Sabtu, 20 Juli 2026 pukul 08.00. Semua penghuni diharap berpartisipasi.",
            prioritas="sedang", created_by=admin.id
        )
        db.session.add(ann)
        db.session.add(Announcement(
            judul="Pembayaran Bulanan", isi="Pengingat: Pembayaran kos bulanan paling lambat tanggal 10 setiap bulan. Terima kasih.",
            prioritas="penting", created_by=admin.id
        ))
        db.session.commit()

        # Seed activity logs
        db.session.add(ActivityLog(user_id=admin.id, tindakan="Buat pengumuman", deskripsi="Judul: Pembersihan Lingkungan", model="Announcement"))
        db.session.add(ActivityLog(user_id=admin.id, tindakan="Buat pengumuman", deskripsi="Judul: Pembayaran Bulanan", model="Announcement"))

        # Complaint (from client budi)
        db.session.add(Complaint(
            user_id=clients[0].id, kos_id=kos1.id, judul="AC kamar kurang dingin",
            deskripsi="AC di kamar 101 sudah 2 hari ini tidak dingin. Mohon segera diperbaiki.",
            kategori="fasilitas", status="ditindaklanjuti",
            tanggapan="Akan kami kirim teknisi besok pagi.", ditanggapi_oleh=admin.id
        ))
        db.session.add(Complaint(
            user_id=clients[1].id, kos_id=kos1.id, judul="Kamar mandi bocor",
            deskripsi="Air dari lantai atas menetes di kamar mandi. Mohon dicek.",
            kategori="fasilitas", status="diajukan"
        ))
        db.session.commit()

        # Activity logs for complaint
        db.session.add(ActivityLog(user_id=admin.id, tindakan="Tanggapi komplain", deskripsi="Judul: AC kamar kurang dingin, Status: ditindaklanjuti", model="Complaint"))
        db.session.commit()

        # Notifications
        db.session.add(Notification(user_id=clients[0].id, pesan="Selamat datang di Kos Melati!", jenis="umum", dibaca=True))
        db.session.add(Notification(user_id=clients[0].id, pesan="Pembayaran bulan Juli sudah diterima.", jenis="pembayaran"))
        db.session.add(Notification(user_id=clients[1].id, pesan="Selamat datang di Kos Melati!", jenis="umum", dibaca=True))
        db.session.add(Notification(user_id=clients[3].id, pesan="Selamat datang di Kos Anggrek!", jenis="umum"))
        db.session.add(Notification(user_id=clients[3].id, pesan="Pembayaran bulan Juni sudah diterima.", jenis="pembayaran", dibaca=True))
        db.session.commit()

        # Room inventory
        items = [
            (rooms[0], "AC Split 1PK", 1, "baik", "Daikin, dipasang 2024"),
            (rooms[0], "Kasur Springbed", 1, "baik", "Ukuran 160x200"),
            (rooms[0], "Lemari Pakaian", 1, "baik", "3 pintu"),
            (rooms[0], "Meja Belajar", 1, "rusak", "Kaki meja goyang"),
            (rooms[0], "Kursi", 1, "baik", ""),
            (rooms[2], "AC Split 1.5PK", 1, "baik", "Panasonic, dipasang 2025"),
            (rooms[2], "TV 32 inch", 1, "baik", "Smart TV"),
            (rooms[2], "Kulkas 1 pintu", 1, "baik", "Polytron"),
        ]
        for room, nama, jumlah, kondisi, catatan in items:
            db.session.add(RoomItem(room_id=room.id, nama=nama, jumlah=jumlah, kondisi=kondisi, catatan=catatan))
        db.session.commit()

        # Activity logs for room items
        db.session.add(ActivityLog(user_id=admin.id, tindakan="Tambah barang", deskripsi="AC Split 1PK di 101", model="RoomItem"))
        db.session.add(ActivityLog(user_id=admin.id, tindakan="Tambah barang", deskripsi="Kasur Springbed di 101", model="RoomItem"))
        db.session.commit()

        print("Seed data created successfully!")
        print("\nLogin credentials:")
        print("  Admin: admin / admin123")
        print("  Management: management / mgmt123")
        print("  Clients: budi, siti, agus, dewi, eko / client123")


if __name__ == "__main__":
    seed()
