from datetime import datetime
from uuid import UUID

from app.analytics import to_json_value
from app.models import PaymentInput, PaymentPatch


PAYMENT_FIELDS = "transaction_time, pump_id, fuel_type, quantity_litres, unit_price, payment_app, payment_status, gross_amount, received_amount, shift_name, external_reference"


def serialise_payment(row: dict) -> dict:
    return {key: to_json_value(value) for key, value in row.items()}


def create_payment(conn, payment: PaymentInput) -> dict:
    values = payment.model_dump()
    with conn.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO payments ({PAYMENT_FIELDS}) VALUES (%(transaction_time)s, %(pump_id)s, %(fuel_type)s, %(quantity_litres)s, %(unit_price)s, %(payment_app)s, %(payment_status)s, %(gross_amount)s, %(received_amount)s, %(shift_name)s, %(external_reference)s) RETURNING *",
            values,
        )
        row = cursor.fetchone()
    conn.commit()
    return serialise_payment(row)


def list_payments(conn, from_time: datetime, to_time: datetime, limit: int = 100) -> list[dict]:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM payments WHERE transaction_time >= %s AND transaction_time <= %s ORDER BY transaction_time DESC LIMIT %s",
            (from_time, to_time, limit),
        )
        rows = cursor.fetchall()
    return [serialise_payment(row) for row in rows]


def update_payment(conn, payment_id: UUID, patch: PaymentPatch) -> dict | None:
    changes = {key: value for key, value in patch.model_dump().items() if value is not None}
    if not changes:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM payments WHERE payment_id = %s", (payment_id,))
            row = cursor.fetchone()
        return serialise_payment(row) if row else None
    assignments = ", ".join(f"{column} = %({column})s" for column in changes)
    changes["payment_id"] = payment_id
    with conn.cursor() as cursor:
        cursor.execute(f"UPDATE payments SET {assignments}, updated_at = NOW() WHERE payment_id = %(payment_id)s RETURNING *", changes)
        row = cursor.fetchone()
    conn.commit()
    return serialise_payment(row) if row else None
