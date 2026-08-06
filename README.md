# Sistem Manajemen Kos

Aplikasi manajemen kos (boarding house) berbasis Flask. Multi-kos, multi-user, role-based.

## Tech Stack

- **Backend:** Flask 3.0, SQLAlchemy, Flask-Login, Flask-WTF
- **Database:** SQLite
- **Frontend:** Bootstrap 5.3, Bootstrap Icons, Chart.js

## Quick Start

```bash
conda activate sistem-kos
cd sistem_kos
python seed.py      # reset & seed database
python app.py       # http://localhost:5000
```

**Credentials:**
| User | Password | Role |
|------|----------|------|
| `admin` | `admin123` | admin |
| `budi` | `client123` | client |
| `siti` | `client123` | client |
| `agus` | `client123` | client |
| `dewi` | `client123` | client |
| `eko` | `client123` | client |

---

## Routes

| Prefix | Blueprint | File |
|--------|-----------|------|
| `/auth/` | auth | `routes/auth.py` |
| `/dashboard/` | dashboard | `routes/dashboard.py` |
| `/rooms/` | rooms | `routes/rooms.py` |
| `/clients/` | clients | `routes/clients.py` |
| `/payments/` | payments | `routes/payments.py` |
| `/accounting/` | accounting | `routes/accounting.py` |
| `/maintenance/` | maintenance | `routes/maintenance.py` |
| `/onboarding/` | onboarding | `routes/onboarding.py` |
| `/pengumuman/` | announcements | `routes/announcements.py` |
| `/komplain/` | complaints | `routes/complaints.py` |
| `/inventaris/` | inventory | `routes/inventory.py` |
| `/aktivitas/` | activity | `routes/activity_log.py` |
| `/audit/` | audit | `routes/audit.py` |
| `/kos/` | kos | `routes/kos.py` |

---

## Models

### Kos
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| nama | String(150) | Required |
| alamat | Text | Optional |
| deskripsi | Text | Optional |
| is_active | Boolean | Default True |
| created_at | DateTime | Auto |
| **Relationships:** rooms (→ Room) | | |
| **Properties:** total_kamar, kamar_terisi | | |

### User
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| username | String(80) | Unique, required |
| email | String(120) | Unique, required |
| password_hash | String(256) | Required |
| role | String(20) | admin/management/client, default client |
| nama_lengkap | String(150) | Required |
| no_telepon | String(20) | Optional |
| alamat | Text | Optional |
| is_active | Boolean | Default True |
| created_at | DateTime | Auto |
| **Relationships:** bookings (→ Booking), notifications (→ Notification), complaints (→ Complaint), activity_logs (→ ActivityLog), audits_created (→ RoomAudit), announcements (→ Announcement) | | |

### Room
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| kos_id | Integer | FK → kos.id, nullable |
| nomor_kamar | String(10) | Required, unique per kos |
| lantai | Integer | Default 1 |
| tipe | String(50) | Reguler/Deluxe/VIP, default Reguler |
| harga_per_bulan | Float | Required |
| ukuran | String(50) | e.g. "12m2" |
| fasilitas | Text | Comma-separated |
| status | String(20) | tersedia/terisi/maintenance, default tersedia |
| deskripsi | Text | Optional |
| created_at | DateTime | Auto |
| **Unique constraint:** (kos_id, nomor_kamar) | | |
| **Relationships:** kos (→ Kos), bookings (→ Booking), maintenance_requests (→ MaintenanceRequest), items (→ RoomItem) | | |
| **Properties:** booking_aktif (first active booking) | | |

### Booking
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| user_id | Integer | FK → users.id, required |
| room_id | Integer | FK → rooms.id, required |
| tanggal_masuk | Date | Required |
| tanggal_keluar | Date | Optional |
| status | String(20) | pending/aktif/selesai, default aktif |
| deposit | Float | Default 0 |
| catatan | Text | Optional |
| created_at | DateTime | Auto |
| **Relationships:** client (→ User), room (→ Room), payments (→ Payment), audits (→ RoomAudit) | | |
| **Properties:** durasi_bulan (calculated), tagihan_bulan_ini (bool, checks current month payment) | | |

### Payment
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| booking_id | Integer | FK → bookings.id, required |
| jumlah | Float | Required |
| tanggal_bayar | Date | Default today |
| bulan_dibayar_untuk | String(20) | e.g. "2026-07" |
| metode_bayar | String(20) | transfer/tunai, default transfer |
| status | String(20) | lunas/pending, default lunas |
| bukti_pembayaran | String(255) | Optional, file path |
| catatan | Text | Optional |
| created_at | DateTime | Auto |
| **Relationships:** booking (→ Booking) | | |

### Expense
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| kategori | String(50) | Required (listrik/air/kebersihan/gaji/lainnya) |
| jumlah | Float | Required |
| tanggal | Date | Default today |
| deskripsi | Text | Optional |
| vendor_id | Integer | FK → vendors.id, nullable |
| created_at | DateTime | Auto |
| **Relationships:** vendor (→ Vendor) | | |

