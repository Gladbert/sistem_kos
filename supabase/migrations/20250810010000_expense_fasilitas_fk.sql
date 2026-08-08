-- Link expenses to recurring fasilitas
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS fasilitas_id integer REFERENCES fasilitas_umum(id);
COMMENT ON COLUMN expenses.fasilitas_id IS 'Linked recurring fasilitas, if auto-generated';
