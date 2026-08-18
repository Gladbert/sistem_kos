-- Default stay duration preset per kos (admin/management editable).
-- Applied as the auto-filled duration for new guest bookings.
ALTER TABLE kos ADD COLUMN IF NOT EXISTS default_stay_value integer NOT NULL DEFAULT 1;
ALTER TABLE kos ADD COLUMN IF NOT EXISTS default_stay_unit varchar(10) NOT NULL DEFAULT 'bulan';
