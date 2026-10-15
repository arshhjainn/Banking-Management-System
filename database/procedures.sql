USE banking_management;
DELIMITER $$
-- Educational reporting procedure; application money operations remain in Flask.
CREATE PROCEDURE get_customer_account_count(IN p_customer_id INT)
BEGIN
  SELECT c.customer_id,c.full_name,COUNT(a.account_id) AS account_count
  FROM customers c LEFT JOIN accounts a ON a.customer_id=c.customer_id
  WHERE c.customer_id=p_customer_id GROUP BY c.customer_id,c.full_name;
END$$
DELIMITER ;
