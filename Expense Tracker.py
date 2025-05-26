import sqlite3
import os
import datetime
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import qrcode
from PIL import Image, ImageTk
import uuid

class UPIManager:
    """Manage UPI transactions and connections"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # In a real application, this would use proper API keys stored securely
        self.api_url = "https://api.upi-example.com/v1"  # Example URL
        self.merchant_id = "MERCHANT123"
        # In a production app, this would be stored securely
        self.api_key = "dummy_api_key" 
        
    def generate_transaction_id(self):
        """Generate a unique transaction ID"""
        return str(uuid.uuid4())
    
    def create_payment_request(self, amount, description):
        """Create a UPI payment request and return a QR code"""
        try:
            transaction_id = self.generate_transaction_id()
            
            # In a real implementation, this would make an actual API call
            # Here we simulate the response
            upi_id = "expensetracker@upi"
            payload = {
                "pa": upi_id,                 # Payee address (UPI ID)
                "pn": "Expense Tracker",      # Payee name
                "tr": transaction_id,         # Transaction reference ID
                "am": str(amount),            # Amount
                "cu": "INR",                  # Currency
                "tn": description             # Transaction note
            }
            
            # Create a UPI URI
            upi_uri = "upi://pay?"
            for key, value in payload.items():
                upi_uri += f"{key}={value}&"
            upi_uri = upi_uri[:-1]  # Remove the last '&'
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(upi_uri)
            qr.make(fit=True)
            qr_img = qr.make_image(fill='black', back_color='white')
            
            # Save transaction in database
            self.db_manager.add_pending_transaction(transaction_id, amount, description)
            
            # Return the QR code image
            return qr_img, transaction_id
            
        except Exception as e:
            print(f"Error creating payment request: {e}")
            return None, None
    
    def check_transaction_status(self, transaction_id):
        """Check the status of a transaction"""
        # In a real app, this would make an API call to verify the payment status
        # For this example, we'll assume the payment is completed after verification
        
        try:
            # Simulate API request
            print(f"Checking status for transaction {transaction_id}")
            
            # In a real app, you would get the actual status from the UPI gateway
            # For demo purposes, we'll randomly consider it successful
            import random
            status = "SUCCESS" if random.random() > 0.3 else "PENDING"
            
            if status == "SUCCESS":
                # Update the transaction in the database
                self.db_manager.update_transaction_status(transaction_id, "completed")
                return True
            return False
            
        except Exception as e:
            print(f"Error checking transaction status: {e}")
            return False

class DatabaseManager:
    """Manage SQLite database operations"""
    
    def __init__(self, db_name="expense_tracker.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Categories table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                budget REAL DEFAULT 0
            )
            ''')
            
            # Expenses table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                amount REAL,
                description TEXT,
                category_id INTEGER,
                date TEXT,
                payment_method TEXT,
                transaction_id TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
            ''')
            
            # UPI Transactions table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS upi_transactions (
                transaction_id TEXT PRIMARY KEY,
                amount REAL,
                description TEXT,
                status TEXT,
                date TEXT
            )
            ''')
            
            # Insert default categories if they don't exist
            default_categories = [
                ("Food", 5000),
                ("Transportation", 3000),
                ("Entertainment", 2000),
                ("Utilities", 4000),
                ("Rent", 15000),
                ("Shopping", 3000),
                ("Healthcare", 2000),
                ("Others", 1000)
            ]
            
            for category, budget in default_categories:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO categories (name, budget) VALUES (?, ?)",
                    (category, budget)
                )
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
    
    def get_categories(self):
        """Get all expense categories"""
        try:
            self.cursor.execute("SELECT id, name, budget FROM categories")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching categories: {e}")
            return []
    
    def add_category(self, name, budget=0):
        """Add a new expense category"""
        try:
            self.cursor.execute(
                "INSERT INTO categories (name, budget) VALUES (?, ?)",
                (name, budget)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding category: {e}")
            return False
    
    def update_category_budget(self, category_id, budget):
        """Update the budget for a category"""
        try:
            self.cursor.execute(
                "UPDATE categories SET budget = ? WHERE id = ?",
                (budget, category_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating category budget: {e}")
            return False
    
    def add_expense(self, amount, description, category_id, date, payment_method, transaction_id=None):
        """Add a new expense"""
        try:
            self.cursor.execute(
                "INSERT INTO expenses (amount, description, category_id, date, payment_method, transaction_id) VALUES (?, ?, ?, ?, ?, ?)",
                (amount, description, category_id, date, payment_method, transaction_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding expense: {e}")
            return False
    
    def get_expenses(self, start_date=None, end_date=None, category_id=None):
        """Get expenses with optional filtering"""
        try:
            query = "SELECT e.id, e.amount, e.description, c.name, e.date, e.payment_method FROM expenses e JOIN categories c ON e.category_id = c.id"
            params = []
            
            if start_date or end_date or category_id:
                query += " WHERE"
                
                if start_date:
                    query += " e.date >= ?"
                    params.append(start_date)
                    if end_date or category_id:
                        query += " AND"
                
                if end_date:
                    query += " e.date <= ?"
                    params.append(end_date)
                    if category_id:
                        query += " AND"
                
                if category_id:
                    query += " e.category_id = ?"
                    params.append(category_id)
            
            query += " ORDER BY e.date DESC"
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching expenses: {e}")
            return []
    
    def get_category_totals(self, start_date=None, end_date=None):
        """Get total expenses by category for a date range"""
        try:
            query = """
            SELECT c.name, COALESCE(SUM(e.amount), 0) as total, c.budget 
            FROM categories c
            LEFT JOIN expenses e ON c.id = e.category_id
            """
            params = []
            
            if start_date or end_date:
                query += " WHERE"
                
                if start_date:
                    query += " e.date >= ?"
                    params.append(start_date)
                    if end_date:
                        query += " AND"
                
                if end_date:
                    query += " e.date <= ?"
                    params.append(end_date)
            
            query += " GROUP BY c.id ORDER BY total DESC"
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching category totals: {e}")
            return []
    
    def delete_expense(self, expense_id):
        """Delete an expense by ID"""
        try:
            self.cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting expense: {e}")
            return False
    
    def add_pending_transaction(self, transaction_id, amount, description):
        """Add a pending UPI transaction"""
        try:
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute(
                "INSERT INTO upi_transactions (transaction_id, amount, description, status, date) VALUES (?, ?, ?, ?, ?)",
                (transaction_id, amount, description, "pending", current_date)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding pending transaction: {e}")
            return False
    
    def update_transaction_status(self, transaction_id, status):
        """Update the status of a UPI transaction"""
        try:
            self.cursor.execute(
                "UPDATE upi_transactions SET status = ? WHERE transaction_id = ?",
                (status, transaction_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating transaction status: {e}")
            return False
    
    def get_transaction_details(self, transaction_id):
        """Get details of a specific transaction"""
        try:
            self.cursor.execute(
                "SELECT * FROM upi_transactions WHERE transaction_id = ?",
                (transaction_id,)
            )
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error fetching transaction details: {e}")
            return None
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()

class ExpenseTrackerApp:
    """Main application class for the expense tracker"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker with UPI")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        
        # Initialize UPI manager
        self.upi_manager = UPIManager(self.db_manager)
        
        # Set up the UI
        self.setup_ui()
        
        # Load initial data
        self.load_expenses()
        self.load_categories()
        self.update_dashboard()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tab frames
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.expenses_frame = ttk.Frame(self.notebook)
        self.add_expense_frame = ttk.Frame(self.notebook)
        self.budget_frame = ttk.Frame(self.notebook)
        self.upi_frame = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.expenses_frame, text="Expenses")
        self.notebook.add(self.add_expense_frame, text="Add Expense")
        self.notebook.add(self.budget_frame, text="Budget Management")
        self.notebook.add(self.upi_frame, text="UPI Payments")
        
        # Set up each tab
        self.setup_dashboard_tab()
        self.setup_expenses_tab()
        self.setup_add_expense_tab()
        self.setup_budget_tab()
        self.setup_upi_tab()
    
    def setup_dashboard_tab(self):
        """Set up the dashboard tab"""
        # Title
        tk.Label(self.dashboard_frame, text="Expense Dashboard", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Date filter frame
        date_filter_frame = ttk.Frame(self.dashboard_frame)
        date_filter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(date_filter_frame, text="Start Date:").pack(side=tk.LEFT, padx=5)
        self.start_date_var = tk.StringVar(value=datetime.date.today().replace(day=1).strftime("%Y-%m-%d"))
        tk.Entry(date_filter_frame, textvariable=self.start_date_var, width=10).pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_filter_frame, text="End Date:").pack(side=tk.LEFT, padx=5)
        self.end_date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        tk.Entry(date_filter_frame, textvariable=self.end_date_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(date_filter_frame, text="Apply Filter", command=self.update_dashboard).pack(side=tk.LEFT, padx=10)
        
        # Dashboard content
        dashboard_content = ttk.Frame(self.dashboard_frame)
        dashboard_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Summary
        summary_frame = ttk.LabelFrame(dashboard_content, text="Monthly Summary")
        summary_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.summary_tree = ttk.Treeview(summary_frame, columns=("Category", "Spent", "Budget", "Remaining"), show="headings")
        self.summary_tree.heading("Category", text="Category")
        self.summary_tree.heading("Spent", text="Spent")
        self.summary_tree.heading("Budget", text="Budget")
        self.summary_tree.heading("Remaining", text="Remaining")
        
        self.summary_tree.column("Category", width=120)
        self.summary_tree.column("Spent", width=80)
        self.summary_tree.column("Budget", width=80)
        self.summary_tree.column("Remaining", width=80)
        
        self.summary_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side - Charts
        charts_frame = ttk.LabelFrame(dashboard_content, text="Expense Analysis")
        charts_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a Figure for plots
        self.fig = plt.Figure(figsize=(6, 8), dpi=100)
        
        # Create canvas for figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_expenses_tab(self):
        """Set up the expenses tab"""
        # Title
        tk.Label(self.expenses_frame, text="Expense History", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Filter frame
        filter_frame = ttk.Frame(self.expenses_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(filter_frame, text="Start Date:").pack(side=tk.LEFT, padx=5)
        self.expense_start_date_var = tk.StringVar(value="")
        tk.Entry(filter_frame, textvariable=self.expense_start_date_var, width=10).pack(side=tk.LEFT, padx=5)
        
        tk.Label(filter_frame, text="End Date:").pack(side=tk.LEFT, padx=5)
        self.expense_end_date_var = tk.StringVar(value="")
        tk.Entry(filter_frame, textvariable=self.expense_end_date_var, width=10).pack(side=tk.LEFT, padx=5)
        
        tk.Label(filter_frame, text="Category:").pack(side=tk.LEFT, padx=5)
        self.expense_category_var = tk.StringVar(value="")
        self.expense_category_combo = ttk.Combobox(filter_frame, textvariable=self.expense_category_var, width=15)
        self.expense_category_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Apply Filter", command=self.load_expenses).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="Clear Filter", command=self.clear_expense_filters).pack(side=tk.LEFT, padx=5)
        
        # Expenses treeview
        expenses_tree_frame = ttk.Frame(self.expenses_frame)
        expenses_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.expenses_tree = ttk.Treeview(
            expenses_tree_frame,
            columns=("ID", "Date", "Category", "Description", "Amount", "Payment"),
            show="headings"
        )
        
        self.expenses_tree.heading("ID", text="ID")
        self.expenses_tree.heading("Date", text="Date")
        self.expenses_tree.heading("Category", text="Category")
        self.expenses_tree.heading("Description", text="Description")
        self.expenses_tree.heading("Amount", text="Amount")
        self.expenses_tree.heading("Payment", text="Payment Method")
        
        self.expenses_tree.column("ID", width=50)
        self.expenses_tree.column("Date", width=100)
        self.expenses_tree.column("Category", width=120)
        self.expenses_tree.column("Description", width=200)
        self.expenses_tree.column("Amount", width=100)
        self.expenses_tree.column("Payment", width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(expenses_tree_frame, orient="vertical", command=self.expenses_tree.yview)
        self.expenses_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.expenses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.expenses_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Delete Selected", command=self.delete_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Export to CSV", command=self.export_expenses).pack(side=tk.LEFT, padx=5)
    
    def setup_add_expense_tab(self):
        """Set up the add expense tab"""
        # Title
        tk.Label(self.add_expense_frame, text="Add New Expense", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Form frame
        form_frame = ttk.Frame(self.add_expense_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Amount
        tk.Label(form_frame, text="Amount:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        self.amount_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.amount_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=10)
        
        # Description
        tk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        self.description_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.description_var, width=40).grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)
        
        # Category
        tk.Label(form_frame, text="Category:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=10)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var, width=20)
        self.category_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=10)
        
        # Date
        tk.Label(form_frame, text="Date:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=10)
        self.date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        tk.Entry(form_frame, textvariable=self.date_var, width=20).grid(row=3, column=1, sticky=tk.W, padx=5, pady=10)
        
        # Payment method
        tk.Label(form_frame, text="Payment Method:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=10)
        self.payment_method_var = tk.StringVar(value="Cash")
        payment_methods = ["Cash", "Credit Card", "Debit Card", "UPI", "Bank Transfer", "Other"]
        payment_combo = ttk.Combobox(form_frame, textvariable=self.payment_method_var, values=payment_methods, width=20)
        payment_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="Add Expense", command=self.add_expense).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="Clear Form", command=self.clear_form).pack(side=tk.LEFT, padx=10)
        
        # UPI Payment option
        upi_frame = ttk.LabelFrame(form_frame, text="Pay via UPI")
        upi_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E)
        
        tk.Label(upi_frame, text="Use UPI to pay and track this expense in one go!").pack(pady=5)
        ttk.Button(upi_frame, text="Pay with UPI", command=self.pay_with_upi).pack(pady=10)
    
    def setup_budget_tab(self):
        """Set up the budget management tab"""
        # Title
        tk.Label(self.budget_frame, text="Budget Management", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Left side - Category list with budgets
        categories_frame = ttk.LabelFrame(self.budget_frame, text="Category Budgets")
        categories_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.budget_tree = ttk.Treeview(categories_frame, columns=("ID", "Category", "Budget"), show="headings")
        self.budget_tree.heading("ID", text="ID")
        self.budget_tree.heading("Category", text="Category")
        self.budget_tree.heading("Budget", text="Monthly Budget")
        
        self.budget_tree.column("ID", width=50)
        self.budget_tree.column("Category", width=150)
        self.budget_tree.column("Budget", width=150)
        
        self.budget_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side - Budget management
        budget_actions_frame = ttk.LabelFrame(self.budget_frame, text="Manage Budgets")
        budget_actions_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Update budget
        update_frame = ttk.Frame(budget_actions_frame)
        update_frame.pack(fill=tk.X, padx=10, pady=20)
        
        tk.Label(update_frame, text="Update Selected Category Budget:").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        tk.Label(update_frame, text="New Budget:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.new_budget_var = tk.StringVar()
        tk.Entry(update_frame, textvariable=self.new_budget_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Button(update_frame, text="Update Budget", command=self.update_budget).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Add new category
        add_cat_frame = ttk.Frame(budget_actions_frame)
        add_cat_frame.pack(fill=tk.X, padx=10, pady=20)
        
        tk.Label(add_cat_frame, text="Add New Category:").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        tk.Label(add_cat_frame, text="Category Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.new_category_var = tk.StringVar()
        tk.Entry(add_cat_frame, textvariable=self.new_category_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        tk.Label(add_cat_frame, text="Initial Budget:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.initial_budget_var = tk.StringVar(value="0")
        tk.Entry(add_cat_frame, textvariable=self.initial_budget_var, width=15).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Button(add_cat_frame, text="Add Category", command=self.add_category).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Budget tips
        tips_frame = ttk.LabelFrame(budget_actions_frame, text="Budget Tips")
        tips_frame.pack(fill=tk.X, padx=10, pady=20)
        
        tips_text = """
        1. Allocate 50-30-20 of income to needs, wants, and savings
        2. Track expenses daily for better awareness
        3. Review and adjust budgets monthly
        4. Set specific financial goals
        5. Create an emergency fund
        """
        tk.Label(tips_frame, text=tips_text, justify=tk.LEFT).pack(padx=10, pady=10)
    
    def setup_upi_tab(self):
        """Set up the UPI payments tab"""
        # Title
        tk.Label(self.upi_frame, text="UPI Payments", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Left side - Payment creation
        payment_frame = ttk.LabelFrame(self.upi_frame, text="Create UPI Payment")
        payment_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Payment form
        form_frame = ttk.Frame(payment_frame)
        form_frame.pack(fill=tk.X, padx=10, pady=20)
        
        tk.Label(form_frame, text="Amount:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        self.upi_amount_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.upi_amount_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=5, pady=10)
        
        tk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        self.upi_description_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.upi_description_var, width=30).grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)
        
        ttk.Button(form_frame, text="Generate QR Code", command=self.generate_upi_qr).grid(row=2, column=0, columnspan=2, pady=10)
        
        # QR display area
        self.qr_frame = ttk.LabelFrame(payment_frame, text="Scan QR Code to Pay")
        self.qr_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.qr_label = tk.Label(self.qr_frame, text="Generate a QR code to make a payment")
        self.qr_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Transaction status
        status_frame = ttk.Frame(payment_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(status_frame, text="Check Payment Status", command=self.check_payment_status).pack(side=tk.LEFT, padx=10)
        self.status_label = tk.Label(status_frame, text="No active transaction")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Right side - Transaction history
        history_frame = ttk.LabelFrame(self.upi_frame, text="UPI Transaction History")
        history_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Transaction history treeview
        self.transactions_tree = ttk.Treeview(
            history_frame,
            columns=("ID", "Date", "Amount", "Description", "Status"),
            show="headings"
        )
        
        self.transactions_tree.heading("ID", text="Transaction ID")
        self.transactions_tree.heading("Date", text="Date")
        self.transactions_tree.heading("Amount", text="Amount")
        self.transactions_tree.heading("Description", text="Description")
        self.transactions_tree.heading("Status", text="Status")
        
        self.transactions_tree.column("ID", width=100)
        self.transactions_tree.column("Date", width=100)
        self.transactions_tree.column("Amount", width=80)
        self.transactions_tree.column("Description", width=150)
        self.transactions_tree.column("Status", width=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Current transaction ID
        self.current_transaction_id = None
        
    def generate_upi_qr(self):
        """Generate a UPI QR code for payment"""
        try:
            amount = float(self.upi_amount_var.get())
            description = self.upi_description_var.get()
            
            if amount <= 0:
                messagebox.showerror("Invalid Amount", "Please enter a valid amount greater than zero.")
                return
            
            if not description:
                description = "Expense Tracker Payment"
            
            # Generate QR code
            qr_img, transaction_id = self.upi_manager.create_payment_request(amount, description)
            
            if qr_img and transaction_id:
                # Save the current transaction ID
                self.current_transaction_id = transaction_id
                
                # Convert PIL image to Tkinter PhotoImage
                qr_img = qr_img.resize((300, 300))  # Resize to fit
                self.qr_photo = ImageTk.PhotoImage(qr_img)
                
                # Update QR display
                self.qr_label.config(image=self.qr_photo)
                self.qr_label.image = self.qr_photo  # Keep a reference
                
                # Update status label
                self.status_label.config(text="Transaction pending")
                
                # Show success message
                messagebox.showinfo("QR Code Generated", "Scan the QR code with any UPI app to make payment.")
            else:
                messagebox.showerror("Error", "Failed to generate UPI QR code.")
        
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid amount.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def check_payment_status(self):
        """Check the status of the current UPI transaction"""
        if not self.current_transaction_id:
            messagebox.showinfo("No Transaction", "No active transaction to check.")
            return
        
        # Check status with UPI manager
        success = self.upi_manager.check_transaction_status(self.current_transaction_id)
        
        if success:
            self.status_label.config(text="Payment successful")
            messagebox.showinfo("Payment Status", "Payment completed successfully!")
            
            # Add as expense if successful
            transaction = self.db_manager.get_transaction_details(self.current_transaction_id)
            if transaction:
                # Ask which category to assign
                categories = self.db_manager.get_categories()
                category_names = [cat[1] for cat in categories]
                category_id_map = {cat[1]: cat[0] for cat in categories}
                
                category = simpledialog.askstring(
                    "Select Category", 
                    "Select a category for this expense:",
                    initialvalue=category_names[0] if category_names else ""
                )
                
                if category and category in category_id_map:
                    # Add expense record
                    self.db_manager.add_expense(
                        transaction[1],  # amount
                        transaction[2],  # description
                        category_id_map[category],  # category_id
                        transaction[4],  # date
                        "UPI",  # payment_method
                        transaction[0]   # transaction_id
                    )
                    
                    # Refresh expenses
                    self.load_expenses()
                    self.update_dashboard()
            
            # Reset current transaction
            self.current_transaction_id = None
            self.qr_label.config(image="")
            self.qr_label.config(text="Generate a QR code to make a payment")
        else:
            self.status_label.config(text="Payment pending")
            messagebox.showinfo("Payment Status", "Payment is still pending. Try checking again after a few moments.")
    
    def update_dashboard(self):
        """Update the dashboard data and charts"""
        # Get date range from dashboard filters
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        
        # Get category totals
        category_totals = self.db_manager.get_category_totals(start_date, end_date)
        
        # Update summary treeview
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        total_spent = 0
        total_budget = 0
        
        for category, spent, budget in category_totals:
            spent = float(spent) if spent else 0
            budget = float(budget) if budget else 0
            remaining = budget - spent
            remaining_str = f"{remaining:.2f}" if remaining >= 0 else f"({abs(remaining):.2f})"
            
            self.summary_tree.insert("", "end", values=(
                category,
                f"{spent:.2f}",
                f"{budget:.2f}",
                remaining_str
            ))
            
            total_spent += spent
            total_budget += budget
        
        # Add total row
        total_remaining = total_budget - total_spent
        total_remaining_str = f"{total_remaining:.2f}" if total_remaining >= 0 else f"({abs(total_remaining):.2f})"
        
        self.summary_tree.insert("", "end", values=(
            "TOTAL",
            f"{total_spent:.2f}",
            f"{total_budget:.2f}",
            total_remaining_str
        ))
        
        # Update charts
        self.update_charts(category_totals)
    
    def update_charts(self, category_totals):
        """Update the charts in the dashboard"""
        # Clear previous charts
        self.fig.clear()
        
        # Skip if no data
        if not category_totals:
            self.canvas.draw()
            return
        
        # Extract data
        categories = [cat[0] for cat in category_totals]
        spent = [float(cat[1]) if cat[1] else 0 for cat in category_totals]
        budgets = [float(cat[2]) if cat[2] else 0 for cat in category_totals]
        
        # Create subplots
        ax1 = self.fig.add_subplot(211)  # Pie chart
        ax2 = self.fig.add_subplot(212)  # Bar chart
        
        # Pie chart - Expense distribution
        if sum(spent) > 0:  # Only create chart if there are expenses
            ax1.pie(
                spent, 
                labels=categories, 
                autopct='%1.1f%%',
                startangle=90
            )
            ax1.set_title('Expense Distribution')
        else:
            ax1.text(0.5, 0.5, 'No expenses to display', ha='center', va='center')
            ax1.axis('off')
        
        # Bar chart - Budget vs Actual
        x = range(len(categories))
        width = 0.35
        
        ax2.bar(x, budgets, width, label='Budget')
        ax2.bar([i + width for i in x], spent, width, label='Spent')
        
        ax2.set_title('Budget vs Actual Spending')
        ax2.set_xticks([i + width/2 for i in x])
        ax2.set_xticklabels(categories, rotation=45, ha='right')
        ax2.legend()
        
        # Adjust layout and draw
        self.fig.tight_layout()
        self.canvas.draw()
    
    def load_expenses(self):
        """Load expenses data based on filters"""
        # Get filter values
        start_date = self.expense_start_date_var.get() if self.expense_start_date_var.get() else None
        end_date = self.expense_end_date_var.get() if self.expense_end_date_var.get() else None
        
        # Get selected category ID
        category_id = None
        if self.expense_category_var.get():
            categories = self.db_manager.get_categories()
            category_id_map = {cat[1]: cat[0] for cat in categories}
            if self.expense_category_var.get() in category_id_map:
                category_id = category_id_map[self.expense_category_var.get()]
        
        # Clear existing data
        for item in self.expenses_tree.get_children():
            self.expenses_tree.delete(item)
        
        # Fetch expenses
        expenses = self.db_manager.get_expenses(start_date, end_date, category_id)
        
        # Populate treeview
        for expense in expenses:
            self.expenses_tree.insert("", "end", values=(
                expense[0],  # ID
                expense[4],  # Date
                expense[3],  # Category name
                expense[2],  # Description
                f"{expense[1]:.2f}",  # Amount
                expense[5]   # Payment method
            ))
    
    def load_categories(self):
        """Load categories data"""
        # Load categories for dropdown in add expense tab
        categories = self.db_manager.get_categories()
        category_names = [cat[1] for cat in categories]
        
        self.category_combo['values'] = category_names
        if category_names:
            self.category_combo.current(0)
        
        # Load categories for filter in expenses tab
        self.expense_category_combo['values'] = [""] + category_names
        
        # Update budget management tab
        for item in self.budget_tree.get_children():
            self.budget_tree.delete(item)
            
        for category in categories:
            self.budget_tree.insert("", "end", values=(category[0], category[1], f"{category[2]:.2f}"))
    
    def clear_expense_filters(self):
        """Clear filters in expenses tab"""
        self.expense_start_date_var.set("")
        self.expense_end_date_var.set("")
        self.expense_category_var.set("")
        self.load_expenses()
    
    def add_expense(self):
        """Add a new expense"""
        try:
            # Validate input
            amount = float(self.amount_var.get())
            description = self.description_var.get()
            date = self.date_var.get()
            payment_method = self.payment_method_var.get()
            
            if amount <= 0:
                messagebox.showerror("Invalid Amount", "Please enter a valid amount greater than zero.")
                return
            
            if not description:
                messagebox.showerror("Missing Description", "Please enter a description.")
                return
            
            # Get category ID
            category_name = self.category_var.get()
            categories = self.db_manager.get_categories()
            category_id_map = {cat[1]: cat[0] for cat in categories}
            
            if category_name not in category_id_map:
                messagebox.showerror("Invalid Category", "Please select a valid category.")
                return
            
            category_id = category_id_map[category_name]
            
            # Add expense to database
            success = self.db_manager.add_expense(
                amount,
                description,
                category_id,
                date,
                payment_method
            )
            
            if success:
                messagebox.showinfo("Success", "Expense added successfully.")
                self.clear_form()
                self.load_expenses()
                self.update_dashboard()
            else:
                messagebox.showerror("Error", "Failed to add expense.")
                
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid amount.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def clear_form(self):
        """Clear the add expense form"""
        self.amount_var.set("")
        self.description_var.set("")
        self.date_var.set(datetime.date.today().strftime("%Y-%m-%d"))
        self.payment_method_var.set("Cash")
        
        # Reset to first category
        categories = self.db_manager.get_categories()
        if categories:
            self.category_var.set(categories[0][1])
    
    def pay_with_upi(self):
        """Switch to UPI tab to make a payment"""
        try:
            # Transfer details to UPI tab
            amount = self.amount_var.get()
            description = self.description_var.get()
            
            if amount and float(amount) > 0:
                self.upi_amount_var.set(amount)
            
            if description:
                self.upi_description_var.set(description)
            
            # Switch to UPI tab
            self.notebook.select(self.upi_frame)
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a valid amount.")
    
    def delete_expense(self):
        """Delete the selected expense"""
        selected_item = self.expenses_tree.selection()
        
        if not selected_item:
            messagebox.showinfo("No Selection", "Please select an expense to delete.")
            return
        
        expense_id = self.expenses_tree.item(selected_item[0], "values")[0]
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            "Are you sure you want to delete this expense?"
        )
        
        if confirm:
            success = self.db_manager.delete_expense(expense_id)
            
            if success:
                messagebox.showinfo("Success", "Expense deleted successfully.")
                self.load_expenses()
                self.update_dashboard()
            else:
                messagebox.showerror("Error", "Failed to delete expense.")
    
    def export_expenses(self):
        """Export expenses to CSV"""
        try:
            filename = simpledialog.askstring(
                "Export to CSV",
                "Enter filename for export:",
                initialvalue="expenses_export.csv"
            )
            
            if not filename:
                return
            
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            # Get expenses based on current filters
            start_date = self.expense_start_date_var.get() if self.expense_start_date_var.get() else None
            end_date = self.expense_end_date_var.get() if self.expense_end_date_var.get() else None
            
            # Get selected category ID
            category_id = None
            if self.expense_category_var.get():
                categories = self.db_manager.get_categories()
                category_id_map = {cat[1]: cat[0] for cat in categories}
                if self.expense_category_var.get() in category_id_map:
                    category_id = category_id_map[self.expense_category_var.get()]
            
            expenses = self.db_manager.get_expenses(start_date, end_date, category_id)
            
            # Write to CSV
            with open(filename, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(['ID', 'Amount', 'Description', 'Category', 'Date', 'Payment Method'])
                csvwriter.writerows(expenses)
            
            messagebox.showinfo("Export Successful", f"Expenses exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export expenses: {str(e)}")
    
    def update_budget(self):
        """Update the budget for the selected category"""
        selected_item = self.budget_tree.selection()
        
        if not selected_item:
            messagebox.showinfo("No Selection", "Please select a category to update.")
            return
        
        try:
            category_id = self.budget_tree.item(selected_item[0], "values")[0]
            new_budget = float(self.new_budget_var.get())
            
            if new_budget < 0:
                messagebox.showerror("Invalid Budget", "Budget cannot be negative.")
                return
            
            success = self.db_manager.update_category_budget(category_id, new_budget)
            
            if success:
                messagebox.showinfo("Success", "Budget updated successfully.")
                self.load_categories()
                self.update_dashboard()
                self.new_budget_var.set("")
            else:
                messagebox.showerror("Error", "Failed to update budget.")
        
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid budget amount.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def add_category(self):
        """Add a new expense category"""
        try:
            category_name = self.new_category_var.get()
            
            if not category_name:
                messagebox.showerror("Missing Name", "Please enter a category name.")
                return
            
            budget = float(self.initial_budget_var.get()) if self.initial_budget_var.get() else 0
            
            if budget < 0:
                messagebox.showerror("Invalid Budget", "Budget cannot be negative.")
                return
            
            success = self.db_manager.add_category(category_name, budget)
            
            if success:
                messagebox.showinfo("Success", "Category added successfully.")
                self.load_categories()
                self.new_category_var.set("")
                self.initial_budget_var.set("0")
            else:
                messagebox.showerror("Error", "Failed to add category. Category name might already exist.")
        
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid budget amount.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def main():
    """Run the expense tracker application"""
    import csv
    
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()
    
    # Close database connection when app closes
    app.db_manager.close()

if __name__ == "__main__":
    main() 