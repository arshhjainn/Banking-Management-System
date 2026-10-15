"""Classes, objects, references, constructors, methods, parameters and static data."""
class BankAccount:
    next_id = 1
    def __init__(self, owner: str, balance: float = 0):  # default constructor value
        self.id, self.owner, self._balance = BankAccount.next_id, owner, balance
        BankAccount.next_id += 1
    def deposit(self, amount: float) -> None:
        self._balance += amount
    def transfer_to(self, other: "BankAccount", amount: float) -> None:
        if self._balance >= amount:
            self._balance -= amount
            other._balance += amount
    def copy(self) -> "BankAccount":  # returning an object
        return BankAccount(self.owner, self._balance)
    def __str__(self) -> str:
        return f"{self.id} {self.owner}: ₹{self._balance:.2f}"

if __name__ == "__main__":
    first, second = BankAccount("Asha", 500), BankAccount("Ravi")
    reference = first  # object reference assignment
    reference.deposit(200)
    first.transfer_to(second, 100)
    print(first, second.copy())
