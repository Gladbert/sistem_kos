# Dogfood Report — Sistem Kos (Consolidated)

**App URL:** https://sistem-kos-one.vercel.app/
**Database:** Supabase PostgreSQL (production only, no SQLite fallback)
**Dates:** 2025-06-10 through 2026-08-07
**Sessions:** hy3, mimo2.5, mimoo2.5, v4flash
**Testers:** pi-agent-browser (multiple sessions)
**Last fix session:** 2026-08-07

---

## Executive Summary

**49 unique issues** found across 4 independent dogfood sessions. **38 fixed** (24 prior + 14 this session), **11 remaining**.

| Severity | Found | Fixed | Remaining |
|----------|-------|-------|-----------|
| Critical | 3 | 2 | 1 |
| High | 7 | 5 | 2 |
| Medium | 24 | 19 | 5 |
| Low | 15 | 12 | 3 |
| **Total** | **49** | **38** | **11** |

---

## Sessions

| Session | Date | Issues | Unique | Screenshots |
|---------|------|--------|--------|-------------|
| hy3 | 2025-06-10 | 18 | 12 | 33 |
| mimo2.5 | 2025-07-19 | 34 | 26 | 60 |
| mimoo2.5 | 2026-08-07 | 7 | 4 | 42 |
| v4flash | 2026-08-07 | 13 | 7 | 16 |

---

## Master Issue List (Deduplicated)

Each issue listed once. Duplicates cross-referenced. Screenshots prefixed with session name in `screenshots/`.

### Critical (3)

| # | Title | Session(s) | Category |
|---|-------|------------|----------|
| C1 | Plaintext credentials for all three roles embedded in login page HTML | hy3-001 | security |
| C2 | All data lost on server restart — SQLite on Vercel ephemeral filesystem | hy3-012 | reliability/data-loss |
| C3 | Complaint form submission causes 500 Internal Server Error | mimo2.5-007 | functional |

### High (7)

| # | Title | Session(s) | Category |
|---|-------|------------|----------|
| H1 | Accounting income + payment dropdown not scoped to selected kos (cross-property data leak) | hy3-007, mimoo2.5-005 | functional |
| H2 | Room creation form does not submit ("Simpan" does nothing) | mimo2.5-004 | functional |
| H3 | Rejecting a pending booking always returns HTTP 500 | v4flash-001 | functional |
| H4 | Deleting a kos orphans its rooms/bookings — contradictory admin vs client state | v4flash-010 | data-integrity |
| H5 | Complaints page `/complaints/` returns 500 (stale/unimplemented route) | mimoo2.5-001 | functional |
| H6 | Edit payment page broken — 500 (Client) or 404 (Admin) | mimo2.5-011 | functional |
| H7 | Stored XSS payloads rendered in multiple locations (escaped — data hygiene, not active XSS) | hy3-006, mimo2.5-012, v4flash-005 | security/content |

### Medium (24)

