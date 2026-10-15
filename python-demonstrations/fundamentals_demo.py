"""Types, operators, control flow, conversion, wrappers and arrays (lists)."""
amount_cents: int = 1250
rupees: float = amount_cents / 100
count = int("3")  # conversion
balances: list[float] = [1200.0, 850.0, 430.0]
if rupees > 10:
    print(f"Balance ₹{rupees:.2f}; count={count}")
for balance in balances:
    print(balance)
