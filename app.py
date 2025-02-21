from flask import Flask, render_template, request, redirect, url_for, session, flash
from create_main import main  # Your function to handle the job application logic
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from create_motivation_lettre_2 import get_llm_response

from flask import render_template, request, session, flash, send_file
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
from io import BytesIO
from flask import send_file

import base64
from flask import jsonify


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

    if request.method == "POST":
        job_title = request.form.get("jobTitle", "").strip()
        your_name = request.form.get("yourName", "").strip()
        company_name = request.form.get("applyingCompany", "").strip()
        write_to = request.form.get("writeTo", "").strip()
        skills = request.form.get("skills", "").strip()
        role_type = request.form.get("roleType", "").strip()
        job_location = request.form.get("jobLocation", "").strip()
        today_date = datetime.today().strftime('%d/%m/%Y')
        langue = request.form.get("langue_lettre", "").strip()

        answer = get_llm_response(job_title, your_name, company_name, write_to, skills, role_type, job_location, today_date, langue=langue)
        print(answer)
        flash("Motivation letter generated successfully!", "success")

         # 2) Generate the PDF from the text
        pdf_base64 = generate_pdf_base64(answer)

              # Return both the text AND the PDF in JSON
        return jsonify({"letter_text": answer, "pdf_data": pdf_base64})

        # # --- Generate PDF ---
        # pdf = FPDF()
        # pdf.add_page()
        # pdf.set_font("Arial", size=11.5)

        # pdf.multi_cell(0, 8, answer.lstrip())
        # pdf_data = pdf.output(dest='S')

        # pdf_buffer = BytesIO(pdf_data.encode('latin-1'))
        # pdf_buffer.seek(0)

        # Encode PDF as Base64
        # pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
        # return jsonify({"pdf_data": pdf_base64})
    
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

    pdf.multi_cell(0, 8, letter_text.lstrip())
    
    # 'S' returns a string. We need to convert it to bytes before b64 encoding.
    pdf_str = pdf.output(dest='S')  # returns string in Python 3
    pdf_bytes = pdf_str.encode('latin-1', errors='ignore')  # or utf-8 if appropriate

    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    return pdf_base64


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    Handle new user registrations. If successful, prompt to login.
    """
    flash("To sign up, contact the administrator on LinkedIn (Mhamed BOUGUERRA).", "danger")
    # if request.method == "POST":
    #     username = request.form["username"].strip()
    #     password = request.form["password"].strip()
    #     confirm_password = request.form["confirm_password"].strip()

    #     users = load_users()

    #     if username in users:
    #         flash("Username already exists!", "danger")
    #     elif password != confirm_password:
    #         flash("Passwords do not match!", "danger")
    #     else:
    #         users[username] = {"password": password}
    #         save_users(users)
    #         flash("User registered successfully! You can now log in.", "success")
    #         return redirect(url_for("login"))

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

# -----------------------------------
# Run the App
# -----------------------------------