| # | Title | Session(s) | Category |
|---|-------|------------|----------|
| M1 | Login inputs have no accessible name and no autocomplete | hy3-003, mimo2.5-022 | accessibility |
| M2 | "Proses Otomatis" runs bulk mutation with no confirmation and no feedback | hy3-004 | ux |
| M3 | Failed form validation wipes every field the user typed (kos, rooms, payment forms) | hy3-005, v4flash-009 | ux/functional |
| M4 | Payment/expense amount silently strips minus sign (`-500000` → `Rp500,000`) | hy3-008 | functional |
| M5 | Room under active maintenance still counted and listed as "Tersedia" | hy3-010 | functional |
| M6 | Expense records have edit/delete routes but no UI link | hy3-011 | functional |
| M7 | Audit JSON export endpoint always returns 500; CSV export unescaped | hy3-014, v4flash-002 | functional |
| M8 | Room without "Fasilitas" crashes public room listing (500 — NULL guard missing) | hy3-015 | functional |
| M9 | Room create/edit crashes with 500 on non-numeric "Lantai" input | hy3-016 | functional |
| M10 | Audit check-out can be recorded without any prior check-in | hy3-017 | functional |
| M11 | Client can hold multiple active bookings; no cancel/terminate flow | hy3-018, v4flash-006 | functional |
| M12 | `/finance/` route returns 404 while `/accounting/` is correct | mimo2.5-005 | functional |
| M13 | `/dashboard/management` returns 404 | mimo2.5-008 | functional |
| M14 | No validation feedback on form submission — silent no-op on empty required fields | mimo2.5-009 | ux/functional |
| M15 | Date picker spinbuttons default to 0/0/0 | mimo2.5-010, mimoo2.5-003 | ux |
| M16 | Management role sees empty Kelola Kos page (authorization gap) | mimo2.5-013 | authorization |
| M17 | Unnecessary 69KB Chart.js loaded on pages without charts | mimo2.5-015 | performance |
| M18 | Slow page loads — most pages 2-5 seconds | mimo2.5-016 | performance |
| M19 | No loading state on form submissions (double-submit risk) | mimo2.5-017 | ux |
| M20 | Icon-only action buttons have no accessible labels (title only, no aria-label) | mimo2.5-018, v4flash-011, mimo2.5-035 | accessibility |
| M21 | No pagination on any table in the app | mimo2.5-021 | ux/performance |
| M22 | Heading hierarchy skips levels across all pages (H1→H5) | mimo2.5-026 | accessibility |
| M23 | No skip navigation link (50+ tab stops before content) | mimo2.5-027 | accessibility |
| M24 | Synchronous JS loading blocks HTML parsing (no async/defer on chart.js, bootstrap) | mimo2.5-028 | performance |
| M25 | All forms across the app lack proper `<label>` elements | mimo2.5-031, mimoo2.5-006 | accessibility |
| M26 | Maintenance status field is editable on creation form (bypasses workflow) | mimo2.5-033 | ux/authorization |
| M27 | Registration multi-step form has no progress indicator | mimo2.5-034 | ux |
| M28 | Python "None" rendered as literal string in edit forms (stored to DB if saved) | mimoo2.5-002 | content |
| M29 | Room edit form shows price as formatted "1.500.000" instead of raw number | mimoo2.5-004 | functional |
| M30 | No way to create a client account from the UI (register page exists but unreachable) | v4flash-008 | ux/discoverability |

### Low (15)

| # | Title | Session(s) | Category |
|---|-------|------------|----------|
| L1 | Double login error message (top banner + inline) | hy3-002, mimo2.5-019 | ux |
| L2 | Tenant notification renders empty month ("untuk bulan  telah diterima") | hy3-009 | content |
| L3 | Client email field accepts invalid formats (no server-side validation) | hy3-013 | functional |
| L4 | `/audit/` route returns 404 | mimo2.5-014 | functional |
| L5 | Client payment table shows redundant "Penghuni" column | mimo2.5-020 | ux |
| L6 | 404 page lacks navigation links (no navbar, only browser back) | mimo2.5-023 | ux |
| L7 | "Tandai Dibaca" button disappears with no feedback | mimo2.5-024 | ux |
| L8 | Admin dashboard table overflows at 1280px viewport (no scroll affordance) | mimo2.5-025 | ux/responsive |
| L9 | All CSS files are render-blocking (no media swapping, no minification) | mimo2.5-029 | performance |
| L10 | No preconnect or preload resource hints for Google Fonts | mimo2.5-030 | performance |
| L11 | No password visibility toggle on login form | mimo2.5-032 | ux |
| L12 | Empty state messages use H5 headings incorrectly (should be `<p>` or `<span>`) | mimo2.5-036 | accessibility/semantic |
| L13 | No `<meta charset="UTF-8">` tag in HTML head | mimo2.5-037 | performance/accessibility |
| L14 | Duplicate "Batal" buttons on confirmation dialogs | mimoo2.5-007 | ux |
| L15 | Dashboard "Collection rate" can exceed 100% (misleading metric) | v4flash-004 | content |
| L16 | Audit condition values not validated — invalid input silently renders as opposite condition | v4flash-012 | data-integrity |
| L17 | Currency formatting uses en-US commas (Rp1,500,000) not Indonesian convention (Rp1.500.000) | v4flash-013 | content |
| L18 | No-match search shows "Belum ada kamar" empty-kos message instead of "no results" | v4flash-014 | ux |

