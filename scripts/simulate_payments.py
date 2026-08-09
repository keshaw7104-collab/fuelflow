import json
import random
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:8000/api/payments"

PUMPS = ["Pump 1", "Pump 2", "Pump 3", "Pump 4"]

FUEL_TYPES = ["Petrol", "Diesel"]

PAYMENT_APPS = [
    "Google Pay",
    "PhonePe",
    "Paytm",
    "Card",
    "Cash",
]

def create_payment():
    now = datetime.now(timezone.utc)

    fuel_type = random.choices(
        FUEL_TYPES,
        weights=[60, 40],
        k=1,
    )[0]

    if fuel_type == "Petrol":
        unit_price = round(random.uniform(98, 108), 2)
    else:
        unit_price = round(random.uniform(88, 96), 2)

    quantity = round(
        random.uniform(5, 45),
        2,
    )

    gross_amount = round(
        quantity * unit_price,
        2,
    )

    payment_app = random.choices(
        PAYMENT_APPS,
        weights=[32, 25, 10, 18, 15],
        k=1,
    )[0]

    payment_status = random.choices(
        ["success", "pending", "failed"],
        weights=[92, 5, 3],
        k=1,
    )[0]

    if payment_status == "failed":

        received_amount = 0

    elif payment_status == "pending":

        received_amount = round(
            gross_amount * random.uniform(0.85, 0.99),
            2,
        )

    else:

        if random.random() < 0.90:
            received_amount = gross_amount
        else:
            received_amount = round(
                max(
                    0,
                    gross_amount - random.uniform(1, 15),
                ),
                2,
            )

    if now.hour < 12:
        shift = "Morning"
    elif now.hour < 17:
        shift = "Afternoon"
    elif now.hour < 22:
        shift = "Evening"
    else:
        shift = "Night"

    reference = (
        f"LIVE-{now.strftime('%Y%m%d%H%M%S')}-"
        f"{random.randint(100000, 999999)}"
    )

    return {
        "transaction_time": now.isoformat(),
        "pump_id": random.choice(PUMPS),
        "fuel_type": fuel_type,
        "quantity_litres": quantity,
        "unit_price": unit_price,
        "payment_app": payment_app,
        "payment_status": payment_status,
        "gross_amount": gross_amount,
        "received_amount": received_amount,
        "shift_name": shift,
        "external_reference": reference,
    }


def send_payment(payment):
    data = json.dumps(payment).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:

            response.read()

            return response.status, True

    except urllib.error.HTTPError as error:

        return error.code, False

    except Exception:

        return 0, False


def main():

    print()
    print("==========================================")
    print(" FuelFlow Live Payment Simulator")
    print("==========================================")
    print()
    print("API:", API_URL)
    print("Status: RUNNING")
    print()
    print("A new simulated payment will be generated")
    print("continuously and inserted into PostgreSQL.")
    print()
    print("Press CTRL+C to stop.")
    print()

    total = 0
    successful = 0
    failed = 0

    try:

        while True:

            payment = create_payment()

            status, ok = send_payment(payment)

            total += 1

            if ok:
                successful += 1

                print(
                    f"[{payment['transaction_time'][11:19]}] "
                    f"{payment['pump_id']} | "
                    f"{payment['payment_app']} | "
                    f"{payment['fuel_type']} | "
                    f"{payment['payment_status'].upper()} | "
                    f"₹{payment['received_amount']:,.2f} | "
                    f"#{payment['external_reference']}"
                )

            else:

                failed += 1

                print(
                    f"[ERROR] Payment failed to send | "
                    f"HTTP {status}"
                )

            # Random interval between transactions.
            # Faster during the simulator demo, while still
            # looking like a continuous payment stream.
            delay = random.uniform(3, 8)

            time.sleep(delay)

    except KeyboardInterrupt:

        print()
        print()
        print("==========================================")
        print(" Simulator stopped")
        print("==========================================")
        print(f"Total generated : {total}")
        print(f"Successful      : {successful}")
        print(f"Failed          : {failed}")
        print()


if __name__ == "__main__":
    main()
