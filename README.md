# Banking Management System

A classroom banking project built with React, Vite and Tailwind CSS, a Flask REST API, and MySQL 8. It provides separate **Branch Manager** and **Customer** workspaces. Banking data is fictional; do not use this demo with real customer information.

## Roles and demo accounts

Run `database/migrations/001_role_based_auth.sql` after loading the schema and sample data. It creates the `users` table and two demo logins. Passwords are stored as PBKDF2-SHA256 hashes.

| Role | Username | Password | Assignment |
|---|---|---|---|
| Branch manager | `manager` | `Manager123!` | The branch with the lowest branch ID |
| Customer | `aarav` | `Customer123!` | The customer with the lowest customer ID |

These credentials are for local demonstration only. Change or remove the demo rows before sharing the database. When a manager creates a customer in the UI, they also create that customer's first account and login username/password.

## Setup on macOS

1. Install Python 3, Node.js (LTS), and MySQL 8. Start MySQL.
2. In Workbench, run these files in order:
   1. `database/schema.sql`
   2. `database/sample_data.sql`
   3. `database/views.sql`
   4. `database/triggers.sql`
   5. `database/procedures.sql`
   6. `database/migrations/001_role_based_auth.sql`
   7. `database/migrations/002_credit_and_loans.sql`

   The migration needs at least one branch and one customer so it can link the demo users. For a new database, the sample data supplies them. It uses `CREATE TABLE IF NOT EXISTS` and `INSERT IGNORE` so it can be rerun safely.
3. Configure Flask:
   ```sh
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
   Edit `backend/.env` with your local MySQL credentials, `DB_NAME=banking_management`, and a long random `FLASK_SECRET_KEY`. Keep `.env` private; it is ignored by Git. `SESSION_COOKIE_SECURE=false` is appropriate for local HTTP development only.
4. Start the API from `backend/` with `python app.py`. Check `http://127.0.0.1:5000/api/health`.
5. In another terminal, run `cd frontend && npm install && npm run dev`. Open the Vite URL, usually `http://localhost:5173`, and sign in with one of the demo accounts above.

## Deploy to Vercel

The repository includes a Vercel Services configuration for the existing React frontend and Flask backend. Vercel routes `/api/*` requests to Flask and serves the frontend for the other routes, including direct visits to nested pages.

1. Import this GitHub repository into Vercel and keep the project root set to the repository root so it detects both services.
2. Add these environment variables in Vercel Project Settings → Environment Variables:
   - `FLASK_SECRET_KEY`: a long random secret
   - `SESSION_COOKIE_SECURE`: `true`
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: connection details for a hosted MySQL 8 database accessible from Vercel
3. Deploy. The React app uses same-origin `/api` routes, so no frontend API URL is needed.

The local MySQL server is not reachable from Vercel. Use a managed/hosted MySQL database and load the schema, sample data, views, triggers, procedures, and migrations there before using the deployed app. Do not put database credentials in Git or in frontend variables. Vercel's Python Functions support Flask; see [Vercel's Flask deployment guide](https://vercel.com/docs/frameworks/backend/flask).

## Dashboards and permissions

- **Branch Manager**: `/manager/dashboard`, `/manager/customers`, `/manager/accounts`, and `/manager/transactions`. The manager can see and manage only accounts/customers tied to their assigned branch, create customers and accounts, activate/deactivate accounts, post deposits/withdrawals, filter transactions, and view branch reports.
- **Customer**: `/customer/dashboard`, `/customer/accounts`, `/customer/transfer`, `/customer/transactions`, and `/customer/profile`. Customers can view only their own accounts, profile and transaction history, update their phone/address, and transfer funds from their own active account to any active recipient account by account number. Deposits and withdrawals are branch-manager operated.
- **Customer credit and loans**: `/customer/credit-health` shows the educational simulated score, its factors, missing evidence, debt, and repayment history. `/customer/apply-loan` submits a request, `/customer/emi-calculator` estimates repayment, `/customer/loan-applications` tracks decisions, and `/customer/repayments` shows disbursed balances and instalments.
- **Branch loan management**: `/manager/loans` shows applications assigned to the manager's branch, records a reason with each request for more information/approval/rejection, disburses approved applications, and records scheduled repayments.
- The Meridian score is computed from account age, active account count, the latest stated income/EMIs, and recorded loan repayments. It is an educational simulation, not an official CIBIL score or credit bureau result. Missing inputs are shown. A manager makes the human decision; the score never approves or rejects automatically. Demo annual rates are illustrative: Personal 12.5%, Home 8.5%, Education 7.5%, Vehicle 10.5%.
- Unauthenticated requests receive `401`; a role mismatch receives `403`. The Flask API reads the role and customer/branch assignment from the session-backed `users` row. It does not accept a role or branch scope from the browser.
- Transfers lock both account rows, verify the source belongs to the signed-in customer, validate both account statuses and the available balance, and write both balance changes, transfer reference and transaction rows in one database transaction. The recipient may be another customer. Failures roll back all changes. Transaction history is read-only through ordinary API routes.

## Database notes

`database/schema.sql` creates the core customers, branches, accounts, transfers, transactions and users tables. The role migration creates the same users table for existing installations and seeds the local demo logins. If a database was created from an older version of the classroom project, compare its tables with `database/schema.sql` and apply any missing columns before running the app; `CREATE TABLE IF NOT EXISTS` does not update an existing table's definition.

The additive `002_credit_and_loans.sql` migration creates loan applications, disbursed loans, and instalment schedule tables without changing existing banking records. Run it after `001_role_based_auth.sql`. A manager's branch is derived from the customer's first linked account when an application is submitted. Loan disbursement creates the loan and monthly schedule in one transaction; each repayment updates the instalment and outstanding principal together in one transaction.

## Verification

Run the API unit/security and transfer rollback tests from `backend/`:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Build the frontend from `frontend/` with `npm run build`. The API tests use mocked database rows and verify role gates, branch/customer query scoping, failed login responses, loan calculations and money transaction rollback. They do not replace a full integration run against a disposable MySQL 8 database. Apply `002_credit_and_loans.sql` before opening credit or loan pages.

For SQL demonstrations, run selected queries in `database/demos/queries.sql` and `CALL get_customer_account_count(1);` after loading the procedure.

## Project map

- `backend/` Flask routes, session authentication, role checks and transaction service.
- `database/` schema, fictional data, views, trigger, procedure, migration and SQL lessons.
- `frontend/` responsive manager/customer workspaces and Axios API client.
- `python-demonstrations/` standalone programming concept examples.
- `docs/` ER, normalization, syllabus mapping, project report, tests and viva notes.
