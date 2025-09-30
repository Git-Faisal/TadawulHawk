-- Tadawul Hawk Database Schema
-- Version: v0.0
-- Description: PostgreSQL schema for Saudi Tadawul Exchange stock data

-- ============================================
-- Drop tables if they exist (for clean setup)
-- ============================================
DROP TABLE IF EXISTS data_collection_log CASCADE;
DROP TABLE IF EXISTS annual_fundamentals CASCADE;
DROP TABLE IF EXISTS quarterly_fundamentals CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;
DROP TABLE IF EXISTS stocks CASCADE;

-- ============================================
-- Table 1: stocks (Stock Metadata)
-- ============================================
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    listing_date DATE,
    currency VARCHAR(10) DEFAULT 'SAR',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_symbol_format CHECK (symbol LIKE '%.SR')
);

-- Indexes for stocks table
CREATE INDEX idx_stocks_symbol ON stocks(symbol);
CREATE INDEX idx_stocks_sector ON stocks(sector);
CREATE INDEX idx_stocks_is_active ON stocks(is_active);

COMMENT ON TABLE stocks IS 'Stock metadata for Tadawul-listed companies';
COMMENT ON COLUMN stocks.symbol IS 'Stock symbol with .SR suffix (e.g., 2222.SR)';
COMMENT ON COLUMN stocks.listing_date IS 'Date when stock was first listed on Tadawul';

-- ============================================
-- Table 2: price_history (Price Data)
-- ============================================
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    data_date DATE NOT NULL,

    -- Current/Latest Price
    last_close_price NUMERIC(12, 3),

    -- Historical Prices (specific lookback periods)
    price_1m_ago NUMERIC(12, 3),
    price_3m_ago NUMERIC(12, 3),
    price_6m_ago NUMERIC(12, 3),
    price_9m_ago NUMERIC(12, 3),
    price_12m_ago NUMERIC(12, 3),

    -- 52-week high/low
    week_52_high NUMERIC(12, 3),
    week_52_low NUMERIC(12, 3),

    -- 3-year high/low
    year_3_high NUMERIC(12, 3),
    year_3_low NUMERIC(12, 3),

    -- 5-year high/low
    year_5_high NUMERIC(12, 3),
    year_5_low NUMERIC(12, 3),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_price_stock_date UNIQUE(stock_id, data_date)
);

-- Indexes for price_history table
CREATE INDEX idx_price_stock_id ON price_history(stock_id);
CREATE INDEX idx_price_data_date ON price_history(data_date);

COMMENT ON TABLE price_history IS 'Historical price data including lookback periods and high/low ranges';
COMMENT ON COLUMN price_history.data_date IS 'Date when this price snapshot was taken';

-- ============================================
-- Table 3: quarterly_fundamentals (Quarterly Financial Data)
-- ============================================
CREATE TABLE quarterly_fundamentals (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL CHECK (fiscal_quarter BETWEEN 1 AND 4),
    quarter_end_date DATE NOT NULL,

    -- Financial Metrics (in currency units)
    revenue NUMERIC(18, 2),
    gross_profit NUMERIC(18, 2),
    net_income NUMERIC(18, 2),
    operating_cash_flow NUMERIC(18, 2),
    free_cash_flow NUMERIC(18, 2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_quarterly_stock_period UNIQUE(stock_id, fiscal_year, fiscal_quarter)
);

-- Indexes for quarterly_fundamentals table
CREATE INDEX idx_quarterly_stock_id ON quarterly_fundamentals(stock_id);
CREATE INDEX idx_quarterly_fiscal_year ON quarterly_fundamentals(fiscal_year);
CREATE INDEX idx_quarterly_period ON quarterly_fundamentals(fiscal_year, fiscal_quarter);

COMMENT ON TABLE quarterly_fundamentals IS 'Quarterly financial fundamentals for last 5 years';
COMMENT ON COLUMN quarterly_fundamentals.fiscal_quarter IS 'Quarter number: 1=Q1, 2=Q2, 3=Q3, 4=Q4';
COMMENT ON COLUMN quarterly_fundamentals.revenue IS 'Total revenue/sales for the quarter';

-- ============================================
-- Table 4: annual_fundamentals (Annual Financial Data)
-- ============================================
CREATE TABLE annual_fundamentals (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    fiscal_year INTEGER NOT NULL,
    year_end_date DATE NOT NULL,

    -- Financial Metrics (in currency units)
    revenue NUMERIC(18, 2),
    gross_profit NUMERIC(18, 2),
    net_income NUMERIC(18, 2),
    operating_cash_flow NUMERIC(18, 2),
    free_cash_flow NUMERIC(18, 2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_annual_stock_year UNIQUE(stock_id, fiscal_year)
);

-- Indexes for annual_fundamentals table
CREATE INDEX idx_annual_stock_id ON annual_fundamentals(stock_id);
CREATE INDEX idx_annual_fiscal_year ON annual_fundamentals(fiscal_year);

COMMENT ON TABLE annual_fundamentals IS 'Annual financial fundamentals for last 5 years';
COMMENT ON COLUMN annual_fundamentals.year_end_date IS 'Fiscal year end date';

-- ============================================
-- Table 5: data_collection_log (Audit Trail)
-- ============================================
CREATE TABLE data_collection_log (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    collection_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    records_collected INTEGER DEFAULT 0,
    error_message TEXT,
    collection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_collection_type CHECK (collection_type IN ('price', 'quarterly', 'annual', 'metadata')),
    CONSTRAINT chk_status CHECK (status IN ('success', 'failed', 'partial'))
);

-- Indexes for data_collection_log table
CREATE INDEX idx_log_stock_id ON data_collection_log(stock_id);
CREATE INDEX idx_log_timestamp ON data_collection_log(collection_timestamp);
CREATE INDEX idx_log_status ON data_collection_log(status);
CREATE INDEX idx_log_collection_type ON data_collection_log(collection_type);

COMMENT ON TABLE data_collection_log IS 'Audit trail for data collection operations';
COMMENT ON COLUMN data_collection_log.collection_type IS 'Type of data collected: price, quarterly, annual, metadata';
COMMENT ON COLUMN data_collection_log.status IS 'Collection status: success, failed, partial';

-- ============================================
-- Trigger: Update updated_at timestamp automatically
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at column
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON stocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_price_history_updated_at BEFORE UPDATE ON price_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quarterly_fundamentals_updated_at BEFORE UPDATE ON quarterly_fundamentals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_annual_fundamentals_updated_at BEFORE UPDATE ON annual_fundamentals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- End of Schema
-- ============================================