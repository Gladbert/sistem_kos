# DO / DONT REPO RULES (sistem_kos)

Generated from session work on the audit module. These are hard rules for this project.

## DO

- Use `rtk` prefix for ALL shell commands (ls, cp, mv, rm, git, python, cat, head, wc, sed). Bare shell commands fail.
- Use the test client style already in `test_all.py`: `FlaskClient(app)` from `flask.testing`, login via `client.post('/auth/login', ...)`, then `client.get/post(...)`.
- Run tests with: `rtk python test_all.py`
- Add audit tests under clearly numbered sections (12. AUDIT, 13. AUTHZ, 14. EDGE CASES) matching the existing pattern.
- Clean up DB state between audit tests: delete `RoomItem` for a room, re-add items, delete/recreate `RoomAudit` before asserting.
- Guard all `RoomAudit.query...first()` results with `if x:` before accessing `.id` (avoid `None.id`).
- Commit only what the task touches; stage specific files, not `git add .` blindly.
- When expanding tests, append new sections at the END of `test_all.py` before the SUMMARY block.
- Register new blueprints both in `routes/__init__.py` (import + register) and reference via `url_for("blueprint.func")`.
- Put audit item condition logic in the route: map `kondisi_{item.id}` and `catatan_{item.id}` from form.
- Delete `AuditItemResult` rows via `AuditItemResult.query.filter_by(audit_id=...).delete()` before re-adding in edit.
- Use `db.create_all()` in app context for test setup (re-seed pattern at top of test_all.py).

## DONT

- DONT run bare shell (ls, git, python) without `rtk` prefix — command not found.
- DONT edit `test_all.py` with `sed` — it mangles multiline Python (escaped `\n`, duplicate loops, broken indentation). Use Read+Edit or Write only.
- DONT append content via heredoc `cat >` from bash — JSON/quoting breaks; use the Write tool.
- DONT create `AuditItemResult` with `booking_id=` — column is `audit_id` (NOT NULL). This causes IntegrityError.
- DONT leave list comprehensions spanning multiple lines inside dict literals in `routes/audit.py` — invalid syntax. Build the list first, then assign.
- DONT reference `r.item.audit_results[...]` for export rows — use the `audit.items` relationship and `r.kondisi`/`r.catatan` directly.
- DONT run `git add .` / `git add -A` — it stages `instance/kos.db`, `__pycache__`, and other junk. Stage explicit paths.
- DONT delete and `git checkout HEAD -- test_all.py` to "fix" a broken file — it wipes ALL your new tests. Fix the specific lines instead.
- DONT commit `instance/kos.db` (already in .gitignore as `*.db` and `instance/`).
- DONT hardcode `current_user` outside a request context in tests — wrap DB setup in `with app.app_context():`.
- DONT skip the SUMMARY block at the end of test_all.py (`print` of passed/failed + `sys.exit(len(failed))`).
- DONT add tests that assume a specific booking belongs to a user without checking `booking.user_id` first.
- DONT create the `templates/audit/delete.html` without registering the `delete` route — leave no orphan template/route.

## GOTCHAS
- `rtk` is a required wrapper; treat it as the shell.
- `test_all.py` drops & recreates all tables at start — always re-seed users/rooms/vendors there.
- Audit `check_in` is client-or-admin; `check_out`/`edit`/`delete`/`export` are admin/management only.
- `check-out` requires a prior `check_in` audit to exist.
- `export` route: `?format=json` returns JSON, default returns CSV attachment.
