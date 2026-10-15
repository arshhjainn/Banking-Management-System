# Verification checklist

Use a disposable MySQL database for end-to-end transactions. Do not use real customer data.

## Automated checks

Run from `backend/`:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Build the frontend from `frontend/` with `npm run build`.

The backend unit/security tests mock database connections. They verify unauthenticated and failed-login responses, role gates, branch/customer query scoping, branch/customer dashboard scoping, manager customer/account creation scope, and transfer ownership/status/balance rollback. They do not prove that the local MySQL schema or demo credentials have been integrated successfully.

## Manual MySQL checks

After loading the schema, sample data, and `database/migrations/001_role_based_auth.sql`, sign in with the demo credentials in `README.md`.

| Role / case | Expected result |
|---|---|
| Unauthenticated request to a protected API | 401 response |
| Incorrect login password | Generic 401; no session created |
| Branch manager dashboard | Counts and activity limited to assigned branch |
| Branch manager customers/accounts/transactions | Only assigned branch records are returned |
| Branch manager creates customer | Customer, initial account, and hashed customer login are created together |
| Branch manager posts deposit or withdrawal | Only an active account in assigned branch is changed |
| Branch manager requests another branch account | 404 or 403; no details returned |
| Customer account/dashboard/history | Only records belonging to authenticated customer are returned |
| Customer updates profile | Only phone and address can be changed |
| Customer transfers to own or another customer's active account | Source belongs to customer; both balances and two transaction rows commit with a receipt reference |
| Customer uses another customer's account as transfer source | Rejected; neither balance changes |
| Customer posts deposit or withdrawal | 403; no money movement service call |
| Customer opens credit health | Score is labeled simulated; factor breakdown and missing data are visible; data is customer-scoped |
| Customer submits loan application | Valid application stored with customer, assigned branch, income, EMIs, simulated score and pending status |
| Manager reviews a loan | Only applications for the manager's branch are visible; decision requires a reason |
| Manager disburses an approved application | Loan and complete monthly instalment schedule commit together |
| Manager records repayment | A due instalment is marked paid and loan outstanding principal updates together |
| Customer tracks repayments | Only that customer's disbursed loans and instalments are returned |
| Wrong role accesses credit/loan endpoints | `403`; no customer or branch data leaks |
| Customer withdrawal exceeds available balance or account is inactive | Rejected and rolled back |
| Transfer has invalid amount, inactive account, or insufficient balance | Rejected and transaction rolled back |
| Transaction history update/delete request | No user-facing mutation endpoint exists |