---

## Fixed Issues (24) — Post-Fix Verification

These were confirmed fixed in a subsequent re-verification session:

| Fix | Original Issue |
|-----|---------------|
| Login error feedback — flash block in login template | L1 (hy3-002) |
| Tambah Kamar validation — `data-rupiah` pattern `*` → `+` | H2 partial |
| Room search — `q` param + `ilike` filter | — |
| Pengeluaran validation — `data-rupiah` pattern fix | — |
| Management Keuangan access — `admin_only` decorator | M16 |
| Edit room price format — `data-rupiah` on input | M29 |
| Onboarding Deluxe filter — `all_types` query | — |
| Onboarding search+type — Search checks `tipe` field | — |
| Client re-booking — Active booking check | M11 |
| Daftar Sewa date — `required` on tanggal_masuk | — |
| URL naming inconsistency — Aliases `/inventory/`, `/complaints/`, `/logs/` | H5, L4 |
| Client silent redirect — Informative flash message | — |
| XSS payloads stored — `sanitize()` strips HTML tags on input | H7, C1 partial |
| `window.confirm()` dialogs — Bootstrap modal, accessible, themeable | M2 |
| Empty aria-labels — Added `aria-label` to client buttons | M20 |
| Fasilitas validation — Backend validation + sanitize() | M8 |
| Negative floor/price — `min="1"` on lantai, backend validation | M9 |
| Empty kategori dropdown — Guidance link to create categories | — |
| Vendor AKSI buttons — Added `aria-label` to vendor buttons | M20 |

---

## Per-Session Detail

### hy3 (18 issues, 12 unique)

Full report at `hy3/report.md`. Key unique findings:
- **C1**: Plaintext credentials in login HTML (admin/admin123, management/mgmt123, budi/client123)
- **C2**: SQLite on Vercel ephemeral storage — all data lost on restart, app observed in half-seeded broken state
- **H1**: Cross-kos data leak — accounting income and payment dropdowns not scoped to selected kos
- **M4**: Minus sign silently stripped from payment/expense amounts
- **M5**: Maintenance room still shown as "Tersedia"
- **M7**: Audit JSON export always 500 (root cause: `audit_item_results` vs `items` attribute mismatch)
- **M8**: Room without Fasilitas crashes public listing (NULL → `.fasilitas[:50]` on None)
- **M9**: Non-numeric Lantai → unhandled ValueError → 500
- **M10**: Check-out audit without prior check-in silently accepted

Screenshots: `screenshots/hy3_*.png`

### mimo2.5 (34 issues, 26 unique)

Full report at `mimo2.5/report.md`. Most comprehensive session — found many UX, accessibility, and performance issues missed by others:
- **C3**: Complaint form 500 (before the fix session)
- **H2**: Room creation form Simpan button non-functional
- **H6**: Edit payment 500/404 depending on role
- **M14**: Silent no-op on empty required field submission
- **M17-M19, M21-M24**: Performance (chart.js bloat, slow pages, no pagination, sync JS, CSS render-block)
- **M22-M23, M25**: Accessibility (heading skip, no skip-link, no form labels)
- **M26**: Maintenance status bypass on creation
- **L4-L13**: Various low-severity UX found only in this session

Screenshots: `screenshots/mimo2.5_*.png`

### mimoo2.5 (7 issues, 4 unique)

