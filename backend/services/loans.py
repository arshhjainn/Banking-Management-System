from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")
LOAN_RATES = {
    "PERSONAL": Decimal("12.50"),
    "HOME": Decimal("8.50"),
    "EDUCATION": Decimal("7.50"),
    "VEHICLE": Decimal("10.50"),
}


def decimal_value(value, label):
    try:
        result = Decimal(str(value))
    except Exception:
        raise ValueError(f"Enter a valid {label}")
    if not result.is_finite():
        raise ValueError(f"Enter a valid {label}")
    return result


def emi_for(principal, annual_rate, months):
    principal = decimal_value(principal, "loan amount")
    annual_rate = decimal_value(annual_rate, "interest rate")
    months = int(months)
    if principal <= 0 or months <= 0:
        raise ValueError("Loan amount and tenure must be greater than zero")
    monthly_rate = annual_rate / Decimal("1200")
    if monthly_rate == 0:
        return (principal / months).quantize(CENT, rounding=ROUND_HALF_UP)
    factor = (Decimal("1") + monthly_rate) ** months
    return (principal * monthly_rate * factor / (factor - Decimal("1"))).quantize(CENT, rounding=ROUND_HALF_UP)


def simulated_credit_score(*, repayment_total=0, repayment_paid=0, overdue_count=0,
                           monthly_income=None, existing_emis=0, active_accounts=0,
                           relationship_months=0):
    """A transparent classroom score, never a bureau score or lending decision."""
    repayment_total = int(repayment_total or 0)
    repayment_paid = int(repayment_paid or 0)
    overdue_count = int(overdue_count or 0)
    existing_emis = decimal_value(existing_emis or 0, "existing EMIs")
    active_accounts = int(active_accounts or 0)
    relationship_months = int(relationship_months or 0)

    if repayment_total:
        paid_ratio = Decimal(max(0, repayment_paid)) / Decimal(repayment_total)
        repayment_points = int((Decimal("210") * max(Decimal("0"), min(Decimal("1"), paid_ratio))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        repayment_note = f"{repayment_paid} of {repayment_total} recorded instalments paid; {overdue_count} overdue."
    else:
        repayment_points = 147
        repayment_note = "No repayment history is recorded; a neutral estimate is used for this factor."

    if monthly_income is None or decimal_value(monthly_income, "monthly income") <= 0:
        affordability_points = 90
        affordability_note = "Income and EMI details are missing; a neutral estimate is used."
    else:
        income = decimal_value(monthly_income, "monthly income")
        ratio = existing_emis / income
        if ratio <= Decimal("0.30"):
            affordability_points = 180
        elif ratio <= Decimal("0.50"):
            affordability_points = 135
        elif ratio <= Decimal("0.70"):
            affordability_points = 75
        else:
            affordability_points = 30
        affordability_note = f"Existing EMIs use {(ratio * 100).quantize(Decimal('0.1'))}% of stated monthly income."

    account_points = min(120, 40 + active_accounts * 20)
    account_note = f"{active_accounts} active account(s) are linked to this profile."
    relationship_points = min(90, max(0, relationship_months) * 2)
    relationship_note = (f"Bank relationship: {relationship_months} month(s)." if relationship_months
                         else "Bank relationship is under one month." if active_accounts
                         else "No active account relationship is available.")

    factors = [
        {"name": "Repayment record", "points": repayment_points, "out_of": 210, "detail": repayment_note},
        {"name": "EMI affordability", "points": affordability_points, "out_of": 180, "detail": affordability_note},
        {"name": "Account management", "points": account_points, "out_of": 120, "detail": account_note},
        {"name": "Bank relationship", "points": relationship_points, "out_of": 90, "detail": relationship_note},
    ]
    score = 300 + sum(factor["points"] for factor in factors)
    rating = "Strong" if score >= 780 else "Building" if score >= 650 else "Needs attention"
    suggestions = []
    if repayment_total and overdue_count:
        suggestions.append("Pay instalments by their due dates and clear overdue amounts.")
    elif not repayment_total:
        suggestions.append("Repayment history is not available yet, so this score has limited evidence.")
    if monthly_income is None:
        suggestions.append("Add current income and existing EMI details with a loan application to improve affordability insight.")
    elif monthly_income and existing_emis / decimal_value(monthly_income, "monthly income") > Decimal("0.30"):
        suggestions.append("Keep new borrowing and existing monthly EMIs manageable relative to income.")
    if active_accounts == 0:
        suggestions.append("Maintain an active account relationship and keep contact details current.")
    missing = []
    if not repayment_total:
        missing.append("No loan repayment history is recorded.")
    if monthly_income is None:
        missing.append("Monthly income and existing EMI details are not on file.")
    return {"score": score, "maximum": 900, "rating": rating, "factors": factors,
            "suggestions": suggestions, "missing_data": missing}


def add_months(start_date, months):
    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(start_date.day, monthrange(year, month)[1]))


def repayment_schedule(principal, annual_rate, months, start_date=None):
    principal = decimal_value(principal, "loan amount").quantize(CENT)
    annual_rate = decimal_value(annual_rate, "interest rate")
    emi = emi_for(principal, annual_rate, months)
    monthly_rate = annual_rate / Decimal("1200")
    balance = principal
    start_date = start_date or date.today()
    schedule = []
    for number in range(1, int(months) + 1):
        interest = (balance * monthly_rate).quantize(CENT, rounding=ROUND_HALF_UP)
        principal_due = min(balance, max(Decimal("0.00"), emi - interest)).quantize(CENT)
        amount_due = (principal_due + interest).quantize(CENT)
        if number == int(months):
            principal_due = balance
            amount_due = (principal_due + interest).quantize(CENT)
        schedule.append({"installment_no": number, "due_date": add_months(start_date, number).isoformat(),
                         "amount_due": amount_due, "principal_due": principal_due})
        balance = (balance - principal_due).quantize(CENT)
    return emi, schedule