### Vendor
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| nama | String(150) | Required |
| no_telepon | String(20) | Optional |
| kategori | String(50) | maintenance/listrik/kebersihan/lainnya |
| alamat | Text | Optional |
| catatan | Text | Optional |
| created_at | DateTime | Auto |
| **Relationships:** maintenance_requests (→ MaintenanceRequest), expenses (→ Expense) | | |

### MaintenanceRequest
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| room_id | Integer | FK → rooms.id, required |
| vendor_id | Integer | FK → vendors.id, nullable |
| deskripsi | Text | Required |
| prioritas | String(20) | rendah/normal/tinggi, default normal |
| tanggal_masuk | Date | Default today |
| tanggal_selesai | Date | Auto-set when status=selesai |
| status | String(20) | diajukan/diproses/selesai, default diajukan |
| biaya | Float | Default 0 |
| catatan | Text | Optional |
| created_at | DateTime | Auto |
| **Relationships:** room (→ Room), vendor (→ Vendor) | | |

### Notification
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| user_id | Integer | FK → users.id, nullable |
| pesan | Text | Required |
| jenis | String(50) | umum/pembayaran/maintenance, default umum |
| wa_sent | Boolean | Default False |
| dibaca | Boolean | Default False |
| created_at | DateTime | Auto |
| **Relationships:** user (→ User) | | |

### Announcement
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| judul | String(200) | Required |
| isi | Text | Required |
| prioritas | String(20) | normal/sedang/penting, default normal |
| ditampilkan | Boolean | Default True |
| created_by | Integer | FK → users.id |
| created_at | DateTime | Auto |
| **Relationships:** creator (→ User) | | |

### Complaint
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| user_id | Integer | FK → users.id, required |
| judul | String(200) | Required |
| deskripsi | Text | Required |
| kategori | String(50) | umum/fasilitas, default umum |
| status | String(20) | diajukan/ditindaklanjuti/selesai, default diajukan |
| tanggapan | Text | Optional, admin response |
| ditanggapi_oleh | Integer | FK → users.id, nullable |
| created_at | DateTime | Auto |
| **Relationships:** user (→ User), responder (→ User) | | |

### ActivityLog
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| user_id | Integer | FK → users.id, nullable |
| tindakan | String(100) | Required |
| deskripsi | Text | Optional |
| model | String(50) | e.g. Booking, Room, Payment |
| created_at | DateTime | Auto |
| **Relationships:** user (→ User) | | |

### RoomItem
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| room_id | Integer | FK → rooms.id, required |
| nama | String(150) | Required |
| jumlah | Integer | Default 1 |
| kondisi | String(50) | baik/rusak, default baik |
| catatan | Text | Optional |
| created_at | DateTime | Auto |
| **Relationships:** room (→ Room), audit_results (→ AuditItemResult) | | |

### RoomAudit
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| booking_id | Integer | FK → bookings.id, required |
| tipe | String(20) | check_in/check_out, required |
| catatan | Text | Optional |
| created_by | Integer | FK → users.id |
| created_at | DateTime | Auto |
| **Relationships:** booking (→ Booking), auditor (→ User), items (→ AuditItemResult) | | |

### AuditItemResult
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| audit_id | Integer | FK → room_audits.id, required |
| item_id | Integer | FK → room_items.id, required |
| kondisi | String(20) | baik/rusak, required |
| catatan | Text | Optional |
| **Relationships:** audit (→ RoomAudit), item (→ RoomItem) | | |

---

## Features — Exhaustive Test Checklist

### 1. Auth (`/auth/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 1.1 | Login page renders | `/auth/login` | GET | Status 200, form visible |
| 1.2 | Login success (admin) | `/auth/login` | POST | Redirect to `/dashboard/admin` |
| 1.3 | Login success (client) | `/auth/login` | POST | Redirect to `/dashboard/client` |
| 1.4 | Login wrong password | `/auth/login` | POST | Flash "salah", stays on page |
| 1.5 | Login empty fields | `/auth/login` | POST | Flash "wajib diisi" |
| 1.6 | Login inactive account | `/auth/login` | POST | Flash "dinonaktifkan" |
| 1.7 | Login redirect (`?next=`) | `/auth/login?next=/rooms/` | POST | Redirects to `/rooms/` |
| 1.8 | Already logged in → redirect | `/auth/login` | GET (authenticated) | Redirect to dashboard |
| 1.9 | Register page renders | `/auth/register` | GET | Status 200, form visible |
| 1.10 | Register success | `/auth/register` | POST | Flash "berhasil", redirect login |
| 1.11 | Register duplicate username | `/auth/register` | POST | Flash "sudah digunakan" |
| 1.12 | Register duplicate email | `/auth/register` | POST | Flash "sudah digunakan" |
| 1.13 | Register password mismatch | `/auth/register` | POST | Flash "tidak cocok" |
| 1.14 | Register short password | `/auth/register` | POST | Flash "minimal 6 karakter" |
| 1.15 | Register empty required fields | `/auth/register` | POST | Flash "wajib diisi" for each |
| 1.16 | Register creates client role | DB check | - | New user has `role="client"` |
| 1.17 | Logout | `/auth/logout` | GET | Redirect to login, session cleared |

