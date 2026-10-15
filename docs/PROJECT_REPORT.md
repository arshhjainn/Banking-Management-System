# Banking Management System — project report

## Objective and stack
A classroom banking ledger application showing React/Tailwind pages, Flask JSON APIs, MySQL 8 relational storage, and independent Python programming demonstrations. The browser never holds the system of record: all listings and totals are fetched from Flask/MySQL.

## Design
Six InnoDB tables represent users, customers, branches, accounts, transfers and immutable transaction history. User rows link a branch manager to one branch or a customer login to one customer. Passwords are stored as Werkzeug PBKDF2-SHA256 hashes; Flask signed sessions hold the authenticated user ID. API routes enforce role and branch/customer scope on the server. Foreign keys use RESTRICT to protect financial history. Amounts use DECIMAL; Flask converts input to Python Decimal. Account transfers lock both rows in ascending ID order and commit two balance changes, transfer reference and two transaction rows together. Exceptions roll the transaction back.

## Scope and limitations
This is a fictional college demonstration, not production banking software. It omits interest accrual, regulatory controls, deployment, multi-factor authentication and operational monitoring. Change the local demo credentials and configure a strong session secret before sharing it; do not use real banking or customer data.

## Import and run
Follow the root README. Use fictional `example.test` records only. Start services in separate terminals; Python demonstrations run independently.
