-- 1. Insert Roles
INSERT INTO Role (RoleName) VALUES ('Administrator'), ('Employee'), ('Customer');

-- 2. Insert Transaction Types (Crucial for your Stored Procedure)
INSERT INTO TransactionType (TypeName) VALUES ('Deposit'), ('Withdrawal'), ('Transfer'), ('Fee');

-- 3. Insert Account Types
INSERT INTO AccountType (TypeName, InterestRate) VALUES ('Savings', 2.50), ('Checking', 0.00), ('Business', 1.50);

-- 4. Insert Branches
INSERT INTO Branch (BranchName, Address) VALUES ('Downtown Main', '123 Main St, City'), ('North Branch', '456 North Ave, City');

-- 5. Insert a System User & Employee
INSERT INTO SystemUser (Username, PasswordHash, RoleID) VALUES ('admin', 'hashed_password_123', 1);
INSERT INTO Employee (FirstName, LastName, Position, HireDate, BranchID, UserID) 
VALUES ('John', 'Doe', 'Branch Manager', '2023-01-15', 1, 1);

-- 6. Insert a Customer
INSERT INTO Customer (FirstName, LastName, NationalID, Phone, Address, Email) 
VALUES ('Jane', 'Smith', '1234567890', '555-0101', '789 Oak St, City', 'jane.smith@email.com');