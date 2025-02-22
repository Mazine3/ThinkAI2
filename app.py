from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from fpdf import FPDF
import base64
from create_motivation_lettre_2 import get_llm_response
from create_main import main


load_dotenv()

PORT = os.getenv('PORT','')
DEBUG = os.getenv('DEBUG', '')
SECRET_KEY = "my_secrt_key"
# os.getenv('secret_key', 'mysecretkey')  # Provide default if not found

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configurations
data_file = "./utils/users.json"
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


@app.route("/resume_page")
@login_required
def resume_page():
    # The new page after successful login
    return render_template("resume_page.html", username=session["username"])


@app.route("/motivation_letter", methods=["GET", "POST"])
@login_required
def motivation_letter():
    users = load_users()
    
    # Get the logged-in user from session
    username = session["username"]
    user_data = users.get(username, {})


    if request.method == "POST":

        # Check if user has enough credits
        current_credits = user_data.get("credits", 0)
        if current_credits < 20:
            # Not enough credits => return error JSON
            return jsonify({"error": "You do not have enough credits to generate a letter."}), 400
        
        # User has enough credits => subtract 20
        user_data["credits"] = current_credits - 20
        
        # Save back to users.json
        users[username] = user_data
        save_users(users)


        job_title = request.form.get("jobTitle", "").strip()
        your_name = request.form.get("yourName", "").strip()
        company_name = request.form.get("applyingCompany", "").strip()
        write_to = request.form.get("writeTo", "").strip()
        skills = request.form.get("skills", "").strip()
        role_type = request.form.get("roleType", "").strip()
        job_location = request.form.get("jobLocation", "").strip()
        today_date = datetime.today().strftime('%d/%m/%Y')
        langue = request.form.get("langue_lettre", "").strip()
        jb_offre = request.form.get("offerDescription", "").strip()

        answer = get_llm_response(job_title, your_name, company_name, write_to, skills, role_type, job_location, today_date, jb_offre, langue=langue)
        print(answer)
        flash("Motivation letter generated successfully!", "success")

         # 2) Generate the PDF from the text
        pdf_base64 = generate_pdf_base64(answer)

              # Return both the text AND the PDF in JSON
        return jsonify({"letter_text": answer, "pdf_data": pdf_base64})
    
    return render_template("motivation_letter.html", username=session["username"])

@app.route("/update_motivation_letter", methods=["POST"])
@login_required
def update_motivation_letter():
    """
    This route receives edited text, regenerates the PDF, and returns it.
    """
    edited_text = request.form.get("edited_text", "").strip()

    # Generate PDF from the edited text
    pdf_base64 = generate_pdf_base64(edited_text)

    # Return updated PDF
    return jsonify({
        "pdf_data": pdf_base64
    })



