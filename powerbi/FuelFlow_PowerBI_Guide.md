# FuelFlow Power BI Dashboard Guide

This report connects Power BI directly to the FuelFlow PostgreSQL database. Use the PostgreSQL **DirectQuery** storage mode for the live operational page, and optionally Import mode for historical monthly reporting.

## 1. Connect Power BI Desktop to PostgreSQL

1. Open **Power BI Desktop**.
2. Select **Get data → PostgreSQL database**.
3. Enter the PostgreSQL host and database values from Render's database dashboard. For local testing use `localhost:5432` and database `fuelflow`.
4. Under **Data connectivity mode**, choose **DirectQuery** for the live dashboard.
5. Sign in with the database username and password. Keep the credentials private.
6. Select these database views:

   - `v_daily_payment_summary`
   - `v_payment_app_summary`
   - `v_pump_shift_summary`
   - `v_settlement_exceptions`

Power BI's PostgreSQL connector supports both Import and DirectQuery. Current Power BI Desktop includes the PostgreSQL provider, so a separate Npgsql installation is normally unnecessary. [Microsoft connector guide](https://learn.microsoft.com/en-us/power-query/connectors/postgresql)

## 2. Create the Date table

In **Modeling → New table**, add:

```DAX
Date =
CALENDAR (
    MIN ( 'v_daily_payment_summary'[sale_date] ),
    MAX ( 'v_daily_payment_summary'[sale_date] )
)
```

Add these calculated columns:

```DAX
Year = YEAR ( 'Date'[Date] )
Month Number = MONTH ( 'Date'[Date] )
Month = FORMAT ( 'Date'[Date], "MMM" )
Year Month = FORMAT ( 'Date'[Date], "YYYY-MMM" )
Weekday = FORMAT ( 'Date'[Date], "DDD" )
```

Sort `Date[Month]` by `Date[Month Number]`. Mark this table as the date table, then create single-direction relationships from `Date[Date]` to `sale_date` in each of the three summary views.

## 3. DAX measures

Create these measures in `v_daily_payment_summary`:

```DAX
Payments Received = SUM ( 'v_daily_payment_summary'[received_amount] )

Gross Sales = SUM ( 'v_daily_payment_summary'[gross_sales] )

Fuel Volume Sold = SUM ( 'v_daily_payment_summary'[litres_sold] )

Payment Attempts = SUM ( 'v_daily_payment_summary'[payment_attempts] )

Successful Payments = SUM ( 'v_daily_payment_summary'[successful_payments] )

Payment Success Rate = DIVIDE ( [Successful Payments], [Payment Attempts], 0 )

Average Ticket = DIVIDE ( [Payments Received], [Successful Payments], 0 )

Revenue Budget = SUM ( 'v_daily_payment_summary'[revenue_budget] )

Budget Variance = [Payments Received] - [Revenue Budget]

Budget Variance % = DIVIDE ( [Budget Variance], [Revenue Budget], 0 )

Settlement Variance = SUM ( 'v_daily_payment_summary'[settlement_variance] )
```

Format all currency measures as Indian Rupee and percentage measures as percentages with one decimal place.

## 4. Build the report pages

### Page 1 — Executive overview

- KPI cards: Payments Received, Gross Sales, Fuel Volume Sold, Payment Success Rate, Budget Variance.
- Line chart: `Date[Date]` by Payments Received.
- Clustered column chart: Payment app by received amount using `v_payment_app_summary`.
- Slicers: Date, payment app, pump, shift.

### Page 2 — Payment channels

- Donut chart: payment app share of received amount.
- Stacked column chart: payment app by Date.
- Matrix: payment app, successful payments, received amount, success rate.

### Page 3 — Pump and shift analysis

- Bar chart: pump by received amount.
- Heat map/matrix: shift versus pump.
- Line chart: litres sold by date.

### Page 4 — Settlement exceptions

- Table from `v_settlement_exceptions` showing payment time, app, status, expected amount, received amount, variance, and exception reason.
- Conditional formatting: red for failed, amber for pending, red for a settlement variance.

## 5. Real-time page refresh

For a real-time operational page, the report must use DirectQuery. In the Power BI page formatting pane, turn on **Page refresh** and select a fixed interval suitable for how often payments arrive (for example, 1–5 minutes). Automatic page refresh only appears for DirectQuery sources; service-level limits depend on workspace/capacity settings. [Microsoft automatic-refresh guide](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-automatic-page-refresh)

## 6. Refresh and security notes

- Use the Render database's connection details only in Power BI Desktop/service credentials; never commit them to GitHub.
- Set `SEED_DEMO_DATA=false` in Render once real transactions are being collected.
- Use a read-only PostgreSQL reporting user for Power BI in production.
- Publish the completed `.pbix` file to Power BI Service only after testing the DirectQuery credentials.
