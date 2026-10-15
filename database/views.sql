USE banking_management;
CREATE OR REPLACE VIEW customer_account_summary AS
SELECT c.customer_id,c.full_name,c.email,COUNT(a.account_id) AS account_count,COALESCE(SUM(a.balance),0.00) AS total_balance
FROM customers c LEFT JOIN accounts a ON a.customer_id=c.customer_id GROUP BY c.customer_id,c.full_name,c.email;
CREATE OR REPLACE VIEW branch_statistics AS
SELECT b.branch_id,b.branch_name,b.city,COUNT(a.account_id) AS account_count,COALESCE(SUM(a.balance),0.00) AS total_balance
FROM branches b LEFT JOIN accounts a ON a.branch_id=b.branch_id GROUP BY b.branch_id,b.branch_name,b.city;
