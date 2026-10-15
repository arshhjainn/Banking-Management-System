USE banking_management;
-- Selection and projection; relational algebra: sigma(account_type='savings')(accounts), pi(account_number,balance)(accounts)
SELECT account_number,balance FROM accounts WHERE account_type='savings';
-- INNER JOIN and LEFT JOIN
SELECT c.full_name,a.account_number FROM customers c JOIN accounts a USING(customer_id);
SELECT b.branch_name,COUNT(a.account_id) FROM branches b LEFT JOIN accounts a USING(branch_id) GROUP BY b.branch_id;
-- Aggregates, GROUP BY, HAVING
SELECT account_type,AVG(balance) average_balance FROM accounts GROUP BY account_type HAVING AVG(balance)>0;
-- Subquery and correlated subquery
SELECT full_name FROM customers WHERE customer_id IN (SELECT customer_id FROM accounts WHERE balance>10000);
SELECT c.full_name FROM customers c WHERE EXISTS (SELECT 1 FROM accounts a WHERE a.customer_id=c.customer_id AND a.balance>10000);
-- UNION and set difference using NOT EXISTS
SELECT city FROM branches UNION SELECT address FROM customers;
SELECT c.customer_id FROM customers c WHERE NOT EXISTS(SELECT 1 FROM accounts a WHERE a.customer_id=c.customer_id);
-- Views
SELECT * FROM customer_account_summary;
-- Index use; inspect query plan before and after adding a useful index
EXPLAIN SELECT * FROM transactions WHERE account_id=1 ORDER BY created_at DESC;
-- DDL/DML examples: CREATE TABLE demo(id INT PRIMARY KEY); INSERT INTO demo VALUES(1); UPDATE demo SET id=2 WHERE id=1; DELETE FROM demo WHERE id=2;
-- DCL demonstration for an administrator to run deliberately (replace username): GRANT SELECT ON banking_management.* TO 'student'@'localhost';
-- Transaction, savepoint and rollback demonstration. Run interactively then inspect account balance.
START TRANSACTION;
SELECT balance FROM accounts WHERE account_id=1 FOR UPDATE;
SAVEPOINT before_demo;
UPDATE accounts SET balance=balance+1 WHERE account_id=1;
ROLLBACK TO before_demo;
ROLLBACK;
-- Multivalued dependency/JD illustrative example is documented in docs/NORMALIZATION.md.
