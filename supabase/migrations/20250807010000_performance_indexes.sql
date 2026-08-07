-- Performance optimization indexes for Sistem Kos
-- Based on actual query patterns in routes/

-- ============================================
-- BOOKINGS: heavily filtered by status + room_id, user_id
-- ============================================
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_room_status ON bookings(room_id, status);
CREATE INDEX IF NOT EXISTS idx_bookings_user_status ON bookings(user_id, status);
CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON bookings(created_at DESC);

-- ============================================
-- PAYMENTS: filtered by status, booking_id, tanggal_bayar
-- ============================================
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_booking_status ON payments(booking_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_tanggal_bayar ON payments(tanggal_bayar DESC);
CREATE INDEX IF NOT EXISTS idx_payments_bulan ON payments(bulan_dibayar_untuk);

-- Composite for dashboard monthly income query
CREATE INDEX IF NOT EXISTS idx_payments_status_date ON payments(status, tanggal_bayar);

-- ============================================
-- EXPENSES: filtered by kos_id, tanggal, kategori
-- ============================================
CREATE INDEX IF NOT EXISTS idx_expenses_kos_date ON expenses(kos_id, tanggal DESC);
CREATE INDEX IF NOT EXISTS idx_expenses_kategori ON expenses(kategori);
CREATE INDEX IF NOT EXISTS idx_expenses_tanggal ON expenses(tanggal DESC);

-- ============================================
-- MAINTENANCE: filtered by room_id, status
-- ============================================
CREATE INDEX IF NOT EXISTS idx_maintenance_status ON maintenance_requests(status);
CREATE INDEX IF NOT EXISTS idx_maintenance_room_status ON maintenance_requests(room_id, status);
CREATE INDEX IF NOT EXISTS idx_maintenance_created ON maintenance_requests(created_at DESC);

-- ============================================
-- COMPLAINTS: filtered by user_id, kos_id, status
-- ============================================
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_user_status ON complaints(user_id, status);
CREATE INDEX IF NOT EXISTS idx_complaints_kos_status ON complaints(kos_id, status);

-- ============================================
-- NOTIFICATIONS: filtered by user_id, dibaca
-- ============================================
CREATE INDEX IF NOT EXISTS idx_notifications_user_dibaca ON notifications(user_id, dibaca);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

-- ============================================
-- ACTIVITY LOGS: ordered by created_at
-- ============================================
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_created ON activity_logs(user_id, created_at DESC);

-- ============================================
-- ROOMS: filtered by kos_id, status, tipe
-- ============================================
CREATE INDEX IF NOT EXISTS idx_rooms_kos_status ON rooms(kos_id, status);
CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status);
CREATE INDEX IF NOT EXISTS idx_rooms_tipe ON rooms(tipe);

-- ============================================
-- ANNOUNCEMENTS: filtered by ditampilkan
-- ============================================
CREATE INDEX IF NOT EXISTS idx_announcements_ditampilkan ON announcements(ditampilkan, created_at DESC);

-- ============================================
-- ROOM AUDITS: filtered by booking_id, tipe
-- ============================================
CREATE INDEX IF NOT EXISTS idx_room_audits_booking_tipe ON room_audits(booking_id, tipe);

-- ============================================
-- VACUUM & ANALYZE for query planner
-- ============================================
ANALYZE users;
ANALYZE rooms;
ANALYZE bookings;
ANALYZE payments;
ANALYZE expenses;
ANALYZE maintenance_requests;
ANALYZE complaints;
ANALYZE notifications;
ANALYZE announcements;
ANALYZE activity_logs;
ANALYZE vendors;
ANALYZE kos;
ANALYZE room_items;
ANALYZE room_audits;
ANALYZE audit_item_results;
