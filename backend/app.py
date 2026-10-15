import os
import secrets
import sys
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, session, g
from flask_cors import CORS
from mysql.connector import IntegrityError, Error as MySQLError
from werkzeug.security import check_password_hash, generate_password_hash
from decimal import Decimal

# Keep the existing backend imports working when Vercel loads this module from
# the repository root as `backend.app`.
BACKEND_DIR = str(Path(__file__).resolve().parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from db import connection, query
from services.operations import amount_value, move_money
from services.loans import LOAN_RATES, decimal_value, emi_for, repayment_schedule, simulated_credit_score


MANAGER = "BRANCH_MANAGER"
CUSTOMER = "CUSTOMER"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-development-key-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8,
)
CORS(
    app,
    resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
    supports_credentials=True,
)


def body():
    return request.get_json(silent=True) or {}


def required(data, fields):
    missing = [field for field in fields if not str(data.get(field, "")).strip()]
    if missing:
        raise ValueError("Required fields: " + ", ".join(missing))


def fail(message, status=400):
    return jsonify({"error": message}), status


def account_number(cur):
    for _ in range(10):
        number = "1" + "".join(str(secrets.randbelow(10)) for _ in range(11))
        cur.execute("SELECT account_id FROM accounts WHERE account_number=%s", (number,))
        if not cur.fetchone():
            return number
    raise RuntimeError("Could not generate a unique account number")


def actor_row(user_id):
    return query(
        "SELECT u.user_id,u.username,u.role,u.customer_id,u.branch_id,"
        "c.full_name customer_name,c.email customer_email,b.branch_name "
        "FROM users u LEFT JOIN customers c ON c.customer_id=u.customer_id "
        "LEFT JOIN branches b ON b.branch_id=u.branch_id WHERE u.user_id=%s",
        (user_id,), one=True,
    )


def public_user(user):
    return {key: user.get(key) for key in (
        "user_id", "username", "role", "customer_id", "branch_id",
        "customer_name", "customer_email", "branch_name",
    )}


def require_roles(*roles):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return fail("Please log in", 401)
            user = actor_row(user_id)
            if not user:
                session.clear()
                return fail("Please log in", 401)
            g.user = user
            if roles and user["role"] not in roles:
                return fail("You do not have permission for this action", 403)
            return view(*args, **kwargs)
        return wrapped
    return decorate


@app.errorhandler(ValueError)
def bad_request(error):
    return fail(str(error), 400)


@app.errorhandler(PermissionError)
def forbidden(error):
    return fail(str(error), 403)


@app.errorhandler(IntegrityError)
def conflict(error):
    return fail("A record conflicts with an existing value or related record", 409)


@app.errorhandler(MySQLError)
def database_error(error):
    app.logger.exception("Database request failed")
    return fail("Database unavailable or query failed. Check the MySQL service and configuration.", 503)


@app.get("/api/health")
def health():
    query("SELECT 1")
    return jsonify({"status": "ok"})


@app.post("/api/auth/login")
def login():
    data = body()
    identifier = str(data.get("username", data.get("email", ""))).strip()
    password = str(data.get("password", ""))
    if not identifier or not password:
        return fail("Enter your username/email and password", 400)
    user = query(
        "SELECT u.user_id,u.username,u.password_hash,u.role,u.customer_id,u.branch_id,"
        "c.full_name customer_name,c.email customer_email,b.branch_name "
        "FROM users u LEFT JOIN customers c ON c.customer_id=u.customer_id "
        "LEFT JOIN branches b ON b.branch_id=u.branch_id "
        "WHERE u.username=%s OR c.email=%s LIMIT 1",
        (identifier, identifier.lower()), one=True,
    )
    if not user or not check_password_hash(user["password_hash"], password):
        return fail("Invalid username/email or password", 401)
    session.clear()
    session["user_id"] = user["user_id"]
    session.permanent = True
    return jsonify({"user": public_user(user)})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.get("/api/auth/me")
@require_roles(MANAGER, CUSTOMER)
def me():
    return jsonify({"user": public_user(g.user)})


