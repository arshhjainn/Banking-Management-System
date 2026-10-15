import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import services.operations as operations


class FakeCursor:
    def __init__(self, rows, one=None):
        self.rows = rows
        self.one = one
        self.lastrowid = 55
        self.executed = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.one

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows, one=None):
        self.fake_cursor = FakeCursor(rows, one)
        self.committed = False
        self.rolled_back = False

    def cursor(self, dictionary=False):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class ConnectionContext:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, *_args):
        return False


def account(account_id, customer_id, branch_id, balance, status="ACTIVE"):
    return {"account_id": account_id, "customer_id": customer_id, "branch_id": branch_id,
            "balance": Decimal(balance), "status": status}


class TransferServiceTests(unittest.TestCase):
    def test_customer_transfer_to_another_customer_commits_as_one_unit(self):
        conn = FakeConnection([account(1, 7, 2, "100.00"), account(2, 8, 2, "25.00")], {"account_id": 2})
        with patch.object(operations, "connection", return_value=ConnectionContext(conn)):
            result = operations.move_money("transfer", {
                "source_account_id": 1, "destination_account_number": "RECIPIENT-002", "amount": "10.00",
            }, actor={"role": "CUSTOMER", "customer_id": 7})
        self.assertTrue(conn.committed)
        self.assertFalse(conn.rolled_back)
        self.assertEqual(len(result["reference_code"]), 36)
        self.assertEqual(sum("INSERT INTO transactions" in sql for sql, _ in conn.fake_cursor.executed), 1)
        transfer_insert = next(sql for sql, _ in conn.fake_cursor.executed if sql.startswith("INSERT INTO transfers"))
        self.assertIn("from_account_id,to_account_id", transfer_insert)

    def test_customer_cannot_transfer_from_another_customers_account(self):
        conn = FakeConnection([account(1, 8, 2, "100.00"), account(2, 7, 2, "25.00")], {"account_id": 2})
        with patch.object(operations, "connection", return_value=ConnectionContext(conn)):
            with self.assertRaises(PermissionError):
                operations.move_money("transfer", {
                    "source_account_id": 1, "destination_account_number": "OWN-002", "amount": "10.00",
                }, actor={"role": "CUSTOMER", "customer_id": 7})
        self.assertTrue(conn.rolled_back)
        self.assertFalse(conn.committed)

    def test_insufficient_funds_rolls_back_without_writes(self):
        conn = FakeConnection([account(1, 7, 2, "5.00"), account(2, 8, 2, "25.00")], {"account_id": 2})
        with patch.object(operations, "connection", return_value=ConnectionContext(conn)):
            with self.assertRaisesRegex(ValueError, "Insufficient balance"):
                operations.move_money("transfer", {
                    "source_account_id": 1, "destination_account_number": "RECIPIENT-002", "amount": "10.00",
                }, actor={"role": "CUSTOMER", "customer_id": 7})
        self.assertTrue(conn.rolled_back)
        self.assertFalse(conn.committed)
        self.assertFalse(any(sql.startswith("INSERT") or sql.startswith("UPDATE") for sql, _ in conn.fake_cursor.executed))

    def test_manager_deposit_is_limited_to_assigned_branch(self):
        conn = FakeConnection([], {"balance": Decimal("10.00"), "status": "ACTIVE", "customer_id": 7, "branch_id": 2})
        with patch.object(operations, "connection", return_value=ConnectionContext(conn)):
            result = operations.move_money("deposit", {"account_id": 5, "amount": "3.00"},
                                           actor={"role": "BRANCH_MANAGER", "branch_id": 2})
        self.assertTrue(conn.committed)
        self.assertEqual(result["message"], "Deposit completed")
        self.assertTrue(any(sql.startswith("INSERT INTO transactions") for sql, _ in conn.fake_cursor.executed))

    def test_manager_deposit_to_another_branch_rolls_back(self):
        conn = FakeConnection([], {"balance": Decimal("10.00"), "status": "ACTIVE", "customer_id": 7, "branch_id": 9})
        with patch.object(operations, "connection", return_value=ConnectionContext(conn)):
            with self.assertRaises(PermissionError):
                operations.move_money("deposit", {"account_id": 5, "amount": "3.00"},
                                      actor={"role": "BRANCH_MANAGER", "branch_id": 2})
        self.assertTrue(conn.rolled_back)
        self.assertFalse(conn.committed)

    def test_customer_deposit_and_withdrawal_are_rejected_before_database_access(self):
        with patch.object(operations, "connection") as db_connection:
            for kind in ("deposit", "withdraw"):
                with self.subTest(kind=kind):
                    with self.assertRaisesRegex(PermissionError, "handled by your branch manager"):
                        operations.move_money(kind, {"account_id": 5, "amount": "3.00"},
                                              actor={"role": "CUSTOMER", "customer_id": 7})
        db_connection.assert_not_called()

    def test_transfer_involving_inactive_account_rolls_back(self):
        conn = FakeConnection([account(1, 7, 2, "100.00"), account(2, 8, 2, "25.00", "INACTIVE")], {"account_id": 2})
        with patch.object(operations, "connection", return_value=ConnectionContext(conn)):
            with self.assertRaisesRegex(ValueError, "Both accounts must be active"):
                operations.move_money("transfer", {
                    "source_account_id": 1, "destination_account_number": "RECIPIENT-002", "amount": "10.00",
                }, actor={"role": "CUSTOMER", "customer_id": 7})
        self.assertTrue(conn.rolled_back)
        self.assertFalse(conn.committed)

    def test_invalid_amount_is_rejected_before_database_access(self):
        with patch.object(operations, "connection") as connection:
            with self.assertRaisesRegex(ValueError, "greater than zero"):
                operations.move_money("transfer", {
                    "source_account_id": 1, "destination_account_number": "RECIPIENT-002", "amount": "0",
                }, actor={"role": "CUSTOMER", "customer_id": 7})
        connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
