

# ---- STEP 1: Import the tools we need ----
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps                     # used to build our own decorator
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # where this file lives
filename = os.path.join(BASE_DIR, "students.db")        # the database file 

# ---- STEP 2: Create the Flask application ----
app = Flask(__name__)
app.secret_key = "student_registration_secret_key"   # needed for session + flash

DB_NAME = os.path.join(BASE_DIR, "students.db")

# ---- Admin credentials ----
# In a real production app these would live in a database or environment
# variables, never in plain code. For this mini project we keep ONE admin
# account, but we still HASH the password instead of storing it as plain
# text, so the technique is realistic and explainable.
ADMIN_USERNAME = "Senior Man"
ADMIN_PASSWORD_HASH = generate_password_hash("Seniorman237")   # login: admin / admin123


# ---- STEP 3: Database setup ----
def init_db():
    """Creates the 'students' table if it doesn't already exist."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            course TEXT NOT NULL,
            age INTEGER
        )
    """)
    connection.commit()
    connection.close()


def get_db_connection():
    """Opens a connection and lets us read columns by name, e.g. row['name']."""
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# ---- STEP 4a: Our own "gatekeeper" decorator ----
def login_required(view_function):
    """
    Wraps an admin route. Before the real view function runs, we check
    if session['admin_logged_in'] is True. If not, we bounce the visitor
    to the login page instead of letting them see admin data.
    """
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in to access the admin area.", "error")
            return redirect(url_for("admin_login"))
        return view_function(*args, **kwargs)
    return wrapper


# ---- STEP 4b: PUBLIC HOME PAGE ----
@app.route("/")
def home():
    connection = get_db_connection()
    # COUNT(*) asks SQLite to count rows for us instead of pulling all data
    # into Python -- fast, and we never expose the private list publicly.
    total = connection.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    connection.close()
    return render_template("home.html", total=total)


# ---- STEP 4c: PUBLIC REGISTRATION ----
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        age = request.form.get("age", "").strip()

        if not name or not email or not course:
            flash("Please fill in Name, Email and Course.", "error")
            return redirect(url_for("register"))

        if age and not age.isdigit():
            flash("Age must be a valid number.", "error")
            return redirect(url_for("register"))

        age_value = int(age) if age else None

        connection = get_db_connection()
        # "?" placeholders keep us safe from SQL Injection attacks
        connection.execute(
            "INSERT INTO students (name, email, course, age) VALUES (?, ?, ?, ?)",
            (name, email, course, age_value)
        )
        connection.commit()
        connection.close()

        flash(f"{name} was registered successfully!", "success")
        return redirect(url_for("home"))

    return render_template("register.html")


# ---- STEP 5a: ADMIN LOGIN ----
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    # If they're already logged in, no need to show the form again
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # check_password_hash compares the typed password against the
        # stored hash WITHOUT ever needing to know the original password.
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Welcome back, admin!", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


# ---- STEP 5f: ADMIN LOGOUT ----
@app.route("/admin/logout")
def admin_logout():
    session.clear()   # wipes all session data, including admin_logged_in
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))


# ---- STEP 5c: ADMIN DASHBOARD (protected) ----
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    connection = get_db_connection()
    students = connection.execute(
        "SELECT * FROM students ORDER BY id DESC"
    ).fetchall()

    total_students = len(students)

    # GROUP BY course lets SQLite count students per course for us --
    # this powers the little stat cards on the dashboard.
    course_counts = connection.execute("""
        SELECT course, COUNT(*) AS count
        FROM students
        GROUP BY course
        ORDER BY count DESC
    """).fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        total_students=total_students,
        course_counts=course_counts,
        total_courses=len(course_counts)
    )


# ---- STEP 5d: ADMIN EDIT (protected) ----
@app.route("/admin/edit/<int:student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    connection = get_db_connection()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        age = request.form.get("age", "").strip()

        if not name or not email or not course:
            flash("Please fill in Name, Email and Course.", "error")
            connection.close()
            return redirect(url_for("edit_student", student_id=student_id))

        age_value = int(age) if age.isdigit() else None

        connection.execute(
            "UPDATE students SET name = ?, email = ?, course = ?, age = ? WHERE id = ?",
            (name, email, course, age_value, student_id)
        )
        connection.commit()
        connection.close()
        flash("Student record updated.", "success")
        return redirect(url_for("admin_dashboard"))

    # GET -> load the current record so the form can be pre-filled
    student = connection.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()
    connection.close()

    if student is None:
        flash("Student not found.", "error")
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_student.html", student=student)


# ---- STEP 5e: ADMIN DELETE (protected) ----
@app.route("/admin/delete/<int:student_id>")
@login_required
def delete_student(student_id):
    connection = get_db_connection()
    connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
    connection.commit()
    connection.close()
    flash("Student record deleted.", "success")
    return redirect(url_for("admin_dashboard"))


# ---- STEP 6: Start the app ----
if __name__ == "__main__":
    init_db()
    app.run(debug=True)