import json
import random
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "http://127.0.0.1:8000/api/payments"

PUMPS = ["Pump 1", "Pump 2", "Pump 3", "Pump 4"]
FUEL_TYPES = ["Petrol", "Diesel"]
PAYMENT_APPS = ["Google Pay", "PhonePe", "Paytm", "Card", "Cash"]
SHIFTS = ["Morning", "Afternoon", "Evening", "Night"]

def create_payment(dt):
    fuel = random.choice(FUEL_TYPES)

    if fuel == "Petrol":
        unit_price = round(random.uniform(98, 108), 2)
    else:
        unit_price = round(random.uniform(88, 96), 2)

    quantity = round(random.uniform(5, 45), 2)
    gross = round(quantity * unit_price, 2)

    payment_app = random.choices(
        PAYMENT_APPS,
        weights=[32, 25, 10, 18, 15],
        k=1
    )[0]

    status = random.choices(
        ["success", "pending", "failed"],
        weights=[92, 5, 3],
        k=1
    )[0]

    if status == "failed":
        received = 0
    elif status == "pending":
        received = round(gross * random.uniform(0.85, 0.99), 2)
    else:
        variance = random.choices(
            [0, random.uniform(1, 15)],
            weights=[90, 10],
            k=1
        )[0]
        received = round(max(0, gross - variance), 2)

    shift = (
        "Morning" if dt.hour < 12 else
        "Afternoon" if dt.hour < 17 else
        "Evening" if dt.hour < 22 else
        "Night"
    )

    return {
        "transaction_time": dt.isoformat(),
        "pump_id": random.choice(PUMPS),
        "fuel_type": fuel,
        "quantity_litres": quantity,
        "unit_price": unit_price,
        "payment_app": payment_app,
        "payment_status": status,
        "gross_amount": gross,
        "received_amount": received,
        "shift_name": shift,
        "external_reference": f"HIST-{dt.strftime('%Y%m%d%H%M%S')}-{random.randint(100000,999999)}"
    }

def send_payment(payment):
    data = json.dumps(payment).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, True
    except urllib.error.HTTPError as e:
        return e.code, False
    except Exception:
        return 0, False

def main():
    print("FuelFlow historical data generator")
    print("Generating 12 months of realistic payment history...")

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=365)

    payments = []

    current = start

    while current <= now:
        weekday = current.weekday()
        hour = current.hour

        if weekday >= 5:
            transactions = random.randint(18, 35)
        else:
            transactions = random.randint(25, 50)

        if 7 <= hour <= 10 or 17 <= hour <= 21:
            transactions += random.randint(5, 12)

        for _ in range(transactions):
            random_hour = random.randint(0, 23)
            random_minute = random.randint(0, 59)
            random_second = random.randint(0, 59)

            dt = current.replace(
                hour=random_hour,
                minute=random_minute,
                second=random_second,
                microsecond=0
            )

            payments.append(create_payment(dt))

        current += timedelta(days=1)

    random.shuffle(payments)

    print(f"Prepared {len(payments)} transactions.")
    print("Uploading transactions to FastAPI...")
    print("This may take a few minutes.")

    success = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(send_payment, p) for p in payments]

        for i, future in enumerate(as_completed(futures), 1):
            status, ok = future.result()

            if ok:
                success += 1
            else:
                failed += 1

            if i % 100 == 0 or i == len(payments):
                print(
                    f"Progress: {i}/{len(payments)} | "
                    f"Success: {success} | Failed: {failed}"
                )

    print()
    print("====================================")
    print("Historical data generation complete")
    print(f"Total transactions : {len(payments)}")
    print(f"Successfully added : {success}")
    print(f"Failed             : {failed}")
    print("====================================")

if __name__ == "__main__":
    main()
