USE banking_management;

CREATE TABLE IF NOT EXISTS loan_applications (
  application_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  customer_id BIGINT NOT NULL,
  branch_id BIGINT NOT NULL,
  loan_type ENUM('PERSONAL','HOME','EDUCATION','VEHICLE') NOT NULL,
  requested_amount DECIMAL(14,2) NOT NULL,
  tenure_months SMALLINT UNSIGNED NOT NULL,
  monthly_income DECIMAL(14,2) NOT NULL,
  existing_emis DECIMAL(14,2) NOT NULL DEFAULT 0.00,
  simulated_score SMALLINT UNSIGNED NOT NULL,
  status ENUM('PENDING','MORE_INFO','APPROVED','REJECTED','DISBURSED') NOT NULL DEFAULT 'PENDING',
  decision_reason VARCHAR(500) NULL,
  decided_by INT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_loan_app_branch_status (branch_id,status,created_at),
  INDEX idx_loan_app_customer (customer_id,created_at),
  CONSTRAINT fk_loan_app_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT,
  CONSTRAINT fk_loan_app_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE RESTRICT,
  CONSTRAINT fk_loan_app_decider FOREIGN KEY (decided_by) REFERENCES users(user_id) ON DELETE RESTRICT,
  CONSTRAINT chk_loan_application_amount CHECK (requested_amount > 0),
  CONSTRAINT chk_loan_application_income CHECK (monthly_income > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS loans (
  loan_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  application_id BIGINT NOT NULL UNIQUE,
  customer_id BIGINT NOT NULL,
  branch_id BIGINT NOT NULL,
  principal DECIMAL(14,2) NOT NULL,
  annual_rate DECIMAL(5,2) NOT NULL,
  tenure_months SMALLINT UNSIGNED NOT NULL,
  monthly_emi DECIMAL(14,2) NOT NULL,
  outstanding_balance DECIMAL(14,2) NOT NULL,
  status ENUM('ACTIVE','PAID') NOT NULL DEFAULT 'ACTIVE',
  disbursed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_loans_customer (customer_id,status),
  INDEX idx_loans_branch (branch_id,status),
  CONSTRAINT fk_loans_application FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE RESTRICT,
  CONSTRAINT fk_loans_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT,
  CONSTRAINT fk_loans_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS loan_installments (
  installment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  loan_id BIGINT NOT NULL,
  installment_no SMALLINT UNSIGNED NOT NULL,
  due_date DATE NOT NULL,
  amount_due DECIMAL(14,2) NOT NULL,
  principal_due DECIMAL(14,2) NOT NULL,
  amount_paid DECIMAL(14,2) NOT NULL DEFAULT 0.00,
  status ENUM('DUE','PAID') NOT NULL DEFAULT 'DUE',
  paid_at TIMESTAMP NULL,
  UNIQUE KEY uq_installment_number (loan_id,installment_no),
  INDEX idx_installment_due (due_date,status),
  CONSTRAINT fk_installments_loan FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
