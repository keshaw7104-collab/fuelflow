import unittest

import pandas as pd

from app.analytics import dashboard_metrics


class DashboardMetricsTests(unittest.TestCase):
    def test_success_rate_and_payment_app_rollup(self) -> None:
        frame = pd.DataFrame(
            [
                {"transaction_time": pd.Timestamp("2026-08-01T08:00:00Z"), "pump_id": "Pump 1", "payment_app": "Google Pay", "payment_status": "success", "gross_amount": 1000.0, "received_amount": 1000.0, "quantity_litres": 10.0, "is_success": 1, "successful_received": 1000.0, "successful_litres": 10.0, "settlement_variance": 0.0, "sale_date": pd.Timestamp("2026-08-01").date()},
                {"transaction_time": pd.Timestamp("2026-08-01T09:00:00Z"), "pump_id": "Pump 2", "payment_app": "PhonePe", "payment_status": "pending", "gross_amount": 500.0, "received_amount": 0.0, "quantity_litres": 5.0, "is_success": 0, "successful_received": 0.0, "successful_litres": 0.0, "settlement_variance": 0.0, "sale_date": pd.Timestamp("2026-08-01").date()},
                {"transaction_time": pd.Timestamp("2026-08-02T10:00:00Z"), "pump_id": "Pump 1", "payment_app": "Google Pay", "payment_status": "success", "gross_amount": 2000.0, "received_amount": 1990.0, "quantity_litres": 20.0, "is_success": 1, "successful_received": 1990.0, "successful_litres": 20.0, "settlement_variance": 10.0, "sale_date": pd.Timestamp("2026-08-02").date()},
            ]
        )
        result = dashboard_metrics(frame)

        self.assertEqual(result["summary"]["payment_attempts"], 3)
        self.assertEqual(result["summary"]["successful_payments"], 2)
        self.assertEqual(result["summary"]["received_amount"], 2990.0)
        self.assertAlmostEqual(result["summary"]["success_rate"], 66.67, places=2)
        self.assertEqual(result["payment_apps"][0]["payment_app"], "Google Pay")
        self.assertEqual(result["exceptions"][0]["settlement_variance"], 10.0)


if __name__ == "__main__":
    unittest.main()
