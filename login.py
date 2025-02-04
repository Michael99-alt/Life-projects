import tkinter as tk
from tkinter import messagebox
import sqlite3

# -------------------
# Database Setup
# -------------------
def init_user_db():
    """Initialize the SQLite database with a user table if it doesn't exist."""
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

# Create an example user if the database is empty
def create_example_user():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    if not c.fetchall():  # If no users exist, create an example user
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "password123"))
        conn.commit()
    conn.close()

init_user_db()
create_example_user()

# -------------------
# Login System
# -------------------
class LoginApp:
    def __init__(self, master):
        self.master = master
        master.title("Login System")
        master.geometry("300x200")

        # Username Label and Entry
        tk.Label(master, text="Username:").pack(pady=10)
        self.entry_username = tk.Entry(master)
        self.entry_username.pack(pady=5)

        # Password Label and Entry
        tk.Label(master, text="Password:").pack(pady=10)
        self.entry_password = tk.Entry(master, show="*")
        self.entry_password.pack(pady=5)

        # Login Button
        self.login_button = tk.Button(master, text="Login", command=self.login)
        self.login_button.pack(pady=10)

    def login(self):
        """Authenticate user credentials."""
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password!")
            return

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            messagebox.showinfo("Success", "Login successful!")
            self.master.destroy()  # Close the login window
            self.open_dashboard()  # Open the dashboard after login
        else:
            messagebox.showerror("Error", "Invalid credentials! Please try again.")

    def open_dashboard(self):
        """Open the sales dashboard (for example, after successful login)."""
        dashboard_root = tk.Tk()
        dashboard_root.title("Sales Dashboard")
        dashboard_root.geometry("750x450")
        tk.Label(dashboard_root, text="Welcome to the Sales Dashboard", font=("Arial", 16)).pack(pady=20)
        dashboard_root.mainloop()

# -------------------
# Run the Application
# -------------------
if __name__ == "__main__":
    root = tk.Tk()
    login_app = LoginApp(root)
    root.mainloop()