### 2. Multi-Kos Management (`/kos/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 2.1 | Kos index renders (admin) | `/kos/` | GET | 200, shows all kos cards |
| 2.2 | Kos index blocked (client) | `/kos/` | GET | 302 redirect, flash "ditolak" |
| 2.3 | Add kos form | `/kos/tambah` | GET | 200, form visible |
| 2.4 | Add kos success | `/kos/tambah` | POST | Flash "berhasil ditambahkan", DB has new kos |
| 2.5 | Add kos empty nama | `/kos/tambah` | POST | Flash "wajib diisi" |
| 2.6 | Edit kos form | `/kos/edit/<id>` | GET | 200, form pre-filled |
| 2.7 | Edit kos success | `/kos/edit/<id>` | POST | Flash "berhasil diperbarui", DB updated |
| 2.8 | Edit kos empty nama | `/kos/edit/<id>` | POST | Flash "wajib diisi" |
| 2.9 | Delete empty kos | `/kos/hapus/<id>` | POST | Flash "berhasil dihapus", removed from DB |
| 2.10 | Delete kos with rooms | `/kos/hapus/<id>` | POST | Flash "Tidak bisa hapus", kos NOT deleted |
| 2.11 | Delete kos blocked for non-admin | `/kos/hapus/<id>` | POST | Flash "Hanya admin" |
| 2.12 | Kos switcher in navbar | - | - | Dropdown shows all kos names |
| 2.13 | Switch kos | `/kos/pilih/<id>` | POST | Flash "Beralih ke...", session kos_id changed |
| 2.14 | Session persists kos selection | Navigate pages | - | All pages reflect selected kos |
| 2.15 | Default kos auto-selected | First login | - | First kos auto-selected if none in session |
| 2.16 | Active kos badge | `/kos/` | GET | Selected kos shows "Aktif" badge |
| 2.17 | Kelola Kos link in navbar | Lainnya dropdown | - | Link visible and works |

### 3. Admin Dashboard (`/dashboard/admin`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 3.1 | Dashboard renders | `/dashboard/admin` | GET | 200 for admin |
| 3.2 | Dashboard blocked for client | `/dashboard/admin` | GET | 302 redirect |
| 3.3 | `/dashboard/` redirects (admin) | `/dashboard/` | GET | 302 → `/dashboard/admin` |
| 3.4 | `/dashboard/` redirects (client) | `/dashboard/` | GET | 302 → `/dashboard/client` |
| 3.5 | Total kamar correct | - | - | Matches rooms in selected kos |
| 3.6 | Kamar terisi correct | - | - | Matches active bookings in selected kos |
| 3.7 | Kamar tersedia correct | - | - | Matches available rooms in selected kos |
| 3.8 | Kamar pending correct | - | - | Matches pending bookings in selected kos |
| 3.9 | Kamar maintenance correct | - | - | Matches rooms with status=maintenance |
| 3.10 | Total penghuni correct | - | - | Distinct active booking users in selected kos |
| 3.11 | Penghuni list shows nama + kamar | - | - | Each entry has name and room number |
| 3.12 | Pemasukan bulan ini | - | - | Sum of lunas payments this month for selected kos |
| 3.13 | Pengeluaran bulan ini | - | - | Sum of expenses this month (global) |
| 3.14 | Collection rate | - | - | (paid / total active) * 100 |
| 3.15 | Occupancy rate | - | - | (occupied / total) * 100 |
| 3.16 | Tipe kamar breakdown | - | - | Grouped count by tipe for selected kos |
| 3.17 | Pemasukan 6 bulan chart | - | - | Chart.js renders, data correct |
| 3.18 | Pembayaran terbaru list | - | - | Last 5 payments for selected kos bookings |
| 3.19 | Pengeluaran terbaru list | - | - | Last 5 expenses (global) |
| 3.20 | Permintaan maintenance list | - | - | Pending/diproses for selected kos rooms |
| 3.21 | Komplain baru count | - | - | Count of diajukan complaints |
| 3.22 | Booking pending list | - | - | Pending bookings for selected kos rooms |
| 3.23 | Unpaid bookings list | - | - | Active bookings with no payment this month |
| 3.24 | Auto-proses button | `/dashboard/auto-proses` | POST | Ends expired bookings, sends reminders |
| 3.25 | Approve booking | `/dashboard/booking/<id>/approve` | POST | Status → aktif, room → terisi, notification sent |
| 3.26 | Approve already-processed booking | `/dashboard/booking/<id>/approve` | POST | Flash "sudah diproses" |
| 3.27 | Reject booking | `/dashboard/booking/<id>/tolak` | POST | Booking deleted, notification sent |
| 3.28 | Reject already-processed booking | `/dashboard/booking/<id>/tolak` | POST | Flash "sudah diproses" |
| 3.29 | Mark notification read | `/dashboard/notifikasi/baca/<id>` | POST | `dibaca=True` |
| 3.30 | Mark all notifications read | `/dashboard/notifikasi/baca-semua` | POST | All user's unread → read |
| 3.31 | Stats scoped to kos | Switch kos | - | Numbers change per kos |

