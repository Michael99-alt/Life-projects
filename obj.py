import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import sqlite3
import cv2
import numpy as np
import time
import pandas as pd
import datetime

# --- Initialize Databases --- #

# Sales Database Setup (Tracking sales)
def init_sales_db():
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

# User Database Setup (Login system)
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

init_sales_db()
init_db()

# Object Detection System (with billing logic)
def object_detection_and_billing_system():
    thres = 0.45  # Confidence threshold
    nms_threshold = 0.2
    cap = cv2.VideoCapture(0)

    # Load class names from coco.names file
    classNames = []
    classFile = 'coco.names'
    with open(classFile, 'rt') as f:
        classNames = f.read().rstrip('\n').split('\n')

    # Define objects of interest and prices
    items_of_interest = {"bottle", "book", "toothbrush"}
    items_prices = {"bottle": 5, "book": 10, "toothbrush": 3}

    detected_items = {}  # Stores item counts
    seen_items = set()   # Ensures each item is counted only once
    last_detected_item = None  # Tracks the last detected item

    weightsPath = 'frozen_inference_graph.pb'
    configPath = 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'

    # Load pre-trained model
    net = cv2.dnn_DetectionModel(weightsPath, configPath)
    net.setInputSize(320, 320)
    net.setInputScale(1.0 / 127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)

    prev_time = 0
    while True:
        success, img = cap.read()
        if not success:
            break

        classIds, confs, bbox = net.detect(img, confThreshold=thres)
        if classIds is not None:
            if isinstance(classIds, np.ndarray) and len(classIds) > 0:
                indices = cv2.dnn.NMSBoxes(bbox, confs, thres, nms_threshold)

                if len(indices) > 0:
                    indices = indices.flatten()

                    for i in indices:
                        classId = int(classIds[i]) if isinstance(classIds, np.ndarray) else int(classIds)
                        confidence = float(confs[i]) if isinstance(confs, np.ndarray) else float(confs)
                        box = bbox[i]

                        class_name = classNames[classId - 1].lower()

                        if class_name in items_of_interest and confidence > thres:
                            cv2.rectangle(img, box, (0, 255, 0), 2)
                            cv2.putText(img, f"{class_name.upper()} ({confidence:.2f})",
                                       (box[0] + 10, box[1] + 30),
                                       cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 0), 2)

                            if class_name not in seen_items:
                                detected_items[class_name] = detected_items.get(class_name, 0) + 1
                                seen_items.add(class_name)
                                last_detected_item = class_name

        height, width = img.shape[:2]
        panel_width = 320
        white_panel = np.ones((height, panel_width, 3), dtype=np.uint8) * 255

        cv2.putText(white_panel, "Invoice", (100, 40),
                   cv2.FONT_HERSHEY_TRIPLEX, 0.8, (0, 0, 255), 2)

        y_position = 80
        total = 0
        for item, count in detected_items.items():
            price = items_prices[item]
            item_total = price * count
            total += item_total
            cv2.putText(white_panel, f"{item}: {count} x ${price} = ${item_total}",
                       (20, y_position), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
            y_position += 30

        cv2.putText(white_panel, f"Total: ${total}", (20, height - 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time
        cv2.putText(img, f"FPS: {int(fps)}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        combined = np.hstack((img, white_panel))
        cv2.imshow("Object Detection & Billing System", combined)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        cap.release()
cv2.destroyAllWindows()

# ------------------- User Login System ------------------- #
class LoginApp:
    def __init__(self, master):
        self.master = master
        master.title("Login System")

        # Username and Password fields
        tk.Label(master, text="Username:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_username = tk.Entry(master)
        self.entry_username.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(master, text="Password:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_password = tk.Entry(master, show="*")
        self.entry_password.grid(row=1, column=1, padx=10, pady=5)

        self.btn_login = tk.Button(master, text="Login", command=self.login)
        self.btn_login.grid(row=2, column=0, columnspan=2, pady=10)

        self.btn_register = tk.Button(master, text="Create Account", command=self.open_register_window)
        self.btn_register.grid(row=3, column=0, columnspan=2, pady=5)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        result = c.fetchone()
        conn.close()

        if result:
            messagebox.showinfo("Login Successful", "Welcome!")
            self.master.destroy()
            object_detection_and_billing_system()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def open_register_window(self):
        RegisterWindow()

# ------------------- Register Window ------------------- #
class RegisterWindow:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Create Account")

        tk.Label(self.window, text="New Username:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_username = tk.Entry(self.window)
        self.entry_username.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.window, text="New Password:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_password = tk.Entry(self.window, show="*")
        self.entry_password.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Employer Password:").grid(row=2, column=0, padx=10, pady=5)
        self.entry_employer_password = tk.Entry(self.window, show="*")
        self.entry_employer_password.grid(row=2, column=1, padx=10, pady=5)

        self.btn_register = tk.Button(self.window, text="Register", command=self.register_user)
        self.btn_register.grid(row=3, column=0, columnspan=2, pady=10)

    def register_user(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        employer_password = self.entry_employer_password.get()

        if employer_password != "555":
            messagebox.showerror("Error", "Incorrect Employer Password!")
            return

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone():
            messagebox.showerror("Error", "Username already taken!")
        else:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Account created successfully!")
            self.window.destroy()

        conn.close()

# ------------------- Running the Application ------------------- #
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
