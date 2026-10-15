import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.loans import emi_for, repayment_schedule, simulated_credit_score


class LoanCalculationTests(unittest.TestCase):
    def test_emi_matches_monthly_reducing_balance_formula(self):
        self.assertEqual(emi_for("100000", "12", 12), Decimal("8884.88"))

    def test_zero_interest_emi_is_principal_divided_by_tenure(self):
        self.assertEqual(emi_for("1200", "0", 12), Decimal("100.00"))

    def test_repayment_schedule_finishes_principal_and_has_monthly_dates(self):
        emi, schedule = repayment_schedule("1000", "0", 3, date(2026, 1, 31))
        self.assertEqual(emi, Decimal("333.33"))
        self.assertEqual([row["due_date"] for row in schedule], ["2026-02-28", "2026-03-31", "2026-04-30"])
        self.assertEqual(sum(row["principal_due"] for row in schedule), Decimal("1000.00"))

    def test_simulated_score_explains_missing_evidence_and_stays_in_range(self):
        result = simulated_credit_score(active_accounts=2, relationship_months=18)
        self.assertGreaterEqual(result["score"], 300)
        self.assertLessEqual(result["score"], 900)
        self.assertTrue(result["missing_data"])
        self.assertIn("No loan repayment history is recorded", result["missing_data"][0])
        self.assertEqual(sum(factor["out_of"] for factor in result["factors"]), 600)

    def test_emi_rejects_invalid_principal_and_tenure(self):
        for principal, rate, months in ((0, 12, 12), (1000, 12, 0)):
            with self.subTest(principal=principal, months=months):
                with self.assertRaises(ValueError):
                    emi_for(principal, rate, months)


if __name__ == "__main__":
    unittest.main()