@app.get("/api/customers")
@require_roles(MANAGER)
def customers():
    term = "%" + request.args.get("search", "").strip() + "%"
    return jsonify(query(
        "SELECT c.*,COUNT(DISTINCT a.account_id) account_count FROM customers c "
        "JOIN accounts a ON a.customer_id=c.customer_id "
        "WHERE a.branch_id=%s AND (c.full_name LIKE %s OR c.email LIKE %s) "
        "GROUP BY c.customer_id ORDER BY c.customer_id DESC",
        (g.user["branch_id"], term, term),
    ))


@app.get("/api/customers/<int:item_id>")
@require_roles(MANAGER)
def customer(item_id):
    row = query(
        "SELECT c.* FROM customers c WHERE c.customer_id=%s AND EXISTS "
        "(SELECT 1 FROM accounts a WHERE a.customer_id=c.customer_id AND a.branch_id=%s)",
        (item_id, g.user["branch_id"]), one=True,
    )
    if not row:
        return fail("Customer not found", 404)
    row["accounts"] = query(
        "SELECT a.*,b.branch_name FROM accounts a JOIN branches b ON b.branch_id=a.branch_id "
        "WHERE a.customer_id=%s AND a.branch_id=%s ORDER BY a.account_id DESC",
        (item_id, g.user["branch_id"]),
    )
    return jsonify(row)