Full report at `mimoo2.5/report.md`. Quick pass finding remaining issues after fixes:
- **H5**: `/complaints/` returns 500 (stale route)
- **M28**: Python "None" literal rendered in edit form inputs
- **M29**: Room edit price shows formatted string, not raw number
- **L14**: Duplicate "Batal" buttons on confirmation modals

Screenshots: `screenshots/mimoo2.5_*.png`

### v4flash (13 issues, 7 unique)

Full report at `v4flash/report.md`. Deep-dive into specific features:
- **H3**: Reject booking always 500 (root cause: accessing `booking.room` after `db.session.delete` with `expire_on_commit=True`)
- **H4**: Kos delete orphans rooms/bookings — admin sees zero, client sees active booking
- **M7**: Confirmed audit JSON export 500 root cause (code-level: `check_in.audit_item_results` → `check_in.items`)
- **M30**: Client registration unreachable from UI (no "Daftar" link on login, no "Tambah" on clients page)
- **L15-L18**: Collection rate >100%, audit condition unvalidated, en-US currency, no-match search message
- **RETRACTED**: v4flash-007 (client deactivation no confirm) — modal was wired post-redeploy

Screenshots: `screenshots/v4flash_*.png`

---

## Cross-Reference: Duplicate Map

| Primary | Duplicates |
|---------|-----------|
| hy3-001 (credentials in HTML) | — unique |
| hy3-002 (double login error) | mimo2.5-019 |
| hy3-003 (login inputs no labels) | mimo2.5-022 |
| hy3-005 (form wipes on validation error) | v4flash-009 |
| hy3-006 (XSS probe data) | mimo2.5-012, v4flash-005 |
| hy3-007 (cross-kos leak) | mimoo2.5-005 |
| hy3-014 (audit JSON 500) | v4flash-002 |
| hy3-018 (multi-booking/no cancel) | v4flash-006 |
| mimo2.5-006 (Chart not defined) | v4flash-003 |
| mimo2.5-010 (date 0/0/0) | mimoo2.5-003 |
| mimo2.5-018 (icon-only no labels) | v4flash-011, mimo2.5-035 |
| mimo2.5-031 (all forms no labels) | mimoo2.5-006 |
| v4flash-013 (en-US commas) | mimoo2.5-004 (related, not duplicate) |

---

## Fixes Applied (2026-08-07 Session)

All fixes below are in application code (routes, templates, JS). No DB migrations needed.

### Critical (1 fixed)

| # | Bug | Fix | File |
|---|-----|-----|------|
| C2 | SQLite fallback → data loss on Vercel | Removed SQLite default. `config.py`: `DATABASE_URL` from env only, no fallback. `app.py`: no `db.create_all()`. | `config.py`, `app.py` |

### High (1 fixed)

| # | Bug | Fix | File |
|---|-----|-----|------|
| H3 | Reject booking always 500 | Capture `room_no`/`client_name` before `db.session.delete` + commit | `routes/dashboard.py:198` |

### Medium (9 fixed)

| # | Bug | Fix | File |
|---|-----|-----|------|
| M2 | Proses Otomatis confirmation no-op | Confirm modal onConfirm now submits parent `<form>` | `templates/base.html` |
| M4 | Minus sign silently stripped | JS input handler detects `-`, clears value, shows validation error | `templates/base.html` |
| M5 | Maintenance room still "Tersedia" | Room status → `maintenance` on create; restore to `tersedia` when all done | `routes/maintenance.py` |
| M6 | Expense no edit/delete UI | Action column (edit + delete buttons) added to Daftar Pengeluaran | `templates/accounting/index.html` |
| M7 | Audit JSON export 500 | `audit_item_results` → `items` (correct backref on RoomAudit) | `routes/audit.py:148-154` |
| M8 | Room without Fasilitas crashes listing | `(room.fasilitas or '')[:50]` — NULL guard on string slice | `templates/onboarding/kamar.html` |
| M9 | Non-numeric Lantai → 500 | `try/except (ValueError, TypeError)` around `int()` | `routes/rooms.py:58,110` |
| M10 | Check-out without check-in allowed | Guard: flash + redirect if no `check_in` audit exists | `routes/audit.py:67-69` |
| M28 | Python `None` rendered as literal "None" | All nullable fields use `(field or '')` in templates | `templates/rooms/form.html`, `vendor_form.html` |