### 4. Client Dashboard (`/dashboard/client`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 4.1 | Dashboard renders | `/dashboard/client` | GET | 200 |
| 4.2 | Shows active booking | - | - | Room number, dates visible |
| 4.3 | Shows pending booking | - | - | If no active, shows pending |
| 4.4 | Booking history | - | - | All user's bookings listed |
| 4.5 | Payment history | - | - | All user's payments listed |
| 4.6 | Notifications list | - | - | Last 10 notifications |
| 4.7 | Unread notification count | - | - | Badge shows correct count |
| 4.8 | Mark notification read | `/dashboard/notifikasi/baca/<id>` | POST | Redirects back to client |
| 4.9 | Mark all read | `/dashboard/notifikasi/baca-semua` | POST | Flash message, count → 0 |
| 4.10 | Read own notification only | `/dashboard/notifikasi/baca/<other_id>` | POST | Flash "ditolak" |

### 5. Rooms (`/rooms/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 5.1 | Room list (admin) | `/rooms/` | GET | 200, shows rooms for selected kos |
| 5.2 | Room list (client) | `/rooms/` | GET | 200, shows tersedia rooms only |
| 5.3 | Filter by lantai | `/rooms/?lantai=1` | GET | Only lantai 1 rooms shown |
| 5.4 | Filter by status | `/rooms/?status=tersedia` | GET | Only tersedia rooms shown |
| 5.5 | Add room form | `/rooms/tambah` | GET | 200 for admin |
| 5.6 | Add room success | `/rooms/tambah` | POST | Flash "berhasil ditambahkan", DB has room |
| 5.7 | Add room assigned to current kos | DB check | - | `kos_id` matches session `kos_id` |
| 5.8 | Add room empty nomor | `/rooms/tambah` | POST | Flash "wajib diisi" |
| 5.9 | Add room duplicate nomor (same kos) | `/rooms/tambah` | POST | Flash "sudah ada di kos ini" |
| 5.10 | Add room same nomor (different kos) | `/rooms/tambah` | POST | Success — allowed |
| 5.11 | Add room invalid harga | `/rooms/tambah` | POST | Flash "Harga harus angka" |
| 5.12 | Edit room form | `/rooms/edit/<id>` | GET | 200, form pre-filled |
| 5.13 | Edit room success | `/rooms/edit/<id>` | POST | Flash "berhasil diperbarui", DB updated |
| 5.14 | Edit room duplicate nomor | `/rooms/edit/<id>` | POST | Flash "sudah digunakan" |
| 5.15 | Delete available room | `/rooms/hapus/<id>` | POST | Flash "berhasil dihapus", removed |
| 5.16 | Delete occupied room | `/rooms/hapus/<id>` | POST | Flash "sedang terisi", NOT deleted |
| 5.17 | Room detail | `/rooms/<id>` | GET | 200, shows room info + booking + maintenance |
| 5.18 | Room detail shows active booking | - | - | Client name, dates visible |
| 5.19 | Room detail shows maintenance history | - | - | All maintenance requests listed |
| 5.20 | Add/edit blocked for client | `/rooms/tambah` | GET | 302 redirect |
| 5.21 | Delete blocked for client | `/rooms/hapus/<id>` | POST | 302 redirect |
| 5.22 | Unique constraint (kos_id, nomor_kamar) | DB | - | Cannot insert duplicate pair |

### 6. Clients/Penghuni (`/clients/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 6.1 | Client list | `/clients/` | GET | 200, shows all clients |
| 6.2 | Search by nama | `/clients/?search=budi` | GET | Filtered results |
| 6.3 | Search by username | `/clients/?search=budi` | GET | Matches username |
| 6.4 | Search by email | `/clients/?search=budi@email` | GET | Matches email |
| 6.5 | Search by telepon | `/clients/?search=0811` | GET | Matches phone |
| 6.6 | Client detail | `/clients/<id>` | GET | 200, shows client + bookings + payments |
| 6.7 | Client detail (own) | `/clients/<id>` | GET (as client) | 200 for own profile |
| 6.8 | Client detail (other) | `/clients/<other_id>` | GET (as client) | 302 redirect, "ditolak" |
| 6.9 | Edit client form | `/clients/edit/<id>` | GET | 200, form pre-filled |
| 6.10 | Edit client success | `/clients/edit/<id>` | POST | Flash "berhasil diperbarui" |
| 6.11 | Edit client password | `/clients/edit/<id>` | POST | Password updated if ≥6 chars |
| 6.12 | Edit client short password | `/clients/edit/<id>` | POST | Flash "minimal 6 karakter" |
| 6.13 | Deactivate client | `/clients/nonaktifkan/<id>` | POST | `is_active=False`, flash "dinonaktifkan" |
| 6.14 | Activate client | `/clients/nonaktifkan/<id>` | POST | `is_active=True`, flash "diaktifkan" |
| 6.15 | Blocked for client | `/clients/` | GET | 302 redirect |

