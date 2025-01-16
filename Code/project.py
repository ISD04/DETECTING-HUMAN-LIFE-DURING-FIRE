import cv2
import threading
import mysql.connector
from ultralytics import YOLO
from tkinter import *
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
from tkinter import messagebox
import re
import tkinter as tk
from tkinter import PhotoImage

# Load the YOLO model
model = YOLO("best.pt")  # Make sure the model path is correct
class_names = ["fire", "human", "smoke"]  # Replace with your class names

# Define class colors (fire: red, human: blue, smoke: white)
class_colors = {
    "fire": (0, 0, 255),    # Red
    "human": (255, 0, 0),   # Blue
    "smoke": (255, 255, 255)  # White
}

# Initialize the camera
camera = cv2.VideoCapture(0)  # Open the webcam (index 0 for default camera)

# Create a Tkinter window
root = Tk()
root.title("Determining Human Life in Fire")
# root.attributes("-fullscreen", True)  # Set window to fullscreen
# root.resizable(False, False)  # Disable resizing

# Set a modern look
style = ttk.Style()
style.configure("TButton",
                font=("Helvetica", 12),
                padding=10,
                relief="flat")
style.configure("TLabel", font=("Helvetica", 14))

# Global variables for navigation
current_page = None

# MySQL Database Connection
def connect_db():
    # Establish a connection to MySQL database
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        port="3306",
        database="fire_detection_system"
    )


# Create frames for sidebar and content area
sidebar_frame = Frame(root, width=200, bg="#34495e")
sidebar_frame.pack(side="left", fill="y")

content_frame = Frame(root, bg="#ecf0f1")
content_frame.pack(side="right", expand=True, fill="both")

# Create an image label for the content area
image_label = Label(content_frame, bd=5, relief="flat")
image_label.pack(expand=True, fill="both")
#C:\\Users\\akhil\\Downloads\\Human life in fire\\Human life in fire\\bg1.jpg
# Load the background image
background_image = Image.open("C:\\Users\\akhil\\Downloads\\Human life in fire\\Human life in fire\\bg1.jpg")  # Replace with the path to your image
background_image = background_image.resize((1024, 600), Image.ANTIALIAS)  # Resize to fit the image_label area
background_photo = ImageTk.PhotoImage(background_image)

# Configure the image label to display the background image
image_label.configure(image=background_photo)
image_label.image = background_photo  # Keep a reference to avoid garbage collection


# Add a control frame below the image label
control_frame = Frame(sidebar_frame, bg="#34495e")
control_frame.pack(pady=20, padx=10, fill="y")

# Global stop flag for live feed
stop_live_feed = False


