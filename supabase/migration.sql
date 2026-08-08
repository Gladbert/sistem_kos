-- Supabase migration: all tables + indexes
-- Run against target database

CREATE TABLE IF NOT EXISTS kos (
	id SERIAL NOT NULL, 
	nama VARCHAR(150) NOT NULL, 
	alamat TEXT, 
	deskripsi TEXT, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS users (
	id SERIAL NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	nama_lengkap VARCHAR(150) NOT NULL, 
	no_telepon VARCHAR(20), 
	alamat TEXT, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS user_kos (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	kos_id INTEGER NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	joined_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_kos UNIQUE (user_id, kos_id), 
	CONSTRAINT fk_userkos_user FOREIGN KEY(user_id) REFERENCES users (id), 
	CONSTRAINT fk_userkos_kos FOREIGN KEY(kos_id) REFERENCES kos (id)
);

CREATE TABLE IF NOT EXISTS kos_invites (
	id SERIAL NOT NULL, 
	kos_id INTEGER NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	max_uses INTEGER, 
	used_count INTEGER, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_invite_kos FOREIGN KEY(kos_id) REFERENCES kos (id), 
	UNIQUE (code), 
	CONSTRAINT fk_invite_creator FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS vendors (
	id SERIAL NOT NULL, 
	nama VARCHAR(150) NOT NULL, 
	no_telepon VARCHAR(20), 
	kategori VARCHAR(50), 
	alamat TEXT, 
	catatan TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS rooms (
	id SERIAL NOT NULL, 
	kos_id INTEGER, 
	nomor_kamar VARCHAR(10) NOT NULL, 
	lantai INTEGER, 
	tipe VARCHAR(50), 
	harga_per_bulan NUMERIC(12, 2) NOT NULL, 
	ukuran VARCHAR(50), 
	fasilitas TEXT, 
	status VARCHAR(20), 
	deskripsi TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_kos_kamar UNIQUE (kos_id, nomor_kamar), 
	CONSTRAINT fk_room_kos FOREIGN KEY(kos_id) REFERENCES kos (id)
);

CREATE TABLE IF NOT EXISTS bookings (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	room_id INTEGER NOT NULL, 
	tanggal_masuk DATE NOT NULL, 
	tanggal_keluar DATE, 
	status VARCHAR(20), 
	deposit NUMERIC(12, 2), 
	catatan TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_booking_user FOREIGN KEY(user_id) REFERENCES users (id), 
	CONSTRAINT fk_booking_room FOREIGN KEY(room_id) REFERENCES rooms (id)
);

CREATE TABLE IF NOT EXISTS payments (
	id SERIAL NOT NULL, 
	booking_id INTEGER NOT NULL, 
	jumlah NUMERIC(12, 2) NOT NULL, 
	tanggal_bayar DATE, 
	bulan_dibayar_untuk VARCHAR(20), 
	metode_bayar VARCHAR(20), 
	status VARCHAR(20), 
	bukti_pembayaran VARCHAR(255), 
	catatan TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_payment_booking FOREIGN KEY(booking_id) REFERENCES bookings (id)
);

CREATE TABLE IF NOT EXISTS expenses (
	id SERIAL NOT NULL, 
	kos_id INTEGER, 
	kategori VARCHAR(50) NOT NULL, 
	jumlah NUMERIC(12, 2) NOT NULL, 
	tanggal DATE, 
	deskripsi TEXT, 
	vendor_id INTEGER, 
	fasilitas_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_expense_kos FOREIGN KEY(kos_id) REFERENCES kos (id), 
	CONSTRAINT fk_expense_vendor FOREIGN KEY(vendor_id) REFERENCES vendors (id), 
	FOREIGN KEY(fasilitas_id) REFERENCES fasilitas_umum (id)
);

CREATE TABLE IF NOT EXISTS maintenance_requests (
	id SERIAL NOT NULL, 
	room_id INTEGER NOT NULL, 
	vendor_id INTEGER, 
	deskripsi TEXT NOT NULL, 
	prioritas VARCHAR(20), 
	tanggal_masuk DATE, 
	tanggal_selesai DATE, 
	status VARCHAR(20), 
	biaya NUMERIC(12, 2), 
	catatan TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_maintenance_room FOREIGN KEY(room_id) REFERENCES rooms (id), 
	CONSTRAINT fk_maintenance_vendor FOREIGN KEY(vendor_id) REFERENCES vendors (id)
);

CREATE TABLE IF NOT EXISTS notifications (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	pesan TEXT NOT NULL, 
	jenis VARCHAR(50), 
	wa_sent BOOLEAN, 
	dibaca BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_notification_user FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS announcements (
	id SERIAL NOT NULL, 
	judul VARCHAR(200) NOT NULL, 
	isi TEXT NOT NULL, 
	prioritas VARCHAR(20), 
	ditampilkan BOOLEAN, 
	created_by INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_announcement_creator FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS complaints (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	kos_id INTEGER, 
	judul VARCHAR(200) NOT NULL, 
	deskripsi TEXT NOT NULL, 
	kategori VARCHAR(50), 
	status VARCHAR(20), 
	tanggapan TEXT, 
	ditanggapi_oleh INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_complaint_user FOREIGN KEY(user_id) REFERENCES users (id), 
	CONSTRAINT fk_complaint_kos FOREIGN KEY(kos_id) REFERENCES kos (id), 
	CONSTRAINT fk_complaint_responder FOREIGN KEY(ditanggapi_oleh) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS activity_logs (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	tindakan VARCHAR(100) NOT NULL, 
	deskripsi TEXT, 
	model VARCHAR(50), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_activitylog_user FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS room_items (
	id SERIAL NOT NULL, 
	room_id INTEGER NOT NULL, 
	nama VARCHAR(150) NOT NULL, 
	jumlah INTEGER, 
	kondisi VARCHAR(50), 
	catatan TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_roomitem_room FOREIGN KEY(room_id) REFERENCES rooms (id)
);

CREATE TABLE IF NOT EXISTS room_audits (
	id SERIAL NOT NULL, 
	booking_id INTEGER NOT NULL, 
	tipe VARCHAR(20) NOT NULL, 
	catatan TEXT, 
	created_by INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_roomaudit_booking FOREIGN KEY(booking_id) REFERENCES bookings (id), 
	CONSTRAINT fk_roomaudit_creator FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS audit_item_results (
	id SERIAL NOT NULL, 
	audit_id INTEGER NOT NULL, 
	item_id INTEGER NOT NULL, 
	kondisi VARCHAR(20) NOT NULL, 
	catatan TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_auditresult_audit FOREIGN KEY(audit_id) REFERENCES room_audits (id), 
	CONSTRAINT fk_auditresult_item FOREIGN KEY(item_id) REFERENCES room_items (id)
);

CREATE TABLE IF NOT EXISTS fasilitas_umum (
	id SERIAL NOT NULL, 
	kos_id INTEGER NOT NULL, 
	nama VARCHAR(150) NOT NULL, 
	kategori VARCHAR(50), 
	lokasi VARCHAR(100), 
	kondisi VARCHAR(20), 
	deskripsi TEXT, 
	catatan TEXT, 
	is_recurring BOOLEAN, 
	biaya_per_bulan NUMERIC(12, 2), 
	frekuensi VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_fasilitas_kos FOREIGN KEY(kos_id) REFERENCES kos (id)
);

CREATE TABLE IF NOT EXISTS fasilitas_kategori (
	id SERIAL NOT NULL, 
	nama VARCHAR(50) NOT NULL, 
	icon VARCHAR(30), 
	deskripsi VARCHAR(200), 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (nama)
);

CREATE TABLE IF NOT EXISTS role_permissions (
	id SERIAL NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	module VARCHAR(50) NOT NULL, 
	can_view BOOLEAN, 
	can_create BOOLEAN, 
	can_edit BOOLEAN, 
	can_delete BOOLEAN, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_role_module UNIQUE (role, module)
);

-- Unique constraints (already included above via __table_args__)
-- Done
