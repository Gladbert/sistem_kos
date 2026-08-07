-- Enable UUID extension (optional, using serial for simplicity)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Kos (boarding houses)
CREATE TABLE kos (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(150) NOT NULL,
    alamat TEXT,
    deskripsi TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'client',
    nama_lengkap VARCHAR(150) NOT NULL,
    no_telepon VARCHAR(20),
    alamat TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rooms
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    kos_id INTEGER REFERENCES kos(id),
    nomor_kamar VARCHAR(10) NOT NULL,
    lantai INTEGER DEFAULT 1,
    tipe VARCHAR(50) DEFAULT 'Reguler',
    harga_per_bulan FLOAT NOT NULL,
    ukuran VARCHAR(50),
    fasilitas TEXT,
    status VARCHAR(20) DEFAULT 'tersedia',
    deskripsi TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(kos_id, nomor_kamar)
);

CREATE INDEX idx_rooms_kos_id ON rooms(kos_id);

-- Vendors
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(150) NOT NULL,
    no_telepon VARCHAR(20),
    kategori VARCHAR(50) DEFAULT 'lainnya',
    alamat TEXT,
    catatan TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bookings
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    tanggal_masuk DATE NOT NULL,
    tanggal_keluar DATE,
    status VARCHAR(20) DEFAULT 'aktif',
    deposit FLOAT DEFAULT 0,
    catatan TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_room_id ON bookings(room_id);

-- Payments
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES bookings(id),
    jumlah FLOAT NOT NULL,
    tanggal_bayar DATE DEFAULT CURRENT_DATE,
    bulan_dibayar_untuk VARCHAR(20),
    metode_bayar VARCHAR(20) DEFAULT 'transfer',
    status VARCHAR(20) DEFAULT 'lunas',
    bukti_pembayaran VARCHAR(255),
    catatan TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_booking_id ON payments(booking_id);

-- Expenses
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    kos_id INTEGER REFERENCES kos(id),
    kategori VARCHAR(50) NOT NULL,
    jumlah FLOAT NOT NULL,
    tanggal DATE DEFAULT CURRENT_DATE,
    deskripsi TEXT,
    vendor_id INTEGER REFERENCES vendors(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_expenses_kos_id ON expenses(kos_id);
CREATE INDEX idx_expenses_vendor_id ON expenses(vendor_id);

-- Maintenance Requests
CREATE TABLE maintenance_requests (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    vendor_id INTEGER REFERENCES vendors(id),
    deskripsi TEXT NOT NULL,
    prioritas VARCHAR(20) DEFAULT 'normal',
    tanggal_masuk DATE DEFAULT CURRENT_DATE,
    tanggal_selesai DATE,
    status VARCHAR(20) DEFAULT 'diajukan',
    biaya FLOAT DEFAULT 0,
    catatan TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_maintenance_room_id ON maintenance_requests(room_id);
CREATE INDEX idx_maintenance_vendor_id ON maintenance_requests(vendor_id);

-- Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    pesan TEXT NOT NULL,
    jenis VARCHAR(50) DEFAULT 'umum',
    wa_sent BOOLEAN DEFAULT FALSE,
    dibaca BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);

-- Announcements
CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    judul VARCHAR(200) NOT NULL,
    isi TEXT NOT NULL,
    prioritas VARCHAR(20) DEFAULT 'normal',
    ditampilkan BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_announcements_created_by ON announcements(created_by);

-- Complaints
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    kos_id INTEGER REFERENCES kos(id),
    judul VARCHAR(200) NOT NULL,
    deskripsi TEXT NOT NULL,
    kategori VARCHAR(50) DEFAULT 'umum',
    status VARCHAR(20) DEFAULT 'diajukan',
    tanggapan TEXT,
    ditanggapi_oleh INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_complaints_user_id ON complaints(user_id);
CREATE INDEX idx_complaints_kos_id ON complaints(kos_id);
CREATE INDEX idx_complaints_ditanggapi_oleh ON complaints(ditanggapi_oleh);

-- Activity Logs
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    tindakan VARCHAR(100) NOT NULL,
    deskripsi TEXT,
    model VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);

-- Room Items
CREATE TABLE room_items (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    nama VARCHAR(150) NOT NULL,
    jumlah INTEGER DEFAULT 1,
    kondisi VARCHAR(50) DEFAULT 'baik',
    catatan TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_room_items_room_id ON room_items(room_id);

-- Room Audits
CREATE TABLE room_audits (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES bookings(id),
    tipe VARCHAR(20) NOT NULL, -- check_in / check_out
    catatan TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_room_audits_booking_id ON room_audits(booking_id);
CREATE INDEX idx_room_audits_created_by ON room_audits(created_by);

-- Audit Item Results
CREATE TABLE audit_item_results (
    id SERIAL PRIMARY KEY,
    audit_id INTEGER NOT NULL REFERENCES room_audits(id),
    item_id INTEGER NOT NULL REFERENCES room_items(id),
    kondisi VARCHAR(20) NOT NULL, -- baik / rusak
    catatan TEXT
);

CREATE INDEX idx_audit_item_results_audit_id ON audit_item_results(audit_id);
CREATE INDEX idx_audit_item_results_item_id ON audit_item_results(item_id);

-- Enable Row Level Security (optional, enable per table as needed)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ... etc
