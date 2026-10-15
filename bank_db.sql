
-- 1. CREATE TABLE Statements

CREATE TABLE Role (
    RoleID SERIAL PRIMARY KEY,
    RoleName VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE SystemUser (
    UserID SERIAL PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    RoleID INT REFERENCES Role(RoleID)
);

CREATE TABLE Branch (
    BranchID SERIAL PRIMARY KEY,
    BranchName VARCHAR(100) NOT NULL,
    Address TEXT
);

CREATE TABLE Employee (
    EmployeeID SERIAL PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Position VARCHAR(50),          
    HireDate DATE NOT NULL DEFAULT CURRENT_DATE, 
    BranchID INT REFERENCES Branch(BranchID),
    UserID INT UNIQUE REFERENCES SystemUser(UserID)
);

CREATE TABLE Customer (
    CustomerID SERIAL PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    NationalID VARCHAR(10) UNIQUE NOT NULL,
    Phone VARCHAR(15),
    Address TEXT
);

CREATE TABLE AccountType (
    TypeID SERIAL PRIMARY KEY,
    TypeName VARCHAR(50) NOT NULL,
    InterestRate DECIMAL(5,2) DEFAULT 0.00
);

CREATE TABLE Account (
    AccountID SERIAL PRIMARY KEY,
    AccountNumber VARCHAR(20) UNIQUE NOT NULL,
    CustomerID INT NOT NULL REFERENCES Customer(CustomerID) ON DELETE RESTRICT, 
    BranchID INT NOT NULL REFERENCES Branch(BranchID),
    TypeID INT NOT NULL REFERENCES AccountType(TypeID),
    Balance DECIMAL(15,2) DEFAULT 0.00 CHECK (Balance >= 0),
    OpeningDate DATE DEFAULT CURRENT_DATE, -- Added from ER
    Status VARCHAR(20) DEFAULT 'Active' CHECK (Status IN ('Active', 'Closed', 'Frozen'))
);

CREATE TABLE TransactionType (
    TypeID SERIAL PRIMARY KEY,
    TypeName VARCHAR(50) NOT NULL
);


CREATE TABLE "Transaction" (
    TransactionID SERIAL PRIMARY KEY,
    AccountID INT NOT NULL REFERENCES Account(AccountID),
    TypeID INT NOT NULL REFERENCES TransactionType(TypeID),
    Amount DECIMAL(15,2) NOT NULL CHECK (Amount > 0),
    TransactionDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Description VARCHAR(255),          
    TargetAccountID INT REFERENCES Account(AccountID)
);

CREATE TABLE Loan (
    LoanID SERIAL PRIMARY KEY,
    CustomerID INT REFERENCES Customer(CustomerID),
    Amount DECIMAL(15,2) NOT NULL,
    InterestRate DECIMAL(5,2) NOT NULL,
    DurationMonths INT NOT NULL,
    TotalAmount DECIMAL(15,2) NOT NULL, 
    LoanDate DATE NOT NULL DEFAULT CURRENT_DATE, 
    Status VARCHAR(20) DEFAULT 'Active' CHECK (Status IN ('Active', 'PaidOff', 'Defaulted', 'Approved'))
);

CREATE TABLE Installment (
    InstallmentID SERIAL PRIMARY KEY,
    LoanID INT REFERENCES Loan(LoanID) ON DELETE CASCADE,
    Amount DECIMAL(15,2) NOT NULL,
    DueDate DATE NOT NULL,
    PaymentDate DATE NULL,
    Status VARCHAR(20) DEFAULT 'Pending' CHECK (Status IN ('Pending', 'Paid', 'Overdue'))
);


-- 2. ALTER TABLE Requirement

ALTER TABLE Customer
ADD COLUMN Email VARCHAR(100);

ALTER TABLE Customer
ADD CONSTRAINT UQ_Customer_Email UNIQUE (Email);


-- 3. View Requirement (Using JOIN queries)

CREATE OR REPLACE VIEW vw_CustomerAccounts AS
SELECT
    c.NationalID,
    c.FirstName,
    c.LastName,
    c.Email,
    a.AccountNumber,
    a.Balance,
    b.BranchName,
    aty.TypeName AS AccountType
FROM Customer c
JOIN Account a ON c.CustomerID = a.CustomerID
JOIN Branch b ON a.BranchID = b.BranchID
JOIN AccountType aty ON a.TypeID = aty.TypeID;


-- 4. Stored Procedure Requirement (Transfer with atomic transaction)

CREATE OR REPLACE PROCEDURE TransferFunds(
    sender_id INT,
    receiver_id INT,
    transfer_amount DECIMAL
)
LANGUAGE plpgsql
AS $$
DECLARE
    transfer_type_id INT;
BEGIN
    -- Dynamically find the Transaction ID for 'Transfer' to avoid hardcoding
    SELECT TypeID INTO transfer_type_id FROM TransactionType WHERE TypeName = 'Transfer' LIMIT 1;
    IF transfer_type_id IS NULL THEN
        RAISE EXCEPTION 'Transaction Type "Transfer" not found in TransactionType table.';
    END IF;

    -- 1. Deduct from sender account
    UPDATE Account
    SET Balance = Balance - transfer_amount
    WHERE AccountID = sender_id;

    -- 2. Add to receiver account
    UPDATE Account
    SET Balance = Balance + transfer_amount
    WHERE AccountID = receiver_id;

    -- 3. Log the sender's record (Debit)
    INSERT INTO "Transaction" (AccountID, TypeID, Amount, TargetAccountID, Description)
    VALUES (sender_id, transfer_type_id, transfer_amount, receiver_id, 'Transfer Out');

    -- 4. Log the receiver's record (Credit)
    INSERT INTO "Transaction" (AccountID, TypeID, Amount, Description)
    VALUES (receiver_id, transfer_type_id, transfer_amount, 'Transfer In');

EXCEPTION
    WHEN OTHERS THEN
        RAISE; -- Automatically rolls back the entire transaction if any step fails
END;
$$;


-- 5. Trigger / Audit Trail Requirement

CREATE TABLE AuditLog (
    LogID SERIAL PRIMARY KEY,
    TableName VARCHAR(50),
    Action VARCHAR(10),
    ActionTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Details TEXT
);

CREATE OR REPLACE FUNCTION log_account_changes()
RETURNS TRIGGER
AS $$
BEGIN
    INSERT INTO AuditLog (
        TableName,
        Action,
        Details
    )
    VALUES (
        'Account',
        TG_OP,
        'Account ' || NEW.AccountNumber || ' balance changed to ' || NEW.Balance
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER account_audit_trigger
AFTER UPDATE ON Account
FOR EACH ROW
EXECUTE FUNCTION log_account_changes();


-- 6. Aggregate Query Requirement (SUM, COUNT, GROUP BY)

SELECT 
    b.BranchName, 
    COUNT(a.AccountID) AS TotalAccounts, 
    SUM(a.Balance) AS TotalBranchBalance
FROM Branch b
LEFT JOIN Account a ON b.BranchID = a.BranchID
GROUP BY b.BranchID, b.BranchName
ORDER BY TotalBranchBalance DESC;