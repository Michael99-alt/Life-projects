import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import pandas as pd
import cv2
import numpy as np
import time
import threading
import hashlib
import sqlite3

def save_to_sales_db(customer_name, detected_items, items_prices):
    """Save sales data to the sales database."""
    conn = sqlite3.connect("sales.db")
    c = conn.cursor()

    # Record each item sold in the database
    for item, quantity in detected_items.items():
        price = items_prices.get(item, 0)
        total = price * quantity
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute('''INSERT INTO sales (customer_name, item_name, quantity, price, total, date)
                     VALUES (?, ?, ?, ?, ?, ?)''', 
                     (customer_name, item, quantity, price, total, date))

    conn.commit()
    conn.close()

# -------------------
# Database Setup for Users
# -------------------
def init_db():
    """Initialize the SQLite database with a users table if it doesn't exist."""
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# -------------------
# Password Hashing
# -------------------
def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------
# Login Window
# -------------------
class LoginApp:
    def __init__(self, master):
        self.master = master
        master.title("Login System")

        # Username
        tk.Label(master, text="Username:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_username = tk.Entry(master)
        self.entry_username.grid(row=0, column=1, padx=10, pady=5)

        # Password
        tk.Label(master, text="Password:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_password = tk.Entry(master, show="*")
        self.entry_password.grid(row=1, column=1, padx=10, pady=5)

        # Login Button
        self.btn_login = tk.Button(master, text="Login", command=self.login)
        self.btn_login.grid(row=2, column=0, columnspan=2, pady=10)

        # Register Button
        self.btn_register = tk.Button(master, text="Create Account", command=self.open_register_window)
        self.btn_register.grid(row=3, column=0, columnspan=2, pady=5)

    def login(self):
        """Check username and password against the database."""
        username = self.entry_username.get()
        password = self.entry_password.get()

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
        result = c.fetchone()
        conn.close()

        if result:
            messagebox.showinfo("Login Successful", "Welcome!")
            self.master.destroy()  # Close login window
            open_main_app()  # Open main application
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def open_register_window(self):
        """Open the registration window."""
        RegisterWindow()

# -------------------
# Registration Window
# -------------------
class RegisterWindow:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Create Account")

        # Username
        tk.Label(self.window, text="New Username:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_username = tk.Entry(self.window)
        self.entry_username.grid(row=0, column=1, padx=10, pady=5)

        # Password
        tk.Label(self.window, text="New Password:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_password = tk.Entry(self.window, show="*")
        self.entry_password.grid(row=1, column=1, padx=10, pady=5)

        # Employer Password
        tk.Label(self.window, text="Employer Password:").grid(row=2, column=0, padx=10, pady=5)
        self.entry_employer_password = tk.Entry(self.window, show="*")
        self.entry_employer_password.grid(row=2, column=1, padx=10, pady=5)

        # Register Button
        self.btn_register = tk.Button(self.window, text="Register", command=self.register_user)
        self.btn_register.grid(row=3, column=0, columnspan=2, pady=10)

    def register_user(self):
        """Register a new user if employer password is correct."""
        username = self.entry_username.get()
        password = self.entry_password.get()
        employer_password = self.entry_employer_password.get()

        if employer_password != "555":
            messagebox.showerror("Error", "Incorrect Employer Password!")
            return

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        # Check if username already exists
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone():
            messagebox.showerror("Error", "Username already taken!")
        else:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
            conn.commit()
            messagebox.showinfo("Success", "Account created successfully!")
            self.window.destroy()  # Close the registration window

        conn.close()

# -------------------
# Main Application (after login)
# -------------------
def reset_user_db():
    """Reset the users database (delete all records in the users table)."""
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM users")  # Deletes all rows from the users table
    conn.commit()
    conn.close()
    messagebox.showinfo("Database Reset", "User database has been reset.")
def open_main_app():
    """This function simulates the main application after login."""
    main_window = tk.Tk()
    main_window.title("Main Application")
    main_window.geometry("400x300")  # Set window size

    # Start Object Detection in a separate thread
    threading.Thread(target=start_object_detection, daemon=True).start()

    # Add a "Reset User Database" button to the main window
    reset_db_button = tk.Button(main_window, text="Reset User Database", command=reset_user_db)
    reset_db_button.pack(pady=20)  # Adds padding around the button

    # Add a label to make sure something shows up on the screen
    tk.Label(main_window, text="Welcome to the System!", font=("Arial", 14)).pack(pady=20)
    tk.Button(main_window, text="Open Sales Dashboard", command=open_sales_dashboard).pack(pady=10)
    tk.Button(main_window, text="Exit", command=main_window.destroy).pack(pady=10)

    main_window.mainloop()


# -------------------
# Object Detection and Billing
# -------------------
def start_object_detection():
    """Function to start object detection in a separate thread."""
    thres = 0.45  # Confidence threshold
    nms_threshold = 0.2
    cap = cv2.VideoCapture(0)

    # Load class names from coco.names file
    classNames = []
    classFile = r'C:\Users\analo\object detection model\coco.names'  # Ensure this path is correct
    with open(classFile, 'rt') as f:
        classNames = f.read().rstrip('\n').split('\n')

    # Define objects of interest and prices
    items_of_interest = {"bottle", "book", "toothbrush"}
    items_prices = {"bottle": 5, "book": 10, "toothbrush": 3}

    # Tracking detected items
    detected_items = {}  # Stores item counts
    seen_items = set()   # Ensures each item is counted only once
    last_detected_item = None  # Tracks the last detected item

    # Load model files (Ensure these paths are correct)
    weightsPath = r'C:\Users\analo\object detection model\frozen_inference_graph.pb'
    configPath = r'C:\Users\analo\object detection model\ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'

    # Load the pre-trained model
    net = cv2.dnn_DetectionModel(weightsPath, configPath)
    net.setInputSize(320, 320)
    net.setInputScale(1.0 / 127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)

    # Initialize FPS counter
    prev_time = 0

    while True:
        success, img = cap.read()
        if not success:
            break

        # Detect objects
        classIds, confs, bbox = net.detect(img, confThreshold=thres)

        if classIds is not None:
            if isinstance(classIds, np.ndarray) and len(classIds) > 0:
                indices = cv2.dnn.NMSBoxes(bbox, confs, thres, nms_threshold)

                if len(indices) > 0:
                    indices = indices.flatten()  # Flatten indices array

                    for i in indices:
                        classId = int(classIds[i]) if isinstance(classIds, np.ndarray) else int(classIds)
                        confidence = float(confs[i]) if isinstance(confs, np.ndarray) else float(confs)
                        box = bbox[i]

                        class_name = classNames[classId - 1].lower()

                        if class_name in items_of_interest and confidence > thres:
                            # Draw bounding box and label
                            cv2.rectangle(img, box, (0, 255, 0), 2)
                            cv2.putText(img, f"{class_name.upper()} ({confidence:.2f})",
                                       (box[0] + 10, box[1] + 30),
                                       cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 0), 2)

                            # **Prevent Multiple Counting**
                            if class_name not in seen_items:
                                detected_items[class_name] = detected_items.get(class_name, 0) + 1
                                seen_items.add(class_name)  # Mark as counted
                                last_detected_item = class_name  # Store last detected item

        # Create invoice panel
        height, width = img.shape[:2]
        panel_width = 320
        white_panel = np.ones((height, panel_width, 3), dtype=np.uint8) * 255

        # Invoice Header
        cv2.putText(white_panel, "Invoice", (100, 40),
                   cv2.FONT_HERSHEY_TRIPLEX, 0.8, (0, 0, 255), 2)

        # Display detected items and prices
        y_position = 80
        total = 0
        for item, count in detected_items.items():
            price = items_prices[item]
            item_total = price * count
            total += item_total
            cv2.putText(white_panel, f"{item}: {count} x ${price} = ${item_total}",
                       (20, y_position), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
            y_position += 30

        # Display total cost
        cv2.putText(white_panel, f"Total: ${total}", (20, height - 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        # FPS Counter
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time
        cv2.putText(img, f"FPS: {int(fps)}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Combine main frame and invoice panel
        combined = np.hstack((img, white_panel))
        cv2.imshow("Object Detection & Billing System", combined)

        # Handle key presses
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('c'):  # Reset counts
            detected_items.clear()
            seen_items.clear()  # Reset seen items as well
            last_detected_item = None
        elif key == 13:  # Enter key to increase quantity
            if last_detected_item:
                detected_items[last_detected_item] += 1
        elif key == ord('s'):  # Save invoice to database when 's' is pressed
            customer_name = "Customer"  # You can get the customer name from another part of your system
            save_to_sales_db(customer_name, detected_items, items_prices)
            detected_items.clear()  # Reset the detected items after saving
            seen_items.clear()

    cap.release()
    cv2.destroyAllWindows()

# -------------------
# Sales Dashboard (After Object Detection)
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

class SalesApp:
    def __init__(self, master):
        self.master = master
        master.title("Sales Dashboard")
        master.geometry("750x450")

        # Header
        tk.Label(master, text="Sales Records", font=("Arial", 14, "bold")).pack(pady=10)

        # Table Frame
        self.tree = ttk.Treeview(master, columns=("ID", "Customer", "Item", "Qty", "Price", "Total", "Date"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Customer", text="Customer")
        self.tree.heading("Item", text="Item")
        self.tree.heading("Qty", text="Qty")
        self.tree.heading("Price", text="Price")
        self.tree.heading("Total", text="Total")
        self.tree.heading("Date", text="Date")
        self.tree.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Load sales records into table
        self.load_sales_data()

        # Buttons
        self.btn_export = tk.Button(master, text="Export to CSV", command=self.export_to_csv)
        self.btn_export.pack(pady=10)

        self.btn_back = tk.Button(master, text="Back to Main", command=master.destroy)
        self.btn_back.pack(pady=5)

    def load_sales_data(self):
        """Load sales data from the database into the table."""
        conn = sqlite3.connect("sales.db")
        c = conn.cursor()
        c.execute("SELECT * FROM sales")
        rows = c.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def export_to_csv(self):
        """Export the sales data to a CSV file."""
        rows = []
        for row in self.tree.get_children():
            rows.append(self.tree.item(row)["values"])

        if rows:
            filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if filename:
                df = pd.DataFrame(rows, columns=["ID", "Customer", "Item", "Qty", "Price", "Total", "Date"])
                df.to_csv(filename, index=False)
                messagebox.showinfo("Export Successful", "Sales data exported to CSV.")

def open_sales_dashboard():
    """Open the Sales Dashboard window."""
    sales_window = tk.Tk()
    SalesApp(sales_window)
    sales_window.mainloop()

# -------------------
# Start the Login App
# -------------------
def start():
    """Initialize and run the login application."""
    root = tk.Tk()
    login_app = LoginApp(root)
    root.mainloop()

# Run the login system on startup
start()

