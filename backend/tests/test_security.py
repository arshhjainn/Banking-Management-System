import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as api


MANAGER_USER = {
    "user_id": 10, "username": "manager", "role": "BRANCH_MANAGER",
    "customer_id": None, "branch_id": 3, "customer_name": None,
    "customer_email": None, "branch_name": "Garden Branch",
}
CUSTOMER_USER = {
    "user_id": 20, "username": "customer", "role": "CUSTOMER",
    "customer_id": 7, "branch_id": None, "customer_name": "Demo Customer",
    "customer_email": "customer@example.test", "branch_name": None,
}


class WriteCursor:
    def __init__(self):
        self.lastrowid = 0
        self.rowcount = 1
        self.executed = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        if sql.startswith("INSERT INTO customers"):
            self.lastrowid = 101
        elif sql.startswith("INSERT INTO accounts"):
            self.lastrowid = 202
        elif sql.startswith("INSERT INTO users"):
            self.lastrowid = 303

    def fetchone(self):
        return None

    def close(self):
        pass


class WriteConnection:
    def __init__(self):
        self.write_cursor = WriteCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self.write_cursor

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


class LoanCursor:
    def __init__(self, application, fail_schedule=False):
        self.application = application
        self.fail_schedule = fail_schedule
        self.lastrowid = 700
        self.executed = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        if self.fail_schedule and sql.startswith("INSERT INTO loan_installments") and params[1] == 2:
            raise ValueError("simulated schedule write failure")

    def fetchone(self):
        return self.application

    def close(self):
        pass