### 7. Payments (`/payments/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 7.1 | Payment list (admin) | `/payments/` | GET | 200, all payments |
| 7.2 | Payment list (client) | `/payments/` | GET | 200, own payments only |
| 7.3 | Filter by booking_id | `/payments/?booking_id=1` | GET | Filtered results |
| 7.4 | Filter by status | `/payments/?status=lunas` | GET | Filtered results |
| 7.5 | Client no active booking | `/payments/` | GET (as client) | Flash "belum memiliki kamar", redirect |
| 7.6 | Add payment form | `/payments/tambah` | GET | 200, shows active bookings dropdown |
| 7.7 | Add payment success | `/payments/tambah` | POST | Flash "berhasil dicatat", DB has payment |
| 7.8 | Add payment creates notification | DB check | - | Notification for client with "pembayaran" jenis |
| 7.9 | Add payment jumlah ≤ 0 | `/payments/tambah` | POST | Flash "harus lebih dari 0" |
| 7.10 | Add payment invalid jumlah | `/payments/tambah` | POST | Flash "harus angka" |
| 7.11 | Add payment invalid booking | `/payments/tambah` | POST | Flash "tidak ditemukan" |
| 7.12 | Edit payment form | `/payments/edit/<id>` | GET | 200, form pre-filled |
| 7.13 | Edit payment success | `/payments/edit/<id>` | POST | Flash "berhasil diperbarui" |
| 7.14 | Delete payment | `/payments/hapus/<id>` | POST | Flash "berhasil dihapus" |
| 7.15 | Kirim resi (WhatsApp) | `/payments/resi/<id>` | GET | Redirects to wa.me with receipt text |
| 7.16 | Kirim resi no phone | `/payments/resi/<id>` | GET | Flash "tidak tersedia" |
| 7.17 | Notifikasi WA reminder | `/payments/notifikasi/<booking_id>` | GET | Redirects to wa.me with reminder |
| 7.18 | Resi creates notification | DB check | - | Notification with `wa_sent=True` |
| 7.19 | Add/edit/delete blocked for client | `/payments/tambah` | GET | 302 redirect |

### 8. Accounting (`/accounting/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 8.1 | Accounting index | `/accounting/` | GET | 200, shows financial overview |
| 8.2 | Filter by tahun | `/accounting/?tahun=2026` | GET | Data for that year |
| 8.3 | Filter by bulan | `/accounting/?bulan=7` | GET | Data for that month |
| 8.4 | Pemasukan correct | - | - | Sum of lunas payments in period |
| 8.5 | Pengeluaran correct | - | - | Sum of expenses in period |
| 8.6 | Laba/rugi correct | - | - | pemasukan - pengeluaran |
| 8.7 | 12-month chart data | - | - | Chart.js renders correctly |
| 8.8 | Add pengeluaran form | `/accounting/pengeluaran/tambah` | GET | 200, form with vendor dropdown |
| 8.9 | Add pengeluaran success | `/accounting/pengeluaran/tambah` | POST | Flash "berhasil dicatat" |
| 8.10 | Add pengeluaran invalid jumlah | POST | - | Flash "harus angka" or "harus lebih dari 0" |
| 8.11 | Edit pengeluaran form | `/accounting/pengeluaran/edit/<id>` | GET | 200, pre-filled |
| 8.12 | Edit pengeluaran success | POST | - | Flash "berhasil diperbarui" |
| 8.13 | Delete pengeluaran | `/accounting/pengeluaran/hapus/<id>` | POST | Flash "berhasil dihapus" |
| 8.14 | Laporan page | `/accounting/laporan` | GET | 200, monthly breakdown table |
| 8.15 | Laporan filter by tahun | `/accounting/laporan?tahun=2026` | GET | Correct year data |
| 8.16 | Export CSV | `/accounting/export/csv` | GET | CSV download with correct data |
| 8.17 | Export CSV filter by bulan | `/accounting/export/csv?bulan=7` | GET | Only that month |
| 8.18 | Export CSV filter by jenis | `/accounting/export/csv?jenis=pemasukan` | GET | Only pemasukan section |
| 8.19 | Blocked for client | `/accounting/` | GET | 302 redirect |

