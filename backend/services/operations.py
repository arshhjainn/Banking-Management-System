from decimal import Decimal, InvalidOperation
from uuid import uuid4

from db import connection


def amount_value(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        raise ValueError("Enter a valid amount")
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Amount must be greater than zero")
    return amount


def move_money(kind, data, actor):
    amount = amount_value(data.get("amount"))
    role = actor.get("role")
    if role not in ("BRANCH_MANAGER", "CUSTOMER"):
        raise ValueError("Authenticated role is required")
    if role == "CUSTOMER" and kind != "transfer":
        raise PermissionError("Deposits and withdrawals are handled by your branch manager")
    with connection() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            if kind == "transfer":
                if role != "CUSTOMER":
                    raise PermissionError("Only customers may initiate transfers")
                try:
                    source = int(data["source_account_id"])
                except (KeyError, TypeError, ValueError):
                    raise ValueError("Choose a source account")
                destination_number = str(data.get("destination_account_number", "")).strip()
                if not destination_number:
                    raise ValueError("Enter the recipient account number")
                cur.execute("SELECT account_id FROM accounts WHERE account_number=%s", (destination_number,))
                destination = cur.fetchone()
                if not destination:
                    raise ValueError("Recipient account was not found")
                target = int(destination["account_id"])
                if source == target:
                    raise ValueError("Source and destination must be different")
                # Lock rows in ID order to reduce deadlock risk.
                ids = sorted([source, target])
                cur.execute("SELECT account_id,balance,status,customer_id,branch_id FROM accounts "
                            "WHERE account_id IN (%s,%s) ORDER BY account_id FOR UPDATE", ids)
                locked = {row["account_id"]: row for row in cur.fetchall()}
                if len(locked) != 2:
                    raise ValueError("Account not found")
                src, dst = locked[source], locked[target]
                if src["customer_id"] != actor.get("customer_id"):
                    raise PermissionError("You may transfer only from your own account")
                if str(src["status"]).lower() != "active" or str(dst["status"]).lower() != "active":
                    raise ValueError("Both accounts must be active")
                if Decimal(src["balance"]) < amount:
                    raise ValueError("Insufficient balance")
                ref = str(uuid4())
                cur.execute("INSERT INTO transfers (reference_code,from_account_id,to_account_id,amount) VALUES (%s,%s,%s,%s)", (ref,source,target,amount))
                transfer_id = cur.lastrowid
                cur.execute("UPDATE accounts SET balance=balance-%s WHERE account_id=%s", (amount,source))
                cur.execute("UPDATE accounts SET balance=balance+%s WHERE account_id=%s", (amount,target))
                cur.execute("INSERT INTO transactions (account_id,transaction_type,amount,transfer_id) VALUES (%s,'transfer_out',%s,%s),(%s,'transfer_in',%s,%s)", (source,amount,transfer_id,target,amount,transfer_id))
                conn.commit()
                return {"reference_code": ref}
            try:
                account_id = int(data["account_id"])
            except (KeyError, TypeError, ValueError):
                raise ValueError("Choose an account")
            cur.execute("SELECT balance,status,customer_id,branch_id FROM accounts "
                        "WHERE account_id=%s FOR UPDATE", (account_id,))
            account = cur.fetchone()
            if not account:
                raise ValueError("Account not found")
            if account["branch_id"] != actor.get("branch_id"):
                raise PermissionError("This account is outside your assigned branch")
            if str(account["status"]).lower() != "active":
                raise ValueError("Account is inactive")
            if kind == "withdraw" and Decimal(account["balance"]) < amount:
                raise ValueError("Insufficient balance")
            sign = "+" if kind == "deposit" else "-"
            tx_type = "deposit" if kind == "deposit" else "withdrawal"
            cur.execute(f"UPDATE accounts SET balance=balance{sign}%s WHERE account_id=%s", (amount,account_id))
            cur.execute("INSERT INTO transactions (account_id,transaction_type,amount) VALUES (%s,%s,%s)", (account_id,tx_type,amount))
            conn.commit()
            return {"message": f"{tx_type.title()} completed"}
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
