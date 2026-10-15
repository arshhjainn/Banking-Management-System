"""Nested class and inner class."""
class Banking:
    class AccountType:  # nested class
        name = "Savings"
    def __init__(self): self.owner = "Asha"
    class Receipt:  # nested class using an instance supplied by caller
        def __init__(self, banking): self.banking = banking
        def text(self): return f"Statement for {self.banking.owner}"
if __name__ == "__main__":
    bank = Banking()
    print(Banking.AccountType.name, Banking.Receipt(bank).text())
