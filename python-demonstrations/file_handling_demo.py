"""Read a sample file and write a simple account statement."""
from pathlib import Path
if __name__ == "__main__":
    sample, statement = Path("sample.txt"), Path("account-statement.txt")
    if not sample.exists(): sample.write_text("Opening balance: 1000\nDeposit: 250\n")
    statement.write_text("ACCOUNT STATEMENT\n" + sample.read_text() + "Closing balance: 1250\n")
    print(statement.read_text())
