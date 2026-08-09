from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd


def _number(value: object) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(value)


def payment_frame(conn, from_time: datetime, to_time: datetime) -> pd.DataFrame:
    """Load payment data into Pandas for reusable KPI and trend calculations."""
    query = """
        SELECT transaction_time, pump_id, fuel_type, quantity_litres, unit_price,
               payment_app, payment_status, gross_amount, received_amount, shift_name
        FROM payments
        WHERE transaction_time >= %s AND transaction_time <= %s
        ORDER BY transaction_time
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (from_time, to_time))
        frame = pd.DataFrame(cursor.fetchall())
    if frame.empty:
        return frame
    frame["transaction_time"] = pd.to_datetime(frame["transaction_time"], utc=True)
    for column in ["quantity_litres", "unit_price", "gross_amount", "received_amount"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    frame["is_success"] = np.where(frame["payment_status"].eq("success"), 1, 0)
    frame["successful_received"] = np.where(frame["is_success"].eq(1), frame["received_amount"], 0.0)
    frame["successful_litres"] = np.where(frame["is_success"].eq(1), frame["quantity_litres"], 0.0)
    frame["settlement_variance"] = np.where(frame["is_success"].eq(1), frame["gross_amount"] - frame["received_amount"], 0.0)
    frame["sale_date"] = frame["transaction_time"].dt.date
    return frame


def dashboard_metrics(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {
            "summary": {"payment_attempts": 0, "successful_payments": 0, "received_amount": 0, "litres_sold": 0, "average_ticket": 0, "success_rate": 0},
            "daily_sales": [], "payment_apps": [], "exceptions": []
        }
    successes = frame[frame["is_success"].eq(1)]
    attempts = int(len(frame)); successful_payments = int(len(successes)); received = _number(successes["received_amount"].sum())
    daily = frame.groupby("sale_date", as_index=False).agg(
        received_amount=("successful_received", "sum"), litres_sold=("successful_litres", "sum"), payment_attempts=("payment_status", "count"), successful_payments=("is_success", "sum")
    )
    by_app = frame.groupby("payment_app", as_index=False).agg(
        received_amount=("successful_received", "sum"), successful_payments=("is_success", "sum")
    ).sort_values("received_amount", ascending=False)
    exceptions = frame[(frame["payment_status"] != "success") | (frame["settlement_variance"] >= 5) | (frame["gross_amount"] >= 4000)].sort_values("transaction_time", ascending=False).head(10)
    return {
        "summary": {
            "payment_attempts": attempts,
            "successful_payments": successful_payments,
            "received_amount": round(received, 2),
            "litres_sold": round(_number(successes["quantity_litres"].sum()), 2),
            "average_ticket": round(received / successful_payments, 2) if successful_payments else 0,
            "success_rate": round(successful_payments / attempts * 100, 2) if attempts else 0
        },
        "daily_sales": [{"sale_date": str(row.sale_date), "received_amount": round(_number(row.received_amount), 2), "litres_sold": round(_number(row.litres_sold), 2), "payment_attempts": int(row.payment_attempts), "successful_payments": int(row.successful_payments)} for row in daily.itertuples(index=False)],
        "payment_apps": [{"payment_app": row.payment_app, "received_amount": round(_number(row.received_amount), 2), "successful_payments": int(row.successful_payments)} for row in by_app.itertuples(index=False)],
        "exceptions": [{"transaction_time": row.transaction_time.isoformat(), "pump_id": row.pump_id, "payment_app": row.payment_app, "payment_status": row.payment_status, "gross_amount": round(_number(row.gross_amount), 2), "received_amount": round(_number(row.received_amount), 2), "settlement_variance": round(_number(row.settlement_variance), 2)} for row in exceptions.itertuples(index=False)]
    }


def to_json_value(value: object) -> object:
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value
