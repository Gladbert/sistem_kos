-- Additional query-pattern indexes not covered by 20250807010000_performance_indexes.sql
-- Gaps found by auditing routes/ against actual WHERE/ORDER BY clauses.
-- All indexes are additive and use IF NOT EXISTS so re-running is safe.

-- ============================================
-- MONTHLY AGGREGATION (dashboard.admin + accounting.index)
-- Queries filter to_char(tanggal_bayar, 'YYYY-MM') = :bulan and
-- to_char(tanggal, 'YYYY-MM') = :bulan. A plain tanggal_bayar index
-- cannot serve an expression filter, so add functional indexes.
-- ============================================
CREATE INDEX IF NOT EXISTS idx_payments_yyyymm
    ON payments (to_char(tanggal_bayar, 'YYYY-MM'));

CREATE INDEX IF NOT EXISTS idx_expenses_yyyymm
    ON expenses (to_char(tanggal, 'YYYY-MM'));

-- ============================================
-- AUTO-PROSES (dashboard.auto_proses)
-- SELECT ... WHERE status = 'aktif' AND tanggal_keluar < :today
-- (and a second range on tanggal_keluar). Composite (status, tanggal_keluar)
-- lets Postgres seek active bookings then range-scan by exit date.
-- ============================================
CREATE INDEX IF NOT EXISTS idx_bookings_status_keluar
    ON bookings (status, tanggal_keluar);

-- ============================================
-- RECENT-LIST ORDERING (limit N by created_at DESC)
-- payments/index, dashboard pembayaran_terbaru, pengeluaran_terbaru,
-- complaints/index all order by created_at. Composite with the leading
-- filter column lets Postgres satisfy filter + order from the index.
-- ============================================
CREATE INDEX IF NOT EXISTS idx_payments_booking_created
    ON payments (booking_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_expenses_kos_created
    ON expenses (kos_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_complaints_kos_created
    ON complaints (kos_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_complaints_user_created
    ON complaints (user_id, created_at DESC);

-- ============================================
-- Refresh planner statistics for the touched tables
-- ============================================
ANALYZE payments;
ANALYZE expenses;
ANALYZE bookings;
ANALYZE complaints;
