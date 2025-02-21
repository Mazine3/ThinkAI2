from flask import Flask, render_template, request, redirect, url_for, session, flash
from create_main import main  # Your function to handle the job application logic
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

PORT = os.getenv('PORT','')
DEBUG = os.getenv('DEBUG', '')
SECRET_KEY = os.getenv('secret_key', 'mysecretkey')  # Provide default if not found

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configurations
data_file = "users.json"
upload_folder = "upload_files"
app.config['UPLOAD_FOLDER'] = upload_folder
app.permanent_session_lifetime = timedelta(minutes=30)

# Create upload folder if not exists
os.makedirs(upload_folder, exist_ok=True)

# -----------------------------------
# Helper Functions
# -----------------------------------
def login_required(f):
    """
    Decorator to ensure a user is logged in.
    If not logged in, they are redirected to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_users():
    """Load users from a JSON file."""
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    """Save users to a JSON file."""
    with open(data_file, "w") as file:
        json.dump(users, file, indent=4)

# -----------------------------------
# Routes
# -----------------------------------
@app.route("/")
def home():
    """
    Home route. If user is logged in, redirect to application page.
    Otherwise, redirect to login. """
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login. If successful, redirect to job application.
    If not, flash an error message.
    """
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        users = load_users()

        if username in users and users[username]["password"] == password:
            session["username"] = username
            return redirect(url_for("features"))
        else:
            flash("Invalid username or password!", "danger")

    return render_template("login.html")

@app.route("/features")
@login_required
def features():
    # The new page after successful login
    return render_template("features.html", username=session["username"])

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    Handle new user registrations. If successful, prompt to login.
    """
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form["confirm_password"].strip()

        users = load_users()

        if username in users:
            flash("Username already exists!", "danger")
        elif password != confirm_password:
            flash("Passwords do not match!", "danger")
        else:
            users[username] = {"password": password}
            save_users(users)
            flash("User registered successfully! You can now log in.", "success")
            return redirect(url_for("login"))

    return render_template("signup.html")
    

@app.route("/profile")
@login_required
def profile():
    # Example user data (in reality, fetch from DB or session)
    user_info = {
        "initials": "MB",
        "full_name": "Mhamed BOUGUERRA",
        "email": "mhamedbouguerra@gmail.com"
    }
    return render_template("profile.html", user=user_info)


@app.route("/job_application", methods=["GET", "POST"])
@login_required
def job_application():
    """
    Main application form for job application.
    After submission, calls `main()` function from 'create_main.py'.
    """
    username = session["username"]

    if request.method == "POST":
        tj_username = request.form["tj_username"].strip()
        tj_password = request.form["tj_password"].strip()
        language = request.form["language"].strip()
        full_name = request.form["full_name"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()
        location = request.form["location"].strip()
        poste = request.form["poste_recherche"].strip()

        pdf_file = request.files["pdf_file"]
        today_date = datetime.today().strftime('%d/%m/%Y')

        if all([tj_username, tj_password, full_name, phone, email, location]) and pdf_file:

            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
            pdf_file.save(pdf_path)


            main(
                tj_username,
                tj_password,
                full_name,
                location,
                phone,
                today_date,
                language,
                pdf_path,
                poste)
            
            flash("Your application has been submitted!", "success")
        else:
            flash("Please fill in all required fields.", "danger")

    return render_template("job_application.html", username=username)

@app.route("/logout")
def logout():
    """
    Clear the session and redirect to login.
    """
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# -----------------------------------
# Run the App
# -----------------------------------
if __name__ == "__main__":
    app.run(debug=DEBUG, port=PORT)