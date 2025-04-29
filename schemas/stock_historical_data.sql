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
) PARTITION BY RANGE (date);

COMMENT ON TABLE stock_historical_data IS 'Daily historical stock prices';