@app.post("/api/customers")
@require_roles(MANAGER)
def create_customer():
    data = body()
    required(data, ["full_name", "email", "phone", "address", "username", "password"])
    if len(str(data["password"])) < 8:
        raise ValueError("Customer password must be at least 8 characters")
    account_type = str(data.get("account_type", "savings")).lower()
    if account_type not in ("savings", "current"):
        raise ValueError("Account type must be savings or current")
    with connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO customers(full_name,email,phone,address) VALUES(%s,%s,%s,%s)",
                (data["full_name"].strip(), data["email"].strip().lower(),
                 data["phone"].strip(), data["address"].strip()),
            )
            customer_id = cur.lastrowid
            number = account_number(cur)
            cur.execute(
                "INSERT INTO accounts(account_number,customer_id,branch_id,account_type) "
                "VALUES(%s,%s,%s,%s)",
                (number, customer_id, g.user["branch_id"], account_type),
            )
            account_id = cur.lastrowid
            cur.execute(
                "INSERT INTO users(username,password_hash,role,customer_id) VALUES(%s,%s,%s,%s)",
                (data["username"].strip(), generate_password_hash(data["password"], method="pbkdf2:sha256:600000"),
                 CUSTOMER, customer_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    return jsonify({"customer_id": customer_id, "account_id": account_id,
                    "account_number": number}), 201


@app.put("/api/customers/<int:item_id>")
@require_roles(MANAGER)
def update_customer(item_id):
    data = body()
    required(data, ["full_name", "email", "phone", "address"])
    with connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE customers SET full_name=%s,email=%s,phone=%s,address=%s "
            "WHERE customer_id=%s AND EXISTS (SELECT 1 FROM accounts a "
            "WHERE a.customer_id=customers.customer_id AND a.branch_id=%s)",
            (data["full_name"].strip(), data["email"].strip().lower(),
             data["phone"].strip(), data["address"].strip(), item_id, g.user["branch_id"]),
        )
        changed = cur.rowcount
        conn.commit()
        cur.close()
    if not changed:
        return fail("Customer not found or unchanged", 404)
    return jsonify({"message": "Customer updated"})


@app.get("/api/accounts")
@require_roles(MANAGER, CUSTOMER)
def accounts():
    clauses, args = [], []
    term = request.args.get("search", "").strip()
    if term:
        clauses.append("(a.account_number LIKE %s OR c.full_name LIKE %s)")
        args.extend([f"%{term}%", f"%{term}%"])
    for key, column in (("type", "a.account_type"), ("status", "a.status")):
        if request.args.get(key):
            clauses.append(f"LOWER({column})=LOWER(%s)")
            args.append(request.args[key])
    if g.user["role"] == MANAGER:
        clauses.append("a.branch_id=%s")
        args.append(g.user["branch_id"])
    else:
        clauses.append("a.customer_id=%s")
        args.append(g.user["customer_id"])
    where = " WHERE " + " AND ".join(clauses)
    return jsonify(query(
        "SELECT a.*,c.full_name customer_name,b.branch_name FROM accounts a "
        "JOIN customers c ON c.customer_id=a.customer_id "
        "JOIN branches b ON b.branch_id=a.branch_id" + where + " ORDER BY a.account_id DESC",
        tuple(args),
    ))


@app.get("/api/accounts/<int:item_id>")
@require_roles(MANAGER, CUSTOMER)
def account(item_id):
    scope_sql = "a.branch_id=%s" if g.user["role"] == MANAGER else "a.customer_id=%s"
    scope_id = g.user["branch_id"] if g.user["role"] == MANAGER else g.user["customer_id"]
    row = query(
        "SELECT a.*,c.full_name customer_name,b.branch_name FROM accounts a "
        "JOIN customers c ON c.customer_id=a.customer_id "
        "JOIN branches b ON b.branch_id=a.branch_id WHERE a.account_id=%s AND " + scope_sql,
        (item_id, scope_id), one=True,
    )
    return (jsonify(row), 200) if row else fail("Account not found", 404)


@app.post("/api/accounts")
@require_roles(MANAGER)
def create_account():
    data = body()
    required(data, ["customer_id", "account_type"])
    account_type = str(data["account_type"]).lower()
    if account_type not in ("savings", "current"):
        raise ValueError("Account type must be savings or current")
    if not query(
        "SELECT customer_id FROM accounts WHERE customer_id=%s AND branch_id=%s LIMIT 1",
        (int(data["customer_id"]), g.user["branch_id"]), one=True,
    ):
        return fail("Customer is not assigned to your branch", 403)
    with connection() as conn:
        cur = conn.cursor()
        try:
            number = account_number(cur)
            cur.execute(
                "INSERT INTO accounts(account_number,customer_id,branch_id,account_type) "
                "VALUES(%s,%s,%s,%s)",
                (number, int(data["customer_id"]), g.user["branch_id"], account_type),
            )
            account_id = cur.lastrowid
            conn.commit()
        finally:
            cur.close()
    return jsonify({"account_id": account_id, "account_number": number}), 201


@app.put("/api/accounts/<int:item_id>")
@require_roles(MANAGER)
def update_account(item_id):
    data = body()
    required(data, ["status"])
    status = str(data["status"]).lower()
    if status not in ("active", "inactive"):
        raise ValueError("Status must be active or inactive")
    with connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET status=%s WHERE account_id=%s AND branch_id=%s",
                    (status, item_id, g.user["branch_id"]))
        changed = cur.rowcount
        conn.commit()
        cur.close()
    if not changed:
        exists = query("SELECT account_id FROM accounts WHERE account_id=%s AND branch_id=%s",
                       (item_id, g.user["branch_id"]), one=True)
        if not exists:
            return fail("Account not found", 404)
    return jsonify({"message": "Account status updated"})


@app.post("/api/transactions/<kind>")
@require_roles(MANAGER, CUSTOMER)
def transaction(kind):
    if kind not in ("deposit", "withdraw", "transfer"):
        return fail("Unsupported operation", 404)
    role = g.user["role"]
    if role == MANAGER and kind not in ("deposit", "withdraw"):
        return fail("Branch managers can deposit or withdraw only", 403)
    if role == CUSTOMER and kind != "transfer":
        return fail("Deposits and withdrawals are handled by your branch manager", 403)
    result = move_money(kind, body(), actor=g.user)
    return jsonify(result), 201