### 9. Maintenance (`/maintenance/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 9.1 | Maintenance list | `/maintenance/` | GET | 200 |
| 9.2 | Filter by status | `/maintenance/?status=diajukan` | GET | Filtered results |
| 9.3 | Add maintenance form | `/maintenance/tambah` | GET | 200, room + vendor dropdowns |
| 9.4 | Add maintenance success | `/maintenance/tambah` | POST | Flash "berhasil diajukan" |
| 9.5 | Add maintenance empty deskripsi | POST | - | Flash "wajib diisi" |
| 9.6 | Add creates notification for occupant | DB check | - | Notification if room has active booking |
| 9.7 | Edit maintenance form | `/maintenance/edit/<id>` | GET | 200, pre-filled |
| 9.8 | Edit maintenance success | POST | - | Flash "berhasil diperbarui" |
| 9.9 | Edit sets tanggal_selesai when status=selesai | POST | - | `tanggal_selesai` auto-set |
| 9.10 | Delete maintenance | `/maintenance/hapus/<id>` | POST | Flash "berhasil dihapus" |
| 9.11 | Vendor list | `/maintenance/vendor` | GET | 200 |
| 9.12 | Add vendor form | `/maintenance/vendor/tambah` | GET | 200 |
| 9.13 | Add vendor success | POST | - | Flash "berhasil ditambahkan" |
| 9.14 | Add vendor empty nama | POST | - | Flash "wajib diisi" |
| 9.15 | Edit vendor form | `/maintenance/vendor/edit/<id>` | GET | 200, pre-filled |
| 9.16 | Edit vendor success | POST | - | Flash "berhasil diperbarui" |
| 9.17 | Delete vendor | `/maintenance/vendor/hapus/<id>` | POST | Flash "berhasil dihapus" |
| 9.18 | WhatsApp vendor | `/maintenance/vendor/wa/<id>` | GET | Redirect to wa.me |
| 9.19 | WhatsApp vendor for specific request | `/maintenance/vendor/hubungi/<mr_id>` | GET | Redirect with request details |
| 9.20 | Notify occupant (maintenance done) | `/maintenance/notif-penghuni/<mr_id>` | GET | Redirect to wa.me, notification created |
| 9.21 | Notify occupant no booking | GET | - | Flash "tidak ada penghuni aktif" |
| 9.22 | Blocked for client | `/maintenance/` | GET | 302 redirect |

### 10. Onboarding (`/onboarding/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 10.1 | Onboarding index | `/onboarding/` | GET | 200, shows tersedia rooms |
| 10.2 | Lihat kamar | `/onboarding/kamar` | GET | 200, sorted by harga |
| 10.3 | Kamar detail | `/onboarding/kamar/<id>` | GET | 200, room info visible |
| 10.4 | Daftar form | `/onboarding/daftar/<room_id>` | GET | 200 |
| 10.5 | Daftar not logged in | `/onboarding/daftar/<room_id>` | POST | Redirect to login with `?next=` |
| 10.6 | Daftar success | POST (as client) | - | Booking created with status="pending" |
| 10.7 | Daftar calculates tanggal_keluar | POST | - | Correct end date based on durasi |
| 10.8 | Daftar creates notification for client | DB check | - | "Permintaan sewa... dikirim" |
| 10.9 | Daftar creates notification for admins | DB check | - | All admin/management users notified |
| 10.10 | Daftar room not tersedia | POST | - | Flash "sudah tidak tersedia" |
| 10.11 | Daftar empty tanggal_masuk | POST | - | Flash "wajib diisi" |
| 10.12 | Daftar invalid date format | POST | - | Flash "Format tanggal salah" |
| 10.13 | Daftar as admin | POST | - | Flash "Hanya client" |

### 11. Announcements/Pengumuman (`/pengumuman/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 11.1 | Index (admin) | `/pengumuman/` | GET | 200, all announcements |
| 11.2 | Index (client) | `/pengumuman/` | GET | 200, only `ditampilkan=True` |
| 11.3 | Add form | `/pengumuman/tambah` | GET | 200 for admin |
| 11.4 | Add success | POST | - | Flash "berhasil dibuat", activity logged |
| 11.5 | Edit form | `/pengumuman/edit/<id>` | GET | 200, pre-filled |
| 11.6 | Edit success | POST | - | Flash "diperbarui", activity logged |
| 11.7 | Delete | `/pengumuman/hapus/<id>` | GET | Flash "dihapus", activity logged |
| 11.8 | Blocked for client | `/pengumuman/tambah` | GET | 302 redirect |
| 11.9 | Prioritas field | Add/edit | - | normal/sedang/penting saved |
| 11.10 | Ditampilkan checkbox | Add/edit | - | Controls client visibility |

### 12. Complaints/Komplain (`/komplain/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 12.1 | Index (admin) | `/komplain/` | GET | 200, all complaints |
| 12.2 | Index (client) | `/komplain/` | GET | 200, own complaints only |
| 12.3 | Add form | `/komplain/tambah` | GET | 200 |
| 12.4 | Add success | POST | - | Flash "terkirim", activity logged |
| 12.5 | Add as any authenticated user | POST | - | Works for both admin and client |
| 12.6 | Respond (admin) | `/komplain/tanggap/<id>` | POST | Tanggapan saved, status updated, activity logged |
| 12.7 | Respond blocked for client | `/komplain/tanggap/<id>` | POST | 302 redirect |
| 12.8 | Status values | - | - | diajukan, ditindaklanjuti, selesai |
| 12.9 | Kategori field | Add form | - | umum, fasilitas, etc. |

