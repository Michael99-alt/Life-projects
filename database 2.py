import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import pandas as pd

# -------------------
# Database Setup
# -------------------
def init_sales_db():
    """Initialize the SQLite database with a sales table if it doesn't exist."""
    conn = sqlite3.connect("sales.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    item_name TEXT,
                    quantity INTEGER,
                    price REAL,
                    total REAL,
                    date TEXT
                )''')
    conn.commit()
    conn.close()

init_sales_db()

# -------------------
# Sales Dashboard
# -------------------
class SalesApp:
    def __init__(self, master):
        self.master = master
        master.title("Sales Dashboard")
        master.geometry("750x450")

        # Header
        tk.Label(master, text="Sales Records", font=("Arial", 14, "bold")).pack(pady=10)

        # Table Frame
        self.tree = ttk.Treeview(master, columns=("ID", "Customer", "Item", "Qty", "Price", "Total", "Date"), show="headings")
        self.tree.pack(expand=True, fill="both", padx=10, pady=5)

        # Define column headings
        for col in ("ID", "Customer", "Item", "Qty", "Price", "Total", "Date"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Buttons
        frame = tk.Frame(master)
        frame.pack(pady=10)

        self.add_button = tk.Button(frame, text="Add Sale", command=self.add_sale_window)
        self.add_button.grid(row=0, column=0, padx=10)

        self.export_button = tk.Button(frame, text="Export to Excel", command=self.export_to_excel)
        self.export_button.grid(row=0, column=1, padx=10)

        self.load_sales_data()

    def load_sales_data(self):
        """Load sales data into the table."""
        self.tree.delete(*self.tree.get_children())  # Clear existing records
        conn = sqlite3.connect("sales.db")
        c = conn.cursor()
        c.execute("SELECT * FROM sales")
        rows = c.fetchall()
        for row in rows:
            self.tree.insert("", "end", values=row)
        conn.close()

    def add_sale_window(self):
        """Open a window to add a new sale."""
        self.new_window = tk.Toplevel()
        self.new_window.title("Add Sale")

        # Labels and Entries
        tk.Label(self.new_window, text="Customer Name:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_customer = tk.Entry(self.new_window)
        self.entry_customer.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.new_window, text="Item Name:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_item = tk.Entry(self.new_window)
        self.entry_item.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.new_window, text="Quantity:").grid(row=2, column=0, padx=10, pady=5)
        self.entry_qty = tk.Entry(self.new_window)
        self.entry_qty.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(self.new_window, text="Price per Item:").grid(row=3, column=0, padx=10, pady=5)
        self.entry_price = tk.Entry(self.new_window)
        self.entry_price.grid(row=3, column=1, padx=10, pady=5)

        # Add Button
        self.add_btn = tk.Button(self.new_window, text="Add Sale", command=self.add_sale)
        self.add_btn.grid(row=4, column=0, columnspan=2, pady=10)

    def add_sale(self):
        """Save new sales data to the database."""
        customer = self.entry_customer.get().strip()
        item = self.entry_item.get().strip()
        qty = self.entry_qty.get().strip()
        price = self.entry_price.get().strip()

        if not customer or not item or not qty or not price:
            messagebox.showerror("Error", "All fields are required!")
            return

        if not qty.isnumeric() or not price.replace('.', '', 1).isdigit():
            messagebox.showerror("Error", "Quantity must be a number and Price must be a valid decimal!")
            return

        qty = int(qty)
        price = float(price)
        total = qty * price
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("sales.db")
        c = conn.cursor()
        c.execute("INSERT INTO sales (customer_name, item_name, quantity, price, total, date) VALUES (?, ?, ?, ?, ?, ?)",
                  (customer, item, qty, price, total, date_time))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Sale added successfully!")
        self.new_window.destroy()
        self.load_sales_data()  # Refresh table

    def export_to_excel(self):
        """Export sales data to an Excel file."""
        conn = sqlite3.connect("sales.db")
        c = conn.cursor()
        c.execute("SELECT * FROM sales")
        data = c.fetchall()
        conn.close()

        if not data:
            messagebox.showerror("Error", "No sales data to export!")
            return

        df = pd.DataFrame(data, columns=["ID", "Customer Name", "Item Name", "Quantity", "Price", "Total", "Date"])
        
        folder_selected = filedialog.askdirectory()
        if not folder_selected:
            return  # User canceled

        save_path = f"{folder_selected}/sales_data.xlsx"
        df.to_excel(save_path, index=False)

        messagebox.showinfo("Success", f"Sales data exported to:\n{save_path}")

# -------------------
# Open Sales Dashboard After Login
# -------------------
def open_sales_dashboard():
    """Open the sales dashboard after login."""
    root = tk.Tk()
    app = SalesApp(root)
    root.mainloop()

# -------------------
# Run the Application
# -------------------
if __name__ == "__main__":
    open_sales_dashboard()