@app.get("/api/transactions")
@require_roles(MANAGER, CUSTOMER)
def transactions():
    filters, args = [], []
    if request.args.get("account_id"):
        filters.append("t.account_id=%s")
        args.append(request.args["account_id"])
    if request.args.get("type"):
        filters.append("LOWER(t.transaction_type)=LOWER(%s)")
        args.append(request.args["type"])
    if request.args.get("from"):
        filters.append("t.created_at >= %s")
        args.append(request.args["from"])
    if request.args.get("to"):
        filters.append("t.created_at < DATE_ADD(%s, INTERVAL 1 DAY)")
        args.append(request.args["to"])
    term = request.args.get("search", "").strip()
    if term:
        filters.append("(a.account_number LIKE %s OR c.full_name LIKE %s)")
        args.extend([f"%{term}%", f"%{term}%"])
    if g.user["role"] == MANAGER:
        filters.append("a.branch_id=%s")
        args.append(g.user["branch_id"])
    else:
        filters.append("a.customer_id=%s")
        args.append(g.user["customer_id"])
    return jsonify(query(
        "SELECT t.transaction_id,t.account_id,a.account_number,c.full_name customer_name,"
        "t.transaction_type,t.amount,t.created_at,tr.reference_code "
        "FROM transactions t JOIN accounts a ON a.account_id=t.account_id "
        "JOIN customers c ON c.customer_id=a.customer_id "
        "LEFT JOIN transfers tr ON tr.transfer_id=t.transfer_id WHERE "
        + " AND ".join(filters)
        + " ORDER BY t.created_at DESC,t.transaction_id DESC LIMIT 500",
        tuple(args),
    ))


@app.get("/api/branches")
@require_roles(MANAGER)
def branches():
    return jsonify(query(
        "SELECT b.*,COUNT(a.account_id) account_count FROM branches b "
        "LEFT JOIN accounts a ON a.branch_id=b.branch_id WHERE b.branch_id=%s "
        "GROUP BY b.branch_id ORDER BY b.branch_id",
        (g.user["branch_id"],),
    ))


@app.get("/api/dashboard/stats")
@require_roles(MANAGER)
def manager_dashboard():
    branch_id = g.user["branch_id"]
    totals = query(
        "SELECT COUNT(DISTINCT a.customer_id) customers,COUNT(a.account_id) accounts,"
        "COALESCE(SUM(a.balance),0) total_balance,"
        "COALESCE(SUM(LOWER(a.status)='active'),0) active_accounts "
        "FROM accounts a WHERE a.branch_id=%s", (branch_id,), one=True,
    )
    activity = query(
        "SELECT COALESCE(SUM(CASE WHEN t.transaction_type='deposit' THEN t.amount ELSE 0 END),0) deposits,"
        "COALESCE(SUM(CASE WHEN t.transaction_type='withdrawal' THEN t.amount ELSE 0 END),0) withdrawals "
        "FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE a.branch_id=%s",
        (branch_id,), one=True,
    )
    distribution = query(
        "SELECT LOWER(a.account_type) account_type,COUNT(*) count FROM accounts a "
        "WHERE a.branch_id=%s GROUP BY LOWER(a.account_type)", (branch_id,),
    )
    recent = query(
        "SELECT t.transaction_id,a.account_number,c.full_name customer_name,t.transaction_type,"
        "t.amount,t.created_at FROM transactions t JOIN accounts a ON a.account_id=t.account_id "
        "JOIN customers c ON c.customer_id=a.customer_id WHERE a.branch_id=%s "
        "ORDER BY t.created_at DESC,t.transaction_id DESC LIMIT 8", (branch_id,),
    )
    return jsonify({**totals, **activity, "distribution": distribution, "recent_transactions": recent,
                    "branch_name": g.user["branch_name"]})


