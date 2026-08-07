# Sistem Manajemen Kos

Aplikasi manajemen kos (boarding house) berbasis Flask. Multi-kos, multi-user, role-based, SaaS-ready.

## Tech Stack

- **Backend:** Flask 3.0, SQLAlchemy, Flask-Login, Flask-WTF
- **Database:** PostgreSQL (Supabase) / SQLite (local dev)
- **Frontend:** Bootstrap 5.3, Bootstrap Icons, Chart.js
- **Deployment:** Vercel

## Quick Start

```bash
conda activate sistem-kos
cd sistem_kos
python seed.py      # reset & seed database
python app.py       # http://localhost:5000
```

**Demo Login (one-click):**
| Button | Role | Access |
|--------|------|--------|
| Admin | admin | Full system access |
| Management | management | Kos operations |
| Client | client | View own data only |

---

## Architecture

### Multi-Tenancy (SaaS)

```
User ──┬── UserKos ──┬── Kos A (role: admin)
       │             ├── Kos B (role: management)
       │             └── Kos C (role: client)
       └── Global role (legacy fallback)
```

- **UserKos** — junction table: user ↔ kos with role
- **KosInvite** — invite codes for joining kos
- **Access Control** — per-kos role checked first, falls back to global `role` field
- **Session** — `kos_id` in session determines active kos context

### Models

| Model | Table | Key Fields |
|-------|-------|------------|
| Kos | kos | nama, alamat, is_active |
| User | users | username, email, role (legacy) |
| UserKos | user_kos | user_id, kos_id, role |
| KosInvite | kos_invites | code, kos_id, role, max_uses, expires_at |
| Room | rooms | kos_id, nomor_kamar, tipe, harga_per_bulan, status |
| Booking | bookings | user_id, room_id, tanggal_masuk, tanggal_keluar, status |
| Payment | payments | booking_id, jumlah, tanggal_bayar, bulan_dibayar_untuk, metode_bayar |
| Expense | expenses | kos_id, kategori, jumlah, tanggal, vendor_id |
| Vendor | vendors | nama, no_telepon, kategori |
| MaintenanceRequest | maintenance_requests | room_id, vendor_id, deskripsi, prioritas, status, biaya |
| Notification | notifications | user_id, pesan, jenis, dibaca, wa_sent |
| Announcement | announcements | judul, isi, prioritas, ditampilkan |
| Complaint | complaints | user_id, kos_id, judul, deskripsi, kategori, status, tanggapan |
| ActivityLog | activity_logs | user_id, tindakan, deskripsi, model |
| RoomItem | room_items | room_id, nama, jumlah, kondisi |
| RoomAudit | room_audits | booking_id, tipe, catatan |
| AuditItemResult | audit_item_results | audit_id, item_id, kondisi |
| FasilitasUmum | fasilitas_umum | kos_id, nama, kategori, lokasi, kondisi |
| FasilitasKategori | fasilitas_kategori | nama, icon, deskripsi, is_active |

### Routes

| Prefix | Blueprint | Access |
|--------|-----------|--------|
| `/auth/` | auth | Public |
| `/dashboard/` | dashboard | All (redirects by role) |
| `/rooms/` | rooms | Admin/Management |
| `/clients/` | clients | Admin/Management |
| `/payments/` | payments | All (scoped by role) |
| `/accounting/` | accounting | Admin/Management |
| `/maintenance/` | maintenance | Admin/Management |
| `/onboarding/` | onboarding | Public/Client |
| `/pengumuman/` | announcements | All (scoped by role) |
| `/komplain/` | complaints | All (scoped by role) |
| `/inventaris/` | inventory | Admin/Management |
| `/aktivitas/` | activity | Admin/Management |
| `/audit/` | audit | All (scoped by role) |
| `/kos/` | kos | Admin/Management |
| `/fasilitas/` | fasilitas | Admin/Management |

---

## Features

### 1. Multi-Kos Management
- Create/edit/delete kos
- Kos switcher in navbar (admin/management)
- Session-based kos context
- Invite codes for joining kos (KosInvite)
- Auto-assign creator as kos admin on creation

### 2. User & Role Management
- UserKos per-kos role assignment
- Roles: admin, management, client
- Global role fallback for backward compatibility
- `has_kos_access(kos_id, role)` — check access
- `get_managed_kos()` — list accessible kos
- `get_role_for_kos(kos_id)` — get role for specific kos

### 3. Room Management
- CRUD rooms per kos
- Status: tersedia, terisi, maintenance
- Tipe: Reguler, Deluxe, VIP, Suite
- Unique constraint: (kos_id, nomor_kamar)
- Room items inventory (RoomItem)
- Rupiah auto-format on monetary inputs

### 4. Booking System
- Client requests booking via onboarding
- Admin approves/rejects pending bookings
- Auto-status: pending → aktif → selesai
- Notification on status changes
- Check-in date, check-out date tracking

### 5. Payment Management
- Record payments against bookings
- Track: jumlah, tanggal_bayar, bulan_dibayar_untuk, metode
- Payment status: lunas, pending
- WhatsApp receipt (resi) integration
- Payment reminders via WhatsApp
- Rupiah auto-format

### 6. Accounting
- Income vs expense tracking
- 12-month chart visualization
- Filter by year/month
- Export CSV
- Expense categories: listrik, air, kebersihan, gaji, lainnya
- Vendor association for expenses

### 7. Maintenance
- Maintenance requests per room
- Priority: rendah, normal, tinggi
- Status: diajukan, diproses, selesai
- Vendor assignment
- WhatsApp vendor contact
- Notify occupant on completion
- Auto-set tanggal_selesai on completion

