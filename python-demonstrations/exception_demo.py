"""Exception types, raise/propagate and a custom insufficient-balance error."""
class InsufficientBalanceError(Exception): pass
def withdraw(balance: float, amount: float) -> float:
    if amount > balance: raise InsufficientBalanceError("Insufficient funds")
    return balance - amount
if __name__ == "__main__":
    try: print(withdraw(100, 150))
    except InsufficientBalanceError as error: print(error)
    except ArithmeticError as error: print("Arithmetic error", error)
