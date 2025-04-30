-- Create yearly partitions
CREATE TABLE stock_historical_data_2023 PARTITION OF stock_historical_data
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

-- Enable compression
ALTER TABLE stock_historical_data_2023 SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'date DESC'
);