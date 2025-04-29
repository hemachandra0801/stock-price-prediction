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