@app.get("/api/customer/dashboard")
@require_roles(CUSTOMER)
def customer_dashboard():
    customer_id = g.user["customer_id"]
    totals = query(
        "SELECT COUNT(*) accounts,COALESCE(SUM(balance),0) total_balance FROM accounts "
        "WHERE customer_id=%s", (customer_id,), one=True,
    )
    distribution = query(
        "SELECT LOWER(account_type) account_type,COUNT(*) count FROM accounts "
        "WHERE customer_id=%s GROUP BY LOWER(account_type)", (customer_id,),
    )
    account_rows = query(
        "SELECT a.account_id,a.account_number,a.account_type,a.balance,a.status,a.created_at,b.branch_name "
        "FROM accounts a JOIN branches b ON b.branch_id=a.branch_id "
        "WHERE a.customer_id=%s ORDER BY a.account_id DESC", (customer_id,),
    )
    recent = query(
        "SELECT t.transaction_id,t.account_id,a.account_number,t.transaction_type,t.amount,"
        "t.created_at,tr.reference_code FROM transactions t JOIN accounts a ON a.account_id=t.account_id "
        "LEFT JOIN transfers tr ON tr.transfer_id=t.transfer_id WHERE a.customer_id=%s "
        "ORDER BY t.created_at DESC,t.transaction_id DESC LIMIT 8", (customer_id,),
    )
    return jsonify({**totals, "customer_name": g.user["customer_name"], "distribution": distribution,
                    "accounts_list": account_rows, "recent_transactions": recent})


@app.get("/api/profile")
@require_roles(CUSTOMER)
def profile():
    # The profile page only displays these fields; older project databases may
    # not have customers.created_at yet.
    row = query("SELECT customer_id,full_name,email,phone,address FROM customers WHERE customer_id=%s",
                (g.user["customer_id"],), one=True)
    if not row:
        return fail("Customer profile not found", 404)
    return jsonify(row)


@app.put("/api/profile")
@require_roles(CUSTOMER)
def update_profile():
    data = body()
    required(data, ["phone", "address"])
    with connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE customers SET phone=%s,address=%s WHERE customer_id=%s",
                    (data["phone"].strip(), data["address"].strip(), g.user["customer_id"]))
        conn.commit()
        cur.close()
    return jsonify({"message": "Profile updated"})


@app.get("/api/reports/branch")
@require_roles(MANAGER)
def branch_report():
    branch_id = g.user["branch_id"]
    return jsonify({
        "branch_name": g.user["branch_name"],
        "accounts": query(
            "SELECT LOWER(account_type) account_type,LOWER(status) status,COUNT(*) account_count,"
            "COALESCE(SUM(balance),0) total_balance FROM accounts WHERE branch_id=%s "
            "GROUP BY LOWER(account_type),LOWER(status) ORDER BY account_type,status", (branch_id,),
        ),
        "monthly_activity": query(
            "SELECT DATE_FORMAT(t.created_at,'%Y-%m') month,"
            "SUM(CASE WHEN t.transaction_type='deposit' THEN t.amount ELSE 0 END) deposits,"
            "SUM(CASE WHEN t.transaction_type='withdrawal' THEN t.amount ELSE 0 END) withdrawals "
            "FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE a.branch_id=%s "
            "GROUP BY DATE_FORMAT(t.created_at,'%Y-%m') ORDER BY month DESC LIMIT 12", (branch_id,),
        ),
    })