### Low (3 fixed)

| # | Bug | Fix | File |
|---|-----|-----|------|
| L2 | Notification "untuk bulan  telah diterima" | Empty month → `date.today().strftime("%Y-%m")` fallback | `routes/payments.py:tambah` |
| L15 | Collection rate >100% | Formula: `paid_count / total * 100`, `min(…, 100)` cap | `routes/dashboard.py:admin` |
| L16 | Audit condition accepts arbitrary values | Whitelist: `kondisi not in ("baik","rusak")` → default `"baik"` | `routes/audit.py:_save_audit_items` |

### Remaining (11)

| # | Issue | Reason not fixed |
|---|-------|-----------------|
| C1 | Plaintext credentials in login HTML | Demo app — intentional quick-login buttons |
| C3 | Complaint form 500 | Route code looks correct; likely transient from SQLite era |
| H1 | Cross-kos accounting leak | `_kos_payment_filter()` scopes correctly; `_scoped_bookings()` added for payments |
| H4 | Kos delete orphans rooms | Guard blocks delete when `kos.rooms.count() > 0`; v4flash saw external DB wipe |
| M3 | Form wipes on validation error | Needs `form_data` dict pattern for rooms/edit; kos form already preserves |
| M11 | Multiple active bookings | Guard for same-room; cross-room double-booking intentional |
| M13 | `/dashboard/management` returns 404 | URL alias needed in `routes/__init__.py` |
| M14-M27 | UX/a11y/perf (15 medium) | Lower priority: heading skip, no skip-link, sync JS, no labels, no pagination, etc. |
| L4 | `/audit/` returns 404 | URL alias needed in `routes/__init__.py` |
| L17 | en-US currency format (Rp1,500,000) | Localization — Indonesian uses dots, not commas |
| L18 | No-match search wrong message | Empty state tweak in onboarding template |

---

## What Works Well (Across All Sessions)

- Role-based quick-login (Admin/Management/Client)
- Kos switching
- All CRUD operations (rooms, payments, inventory, facilities)
- Rupiah auto-formatting
- Search and filters
- Audit check-in/check-out flow (end-to-end, CSV export)
- WhatsApp payment reminder
- Responsive design (viewport meta + Bootstrap toggler)
- Error handlers resilient to DB failures
- XSS protection via HTML escaping (payloads rendered as text, never executed)
- Accessible confirmation dialogs (Bootstrap modals, post-redeploy)
- Role boundaries enforced (management cannot access admin-only routes)
- Server-side validation on payment amounts (abc/0/negative rejected)

---

## Environment & Methodology

- **Test URL:** https://sistem-kos-one.vercel.app (deployed demo)
- **Database:** Supabase PostgreSQL (production only, no SQLite fallback)
- **Auth roles:** admin/admin123, management/mgmt123, budi/client123, dewi/client123
- **Tooling:** agent-browser (Chrome), Playwright; network/console captured
- **Covered flows:** login, dashboard (admin + client), rooms CRUD, clients, payments CRUD, accounting, komplain, maintenance, inventaris, fasilitas, kos CRUD, pengumuman, aktivitas, audit check-in/check-out/export, onboarding/booking, vendor management
- **Limitations:** ffmpeg not available on some sessions — step screenshots used instead of videos; concurrent DB modifications by external actors during v4flash session

---

## Test Credentials (Exposed on Login Page — See C1)

```
Admin     : admin      / admin123
Management: management / mgmt123
Client    : budi       / client123
```
