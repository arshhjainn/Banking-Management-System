USE banking_management;
DELIMITER $$
CREATE TRIGGER validate_transaction_amount BEFORE INSERT ON transactions FOR EACH ROW
BEGIN
  IF NEW.amount <= 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Transaction amount must be positive'; END IF;
END$$
DELIMITER ;