# Function to display the live camera feed
def show_live_feed():
    global stop_live_feed

    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()
        
    ret, frame = camera.read()

    if not ret:
        print("Failed to grab frame")
        return

    # Perform object detection on the frame
    results = model(frame, conf=0.25)

    # Draw bounding boxes on the frame
    for box, cls in zip(results[0].boxes.xyxy, results[0].boxes.cls):
        x1, y1, x2, y2 = box.tolist()
        cls = int(cls)  # Convert class index to integer
        label = class_names[cls]  # Get class name from class index
        color = class_colors[label]  # Get the color for the detected class

        # Draw bounding box
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

        # Add label with black text inside bounding box
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        label_width, label_height = label_size

        # Calculate text position inside bounding box
        text_x = int(x1) + 5
        text_y = int(y1) + label_height + 5
        text_y = min(int(y2) - 5, text_y)

        # Draw filled rectangle for label background
        cv2.rectangle(frame, (text_x - 5, text_y - label_height - 5),
                      (text_x + label_width + 5, text_y + 5), color, -1)

        # Always use black text for labels
        cv2.putText(frame, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    # Convert frame to image for Tkinter
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    img_tk = ImageTk.PhotoImage(image=img)

    # Update the image label
    image_label.img_tk = img_tk  # Keep a reference to avoid garbage collection
    image_label.configure(image=img_tk)

    if stop_live_feed:
        return

    # Call the function again after a delay to update the feed
    root.after(10, show_live_feed)

def stop_feed():
    global stop_live_feed

    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()

    stop_live_feed = True

    # Release the camera
    camera.release()  # Stop capturing from the camera

    # Clear the image label
    image_label.configure(image=None)
    image_label.img_tk = None  # Clear the image reference to avoid memory issues

    # Call the function to display buttons again
    display_buttons()  # Ensure the "Back to Home" button is shown again

# Function to start live detection
def start_live_feed():
    global stop_live_feed

    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()

    # Reset the stop_live_feed flag to False to allow the feed to restart
    stop_live_feed = False

    # Clear the image label from previous frames
    image_label.configure(image=None)

    # Re-initialize the camera if it was released
    if not camera.isOpened():
        camera.open(0)  # Reopen the camera (index 0 for the default camera)

    # Start the live feed
    show_live_feed()  # Call show_live_feed to start capturing frames

    # Hide previous buttons and show the stop button
    for widget in control_frame.winfo_children():
        widget.pack_forget()

    stop_button = Button(control_frame, text="Stop Live Detection", command=stop_feed, bg="#e74c3c", fg="white", font=("Helvetica", 14), width=20)
    stop_button.pack(pady=20)

# Function to upload an image and detect objects
def upload_image():
    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()

    # Create a loading spinner
    spinner = ttk.Progressbar(image_label, mode='indeterminate')
    spinner.pack(pady=20)
    spinner.start()  # Start the spinner

    # Use a separate thread to handle the image upload and processing
    threading.Thread(target=process_image, args=(spinner,), daemon=True).start()

def process_image(spinner):
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.jfif")])
    if file_path:
        # Read the uploaded image
        image = cv2.imread(file_path)

        # Perform object detection on the uploaded image
        results = model(image, conf=0.25)

        # Draw bounding boxes on the image
        for box, cls in zip(results[0].boxes.xyxy, results[0].boxes.cls):
            x1, y1, x2, y2 = box.tolist()
            cls = int(cls)  # Convert class index to integer
            label = class_names[cls]  # Get class name from class index
            color = class_colors[label]  # Get the color for the detected class

            # Draw bounding box
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            # Add label with black text inside bounding box
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            label_width, label_height = label_size

            # Calculate text position inside bounding box
            text_x = int(x1) + 5
            text_y = int(y1) + label_height + 5
            text_y = min(int(y2) - 5, text_y)

            # Draw filled rectangle for label background
            cv2.rectangle(image, (text_x - 5, text_y - label_height - 5),
                          (text_x + label_width + 5, text_y + 5), color, -1)

            # Always use black text for labels
            cv2.putText(image, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        # Convert the image to RGB for display in Tkinter
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Define the desired width and height
        desired_width = 700  # Set desired width
        desired_height = 700  # Set desired height

        # Resize the image
        image_resized = cv2.resize(image_rgb, (desired_width, desired_height))

        # Convert resized image to a format that Tkinter can display
        img = Image.fromarray(image_resized)
        img_tk = ImageTk.PhotoImage(image=img)

        # Update the image label with the resized image
        image_label.img_tk = img_tk  # Keep a reference to avoid garbage collection
        image_label.configure(image=img_tk)

    # Stop the spinner after processing
    spinner.stop()
    spinner.destroy()  # Optionally remove the spinner from the UI
# Function to display the buttons
def display_buttons():
    for widget in control_frame.winfo_children():
        widget.destroy()

    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()

    # Add the "Start Live Detection" and "Upload Image" buttons
    start_button = Button(control_frame, text="Start Live Detection", command=start_live_feed, bg="#2ecc71", fg="white", font=("Helvetica", 14), width=20)
    start_button.pack(pady=20)

    upload_button = Button(control_frame, text="Upload Image", command=upload_image, bg="#2980b9", fg="white", font=("Helvetica", 14), width=20)
    upload_button.pack(pady=20)

    # Add the "Back to Home" button
    back_to_home_button = Button(control_frame, text="Back to Home", command=index_page, bg="#7f8c8d", fg="white", font=("Helvetica", 14), width=20)
    back_to_home_button.pack(pady=20)




def index_page():
    global current_page
    current_page = 'index'

    # Clear the current page
    for widget in control_frame.winfo_children():
        widget.destroy()

    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()
    welcome_text = Label(
        image_label,
        text="Welcome to Fire Detection System",
        font=("Helvetica", 30, "bold"),
        fg="#ecf0f1",
        bg="#2c3e50",
        padx=10,
        pady=10,
    )
    welcome_text.place(relx=0.5, rely=0.1, anchor="center")

    background_image = Image.open("C:\\Users\\akhil\\Downloads\\Human life in fire\\Human life in fire\\bg1.jpg")  # Replace with the path to your image
    background_image = background_image.resize((1024, 600), Image.ANTIALIAS)  # Resize to fit the image_label area
    background_photo = ImageTk.PhotoImage(background_image)
    

    image_label.configure(image=background_photo)
    image_label.image = background_photo
    # Clear the image label
    #image_label.configure(image=None)
    #image_label.img_tk = None  # Clear the image reference

    # Set background color for the entire root window
    root.configure(bg="#ecf0f1")  # Light gray background for the root window

    # Set the background for the control frame
    control_frame.configure(bg="#2c3e50")  # Dark background for the control frame

    # Add a large, welcoming label
    #welcome_label = Label(image_label, text="Welcome to Fire Detection System", font=("Helvetica", 30, "bold"), fg="#ecf0f1", bg="#2c3e50")
    #welcome_label.pack(pady=50)
   

    # Register button with stylish appearance
    register_button = Button(control_frame, text="Home", command=index_page, bg="#1abc9c", fg="white", font=("Helvetica", 16, "bold"), width=20, relief="flat")
    register_button.pack(pady=10, fill=BOTH, expand=False)

    # Register button with stylish appearance
    register_button = Button(control_frame, text="Register", command=register_user, bg="#3498db", fg="white", font=("Helvetica", 16, "bold"), width=20, relief="flat")
    register_button.pack(pady=10, fill=BOTH, expand=False)

    # Login button with stylish appearance
    login_button = Button(control_frame, text="Login", command=login_user, bg="#e74c3c", fg="white", font=("Helvetica", 16, "bold"), width=20, relief="flat")
    login_button.pack(pady=10, fill=BOTH, expand=False)
    

    # Ensure the control frame stretches to fill the entire screen
    control_frame.pack(fill=BOTH, expand=True)

    # Allow resizing of the root window
    root.resizable(True, True)  # Allow resizing of window



def register_user():
    global current_page
    current_page = 'register'

    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()

    # Add registration form widgets
    username_label = Label(image_label, text="Username:",bg="#3498db", fg="white",font=("Helvetica", 14))
    username_label.pack(pady=5)
    #username_label.place(relx=0.5, rely=0.5, anchor="center")
    username_entry = Entry(image_label, font=("Helvetica", 14))
    username_entry.pack(pady=5)
    #username_entry.place(relx=0.5, rely=0.5, anchor="center")

    password_label = Label(image_label, text="Password:",bg="#e74c3c", fg="white", font=("Helvetica", 14))
    password_label.pack(pady=5)
    #password_label.place(relx=0.5, rely=0.5, anchor="center")
    password_entry = Entry(image_label, show="*", font=("Helvetica", 14))
    password_entry.pack(pady=5)
    #password_entry.place(relx=0.5, rely=0.5, anchor="center")

    def validate_username(username):
        """
        Validates the username:
        - Must start with a letter.
        - Can contain letters, digits, underscores, or hyphens.
        - Must be at least 3 characters long.
        """
        pattern = r"^[a-zA-Z][a-zA-Z0-9_-]*$"
        return re.match(pattern, username) is not None and len(username) >= 3

  

    def validate_password(password):
        # Password must be at least 6 characters long and contain:
        # - at least one uppercase letter
        # - at least one lowercase letter
        # - at least one digit
        # - at least one special character
        if len(password) < 6:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"[0-9]", password):
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False
        return True

    def submit_registration():
        username = username_entry.get()
        password = password_entry.get()

        if username and password:
            if not validate_username(username):
                messagebox.showerror("Error", "Username Must start with a letter and Can contain letters, digits, underscores, or hyphens and must be at least 3 characters long..")
                return
            
            if not validate_password(password):
                messagebox.showerror("Error", "Password must be at least 6 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character.")
                return

            try:
                conn = connect_db()
                cursor = conn.cursor()

                # Check if user already exists
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    messagebox.showerror("Error", "Username already exists!")
                else:
                    # Insert user into database
                    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                    conn.commit()
                    messagebox.showinfo("Success", "Registration successful!")
                    index_page()  # Go back to the index page after successful registration
            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Database error: {err}")
            finally:
                cursor.close()
                conn.close()
        else:
            messagebox.showerror("Error", "Both fields are required!")

    submit_button = Button(image_label, text="Register", command=submit_registration, bg="#2ecc71", fg="white", font=("Helvetica", 14), width=20)
    submit_button.pack(pady=20)

    # Ensure the control frame stretches to fill the entire screen
    image_label.pack(fill=BOTH, expand=True)

# Register page



def login_user():
    global current_page
    current_page = 'login'

    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()

    # Add login form widgets
    username_label = Label(image_label, text="Username:", font=("Helvetica", 14))
    username_label.pack(pady=5)
    username_entry = Entry(image_label, font=("Helvetica", 14))
    username_entry.pack(pady=5)

    password_label = Label(image_label, text="Password:", font=("Helvetica", 14))
    password_label.pack(pady=5)
    password_entry = Entry(image_label, show="*", font=("Helvetica", 14))
    password_entry.pack(pady=5)

    def submit_login():
        username = username_entry.get()
        password = password_entry.get()

        if username and password:
            try:
                conn = connect_db()
                cursor = conn.cursor()

                # Check if user exists and the password is correct
                cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
                user = cursor.fetchone()
                if user:
                    user_home_page()  # Navigate to the user home page
                else:
                    messagebox.showerror("Error", "Invalid credentials!")

            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Database error: {err}")
            finally:
                cursor.close()
                conn.close()
        else:
            messagebox.showerror("Error", "Both fields are required!")

    submit_button = Button(image_label, text="Login", command=submit_login, bg="#2ecc71", fg="white", font=("Helvetica", 14), width=20)
    submit_button.pack(pady=20)





def user_home_page():
    global current_page
    current_page = 'user_home'

    # Clear the current page
    for widget in control_frame.winfo_children():
        widget.destroy()

    # Clear the current page
    for widget in image_label.winfo_children():
        widget.destroy()

    # Display user-specific buttons
    start_button = Button(control_frame, text="Start Live Detection", command=start_live_feed, bg="#2ecc71", fg="white", font=("Helvetica", 14), width=20)
    start_button.pack(pady=20)

    upload_button = Button(control_frame, text="Upload Image", command=upload_image, bg="#2980b9", fg="white", font=("Helvetica", 14), width=20)
    upload_button.pack(pady=20)

    logout_button = Button(control_frame, text="Logout", command=index_page, bg="#7f8c8d", fg="white", font=("Helvetica", 14), width=20)
    logout_button.pack(pady=20)

    # Ensure the control frame stretches to fill the entire screen
    control_frame.pack(fill=BOTH, expand=True)


# Start with the index page
index_page()

# Start the Tkinter event loop
root.mainloop()
