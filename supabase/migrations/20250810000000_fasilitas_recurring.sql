-- fasilitas_umum recurring cost support
ALTER TABLE fasilitas_umum ADD COLUMN IF NOT EXISTS is_recurring boolean NOT NULL DEFAULT false;
ALTER TABLE fasilitas_umum ADD COLUMN IF NOT EXISTS biaya_per_bulan numeric(12,2);
ALTER TABLE fasilitas_umum ADD COLUMN IF NOT EXISTS frekuensi varchar(20) NOT NULL DEFAULT 'bulanan';
COMMENT ON COLUMN fasilitas_umum.is_recurring IS 'Apakah fasilitas ini biaya berulang (langganan)';
COMMENT ON COLUMN fasilitas_umum.biaya_per_bulan IS 'Biaya per bulan (Rp)';
COMMENT ON COLUMN fasilitas_umum.frekuensi IS 'Frekuensi pembayaran: bulanan, 3_bulan, 6_bulan, tahunan';
