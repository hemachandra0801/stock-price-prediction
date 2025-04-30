-- Users
CREATE INDEX idx_users_email ON users USING HASH (email);

-- Portfolios
CREATE INDEX idx_portfolios_user ON portfolios(user_id);
CREATE INDEX idx_portfolios_stock ON portfolios(stock_id);

-- Historical Data
CREATE INDEX idx_historical_date ON stock_historical_data USING BRIN (date);
CREATE INDEX idx_historical_stock_date ON stock_historical_data(stock_id, date);

-- Transactions
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_time);

CREATE EXTENSION pgcrypto; -- For password hashing
CREATE EXTENSION timescaledb; -- For time-series optimization