def customer_credit_data(customer_id, income_override=None, emis_override=None):
    accounts = query(
        "SELECT COUNT(*) active_accounts,COALESCE(TIMESTAMPDIFF(MONTH,MIN(created_at),CURRENT_DATE),0) relationship_months "
        "FROM accounts WHERE customer_id=%s AND LOWER(status)='active'", (customer_id,), one=True,
    ) or {}
    history = query(
        "SELECT COUNT(*) repayment_total,COALESCE(SUM(i.status='PAID'),0) repayment_paid,"
        "COALESCE(SUM(i.status='DUE' AND i.due_date<CURRENT_DATE),0) overdue_count "
        "FROM loan_installments i JOIN loans l ON l.loan_id=i.loan_id WHERE l.customer_id=%s "
        "AND (i.status='PAID' OR i.due_date<CURRENT_DATE)",
        (customer_id,), one=True,
    ) or {}
    latest_financials = query(
        "SELECT monthly_income,existing_emis FROM loan_applications WHERE customer_id=%s "
        "ORDER BY created_at DESC,application_id DESC LIMIT 1", (customer_id,), one=True,
    )
    debt = query(
        "SELECT COALESCE(SUM(CASE WHEN status='ACTIVE' THEN outstanding_balance ELSE 0 END),0) existing_debt,"
        "COALESCE(SUM(CASE WHEN status='ACTIVE' THEN monthly_emi ELSE 0 END),0) monthly_loan_emis "
        "FROM loans WHERE customer_id=%s", (customer_id,), one=True,
    ) or {}
    score = simulated_credit_score(
        repayment_total=history.get("repayment_total", 0), repayment_paid=history.get("repayment_paid", 0),
        overdue_count=history.get("overdue_count", 0),
        monthly_income=income_override if income_override is not None else (latest_financials.get("monthly_income") if latest_financials else None),
        existing_emis=emis_override if emis_override is not None else (latest_financials.get("existing_emis", 0) if latest_financials else 0),
        active_accounts=accounts.get("active_accounts", 0),
        relationship_months=accounts.get("relationship_months", 0),
    )
    score.update({"existing_debt": debt.get("existing_debt", 0),
                  "monthly_loan_emis": debt.get("monthly_loan_emis", 0),
                  "repayment_history": query(
                      "SELECT i.installment_no,i.due_date,i.amount_due,i.amount_paid,i.status,i.paid_at,l.loan_id "
                      "FROM loan_installments i JOIN loans l ON l.loan_id=i.loan_id "
                      "WHERE l.customer_id=%s AND (i.status='PAID' OR i.due_date<CURRENT_DATE) "
                      "ORDER BY i.due_date DESC LIMIT 12", (customer_id,),
                  ), "data_basis": "Meridian account, application, and repayment records"})
    return score


@app.get("/api/customer/credit-health")
@require_roles(CUSTOMER)
def customer_credit_health():
    return jsonify(customer_credit_data(g.user["customer_id"]))


@app.post("/api/customer/loan-applications")
@require_roles(CUSTOMER)
def customer_apply_loan():
    data = body()
    required(data, ["loan_type", "requested_amount", "tenure_months", "monthly_income"])
    loan_type = str(data["loan_type"]).upper()
    if loan_type not in LOAN_RATES:
        raise ValueError("Select a supported loan type")
    amount = amount_value(data["requested_amount"])
    income = amount_value(data["monthly_income"])
    existing_emis = decimal_value(data.get("existing_emis", "0"), "existing EMIs").quantize(Decimal("0.01"))
    if existing_emis < 0:
        raise ValueError("Existing EMIs cannot be negative")
    try:
        tenure = int(data["tenure_months"])
    except (TypeError, ValueError):
        raise ValueError("Enter a valid tenure")
    if tenure < 3 or tenure > 360:
        raise ValueError("Tenure must be between 3 and 360 months")
    if amount > income * 100:
        raise ValueError("Requested amount is above the demo application limit for the stated income")
    branch = query("SELECT branch_id FROM accounts WHERE customer_id=%s ORDER BY account_id LIMIT 1",
                   (g.user["customer_id"],), one=True)
    if not branch:
        return fail("An account linked to a branch is required before applying", 400)
    credit = customer_credit_data(g.user["customer_id"], income_override=income, emis_override=existing_emis)
    with connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO loan_applications(customer_id,branch_id,loan_type,requested_amount,tenure_months,"
                "monthly_income,existing_emis,simulated_score) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                (g.user["customer_id"], branch["branch_id"], loan_type, amount, tenure, income, existing_emis, credit["score"]),
            )
            application_id = cur.lastrowid
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    return jsonify({"application_id": application_id,
                    "application_reference": f"NSL-{application_id:08d}", "status": "PENDING",
                    "estimated_emi": str(emi_for(amount, LOAN_RATES[loan_type], tenure))}), 201


