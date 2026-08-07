-- All performance indexes for Sistem Kos
-- Combines 20250807010000 + 20250808000000 + missing users.role + fasilitas/user_kos
-- All use IF NOT EXISTS so re-running is safe

-- ============================================
-- BOOKINGS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_room_status ON bookings(room_id, status);
CREATE INDEX IF NOT EXISTS idx_bookings_user_status ON bookings(user_id, status);
CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON bookings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookings_status_keluar ON bookings(status, tanggal_keluar);

-- ============================================
-- PAYMENTS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_booking_status ON payments(booking_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_tanggal_bayar ON payments(tanggal_bayar DESC);
CREATE INDEX IF NOT EXISTS idx_payments_bulan ON payments(bulan_dibayar_untuk);
CREATE INDEX IF NOT EXISTS idx_payments_status_date ON payments(status, tanggal_bayar);
CREATE INDEX IF NOT EXISTS idx_payments_booking_created ON payments(booking_id, created_at DESC);
-- Functional index for to_char(tanggal_bayar, 'YYYY-MM') in chart GROUP BY
CREATE INDEX IF NOT EXISTS idx_payments_yyyymm ON payments (to_char(tanggal_bayar, 'YYYY-MM'));

-- ============================================
-- EXPENSES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_expenses_kos_date ON expenses(kos_id, tanggal DESC);
CREATE INDEX IF NOT EXISTS idx_expenses_kategori ON expenses(kategori);
CREATE INDEX IF NOT EXISTS idx_expenses_tanggal ON expenses(tanggal DESC);
CREATE INDEX IF NOT EXISTS idx_expenses_kos_created ON expenses(kos_id, created_at DESC);
-- Functional index for to_char(tanggal, 'YYYY-MM') in chart GROUP BY
CREATE INDEX IF NOT EXISTS idx_expenses_yyyymm ON expenses (to_char(tanggal, 'YYYY-MM'));

-- ============================================
-- MAINTENANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_maintenance_status ON maintenance_requests(status);
CREATE INDEX IF NOT EXISTS idx_maintenance_room_status ON maintenance_requests(room_id, status);
CREATE INDEX IF NOT EXISTS idx_maintenance_created ON maintenance_requests(created_at DESC);

-- ============================================
-- COMPLAINTS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_user_status ON complaints(user_id, status);
CREATE INDEX IF NOT EXISTS idx_complaints_kos_status ON complaints(kos_id, status);
CREATE INDEX IF NOT EXISTS idx_complaints_kos_created ON complaints(kos_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_user_created ON complaints(user_id, created_at DESC);

-- ============================================
-- NOTIFICATIONS (hot: client dashboard every page load)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_notifications_user_dibaca ON notifications(user_id, dibaca);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

-- ============================================
-- ACTIVITY LOGS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_created ON activity_logs(user_id, created_at DESC);

-- ============================================
-- ROOMS (hot: onboarding + dashboard availability)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_rooms_kos_status ON rooms(kos_id, status);
CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status);
CREATE INDEX IF NOT EXISTS idx_rooms_tipe ON rooms(tipe);

-- ============================================
-- USERS (missing from all existing migrations)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================
-- ANNOUNCEMENTS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_announcements_ditampilkan ON announcements(ditampilkan, created_at DESC);

-- ============================================
-- ROOM AUDITS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_room_audits_booking_tipe ON room_audits(booking_id, tipe);

-- ============================================
-- FASILITAS UMUM
-- ============================================
CREATE INDEX IF NOT EXISTS idx_fasilitas_umum_kategori ON fasilitas_umum(kategori);
CREATE INDEX IF NOT EXISTS idx_fasilitas_umum_kondisi ON fasilitas_umum(kondisi);
CREATE INDEX IF NOT EXISTS idx_fasilitas_umum_kos_kategori ON fasilitas_umum(kos_id, kategori);

-- ============================================
-- USER KOS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_userkos_role ON user_kos(role);

-- ============================================
-- Update planner statistics for all touched tables
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
ANALYZE fasilitas_umum;
ANALYZE fasilitas_kategori;
ANALYZE user_kos;
ANALYZE kos_invites;