### 13. Inventory/Inventaris (`/inventaris/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 13.1 | Inventory index | `/inventaris/` | GET | 200, all rooms listed |
| 13.2 | Room items | `/inventaris/kamar/<room_id>` | GET | 200, items for that room |
| 13.3 | Add item form | `/inventaris/tambah/<room_id>` | GET | 200 |
| 13.4 | Add item success | POST | - | Flash "ditambahkan", activity logged |
| 13.5 | Edit item form | `/inventaris/edit/<id>` | GET | 200, pre-filled |
| 13.6 | Edit item success | POST | - | Flash "diperbarui", activity logged |
| 13.7 | Delete item | `/inventaris/hapus/<id>` | GET | Flash "dihapus", activity logged |
| 13.8 | Kondisi field | - | - | baik/rusak saved correctly |
| 13.9 | Blocked for client | `/inventaris/` | GET | 302 redirect |

### 14. Activity Log (`/aktivitas/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 14.1 | Activity log index | `/aktivitas/` | GET | 200 |
| 14.2 | Filter by model | `/aktivitas/?model=Booking` | GET | Filtered results |
| 14.3 | Filter by tindakan | `/aktivitas/?tindakan=tambah` | GET | Filtered results |
| 14.4 | Max 200 results | - | - | Limited to 200 entries |
| 14.5 | Blocked for client | `/aktivitas/` | GET | 302 redirect |
| 14.6 | Distinct models available | - | - | Dropdown populated from DB |

### 15. Audit (`/audit/`)

| # | Feature | Route | Method | Test |
|---|---------|-------|--------|------|
| 15.1 | Check-in form | `/audit/check-in/<booking_id>` | GET | 200, shows room items |
| 15.2 | Check-in success | POST | - | Audit + AuditItemResults created |
| 15.3 | Check-in creates notification | DB check | - | Notification for booking user |
| 15.4 | Check-in duplicate (client) | GET | - | Flash "sudah dilakukan", redirect to detail |
| 15.5 | Check-in duplicate (admin) | GET | - | Can re-do existing check-in |
| 15.6 | Check-in authz | GET | - | Only booking owner or admin |
| 15.7 | Check-out form | `/audit/check-out/<booking_id>` | GET | 200, shows items + check-in comparison |
| 15.8 | Check-out success | POST | - | Audit created, notification sent |
| 15.9 | Check-out duplicate | GET | - | Flash "sudah dilakukan", redirect |
| 15.10 | Check-out admin only | GET | - | Client blocked |
| 15.11 | Audit detail | `/audit/<booking_id>` | GET | 200, shows check-in + check-out |
| 15.12 | Detail authz | GET | - | Only booking owner or admin |
| 15.13 | Edit audit form | `/audit/edit/<audit_id>` | GET | 200, pre-filled |
| 15.14 | Edit audit success | POST | - | Results updated/added |
| 15.15 | Edit admin only | GET | - | Client blocked |
| 15.16 | Delete audit (GET = confirm page) | `/audit/delete/<audit_id>` | GET | 200, confirmation page |
| 15.17 | Delete audit (POST = execute) | POST | - | Audit + AuditItemResults deleted |
| 15.18 | Delete cascade cleanup | DB check | - | No orphaned AuditItemResults |
| 15.19 | Export CSV | `/audit/export/<booking_id>` | GET | CSV download |
| 15.20 | Export JSON | `/audit/export/<booking_id>?format=json` | GET | JSON response |
| 15.21 | Export admin only | GET | - | Client blocked |

### 16. Notifications (cross-cutting)

| # | Feature | Test |
|---|---------|------|
| 16.1 | Created on booking approval | DB: notification for client |
| 16.2 | Created on booking rejection | DB: notification for client |
| 16.3 | Created on payment recorded | DB: notification for client |
| 16.4 | Created on new booking request | DB: notification for client + all admins |
| 16.5 | Created on maintenance request | DB: notification for room occupant |
| 16.6 | Created on audit check-in | DB: notification for booking user |
| 16.7 | Created on audit check-out | DB: notification for booking user |
| 16.8 | Created on resi sent | DB: notification with `wa_sent=True` |
| 16.9 | Created on WA reminder sent | DB: notification with `wa_sent=True` |
| 16.10 | Read/unread tracking | `dibaca` boolean per notification |
| 16.11 | Mark single read | POST sets `dibaca=True` |
| 16.12 | Mark all read | POST sets all user's unread to True |
| 16.13 | Types: umum, pembayaran, maintenance | DB: `jenis` field |

