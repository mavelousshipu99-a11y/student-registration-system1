
==========================================================
 STUDENT REGISTRATION SYSTEM - Flask Backend (app.py)
==========================================================

ALGORITHM (plan before code):
1. START
2. Set up a Flask application + a secret key (needed for sessions/flash).
3. Set up a SQLite database with one table: "students"
      columns -> id (auto number), name, email, course, age
4. PUBLIC SIDE
   a. Route "/" (HOME PAGE)
        - Show a welcome page with a "Register" button.
        - Show only a total COUNT of students (no private details) to
          keep the personal data hidden from the public.
   b. Route "/register"
        - GET  -> show the empty registration form
        - POST -> read form data, validate it, save it to the database,
                  then redirect home with a success message.
5. ADMIN SIDE (protected area)
   a. Route "/admin/login"
        - GET  -> show login form
        - POST -> check username/password against the admin account
                  - if correct: mark the session as "logged in", go to dashboard
                  - if wrong: show an error and ask again
   b. A "gatekeeper" (login_required) that every admin route uses:
        - IF the session is NOT marked as logged in -> send the visitor
          back to the login page
        - ELSE -> let them continue to the page they asked for
   c. Route "/admin/dashboard" (protected)
        - Read every student from the database
        - Calculate simple statistics (total students, students per course)
        - Show the full table with Edit/Delete actions
   d. Route "/admin/edit/<id>" (protected) - update one student's details
   e. Route "/admin/delete/<id>" (protected) - remove one student
   f. Route "/admin/logout" - clear the session, send back to login
6. Run the Flask development server
7. END