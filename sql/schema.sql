CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_time TIMESTAMPTZ NOT NULL,
    pump_id VARCHAR(50) NOT NULL,
    fuel_type VARCHAR(20) NOT NULL CHECK (fuel_type IN ('Petrol', 'Diesel', 'CNG')),
    quantity_litres NUMERIC(10,2) NOT NULL CHECK (quantity_litres > 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    payment_app VARCHAR(30) NOT NULL CHECK (payment_app IN ('Google Pay', 'PhonePe', 'Paytm', 'Card', 'Cash')),
    payment_status VARCHAR(20) NOT NULL CHECK (payment_status IN ('success', 'pending', 'failed')),
    gross_amount NUMERIC(12,2) NOT NULL CHECK (gross_amount > 0),
    received_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (received_amount >= 0),
    shift_name VARCHAR(50) NOT NULL DEFAULT 'General',
    external_reference VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_budgets (
    budget_date DATE PRIMARY KEY,
    revenue_budget NUMERIC(12,2) NOT NULL CHECK (revenue_budget >= 0),
    expense_budget NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (expense_budget >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS payments_transaction_time_idx ON payments (transaction_time DESC);
CREATE INDEX IF NOT EXISTS payments_status_idx ON payments (payment_status);
CREATE INDEX IF NOT EXISTS payments_app_idx ON payments (payment_app);

CREATE OR REPLACE VIEW v_daily_payment_summary AS
SELECT
    transaction_time::date AS sale_date,
    COUNT(*) AS payment_attempts,
    COUNT(*) FILTER (WHERE payment_status = 'success') AS successful_payments,
    COALESCE(SUM(quantity_litres) FILTER (WHERE payment_status = 'success'), 0) AS litres_sold,
    COALESCE(SUM(gross_amount) FILTER (WHERE payment_status = 'success'), 0) AS gross_sales,
    COALESCE(SUM(received_amount) FILTER (WHERE payment_status = 'success'), 0) AS received_amount,
    COALESCE(SUM(gross_amount - received_amount) FILTER (WHERE payment_status = 'success'), 0) AS settlement_variance,
    COALESCE(MAX(b.revenue_budget), 0) AS revenue_budget,
    COALESCE(SUM(received_amount) FILTER (WHERE payment_status = 'success'), 0) - COALESCE(MAX(b.revenue_budget), 0) AS budget_variance
FROM payments p
LEFT JOIN daily_budgets b ON b.budget_date = p.transaction_time::date
GROUP BY transaction_time::date;

CREATE OR REPLACE VIEW v_payment_app_summary AS
SELECT
    transaction_time::date AS sale_date,
    payment_app,
    COUNT(*) AS payment_attempts,
    COUNT(*) FILTER (WHERE payment_status = 'success') AS successful_payments,
    COALESCE(SUM(received_amount) FILTER (WHERE payment_status = 'success'), 0) AS received_amount
FROM payments
GROUP BY transaction_time::date, payment_app;

CREATE OR REPLACE VIEW v_pump_shift_summary AS
SELECT
    transaction_time::date AS sale_date,
    pump_id,
    shift_name,
    COUNT(*) AS payment_attempts,
    COALESCE(SUM(received_amount) FILTER (WHERE payment_status = 'success'), 0) AS received_amount,
    COALESCE(SUM(quantity_litres) FILTER (WHERE payment_status = 'success'), 0) AS litres_sold,
    COALESCE(SUM(gross_amount - received_amount) FILTER (WHERE payment_status = 'success'), 0) AS settlement_variance
FROM payments
GROUP BY transaction_time::date, pump_id, shift_name;

CREATE OR REPLACE VIEW v_settlement_exceptions AS
SELECT
    payment_id,
    transaction_time,
    pump_id,
    payment_app,
    payment_status,
    gross_amount,
    received_amount,
    gross_amount - received_amount AS variance_amount,
    CASE
        WHEN payment_status = 'failed' THEN 'Failed payment'
        WHEN payment_status = 'pending' THEN 'Pending payment'
        WHEN gross_amount - received_amount >= 5 THEN 'Settlement shortfall'
        WHEN gross_amount >= 4000 THEN 'High-value payment'
        ELSE 'Review'
    END AS exception_reason
FROM payments
WHERE payment_status <> 'success'
   OR gross_amount - received_amount >= 5
   OR gross_amount >= 4000;