### 8. Vendor Management
- CRUD vendors
- Kategori: maintenance, listrik, kebersihan, lainnya
- WhatsApp contact integration
- Link to maintenance requests

### 9. Client Dashboard
- Active booking info (room, dates, payment status)
- Payment history
- Notification center (unread count, mark read)
- Booking history
- Mandatory check-in audit prompt

### 10. Admin Dashboard
- Stats: total kamar, terisi, tersedia, maintenance, penghuni
- Financial: pemasukan, pengeluaran, collection rate, occupancy rate
- 6-month income chart
- Recent payments & expenses
- Pending bookings & maintenance requests
- Unpaid bookings tracker
- Complaint counter
- Room audit overview

### 11. Audit System
- Check-in audit (mandatory for clients)
- Check-out audit (admin only)
- Room item condition tracking
- CSV/JSON export
- Audit history per booking

### 12. Inventory Management
- Room items CRUD
- Condition tracking: baik, rusak
- Per-room inventory view

### 13. Announcements
- CRUD announcements
- Priority: normal, sedang, penting
- Visibility toggle (ditampilkan)
- Activity logging

### 14. Complaints
- Client submits complaints
- Kategori: umum, fasilitas
- Admin responds (tanggapan)
- Status: diajukan, ditindaklanjuti, selesai

### 15. Fasilitas Umum
- Shared facility management (toilet, shower, dapur, etc.)
- Dynamic categories (FasilitasKategori)
- Condition tracking: baik, rusak_ringan, rusak_berat, maintenance
- "Laporkan rusak" quick action → redirects to expense form

### 16. Notifications
- System-wide notification engine
- Types: umum, pembayaran, maintenance, pengingat, booking
- WhatsApp integration (wa_sent tracking)
- Mark read/unread
- Client dashboard notification center

### 17. Activity Logging
- All admin actions logged
- Filter by model, tindakan
- Max 200 results per view

### 18. WhatsApp Integration
- Payment receipts (resi)
- Payment reminders
- Vendor contact
- Maintenance occupant notification
- URL-encoded messages

### 19. UI/UX
- Responsive: phone, tablet, desktop
- Rupiah auto-format on inputs
- Fasilitas text expand/collapse
- Chart.js visualizations
- Custom error pages (404, 500, 403)
- Flash messages with auto-dismiss
- Stat cards with icons
- Badge color coding

---

## Database

### Supabase (Production)
- Region: ap-south-1
- Session pooler: `aws-0-ap-south-1.pooler.supabase.com:5432`
- 19 tables, 81 indexes, 24 foreign keys
- Migrations in `supabase/migrations/`

### Migrations
| File | Description |
|------|-------------|
| `20250807000000_initial_schema.sql` | 15 base tables |
| `20250807010000_performance_indexes.sql` | 30 performance indexes |
| `20250807020000_fasilitas_umum.sql` | FasilitasUmum table |
| `20250807030000_fasilitas_kategori.sql` | FasilitasKategori table + defaults |
| `20250807040000_user_kos_roles.sql` | UserKos + KosInvite tables |

---

## Environment Variables

```bash
# .env (gitignored)
DATABASE_URL=postgresql://...      # Supabase connection string
SECRET_KEY=...                     # Flask secret
SUPABASE_URL=https://...           # Supabase project URL
SUPABASE_KEY=sb_publishable_...    # Supabase anon key
SUPABASE_SERVICE_KEY=sb_secret_... # Supabase service key
```

---

## Project Structure

```
sistem_kos/
├── app.py                    # Flask app factory
├── config.py                 # Configuration
├── extensions.py             # SQLAlchemy, LoginManager
├── helpers.py                # Utility functions & decorators
├── models.py                 # 19 SQLAlchemy models
├── requirements.txt          # Python dependencies
├── routes/
│   ├── __init__.py           # Blueprint registration
│   ├── auth.py               # Login, register, logout
│   ├── dashboard.py          # Admin & client dashboards
│   ├── rooms.py              # Room CRUD
│   ├── clients.py            # Client management
│   ├── payments.py           # Payment CRUD + WhatsApp
│   ├── accounting.py         # Financial tracking + export
│   ├── maintenance.py        # Maintenance + vendor
│   ├── onboarding.py         # Room browsing + booking
│   ├── announcements.py      # Announcement CRUD
│   ├── complaints.py         # Complaint system
│   ├── inventory.py          # Room items
│   ├── activity_log.py       # Activity log
│   ├── audit.py              # Room audit
│   ├── kos.py                # Multi-kos management
│   └── fasilitas.py          # Shared facilities
├── templates/
│   ├── base.html             # Layout + navbar
│   ├── auth/                 # Login, register
│   ├── dashboard/            # Admin, client dashboards
│   ├── rooms/                # Room CRUD + detail
│   ├── payments/             # Payment forms
│   ├── accounting/           # Financial views
│   ├── maintenance/          # Maintenance + vendor
│   ├── onboarding/           # Room browsing + booking
│   ├── announcements/        # Announcement views
│   ├── complaints/           # Complaint views
│   ├── inventory/            # Inventory views
│   ├── activity/             # Activity log
│   ├── audit/                # Audit forms
│   ├── kos/                  # Kos management
│   ├── fasilitas/            # Facility management
│   └── errors/               # 404, 500, 403
├── static/
│   └── css/style.css         # Custom styles
└── supabase/
    └── migrations/           # SQL migrations
```