### 17. Role-Based Access Control (cross-cutting)

| # | Test |
|---|------|
| 17.1 | Admin can access all routes |
| 17.2 | Client cannot access `/dashboard/admin` |
| 17.3 | Client cannot access `/rooms/tambah`, `/rooms/edit`, `/rooms/hapus` |
| 17.4 | Client cannot access `/clients/` |
| 17.5 | Client cannot access `/payments/tambah`, `/payments/edit`, `/payments/hapus` |
| 17.6 | Client cannot access `/accounting/` |
| 17.7 | Client cannot access `/maintenance/` |
| 17.8 | Client cannot access `/inventaris/` |
| 17.9 | Client cannot access `/aktivitas/` |
| 17.10 | Client cannot access `/kos/` |
| 17.11 | Client cannot access `/kos/tambah`, `/kos/edit`, `/kos/hapus` |
| 17.12 | Client cannot approve/reject bookings |
| 17.13 | Client cannot respond to complaints |
| 17.14 | Client cannot access audit check-out |
| 17.15 | Client cannot access audit edit/delete |
| 17.16 | Unauthenticated user redirected to login |
| 17.17 | Inactive user cannot login |
| 17.18 | `?next=` parameter preserved on redirect |

### 18. Data Integrity (cross-cutting)

| # | Test |
|---|------|
| 18.1 | Room unique per kos (kos_id + nomor_kamar) |
| 18.2 | Room can have same number in different kos |
| 18.3 | Cannot delete occupied room |
| 18.4 | Cannot delete kos with rooms |
| 18.5 | Booking references valid user_id |
| 18.6 | Booking references valid room_id |
| 18.7 | Payment references valid booking_id |
| 18.8 | MaintenanceRequest references valid room_id |
| 18.9 | AuditItemResult cascade deleted with RoomAudit |
| 18.10 | Notification references valid user_id |
| 18.11 | Complaint references valid user_id |
| 18.12 | ActivityLog references valid user_id |
| 18.13 | RoomItem references valid room_id |
| 18.14 | Expense references valid vendor_id (nullable) |
| 18.15 | Booking status values: pending, aktif, selesai |
| 18.16 | Room status values: tersedia, terisi, maintenance |
| 18.17 | Payment status values: lunas, pending |
| 18.18 | Maintenance status values: diajukan, diproses, selesai |
| 18.19 | Complaint status values: diajukan, ditindaklanjuti, selesai |

### 19. Kos Scoping (cross-cutting)

| # | Test |
|---|------|
| 19.1 | Dashboard stats change per kos |
| 19.2 | Room list shows only selected kos rooms |
| 19.3 | New room auto-assigned to selected kos |
| 19.4 | Payments scoped to selected kos bookings |
| 19.5 | Maintenance scoped to selected kos rooms |
| 19.6 | Inventory scoped to selected kos rooms |
| 19.7 | Booking pending list scoped to selected kos |
| 19.8 | Penghuni list scoped to selected kos |
| 19.9 | Switch kos mid-session works |
| 19.10 | Session persists kos_id across requests |
| 19.11 | All kos selector in navbar (admin only) |
| 19.12 | Client sees no kos selector |

### 20. WhatsApp Integration

| # | Feature | Route | Test |
|---|---------|-------|------|
| 20.1 | Payment receipt (resi) | `/payments/resi/<id>` | wa.me redirect with formatted receipt |
| 20.2 | Payment reminder | `/payments/notifikasi/<booking_id>` | wa.me redirect with reminder |
| 20.3 | Vendor contact | `/maintenance/vendor/wa/<id>` | wa.me redirect |
| 20.4 | Vendor for specific request | `/maintenance/vendor/hubungi/<mr_id>` | wa.me redirect with request details |
| 20.5 | Occupant notification | `/maintenance/notif-penghuni/<mr_id>` | wa.me redirect + DB notification |
| 20.6 | No phone number handling | Various | Flash warning, no redirect |
| 20.7 | Message formatting | - | Correct emoji, line breaks, amounts |
| 20.8 | URL encoding | - | Special chars properly encoded |

---

## Seed Data

| Table | Count | Notes |
|-------|-------|-------|
| kos | 2 | Kos Melati, Kos Anggrek |
| users | 6 | 1 admin, 5 clients |
| rooms | 6 | 3 per kos |
| bookings | 3 | budi→101/Melati, siti→103/Melati, dewi→102/Anggrek |
| payments | 3 | Auto-generated based on booking duration |
| expenses | 4 | listrik, air, kebersihan, gaji |
| vendors | 3 | AC, Listrik, Cleaning |
| maintenance_requests | 1 | AC tidak dingin |
| notifications | 5 | Welcome + payment notifications |
| announcements | 2 | Pembersihan + Pembayaran |
| complaints | 2 | AC kurang dingin + Kamar mandi bocor |
| activity_logs | 5 | Various admin actions |
| room_items | 8 | Items for room 101 + 103 Melati |
