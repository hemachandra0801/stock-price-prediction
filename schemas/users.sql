CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    verification_token TEXT,
    verified BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_users_email ON users(email);

COMMENT ON TABLE users IS 'Stores user authentication details';