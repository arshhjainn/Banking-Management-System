"""Recursive sum with an explicit base case."""
def sum_to(n: int) -> int:
    if n <= 0:  # base case
        return 0
    return n + sum_to(n - 1)
if __name__ == "__main__": print("1..5 =", sum_to(5))
