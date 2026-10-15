import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import bcrypt
import datetime


DB_CONFIG = {
    "dbname": "BankManagement",     
    "user": "postgres",
    "password": "1384",              
    "host": "localhost",
    "port": "5432"
}



class BankDatabase:
    def __init__(self):
        self.conn = None
        self.connect()  

    def connect(self, password=None):
        """Establishes connection to the database."""
        try:
            config = DB_CONFIG.copy()
            if password:
                config["password"] = password
            self.conn = psycopg2.connect(**config)
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to connect to database:\n{e}")
            return False

    def execute_query(self, sql, params=None, fetch=False, commit=False):
        """Executes a query safely (prevents SQL injection via %s placeholders)."""
        cursor = None
        try:
            if self.conn is None or self.conn.closed:
                self.connect()

            cursor = self.conn.cursor()
            cursor.execute(sql, params or ())
            
            if commit:
                self.conn.commit()
                return cursor.rowcount
            
            if fetch:
                return cursor.fetchall()
            
            return True
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            messagebox.showerror("SQL Error", f"An error occurred:\n{e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def authenticate_user(self, username, input_password):
        """Verifies username and hashed password."""
        result = self.execute_query(
            "SELECT UserID, PasswordHash, RoleID FROM SystemUser WHERE Username = %s;",
            (username,),
            fetch=True
        )
        if result:
            user_id, stored_hash, role_id = result[0]
            if bcrypt.checkpw(input_password.encode('utf-8'), stored_hash.encode('utf-8')):
                return {"UserID": user_id, "RoleID": role_id}
        return None

    def create_user(self, username, plain_password, role_id):
        """Handles user sign up with password hashing."""
        check = self.execute_query("SELECT 1 FROM SystemUser WHERE Username = %s;", (username,), fetch=True)
        if check:
            return False, "Username already exists. Please choose another."

        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        sql = "INSERT INTO SystemUser (Username, PasswordHash, RoleID) VALUES (%s, %s, %s);"
        success = self.execute_query(sql, (username, hashed_password, role_id), commit=True)
        
        if success:
            return True, "Account created successfully! You can now log in."
        return False, "Database error occurred while creating user."

    def get_customers(self, search_term=""):
        sql = """SELECT CustomerID, FirstName, LastName, NationalID, Email, Phone, Address 
                 FROM Customer WHERE FirstName ILIKE %s OR LastName ILIKE %s OR NationalID ILIKE %s"""
        param = f"%{search_term}%"
        return self.execute_query(sql, (param, param, param), fetch=True)

    def add_customer(self, fname, lname, national_id, email, phone, address):
        sql = """INSERT INTO Customer (FirstName, LastName, NationalID, Email, Phone, Address) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        return self.execute_query(sql, (fname, lname, national_id, email, phone, address), commit=True)

    def open_account(self, customer_id, branch_id, type_id):
        account_number = f"ACC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        sql = """INSERT INTO Account (AccountNumber, CustomerID, BranchID, TypeID, Balance, Status) 
                 VALUES (%s, %s, %s, %s, 0.00, 'Active')"""
        return self.execute_query(sql, (account_number, customer_id, branch_id, type_id), commit=True)

    def perform_transfer(self, sender_id, receiver_id, amount):
        sql = "CALL TransferFunds(%s, %s, %s);"
        return self.execute_query(sql, (sender_id, receiver_id, amount), commit=True)

    def get_accounts_by_customer(self, customer_id):
        sql = """SELECT a.AccountID, a.AccountNumber, at.TypeName, a.Balance, a.Status 
                 FROM Account a
                 JOIN AccountType at ON a.TypeID = at.TypeID
                 WHERE a.CustomerID = %s"""
        return self.execute_query(sql, (customer_id,), fetch=True)

    def get_all_accounts(self):
        sql = """
            SELECT 
                a.AccountID, 
                c.FirstName || ' ' || c.LastName AS CustomerName, 
                a.AccountNumber, 
                at.TypeName, 
                a.Balance, 
                a.Status 
            FROM Account a
            JOIN Customer c ON a.CustomerID = c.CustomerID
            JOIN AccountType at ON a.TypeID = at.TypeID
            ORDER BY a.AccountID;
        """
        return self.execute_query(sql, fetch=True)

    def create_loan(self, customer_id, amount, interest, months, total_amount):
        sql = """INSERT INTO Loan (CustomerID, Amount, InterestRate, DurationMonths, TotalAmount, Status) 
                 VALUES (%s, %s, %s, %s, %s, 'Active') RETURNING LoanID;"""
        return self.execute_query(sql, (customer_id, amount, interest, months, total_amount), fetch=True)

    def get_all_loans_with_customer(self):
        sql = """
            SELECT l.LoanID, c.FirstName || ' ' || c.LastName AS CustomerName, l.Amount, l.TotalAmount, l.Status
            FROM Loan l
            JOIN Customer c ON l.CustomerID = c.CustomerID
            ORDER BY l.LoanID;
        """
        return self.execute_query(sql, fetch=True)

    def get_all_transactions(self):
        sql = """
            SELECT t.TransactionID, t.AccountID, t.TargetAccountID, t.Amount, t.TransactionDate, tt.TypeName
            FROM "Transaction" t
            JOIN TransactionType tt ON t.TypeID = tt.TypeID
            ORDER BY t.TransactionDate DESC
            LIMIT 100;
        """
        return self.execute_query(sql, fetch=True)



class BankApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = BankDatabase()
        self.current_user = None

        self.title("Modern Bank Management System")
        self.geometry("1100x750")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.login_frame = LoginFrame(self)
        self.login_frame.pack(fill="both", expand=True)

    def on_login_success(self, user_data):
        self.current_user = user_data
        self.login_frame.destroy()
        self.main_frame = MainFrame(self, self.db, self.current_user)
        self.main_frame.pack(fill="both", expand=True)


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.login_box = ctk.CTkFrame(self, width=350, corner_radius=15)
        self.login_box.grid(row=0, column=0, sticky="nsew")
        
        self.login_box.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        self.login_box.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.login_box, text="Bank Login", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(30, 10))
        
        self.username_entry = ctk.CTkEntry(self.login_box, placeholder_text="Username", width=250)
        self.username_entry.grid(row=1, column=0, pady=5)
        
        self.password_entry = ctk.CTkEntry(self.login_box, placeholder_text="Password", show="*", width=250)
        self.password_entry.grid(row=2, column=0, pady=5)
        
        self.login_btn = ctk.CTkButton(self.login_box, text="Login", command=self.login_action, width=250)
        self.login_btn.grid(row=3, column=0, pady=(20, 10))
        
        ctk.CTkLabel(self.login_box, text="Don't have an account?", font=ctk.CTkFont(size=12)).grid(row=4, column=0, pady=(10, 0))
        self.signup_btn = ctk.CTkButton(self.login_box, text="Sign Up", fg_color="gray", command=self.open_signup_dialog, width=250)
        self.signup_btn.grid(row=5, column=0, pady=(0, 30))
        
        self.password_entry.bind("<Return>", lambda event: self.login_action())

    def login_action(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both Username and Password.")
            return

        user = self.parent.db.authenticate_user(username, password)
        
        if user:
            self.parent.on_login_success(user)
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password.")

    def open_signup_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create New Account")
        dialog.geometry("350x450")
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text="Sign Up", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))
        
        username_entry = ctk.CTkEntry(dialog, placeholder_text="Desired Username", width=250)
        username_entry.pack(pady=5)
        
        password_entry = ctk.CTkEntry(dialog, placeholder_text="Password", show="*", width=250)
        password_entry.pack(pady=5)
        
        confirm_pass_entry = ctk.CTkEntry(dialog, placeholder_text="Confirm Password", show="*", width=250)
        confirm_pass_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Select Role:").pack(pady=(10, 0))
        role_combobox = ctk.CTkComboBox(dialog, values=["1 - Administrator", "2 - Employee", "3 - Customer"], width=250)
        role_combobox.set("2 - Employee")
        role_combobox.pack(pady=5)
        
        def register_user():
            uname = username_entry.get()
            pwd = password_entry.get()
            confirm = confirm_pass_entry.get()
            
            if not uname or not pwd:
                messagebox.showwarning("Input Error", "Username and Password cannot be empty.")
                return
            if pwd != confirm:
                messagebox.showwarning("Input Error", "Passwords do not match.")
                return
            
            try:
                role_id = int(role_combobox.get().split()[0])
            except:
                role_id = 2

            success, message = self.parent.db.create_user(uname, pwd, role_id)
            if success:
                messagebox.showinfo("Success", message)
                dialog.destroy()
            else:
                messagebox.showerror("Error", message)

        ctk.CTkButton(dialog, text="Create Account", fg_color="green", command=register_user, width=250).pack(pady=20)


class MainFrame(ctk.CTkFrame):
    def __init__(self, parent, db, user):
        super().__init__(parent)
        self.db = db
        self.user = user
        
        self.tabview = ctk.CTkTabview(self, width=1100, height=750)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_customers = self.tabview.add("Customers")
        self.tab_accounts = self.tabview.add("Accounts")
        self.tab_transactions = self.tabview.add("Transactions")
        self.tab_loans = self.tabview.add("Loans")
        
        self.setup_customers_tab()
        self.setup_accounts_tab()
        self.setup_transactions_tab()
        self.setup_loans_tab()

    def setup_customers_tab(self):
        frame = ctk.CTkFrame(self.tab_customers)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        search_frame = ctk.CTkFrame(frame)
        search_frame.pack(fill="x", pady=(0, 10))
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search by name or National ID...", width=300)
        self.search_entry.pack(side="left", padx=(10, 10))
        ctk.CTkButton(search_frame, text="Search", command=self.load_customers).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="Add Customer", command=self.open_add_customer_dialog, fg_color="green").pack(side="left", padx=10)
        
        self.customer_tree = ttk.Treeview(frame, columns=("ID", "First", "Last", "NID", "Email", "Phone", "Address"), show="headings", height=18)
        self.customer_tree.heading("ID", text="ID")
        self.customer_tree.heading("First", text="First Name")
        self.customer_tree.heading("Last", text="Last Name")
        self.customer_tree.heading("NID", text="National ID")
        self.customer_tree.heading("Email", text="Email")
        self.customer_tree.heading("Phone", text="Phone")
        self.customer_tree.heading("Address", text="Address")
        
        self.customer_tree.column("ID", width=40)
        self.customer_tree.column("First", width=100)
        self.customer_tree.column("Last", width=100)
        self.customer_tree.column("NID", width=120)
        self.customer_tree.column("Email", width=150)
        self.customer_tree.column("Phone", width=100)
        self.customer_tree.column("Address", width=200)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=scrollbar.set)
        self.customer_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="left", fill="y", padx=(0, 10), pady=10)
        
        self.load_customers()

    def load_customers(self):
        for row in self.customer_tree.get_children():
            self.customer_tree.delete(row)
        customers = self.db.get_customers(self.search_entry.get())
        if customers:
            for cust in customers:
                self.customer_tree.insert("", "end", values=cust)

    def open_add_customer_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Customer")
        dialog.geometry("400x500")
        dialog.attributes("-topmost", True)
        
        entries = {}
        fields = [("First Name", "fname"), ("Last Name", "lname"), ("National ID", "nid"), ("Email", "email"), ("Phone", "phone"), ("Address", "address")]
        
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(dialog, text=label).pack(pady=(10, 0))
            entry = ctk.CTkEntry(dialog)
            entry.pack(pady=(0, 5))
            entries[key] = entry
        
        def save():
            if not entries["fname"].get() or not entries["lname"].get():
                messagebox.showwarning("Error", "First and Last name are required.")
                return
            self.db.add_customer(entries["fname"].get(), entries["lname"].get(), entries["nid"].get(), entries["email"].get(), entries["phone"].get(), entries["address"].get())
            dialog.destroy()
            self.load_customers()
            messagebox.showinfo("Success", "Customer added successfully.")
            
        ctk.CTkButton(dialog, text="Save Customer", command=save, fg_color="green").pack(pady=20)

    def setup_accounts_tab(self):
        frame = ctk.CTkFrame(self.tab_accounts)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Open New Account", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Customer ID:").pack(side="left", padx=10)
        self.acc_cust_id = ctk.CTkEntry(form_frame, width=100)
        self.acc_cust_id.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Branch ID:").pack(side="left", padx=10)
        self.acc_branch_id = ctk.CTkEntry(form_frame, width=100, placeholder_text="1")
        self.acc_branch_id.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Account Type:").pack(side="left", padx=10)
        self.acc_type = ctk.CTkComboBox(form_frame, values=["1 - Savings", "2 - Checking", "3 - Business"])
        self.acc_type.pack(side="left", padx=5)
        
        self.open_account_btn = ctk.CTkButton(form_frame, text="Open Account", fg_color="green", command=self.open_new_account)
        self.open_account_btn.pack(side="left", padx=20)

        self.accounts_tree = ttk.Treeview(frame, columns=("ID", "Customer", "Account No.", "Type", "Balance", "Status"), show="headings", height=12)
        self.accounts_tree.heading("ID", text="Account ID")
        self.accounts_tree.heading("Customer", text="Customer Name")
        self.accounts_tree.heading("Account No.", text="Account No.")
        self.accounts_tree.heading("Type", text="Type")
        self.accounts_tree.heading("Balance", text="Balance")
        self.accounts_tree.heading("Status", text="Status")
        
        self.accounts_tree.column("ID", width=60)
        self.accounts_tree.column("Customer", width=150)
        self.accounts_tree.column("Account No.", width=120)
        self.accounts_tree.column("Type", width=100)
        self.accounts_tree.column("Balance", width=100)
        self.accounts_tree.column("Status", width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)
        self.accounts_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="left", fill="y", padx=(0, 10), pady=10)

        self.load_accounts()

    def load_accounts(self):
        for row in self.accounts_tree.get_children():
            self.accounts_tree.delete(row)
        
        accounts = self.db.get_all_accounts()
        if accounts:
            for acc in accounts:
                self.accounts_tree.insert("", "end", values=acc)

    def open_new_account(self):
        try:
            cust_id = int(self.acc_cust_id.get())
            branch_id = int(self.acc_branch_id.get())
            type_id = int(self.acc_type.get().split()[0])
            
            self.db.open_account(cust_id, branch_id, type_id)
            self.load_accounts()
            
            messagebox.showinfo("Success", f"New Account opened for Customer {cust_id}!")
            self.acc_cust_id.delete(0, "end")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric IDs.")

    def setup_transactions_tab(self):
        frame = ctk.CTkFrame(self.tab_transactions)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Transfer Funds", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Sender Account ID:").pack(side="left", padx=10)
        self.trans_sender = ctk.CTkEntry(form_frame, width=120)
        self.trans_sender.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Receiver Account ID:").pack(side="left", padx=10)
        self.trans_receiver = ctk.CTkEntry(form_frame, width=120)
        self.trans_receiver.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Amount ($):").pack(side="left", padx=10)
        self.trans_amount = ctk.CTkEntry(form_frame, width=120)
        self.trans_amount.pack(side="left", padx=5)
        
        ctk.CTkButton(form_frame, text="Execute Transfer", fg_color="#1f6aa5", command=self.execute_transfer).pack(side="left", padx=20)

        # Added a "Transaction History" list
        ctk.CTkLabel(frame, text="Transaction History", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 10))
        
        self.transactions_tree = ttk.Treeview(frame, columns=("ID", "Sender", "Receiver", "Amount", "Date", "Type"), show="headings", height=10)
        self.transactions_tree.heading("ID", text="Trans ID")
        self.transactions_tree.heading("Sender", text="Account ID (Sender)")
        self.transactions_tree.heading("Receiver", text="Target ID (Receiver)")
        self.transactions_tree.heading("Amount", text="Amount ($)")
        self.transactions_tree.heading("Date", text="Date")
        self.transactions_tree.heading("Type", text="Type")
        
        self.transactions_tree.column("ID", width=60)
        self.transactions_tree.column("Sender", width=120)
        self.transactions_tree.column("Receiver", width=120)
        self.transactions_tree.column("Amount", width=100)
        self.transactions_tree.column("Date", width=150)
        self.transactions_tree.column("Type", width=100)
        
        trans_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscrollcommand=trans_scrollbar.set)
        self.transactions_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        trans_scrollbar.pack(side="left", fill="y", padx=(0, 10), pady=10)

        self.load_transactions()

    def load_transactions(self):
        for row in self.transactions_tree.get_children():
            self.transactions_tree.delete(row)
        
        transactions = self.db.get_all_transactions()
        if transactions:
            for t in transactions:
                self.transactions_tree.insert("", "end", values=t)

    def execute_transfer(self):
        try:
            sender = int(self.trans_sender.get())
            receiver = int(self.trans_receiver.get())
            amount = float(self.trans_amount.get())
            
            if amount <= 0:
                messagebox.showwarning("Error", "Amount must be greater than 0.")
                return
            
            self.db.perform_transfer(sender, receiver, amount)
            self.load_transactions()
            self.load_accounts() 
            
            messagebox.showinfo("Success", "Transfer executed successfully!")
            self.trans_sender.delete(0, "end")
            self.trans_receiver.delete(0, "end")
            self.trans_amount.delete(0, "end")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid Account IDs and a numeric Amount.")

    def setup_loans_tab(self):
        frame = ctk.CTkFrame(self.tab_loans)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Create New Loan", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Customer ID:").pack(side="left", padx=10)
        self.loan_cust = ctk.CTkEntry(form_frame, width=100)
        self.loan_cust.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Amount ($):").pack(side="left", padx=10)
        self.loan_amount = ctk.CTkEntry(form_frame, width=100)
        self.loan_amount.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Interest Rate (%):").pack(side="left", padx=10)
        self.loan_rate = ctk.CTkEntry(form_frame, width=80)
        self.loan_rate.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Duration (Months):").pack(side="left", padx=10)
        self.loan_months = ctk.CTkEntry(form_frame, width=80)
        self.loan_months.pack(side="left", padx=5)
        
        ctk.CTkButton(form_frame, text="Create Loan", fg_color="green", command=self.create_new_loan).pack(side="left", padx=20)

        ctk.CTkLabel(frame, text="Active Loan List", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 10))
        
        self.loans_tree = ttk.Treeview(frame, columns=("ID", "Customer", "Amount", "Total", "Status"), show="headings", height=10)
        self.loans_tree.heading("ID", text="Loan ID")
        self.loans_tree.heading("Customer", text="Customer Name")
        self.loans_tree.heading("Amount", text="Loan Amount")
        self.loans_tree.heading("Total", text="Total Payable")
        self.loans_tree.heading("Status", text="Status")
        
        self.loans_tree.column("ID", width=60)
        self.loans_tree.column("Customer", width=150)
        self.loans_tree.column("Amount", width=100)
        self.loans_tree.column("Total", width=100)
        self.loans_tree.column("Status", width=100)
        
        loan_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.loans_tree.yview)
        self.loans_tree.configure(yscrollcommand=loan_scrollbar.set)
        self.loans_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        loan_scrollbar.pack(side="left", fill="y", padx=(0, 10), pady=10)

        self.load_loans()

    def load_loans(self):
        for row in self.loans_tree.get_children():
            self.loans_tree.delete(row)
        
        loans = self.db.get_all_loans_with_customer()
        if loans:
            for loan in loans:
                self.loans_tree.insert("", "end", values=loan)

    def create_new_loan(self):
        try:
            cust_id = int(self.loan_cust.get())
            amount = float(self.loan_amount.get())
            rate = float(self.loan_rate.get())
            months = int(self.loan_months.get())
            
            total = amount + (amount * (rate / 100))
            
            result = self.db.create_loan(cust_id, amount, rate, months, total)
            if result:
                self.load_loans() 
                loan_id = result[0][0]
                messagebox.showinfo("Success", f"Loan ID {loan_id} created successfully! Total payable: ${total:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values.")


if __name__ == "__main__":
    app = BankApp()
    app.mainloop()