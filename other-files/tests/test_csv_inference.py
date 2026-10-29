"""Smoke tests for Option A CSV input; run with python -m unittest discover -s other-files/tests."""
import io
import unittest

from ml.csv_inference import prepare_uploaded_csv

HEADER = ("timestamp_utc,location_id,current_speed_kmph,free_flow_speed_kmph,"
          "confidence,temperature_c,humidity_pct,rain_1h_mm,latitude,longitude\n")
VALID = "2026-10-18T10:00:00Z,H2S-01,24,45,0.92,30.5,78,0,22.5851,88.3468\n"


class CSVValidationTests(unittest.TestCase):
    def test_valid_row_and_kolkata_hour(self):
        valid, invalid = prepare_uploaded_csv(io.StringIO(HEADER + VALID))
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 0)
        self.assertEqual(int(valid.iloc[0]["hour"]), 15)
        self.assertAlmostEqual(float(valid.iloc[0]["speed_ratio"]), 24 / 45)

    def test_invalid_speed_rejected(self):
        valid, invalid = prepare_uploaded_csv(io.StringIO(HEADER + VALID.replace(",24,45,", ",-1,45,")))
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(invalid), 1)
        self.assertIn("current speed", invalid.iloc[0]["error"])

    def test_missing_column_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing columns"):
            prepare_uploaded_csv(io.StringIO("location_id\nH2S-01\n"))


if __name__ == "__main__":
    unittest.main()
