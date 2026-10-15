CREATE DATABASE IF NOT EXISTS banking_management CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE banking_management;

CREATE TABLE IF NOT EXISTS customers (
  customer_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(190) NOT NULL UNIQUE,
  phone VARCHAR(30) NOT NULL,
  address VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS branches (
  branch_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  branch_name VARCHAR(120) NOT NULL,
  city VARCHAR(100) NOT NULL,
  address VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('BRANCH_MANAGER','CUSTOMER') NOT NULL,
  customer_id BIGINT NULL UNIQUE,
  branch_id BIGINT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT,
  CONSTRAINT fk_users_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE RESTRICT,
  CONSTRAINT chk_user_role_link CHECK (
    (role='CUSTOMER' AND customer_id IS NOT NULL AND branch_id IS NULL) OR
    (role='BRANCH_MANAGER' AND customer_id IS NULL AND branch_id IS NOT NULL)
  )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS accounts (
  account_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  account_number VARCHAR(20) NOT NULL UNIQUE,
  customer_id BIGINT NOT NULL,
  branch_id BIGINT NOT NULL,
  account_type ENUM('savings','current') NOT NULL,
  balance DECIMAL(14,2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
  status ENUM('active','inactive') NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_accounts_customer (customer_id), INDEX idx_accounts_branch (branch_id),
  CONSTRAINT fk_accounts_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT,
  CONSTRAINT fk_accounts_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transfers (
  transfer_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  reference_code CHAR(36) NOT NULL UNIQUE,
  from_account_id BIGINT NOT NULL,
  to_account_id BIGINT NOT NULL,
  amount DECIMAL(14,2) NOT NULL CHECK (amount > 0),
  transfer_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_transfer_accounts CHECK (from_account_id <> to_account_id),
  CONSTRAINT fk_transfer_source FOREIGN KEY (from_account_id) REFERENCES accounts(account_id) ON DELETE RESTRICT,
  CONSTRAINT fk_transfer_destination FOREIGN KEY (to_account_id) REFERENCES accounts(account_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transactions (
  transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  account_id BIGINT NOT NULL,
  transaction_type ENUM('deposit','withdrawal','transfer_in','transfer_out') NOT NULL,
  amount DECIMAL(14,2) NOT NULL CHECK (amount > 0),
  transfer_id BIGINT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_transactions_account_date (account_id, created_at),
  CONSTRAINT fk_transactions_account FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE RESTRICT,
  CONSTRAINT fk_transactions_transfer FOREIGN KEY (transfer_id) REFERENCES transfers(transfer_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
