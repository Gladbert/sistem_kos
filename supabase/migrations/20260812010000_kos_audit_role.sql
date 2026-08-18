-- Who performs room audits per kos (admin/management editable).
-- client (default) = guest does own check-in audit; management = admin+management only; admin = admin only.
ALTER TABLE kos ADD COLUMN IF NOT EXISTS audit_role varchar(20) NOT NULL DEFAULT 'client';
