from app.realtime import router as realtime_router
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
from uuid import UUID
import csv

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.analytics import dashboard_metrics, payment_frame
from app.config import settings
from app.database import close_pool, connection, open_pool, run_migrations
from app.models import PaymentInput, PaymentPatch
from app.repository import create_payment, list_payments, update_payment
from scripts.seed_demo import seed_demo_data


def time_range(
    from_time: datetime | None,
    to_time: datetime | None,
) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)

    start = from_time or (
        now - timedelta(days=6)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end = to_time or now

    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    if start > end:
        raise HTTPException(
            status_code=422,
            detail="Start date cannot be after end date.",
        )

    if end - start > timedelta(days=366):
        raise HTTPException(
            status_code=422,
            detail="Use a valid date range of no more than 366 days.",
        )

    return start, end


@asynccontextmanager
async def lifespan(_: FastAPI):
    open_pool()
    run_migrations()

    if settings.seed_demo_data:
        created = seed_demo_data()

        if created:
            print(f"Seeded {created} demo payments.")

    yield

    close_pool()


app = FastAPI(
    title="FuelFlow Payment Intelligence API",
    version="1.0.0",
    description=(
        "Python, Pandas, NumPy, SQL, Excel and PostgreSQL "
        "API for petrol-pump payment analysis."
    ),
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=PlainTextResponse)
def root() -> str:
    return (
        "FuelFlow API is running. "
        "Open /docs for the API."
    )


@app.get("/health")
def health() -> dict:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT 1 AS ok")
        cursor.fetchone()

    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/dashboard")
def dashboard(
    from_time: datetime | None = Query(
        default=None,
        alias="from",
    ),
    to_time: datetime | None = Query(
        default=None,
        alias="to",
    ),
) -> dict:

    start, end = time_range(
        from_time,
        to_time,
    )

    with connection() as conn:
        frame = payment_frame(
            conn,
            start,
            end,
        )

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        **dashboard_metrics(frame),
    }


@app.get("/api/payments")
def payments(
    from_time: datetime | None = Query(
        default=None,
        alias="from",
    ),
    to_time: datetime | None = Query(
        default=None,
        alias="to",
    ),
    limit: int = Query(
        default=5000,
        ge=1,
        le=50000,
    ),
) -> dict:

    start, end = time_range(
        from_time,
        to_time,
    )

    with connection() as conn:
        rows = list_payments(
            conn,
            start,
            end,
            limit,
        )

    return {
        "payments": rows,
        "count": len(rows),
        "from": start.isoformat(),
        "to": end.isoformat(),
    }


@app.post(
    "/api/payments",
    status_code=201,
)
def add_payment(
    payment: PaymentInput,
) -> dict:

    with connection() as conn:
        return {
            "payment": create_payment(
                conn,
                payment,
            )
        }


@app.patch("/api/payments/{payment_id}")
def patch_payment(
    payment_id: UUID,
    patch: PaymentPatch,
) -> dict:

    with connection() as conn:
        payment = update_payment(
            conn,
            payment_id,
            patch,
        )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found.",
        )

    return {
        "payment": payment,
    }


@app.get("/api/payments/export.csv")
def export_csv(
    from_time: datetime | None = Query(
        default=None,
        alias="from",
    ),
    to_time: datetime | None = Query(
        default=None,
        alias="to",
    ),
) -> StreamingResponse:

    start, end = time_range(
        from_time,
        to_time,
    )

    with connection() as conn:
        rows = list_payments(
            conn,
            start,
            end,
            limit=50000,
        )

    fieldnames = (
        rows[0].keys()
        if rows
        else ["payment_id"]
    )

    output = StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(rows)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; "
                "filename=fuelflow-payment-history.csv"
            )
        },
    )


@app.post("/api/import/excel")
async def import_excel(
    file: UploadFile = File(...),
) -> dict:

    if not file.filename or not file.filename.lower().endswith(
        (".xlsx", ".xls")
    ):
        raise HTTPException(
            status_code=422,
            detail="Upload an Excel .xlsx or .xls file.",
        )

    data = pd.read_excel(
        BytesIO(await file.read()),
        sheet_name="Payment Import",
    )

    required = {
        "transaction_time",
        "pump_id",
        "fuel_type",
        "quantity_litres",
        "unit_price",
        "payment_app",
        "payment_status",
        "gross_amount",
        "received_amount",
        "shift_name",
        "external_reference",
    }

    if not required.issubset(
        set(data.columns)
    ):
        missing = ", ".join(
            sorted(
                required - set(data.columns)
            )
        )

        raise HTTPException(
            status_code=422,
            detail=(
                f"Excel template is missing: "
                f"{missing}"
            ),
        )

    data = data.replace(
        {np.nan: None}
    )

    imported = 0
    rejected: list[dict] = []

    with connection() as conn:

        for row_number, row in enumerate(
            data.to_dict(
                orient="records"
            ),
            start=2,
        ):

            if all(
                value is None
                for value in row.values()
            ):
                continue

            try:

                row["transaction_time"] = (
                    pd.Timestamp(
                        row["transaction_time"]
                    )
                    .to_pydatetime()
                    .isoformat()
                )

                payment = (
                    PaymentInput.model_validate(
                        row
                    )
                )

                create_payment(
                    conn,
                    payment,
                )

                imported += 1

            except Exception as error:

                conn.rollback()

                rejected.append(
                    {
                        "row": row_number,
                        "error": str(error),
                    }
                )

    return {
        "imported": imported,
        "rejected": rejected,
    }

app.include_router(realtime_router)