class LoanConnection:
    def __init__(self, application, fail_schedule=False):
        self.loan_cursor = LoanCursor(application, fail_schedule)
        self.committed = False
        self.rolled_back = False

    def cursor(self, dictionary=False):
        return self.loan_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class ScopedApiTests(unittest.TestCase):
    def setUp(self):
        api.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = api.app.test_client()

    def login_as(self, user):
        with self.client.session_transaction() as state:
            state["user_id"] = user["user_id"]

    def test_unauthenticated_account_request_is_rejected(self):
        response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 401)

    def test_failed_login_returns_generic_401(self):
        with patch.object(api, "query", return_value=None):
            response = self.client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid username/email or password", response.get_json()["error"])

    def test_manager_account_list_is_scoped_to_assigned_branch(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(api, "query", return_value=[]) as query_mock:
            response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 200)
        sql, params = query_mock.call_args.args
        self.assertIn("a.branch_id=%s", sql)
        self.assertIn(3, params)

    def test_customer_account_list_is_scoped_to_customer(self):
        self.login_as(CUSTOMER_USER)
        with patch.object(api, "actor_row", return_value=CUSTOMER_USER), patch.object(api, "query", return_value=[]) as query_mock:
            response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 200)
        sql, params = query_mock.call_args.args
        self.assertIn("a.customer_id=%s", sql)
        self.assertIn(7, params)

    def test_customer_cannot_open_manager_api(self):
        self.login_as(CUSTOMER_USER)
        with patch.object(api, "actor_row", return_value=CUSTOMER_USER):
            response = self.client.get("/api/dashboard/stats")
        self.assertEqual(response.status_code, 403)

    def test_manager_cannot_open_customer_dashboard_api(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER):
            response = self.client.get("/api/customer/dashboard")
        self.assertEqual(response.status_code, 403)

    def test_manager_cannot_read_customer_outside_assigned_branch(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(api, "query", return_value=None) as query_mock:
            response = self.client.get("/api/customers/999")
        self.assertEqual(response.status_code, 404)
        sql, params = query_mock.call_args.args
        self.assertIn("a.branch_id=%s", sql)
        self.assertEqual(params, (999, 3))

    def test_customer_cannot_read_another_customers_account(self):
        self.login_as(CUSTOMER_USER)
        with patch.object(api, "actor_row", return_value=CUSTOMER_USER), patch.object(api, "query", return_value=None) as query_mock:
            response = self.client.get("/api/accounts/444")
        self.assertEqual(response.status_code, 404)
        sql, params = query_mock.call_args.args
        self.assertIn("a.customer_id=%s", sql)
        self.assertEqual(params, (444, 7))

    def test_manager_transaction_history_is_branch_scoped(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(api, "query", return_value=[]) as query_mock:
            response = self.client.get("/api/transactions?type=deposit")
        self.assertEqual(response.status_code, 200)
        sql, params = query_mock.call_args.args
        self.assertIn("a.branch_id=%s", sql)
        self.assertIn(3, params)

    def test_manager_dashboard_statistics_are_branch_scoped(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(
            api, "query", side_effect=[{"customers": 1, "accounts": 2, "total_balance": "50.00", "active_accounts": 2},
                                       {"deposits": "10.00", "withdrawals": "2.00"}, [], []]
        ) as query_mock:
            response = self.client.get("/api/dashboard/stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(query_mock.call_args_list), 4)
        for call in query_mock.call_args_list:
            sql, params = call.args
            self.assertIn("branch_id=%s", sql)
            self.assertIn(3, params)

    def test_customer_dashboard_statistics_are_customer_scoped(self):
        self.login_as(CUSTOMER_USER)
        with patch.object(api, "actor_row", return_value=CUSTOMER_USER), patch.object(
            api, "query", side_effect=[{"accounts": 1, "total_balance": "20.00"}, [], [], []]
        ) as query_mock:
            response = self.client.get("/api/customer/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(query_mock.call_args_list), 4)
        for call in query_mock.call_args_list:
            sql, params = call.args
            self.assertIn("customer_id=%s", sql)
            self.assertIn(7, params)

    def test_customer_transaction_history_is_customer_scoped(self):
        self.login_as(CUSTOMER_USER)
        with patch.object(api, "actor_row", return_value=CUSTOMER_USER), patch.object(api, "query", return_value=[]) as query_mock:
            response = self.client.get("/api/transactions")
        self.assertEqual(response.status_code, 200)
        sql, params = query_mock.call_args.args
        self.assertIn("a.customer_id=%s", sql)
        self.assertIn(7, params)

    def test_manager_can_post_branch_deposit_through_service(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(api, "move_money", return_value={"message": "Deposit completed"}) as service:
            response = self.client.post("/api/transactions/deposit", json={"account_id": 3, "amount": "5.00"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(service.call_args.kwargs["actor"]["branch_id"], 3)

    def test_manager_customer_onboarding_creates_branch_account_and_hashed_login(self):
        self.login_as(MANAGER_USER)
        conn = WriteConnection()
        payload = {"full_name": "New Customer", "email": "new@example.test", "phone": "9000000000",
                   "address": "Pune", "account_type": "savings", "username": "newcustomer", "password": "SecurePass123"}
        with patch.object(api, "actor_row", return_value=MANAGER_USER), \
             patch.object(api, "connection", return_value=ConnectionContext(conn)), \
             patch.object(api, "generate_password_hash", return_value="pbkdf2-fake-hash"):
            response = self.client.post("/api/customers", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(conn.committed)
        account_insert = next(params for sql, params in conn.write_cursor.executed if sql.startswith("INSERT INTO accounts"))
        user_insert = next(params for sql, params in conn.write_cursor.executed if sql.startswith("INSERT INTO users"))
        self.assertEqual(account_insert[2], 3)
        self.assertEqual(user_insert[1], "pbkdf2-fake-hash")
        self.assertEqual(user_insert[2], "CUSTOMER")
        self.assertEqual(user_insert[3], 101)

    def test_manager_account_creation_uses_assigned_branch_not_request_branch(self):
        self.login_as(MANAGER_USER)
        conn = WriteConnection()
        with patch.object(api, "actor_row", return_value=MANAGER_USER), \
             patch.object(api, "query", return_value={"customer_id": 8}), \
             patch.object(api, "connection", return_value=ConnectionContext(conn)):
            response = self.client.post("/api/accounts", json={"customer_id": 8, "account_type": "current", "branch_id": 900})
        self.assertEqual(response.status_code, 201)
        account_insert = next(params for sql, params in conn.write_cursor.executed if sql.startswith("INSERT INTO accounts"))
        self.assertEqual(account_insert[2], 3)

    def test_customer_deposit_and_withdrawal_are_forbidden(self):
        self.login_as(CUSTOMER_USER)
        with patch.object(api, "actor_row", return_value=CUSTOMER_USER), patch.object(api, "move_money") as service:
            for endpoint in ("deposit", "withdraw"):
                with self.subTest(endpoint=endpoint):
                    response = self.client.post(f"/api/transactions/{endpoint}", json={"account_id": 1, "amount": "1.00"})
                    self.assertEqual(response.status_code, 403)
        service.assert_not_called()

    def test_manager_cannot_use_customer_transfer_endpoint(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(api, "move_money") as service:
            response = self.client.post("/api/transactions/transfer", json={"source_account_id": 1, "destination_account_id": 2, "amount": "1.00"})
        self.assertEqual(response.status_code, 403)
        service.assert_not_called()

    def test_customer_loan_applications_are_scoped_to_authenticated_customer(self):
        self.login_as(CUSTOMER_USER)
        with patch.object(api, "actor_row", return_value=CUSTOMER_USER), patch.object(api, "query", return_value=[]) as query_mock:
            response = self.client.get("/api/customer/loan-applications")
        self.assertEqual(response.status_code, 200)
        sql, params = query_mock.call_args.args
        self.assertIn("WHERE customer_id=%s", sql)
        self.assertEqual(params, (7,))

    def test_manager_loan_applications_are_scoped_to_assigned_branch(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(api, "query", return_value=[]) as query_mock:
            response = self.client.get("/api/manager/loan-applications")
        self.assertEqual(response.status_code, 200)
        sql, params = query_mock.call_args.args
        self.assertIn("WHERE la.branch_id=%s", sql)
        self.assertEqual(params, (3,))

    def test_customer_cannot_open_manager_loan_management_api(self):
        self.login_as(CUSTOMER_USER)
        with patch.object(api, "actor_row", return_value=CUSTOMER_USER):
            response = self.client.get("/api/manager/loans")
        self.assertEqual(response.status_code, 403)

    def test_manager_cannot_open_customer_credit_health_api(self):
        self.login_as(MANAGER_USER)
        with patch.object(api, "actor_row", return_value=MANAGER_USER):
            response = self.client.get("/api/customer/credit-health")
        self.assertEqual(response.status_code, 403)

    def test_manager_disbursement_creates_schedule_in_single_transaction(self):
        self.login_as(MANAGER_USER)
        application = {"application_id": 41, "status": "APPROVED", "loan_type": "PERSONAL",
                       "requested_amount": Decimal("10000.00"), "tenure_months": 3,
                       "customer_id": 7, "branch_id": 3}
        conn = LoanConnection(application)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(api, "connection", return_value=ConnectionContext(conn)):
            response = self.client.post("/api/manager/loan-applications/41/disburse")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(conn.committed)
        self.assertFalse(conn.rolled_back)
        self.assertEqual(sum(sql.startswith("INSERT INTO loan_installments") for sql, _ in conn.loan_cursor.executed), 3)
        self.assertIn("branch_id=%s FOR UPDATE", conn.loan_cursor.executed[0][0])

    def test_failed_loan_schedule_write_rolls_back_disbursement(self):
        self.login_as(MANAGER_USER)
        application = {"application_id": 41, "status": "APPROVED", "loan_type": "PERSONAL",
                       "requested_amount": Decimal("10000.00"), "tenure_months": 3,
                       "customer_id": 7, "branch_id": 3}
        conn = LoanConnection(application, fail_schedule=True)
        with patch.object(api, "actor_row", return_value=MANAGER_USER), patch.object(api, "connection", return_value=ConnectionContext(conn)):
            response = self.client.post("/api/manager/loan-applications/41/disburse")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(conn.committed)
        self.assertTrue(conn.rolled_back)


if __name__ == "__main__":
    unittest.main()
