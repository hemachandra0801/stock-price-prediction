CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    stock_id INT REFERENCES stocks(stock_id) ON DELETE CASCADE,
    type VARCHAR(4) CHECK (type IN ('BUY', 'SELL')),
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(12,4) NOT NULL,
    transaction_time TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'COMPLETED'
);

COMMENT ON TABLE transactions IS 'All user buy/sell transactions';