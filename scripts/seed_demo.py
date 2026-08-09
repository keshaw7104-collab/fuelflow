import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import numpy as np
import pandas as pd

# Allow this file to be run directly with: python scripts/seed_demo.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import connection


APPS = np.array(["Google Pay", "PhonePe", "Paytm", "Card", "Cash"])
FUELS = np.array(["Petrol", "Diesel", "CNG"])
PUMPS = np.array(["Pump 1", "Pump 2", "Pump 3", "Pump 4"])
SHIFTS = np.array(["Morning", "Afternoon", "Night"])


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def seed_demo_data() -> int:
    """Create 60 days of realistic sample records only for an empty database."""
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM payments")
        if cursor.fetchone()["count"]:
            return 0
        rng = np.random.default_rng(20260809)
        now = datetime.now(timezone.utc)
        dates = pd.date_range(end=now.date(), periods=60, freq="D")
        records: list[dict] = []
        budgets: list[dict] = []
        for day in dates:
            daily_budget = _money(float(rng.integers(145000, 185000)))
            budgets.append({"budget_date": day.date(), "revenue_budget": daily_budget, "expense_budget": _money(float(rng.integers(21000, 31000)))})
            for index in range(int(rng.integers(34, 56))):
                fuel = str(rng.choice(FUELS, p=[0.55, 0.37, 0.08]))
                price = {"Petrol": 102.70, "Diesel": 92.40, "CNG": 79.20}[fuel]
                litres = round(float(rng.uniform(2.0, 42.0)), 2)
                gross = _money(litres * price)
                risk = float(rng.random())
                status = "success" if risk < 0.966 else "pending" if risk < 0.985 else "failed"
                received = gross if status == "success" else Decimal("0")
                if status == "success" and rng.random() < 0.025:
                    received = max(Decimal("0"), gross - _money(float(rng.uniform(1, 8))))
                hour = int(rng.integers(6, 23)); minute = int(rng.integers(0, 60)); second = int(rng.integers(0, 60))
                transaction_time = datetime(day.year, day.month, day.day, hour, minute, second, tzinfo=timezone.utc)
                records.append({
                    "transaction_time": transaction_time, "pump_id": str(rng.choice(PUMPS)), "fuel_type": fuel,
                    "quantity_litres": Decimal(str(litres)), "unit_price": _money(price), "payment_app": str(rng.choice(APPS, p=[0.32, 0.26, 0.12, 0.18, 0.12])),
                    "payment_status": status, "gross_amount": gross, "received_amount": received,
                    "shift_name": str(rng.choice(SHIFTS)), "external_reference": f"DEMO-{day.strftime('%Y%m%d')}-{index:03d}"
                })
        cursor.executemany(
            """INSERT INTO payments (transaction_time, pump_id, fuel_type, quantity_litres, unit_price, payment_app, payment_status, gross_amount, received_amount, shift_name, external_reference)
               VALUES (%(transaction_time)s, %(pump_id)s, %(fuel_type)s, %(quantity_litres)s, %(unit_price)s, %(payment_app)s, %(payment_status)s, %(gross_amount)s, %(received_amount)s, %(shift_name)s, %(external_reference)s)""",
            records,
        )
        cursor.executemany(
            "INSERT INTO daily_budgets (budget_date, revenue_budget, expense_budget) VALUES (%(budget_date)s, %(revenue_budget)s, %(expense_budget)s)",
            budgets,
        )
        conn.commit()
    return len(records)


if __name__ == "__main__":
    from app.database import close_pool, run_migrations

    try:
        run_migrations()
        created = seed_demo_data()
        print(f"Created {created} demo payments." if created else "Database already contains payments; no demo rows added.")
    finally:
        close_pool()