@app.get("/api/customer/loan-applications")
@require_roles(CUSTOMER)
def customer_loan_applications():
    rows = query(
        "SELECT application_id,CONCAT('NSL-',LPAD(application_id,8,'0')) application_reference,loan_type,"
        "requested_amount,tenure_months,monthly_income,existing_emis,simulated_score,status,decision_reason,"
        "created_at,updated_at FROM loan_applications WHERE customer_id=%s ORDER BY created_at DESC,application_id DESC",
        (g.user["customer_id"],),
    )
    return jsonify(rows)


@app.get("/api/customer/loans")
@require_roles(CUSTOMER)
def customer_loans():
    loans = query(
        "SELECT l.*,CONCAT('NSL-',LPAD(l.application_id,8,'0')) application_reference,a.loan_type "
        "FROM loans l JOIN loan_applications a ON a.application_id=l.application_id "
        "WHERE l.customer_id=%s ORDER BY l.disbursed_at DESC", (g.user["customer_id"],),
    )
    for loan in loans:
        loan["installments"] = query(
            "SELECT installment_id,installment_no,due_date,amount_due,principal_due,amount_paid,status,paid_at "
            "FROM loan_installments WHERE loan_id=%s ORDER BY installment_no", (loan["loan_id"],),
        )
    return jsonify(loans)


@app.get("/api/manager/loan-applications")
@require_roles(MANAGER)
def manager_loan_applications():
    status = request.args.get("status", "").upper()
    allowed = ("PENDING", "MORE_INFO", "APPROVED", "REJECTED", "DISBURSED")
    if status and status not in allowed:
        raise ValueError("Unsupported application status filter")
    where = "WHERE la.branch_id=%s"
    params = [g.user["branch_id"]]
    if status:
        where += " AND la.status=%s"
        params.append(status)
    rows = query(
        "SELECT la.application_id,CONCAT('NSL-',LPAD(la.application_id,8,'0')) application_reference,"
        "la.customer_id,la.loan_type,la.requested_amount,la.tenure_months,la.monthly_income,la.existing_emis,"
        "la.simulated_score,la.status,la.decision_reason,la.created_at,c.full_name customer_name,c.email customer_email "
        "FROM loan_applications la JOIN customers c ON c.customer_id=la.customer_id " + where +
        " ORDER BY FIELD(la.status,'PENDING','MORE_INFO','APPROVED','DISBURSED','REJECTED'),la.created_at",
        tuple(params),
    )
    for row in rows:
        row["estimated_emi"] = str(emi_for(row["requested_amount"], LOAN_RATES[row["loan_type"]], row["tenure_months"]))
        income = Decimal(str(row["monthly_income"]))
        row["proposed_emi_ratio"] = str((Decimal(row["estimated_emi"]) + Decimal(str(row["existing_emis"]))) / income)
    return jsonify(rows)


@app.post("/api/manager/loan-applications/<int:application_id>/decision")
@require_roles(MANAGER)
def manager_loan_decision(application_id):
    data = body()
    status = str(data.get("status", "")).upper()
    reason = str(data.get("reason", "")).strip()
    if status not in ("MORE_INFO", "APPROVED", "REJECTED"):
        raise ValueError("Decision must request information, approve, or reject")
    if len(reason) < 4:
        raise ValueError("Enter a brief reason for this decision")
    with connection() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT application_id,status FROM loan_applications WHERE application_id=%s AND branch_id=%s FOR UPDATE",
                        (application_id, g.user["branch_id"]))
            application = cur.fetchone()
            if not application:
                raise ValueError("Loan application not found in your branch")
            if application["status"] not in ("PENDING", "MORE_INFO"):
                raise ValueError("This application already has a final decision")
            cur.execute("UPDATE loan_applications SET status=%s,decision_reason=%s,decided_by=%s WHERE application_id=%s",
                        (status, reason, g.user["user_id"], application_id))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    return jsonify({"message": "Loan application updated", "status": status})


