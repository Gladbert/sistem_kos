-- Multi-tenancy: user-kos roles and invite codes

CREATE TABLE IF NOT EXISTS user_kos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kos_id INTEGER NOT NULL REFERENCES kos(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'client',
    joined_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_user_kos UNIQUE (user_id, kos_id)
);

CREATE INDEX IF NOT EXISTS idx_userkos_user ON user_kos(user_id);
CREATE INDEX IF NOT EXISTS idx_userkos_kos ON user_kos(kos_id);
CREATE INDEX IF NOT EXISTS idx_userkos_role ON user_kos(role);

CREATE TABLE IF NOT EXISTS kos_invites (
    id SERIAL PRIMARY KEY,
    kos_id INTEGER NOT NULL REFERENCES kos(id) ON DELETE CASCADE,
    code VARCHAR(20) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'client',
    max_uses INTEGER DEFAULT 0,
    used_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invite_code ON kos_invites(code);
CREATE INDEX IF NOT EXISTS idx_invite_kos ON kos_invites(kos_id);
