"""Abstract base, inheritance, overriding and runtime polymorphism."""
from abc import ABC, abstractmethod
class Account(ABC):
    def __init__(self, balance: float): self.balance = balance
    @abstractmethod
    def kind(self) -> str: ...
    def show(self) -> None: print(f"{self.kind()} ₹{self.balance:.2f}")
class SavingsAccount(Account):
    def kind(self) -> str: return "Savings"
class CurrentAccount(SavingsAccount):  # small multilevel hierarchy
    def kind(self) -> str: return "Current"
if __name__ == "__main__":
    account: Account = CurrentAccount(900)  # runtime method dispatch
    account.show()
