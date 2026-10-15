from graphviz import Digraph

# Create a new graph object
erd = Digraph('BankDB_Corrected', node_attr={'shape': 'record', 'fontname': 'Helvetica'})

# 1. Create the Tables (Nodes) with corrected attributes
erd.node('Role', '{Role | RoleID (PK) \n RoleName}')
erd.node('SystemUser', '{SystemUser | UserID (PK) \n Username \n PasswordHash \n RoleID (FK)}')
erd.node('Customer', '{Customer | CustomerID (PK) \n FirstName \n LastName \n NationalID \n Email \n PhoneNumber \n Address}')
erd.node('AccountType', '{AccountType | TypeID (PK) \n TypeName \n InterestRate}')
erd.node('Account', '{Account | AccountID (PK) \n AccountNumber \n Balance \n OpeningDate \n Status \n CustomerID (FK) \n BranchID (FK) \n TypeID (FK)}')
erd.node('TransactionType', '{TransactionType | TypeID (PK) \n TypeName}')
erd.node('Transaction', '{Transaction | TransactionID (PK) \n Amount \n TransactionDate \n Description \n AccountID (FK) \n TypeID (FK)}')
erd.node('Branch', '{Branch | BranchID (PK) \n BranchName \n Address}')
erd.node('Employee', '{Employee | EmployeeID (PK) \n FirstName \n LastName \n Position \n HireDate \n BranchID (FK) \n UserID (FK)}')
erd.node('Loan', '{Loan | LoanID (PK) \n Amount \n TotalAmount \n InterestRate \n DurationMonths \n LoanDate \n Status \n CustomerID (FK)}')
erd.node('Installment', '{Installment | InstallmentID (PK) \n Amount \n DueDate \n PaidDate \n Status \n LoanID (FK)}')

# 2. Draw the Relationships (Edges)
erd.edge('Role', 'SystemUser', label='1:N')
erd.edge('SystemUser', 'Employee', label='1:1')
erd.edge('Branch', 'Employee', label='1:N')
erd.edge('Branch', 'Account', label='1:N')
erd.edge('Customer', 'Account', label='1:N')
erd.edge('Customer', 'Loan', label='1:N')
erd.edge('AccountType', 'Account', label='1:N')
erd.edge('Account', 'Transaction', label='1:N')
erd.edge('TransactionType', 'Transaction', label='1:N')
erd.edge('Loan', 'Installment', label='1:N')

# 3. Render and save the diagram as a PNG
erd.render('bank_er_diagram', format='png', cleanup=True)
print("ER Diagram successfully generated as 'bank_er_diagram.png'!")