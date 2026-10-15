USE banking_management;

CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('BRANCH_MANAGER','CUSTOMER') NOT NULL,
  -- Match the existing customers.customer_id type (BIGINT).
  customer_id BIGINT NULL UNIQUE,
  -- Match the existing branches.branch_id type (BIGINT).
  branch_id BIGINT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT,
  CONSTRAINT fk_users_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE RESTRICT,
  CONSTRAINT chk_user_role_link CHECK (
    (role='CUSTOMER' AND customer_id IS NOT NULL AND branch_id IS NULL) OR
    (role='BRANCH_MANAGER' AND customer_id IS NULL AND branch_id IS NOT NULL)
  )
) ENGINE=InnoDB;

-- Demo-only accounts. Login with manager / Manager123! and aarav / Customer123!.
-- The hashes below are PBKDF2-SHA256 hashes; no plaintext password is stored.
INSERT IGNORE INTO users (username,password_hash,role,branch_id)
SELECT 'manager',
       'pbkdf2:sha256:600000$wgYRBD1ZkfLxPMcr$10868272240adfc2628fce445232b1f20220cf095bb597c10f3f6214997a0d51',
       'BRANCH_MANAGER', b.branch_id
FROM branches b ORDER BY b.branch_id LIMIT 1;

INSERT IGNORE INTO users (username,password_hash,role,customer_id)
SELECT 'aarav',
       'pbkdf2:sha256:600000$9meAKrtVybN8qBZL$6de2e2643ab3b3a8e8c3196d65384c61a12daa9135620d9286d58919729b19b2',
       'CUSTOMER', c.customer_id
FROM customers c ORDER BY c.customer_id LIMIT 1;
