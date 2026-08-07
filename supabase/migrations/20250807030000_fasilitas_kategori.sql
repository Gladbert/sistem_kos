-- Fasilitas kategori management
CREATE TABLE fasilitas_kategori (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(50) UNIQUE NOT NULL,
    icon VARCHAR(30) DEFAULT 'bi-box',
    deskripsi VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Default categories
INSERT INTO fasilitas_kategori (nama, icon, deskripsi) VALUES
    ('toilet', 'bi-door-open', 'Toilet dan kamar mandi bersama'),
    ('shower', 'bi-droplet', 'Shower dan area mandi'),
    ('dapur', 'bi-fire', 'Dapur bersama dan peralatan masak'),
    ('ruang_cuci', 'bi-water', 'Mesin cuci dan area jemur'),
    ('ruang_tamu', 'bi-tv', 'Ruang TV dan ruang santai bersama'),
    ('parkir', 'bi-car-front', 'Area parkir motor dan mobil'),
    ('taman', 'bi-flower1', 'Taman dan area hijau'),
    ('laundry', 'bi-basket', 'Fasilitas laundry'),
    ('wifi', 'bi-wifi', 'Internet dan jaringan'),
    ('keamanan', 'bi-shield-check', 'CCTV, pintu otomatis, satpam'),
    ('lainnya', 'bi-grid', 'Fasilitas lainnya');