def generate_pdf_base64(letter_text: str) -> str:
    """
    Helper function that takes raw letter text, creates a PDF via FPDF,
    and returns base64-encoded PDF data.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11.5)


    safe_text = letter_text.encode('latin-1', errors='ignore').decode('latin-1')
    pdf.multi_cell(0, 8, safe_text)
    
    # 'S' returns a string. We need to convert it to bytes before b64 encoding.
    pdf_str = pdf.output(dest='S')  # returns string in Python 3
    pdf_bytes = pdf_str.encode('latin-1', errors='ignore')  # or utf-8 if appropriate

    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    return pdf_base64


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form["confirm_password"].strip()
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()

        users = load_users()

        # Check if username already exists
        if username in users:
            flash("Username already exists!", "danger")
            return redirect(url_for("signup"))

        # Check password match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("signup"))

        # Everything is OK, create new user
        users[username] = {
            "password": password,
            "full_name": full_name,
            "email": email,
            # Automatically assign 10 credits to every new user
            "credits": 10
        }

        save_users(users)
        flash("User registered successfully! You can now log in.", "success")
        return redirect(url_for("login"))
    
    # If GET request, just render signup form
    return render_template("signup.html")


@app.route("/modify_credits", methods=["POST"])
@login_required
def modify_credits():
    if session["username"] != "mhamed":
        flash("Not authorized!", "danger")
        return redirect(url_for("admin_panel"))

    users = load_users()
    username = request.form.get("username")
    credit_change = int(request.form.get("credit_change", "0"))

    if username in users:
        users[username]["credits"] = max(0, users[username].get("credits", 0) + credit_change)
        save_users(users)
        flash(f"Updated credits for {username}: {users[username]['credits']} credits.", "success")
    else:
        flash("User not found!", "danger")

    return redirect(url_for("admin_panel"))


@app.route("/profile")
@login_required
def profile():
    users = load_users()  # load the entire users.json
    username = session["username"]  # current logged-in user
    user_data = users.get(username, {})

    # Check if the user is the administrator (mhamed)
    is_admin = (username == "mhamed")

    # Prepare data for the current user
    name_parts = user_data.get("full_name", "Unknown User").split()
    initials = "".join(part[0] for part in name_parts).upper() if name_parts else "NA"
    
    user_info = {
        "username": username,
        "initials": initials,
        "full_name": user_data.get("full_name", "Unknown User"),
        "email": user_data.get("email", "no-email@example.com"),
        "credits": user_data.get("credits", 0),
        "is_admin": is_admin
    }

    # If admin, pass all users; otherwise, pass None
    all_users = users if is_admin else None

    return render_template("profile.html", user=user_info, all_users=all_users)


@app.route("/add_user", methods=["GET", "POST"])
@login_required
def add_user():
    # Only admin can access:
    if session["username"] != "mhamed":
        flash("Not authorized!", "danger")
        return redirect(url_for("profile"))
    
    if request.method == "POST":
        # Load users
        users = load_users()
        
        new_username = request.form.get("new_username", "").strip()
        new_password = request.form.get("new_password", "").strip()
        new_full_name = request.form.get("new_full_name", "").strip()
        new_email = request.form.get("new_email", "").strip()
        new_credits = request.form.get("new_credits", "0").strip()
        
        if not new_username or not new_password:
            flash("Username and password cannot be empty!", "danger")
            return redirect(url_for("profile"))

        if new_username in users:
            flash("User already exists!", "danger")
            return redirect(url_for("profile"))
        
        # Insert the new user
        users[new_username] = {
            "password": new_password,
            "full_name": new_full_name,
            "email": new_email,
            "credits": int(new_credits)
        }
        
        save_users(users)
        flash(f"New user '{new_username}' added successfully!", "success")
        return redirect(url_for("profile"))
    
    # If it's a GET request, you might want to show some form or redirect:
    return redirect(url_for("profile"))


@app.route("/admin_panel")
@login_required
def admin_panel():
    # Only admin can view
    if session["username"] != "mhamed":
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for("profile"))
    
    users = load_users()  # dict from JSON
    user_data = users.get("mhamed", {})  # or load the current session user
    name_parts = user_data.get("full_name", "Admin").split()
    initials = "".join(part[0] for part in name_parts).upper() if name_parts else "A"
    
    # For the admin user object
    admin_info = {
        "initials": initials,
        "full_name": user_data.get("full_name", "Administrator"),
        "email": user_data.get("email", ""),
        "is_admin": True,
        "credits": user_data.get("credits", 0)  # might not matter for admin
    }
    
    return render_template("admin_panel.html", user=admin_info, all_users=users)


@app.route("/delete_user", methods=["POST"])
@login_required
def delete_user():
    # Ensure only the admin can access this route
    if session["username"] != "mhamed":
        flash("Not authorized!", "danger")
        return redirect(url_for("profile"))

    # Load users
    users = load_users()

    # Get the username to delete from the form
    username_to_delete = request.form.get("username")

    if username_to_delete in users:
        del users[username_to_delete]
        save_users(users)
        flash(f"User {username_to_delete} deleted successfully!", "success")
    else:
        flash("User not found!", "danger")

    return redirect(url_for("profile"))


@app.route("/job_application", methods=["GET", "POST"])
@login_required
def job_application():
    """Job application form."""
    username = session["username"]

    if request.method == "POST":
        tj_username = request.form.get("tj_username", "").strip()
        tj_password = request.form.get("tj_password", "").strip()
        language = request.form.get("language", "").strip()
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        location = request.form.get("location", "").strip()
        poste = request.form.get("poste_recherche", "").strip()

        pdf_file = request.files.get("pdf_file")
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
                poste
            )

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
