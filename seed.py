from app import create_app
from extensions import db
from models import User, Room, Booking, Payment, Expense, Vendor, MaintenanceRequest, Notification
from datetime import date, timedelta
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
            ("101", 1, "Reguler", 1500000, "12m2", "AC, Kasur, Lemari, Meja"),
            ("102", 1, "Reguler", 1500000, "12m2", "AC, Kasur, Lemari, Meja"),
            ("103", 1, "Deluxe", 2000000, "16m2", "AC, Kasur, Lemari, Meja, TV, Kamar Mandi Dalam"),
            ("201", 2, "Reguler", 1500000, "12m2", "AC, Kasur, Lemari, Meja"),
            ("202", 2, "Deluxe", 2000000, "16m2", "AC, Kasur, Lemari, Meja, TV, Kamar Mandi Dalam"),
            ("203", 2, "VIP", 3000000, "24m2", "AC, Kasur, Lemari, Meja, TV, Kulkas, Kamar Mandi Dalam, Balkon"),
        ]
        rooms = []
        for no, lt, tp, hr, uk, fs in rooms_data:
            r = Room(nomor_kamar=no, lantai=lt, tipe=tp, harga_per_bulan=hr,
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
                Payment(
                    booking_id=booking.id, jumlah=room.harga_per_bulan,
                    tanggal_bayar=date.today() - timedelta(days=random.randint(1, 5)),
                    bulan_dibayar_untuk=bulan, metode_bayar="transfer",
                    status="lunas"
                )
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

        print("Seed data created successfully!")
        print("\nLogin credentials:")
        print("  Admin: admin / admin123")
        print("  Clients: budi, siti, agus, dewi, eko / client123")


if __name__ == "__main__":
    seed()
