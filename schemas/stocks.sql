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