USE banking_management;
INSERT IGNORE INTO branches (branch_id, branch_name, city, address) VALUES
(1,'Harbor Branch','Mumbai','12 Marine Drive'),(2,'Central Branch','Pune','45 College Road'),(3,'Garden Branch','Bengaluru','8 MG Road');
INSERT IGNORE INTO customers (customer_id,full_name,email,phone,address) VALUES
(1,'Aarav Mehta','aarav@example.test','9000000001','Mumbai'),(2,'Diya Shah','diya@example.test','9000000002','Pune'),(3,'Kabir Rao','kabir@example.test','9000000003','Bengaluru');
INSERT IGNORE INTO accounts (account_number,customer_id,branch_id,account_type,balance) VALUES
('100000000001',1,1,'savings',12500.00),('100000000002',2,2,'current',8400.00),('100000000003',3,3,'savings',21600.00);
