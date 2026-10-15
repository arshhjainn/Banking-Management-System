# Viva questions and short answers

1. Why MySQL? It provides relational constraints, joins and ACID transactions for related financial records.
2. Why DECIMAL? It represents decimal currency exactly; binary floating point can round unexpectedly.
3. Why parameterized queries? They separate SQL structure from values and block SQL injection.
4. What does a foreign key do? It prevents references to missing customer, branch or account rows.
5. How is transfer atomic? The two account rows are locked, both balances and all ledger rows are changed in one transaction, then committed once.
6. What does rollback do? It discards uncommitted changes when an operation fails.
7. What are 1NF/2NF/3NF? Atomic values, no partial key dependency, and no non-key transitive dependency.
8. Why indexes? They speed lookups and joins at storage/write cost; EXPLAIN shows the chosen plan.
9. What is polymorphism? A base reference can dispatch an overridden method according to the runtime object's class.
10. Why are Thread.stop/suspend unsafe? They can halt while shared state/locks are inconsistent; use interruption and coordination.