@app.post("/api/manager/loan-applications/<int:application_id>/disburse")
@require_roles(MANAGER)
def manager_disburse_loan(application_id):
    with connection() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM loan_applications WHERE application_id=%s AND branch_id=%s FOR UPDATE",
                        (application_id, g.user["branch_id"]))
            application = cur.fetchone()
            if not application:
                raise ValueError("Loan application not found in your branch")
            if application["status"] != "APPROVED":
                raise ValueError("Only an approved application can be disbursed")
            rate = LOAN_RATES[application["loan_type"]]
            emi, schedule = repayment_schedule(application["requested_amount"], rate, application["tenure_months"])
            cur.execute(
                "INSERT INTO loans(application_id,customer_id,branch_id,principal,annual_rate,tenure_months,monthly_emi,outstanding_balance) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                (application_id, application["customer_id"], application["branch_id"], application["requested_amount"],
                 rate, application["tenure_months"], emi, application["requested_amount"]),
            )
            loan_id = cur.lastrowid
            for installment in schedule:
                cur.execute("INSERT INTO loan_installments(loan_id,installment_no,due_date,amount_due,principal_due) "
                            "VALUES(%s,%s,%s,%s,%s)",
                            (loan_id, installment["installment_no"], installment["due_date"],
                             installment["amount_due"], installment["principal_due"]))
            cur.execute("UPDATE loan_applications SET status='DISBURSED' WHERE application_id=%s", (application_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    return jsonify({"loan_id": loan_id, "monthly_emi": str(emi), "installments": len(schedule)}), 201


@app.get("/api/manager/loans")
@require_roles(MANAGER)
def manager_loans():
    loans = query(
        "SELECT l.loan_id,l.application_id,l.customer_id,l.principal,l.annual_rate,l.tenure_months,l.monthly_emi,"
        "l.outstanding_balance,l.status,l.disbursed_at,c.full_name customer_name,"
        "(SELECT COUNT(*) FROM loan_installments i WHERE i.loan_id=l.loan_id AND i.status='DUE') unpaid_installments "
        "FROM loans l JOIN customers c ON c.customer_id=l.customer_id WHERE l.branch_id=%s "
        "ORDER BY l.disbursed_at DESC", (g.user["branch_id"],),
    )
    for loan in loans:
        loan["installments"] = query(
            "SELECT installment_no,due_date,amount_due,status FROM loan_installments "
            "WHERE loan_id=%s ORDER BY installment_no", (loan["loan_id"],),
        )
    return jsonify(loans)


@app.post("/api/manager/loans/<int:loan_id>/repayments")
@require_roles(MANAGER)
def manager_record_repayment(loan_id):
    data = body()
    try:
        installment_no = int(data.get("installment_no"))
    except (TypeError, ValueError):
        raise ValueError("Choose an instalment")
    with connection() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT loan_id,outstanding_balance,status FROM loans WHERE loan_id=%s AND branch_id=%s FOR UPDATE",
                        (loan_id, g.user["branch_id"]))
            loan = cur.fetchone()
            if not loan:
                raise ValueError("Loan not found in your branch")
            if loan["status"] != "ACTIVE":
                raise ValueError("This loan is already paid")
            cur.execute("SELECT installment_id,amount_due,principal_due,status FROM loan_installments "
                        "WHERE loan_id=%s AND installment_no=%s FOR UPDATE", (loan_id, installment_no))
            installment = cur.fetchone()
            if not installment:
                raise ValueError("Instalment not found")
            if installment["status"] == "PAID":
                raise ValueError("This instalment is already recorded as paid")
            cur.execute("UPDATE loan_installments SET amount_paid=amount_due,status='PAID',paid_at=CURRENT_TIMESTAMP "
                        "WHERE installment_id=%s", (installment["installment_id"],))
            balance = max(Decimal("0.00"), Decimal(str(loan["outstanding_balance"])) - Decimal(str(installment["principal_due"])))
            loan_status = "PAID" if balance == 0 else "ACTIVE"
            cur.execute("UPDATE loans SET outstanding_balance=%s,status=%s WHERE loan_id=%s", (balance, loan_status, loan_id))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    return jsonify({"message": "Repayment recorded", "outstanding_balance": str(balance), "loan_status": loan_status})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")),
            debug=os.getenv("FLASK_DEBUG", "true").lower() == "true")
