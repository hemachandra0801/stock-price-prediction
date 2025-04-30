
CREATE TABLE stocks (
    stock_id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    exchange VARCHAR(50),
    sector VARCHAR(100),
    added_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE stocks IS 'Master list of tracked stocks';

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

CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    stock_id INT REFERENCES stocks(stock_id) ON DELETE CASCADE,
    transaction_type VARCHAR(4) CHECK (transaction_type IN ('BUY', 'SELL')),
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(12,4) NOT NULL,
    transaction_time TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'COMPLETED'
);

COMMENT ON TABLE transactions IS 'All user buy/sell transactions';

CREATE TABLE stock_historical_data (
    stock_id INT REFERENCES stocks(stock_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4) NOT NULL,
    volume BIGINT,
    adjusted_close DECIMAL(12,4),
    PRIMARY KEY (stock_id, date)
);

COMMENT ON TABLE stock_historical_data IS 'Daily historical stock prices';

CREATE TABLE portfolios (
    portfolio_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    stock_id INT REFERENCES stocks(stock_id) ON DELETE CASCADE,
    quantity INT NOT NULL CHECK (quantity >= 0),
    avg_purchase_price DECIMAL(12,4) NOT NULL,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, stock_id)
);

COMMENT ON TABLE portfolios IS 'Current stock holdings per user';