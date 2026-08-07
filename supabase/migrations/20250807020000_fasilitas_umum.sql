-- Public facilities management
CREATE TABLE fasilitas_umum (
    id SERIAL PRIMARY KEY,
    kos_id INTEGER NOT NULL REFERENCES kos(id),
    nama VARCHAR(150) NOT NULL,
    kategori VARCHAR(50) DEFAULT 'toilet',
    lokasi VARCHAR(100),
    kondisi VARCHAR(20) DEFAULT 'baik',
    deskripsi TEXT,
    catatan TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fasilitas_umum_kos_id ON fasilitas_umum(kos_id);
CREATE INDEX idx_fasilitas_umum_kategori ON fasilitas_umum(kategori);
CREATE INDEX idx_fasilitas_umum_kondisi ON fasilitas_umum(kondisi);
CREATE INDEX idx_fasilitas_umum_kos_kategori ON fasilitas_umum(kos_id, kategori);
