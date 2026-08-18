-- Deposit policy per kos (admin/management editable): whether a 1-month deposit is charged on move-in.
ALTER TABLE kos ADD COLUMN IF NOT EXISTS deposit_required boolean NOT NULL DEFAULT true;
