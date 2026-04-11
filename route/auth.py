from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from model import db, User, Student, Company
from werkzeug.utils import secure_filename
import os, time
from werkzeug.security import generate_password_hash, check_password_hash
 
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # THis part make sure if anyone logged in, they redirect to their dashboard
    res = redirect_to_dashboard()
    if res:
        return res
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please fill all fields", "warning")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            if user.is_blacklisted:
                flash("Account Blacklisted", "danger")
                return redirect(url_for("auth.login"))

            session["user_id"] = user.id
            session["role"] = user.role

            res = redirect_to_dashboard()
            if res:
                return res
        flash("Invalid credentials", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/register/student", methods=["GET", "POST"])
def register_student():
    res = redirect_to_dashboard()
    if res:
        return res

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        if not name or not password or not username:
            flash("Please Fill all fields", "warning")
            return redirect(url_for("auth.register_student"))
        if password and len(password) < 6:
            flash("Password must be at least 6 characters long", "warning")
            return redirect(url_for("auth.register_student"))
        email = request.form.get("email", "").strip()
        contact_number = request.form.get("contact_number", "").strip()
        if not contact_number or not email:
            flash("Email and contact number required", "warning")
            return redirect(url_for("auth.register_student"))
        try:
            cgpa = float(request.form.get("cgpa", "").strip())
        except:
            flash("Invalid CGPA. Please enter a valid CGPA.", "danger")
            return redirect(url_for("auth.register_student"))
        if  cgpa < 0.0 or cgpa > 10.0:
            flash("Invalid CGPA. Please enter a CGPA between 0.0 and 10.0.", "danger")
            return redirect(url_for("auth.register_student"))
        skills = request.form.get("skills", "").strip()
        course = request.form.get("course", "").strip()
        file = request.files.get("resume")
        resume_path = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            if not filename.endswith(".pdf"):
                flash("Only PDF files allowed", "danger")
                return redirect(url_for("auth.register_student"))
            filename = str(time.time()) + "_" + filename 
            filepath = os.path.join("static/uploads", filename)
            file.save(filepath)
            
            resume_path = filepath
        else:
            flash("Resume file is required", "warning")
            return redirect(url_for("auth.register_student"))
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "warning")
            return redirect(url_for("auth.register_student"))
        password=generate_password_hash(password)
        user = User(
            username=username,
            password=password,
            role="student"
        )
        db.session.add(user)
        db.session.commit()
        student = Student(
            user_id=user.id,
            name=name,
            email=email,
            contact_number=contact_number,
            resume=resume_path,
            cgpa=cgpa,
            skills=skills,
            course=course
        )

        db.session.add(student)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_student.html")

@auth_bp.route("/register/company", methods=["GET", "POST"])
def register_company():
    res = redirect_to_dashboard()
    if res:
        return res

    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        company_name = request.form.get("company_name").strip()
        hr_contact = request.form.get("hr_contact").strip()
        website = request.form.get("website").strip()

        if not username or not password:
            flash("Username and password required", "warning")
            return redirect(url_for("auth.register_company"))
        if not company_name or not hr_contact or not website:
            flash("All fields are required", "warning")
            return redirect(url_for("auth.register_company"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "warning")
            return redirect(url_for("auth.register_company"))
        password=generate_password_hash(password)
        user = User(username=username, password=password, role="company")
        db.session.add(user)
        db.session.commit()

        company = Company(
            user_id=user.id,
            name=company_name,
            hr_contact=hr_contact,
            website=website
        )
        db.session.add(company)
        db.session.commit()

        flash("Registered! Await approval.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_company.html")

@auth_bp.route("/logout")
def logout():
    print(session.get("user_id"), session.get("role"), session)
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("auth.login"))

def redirect_to_dashboard():
    if session.get("user_id"):
        user = User.query.get_or_404(session["user_id"])
        if user and user.is_blacklisted:
            session.clear()
            flash("Account Blacklisted", "danger")
            return redirect(url_for("auth.login"))
        if user and not user.is_blacklisted:
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user.role == "company":
                if user.company.is_approved == "pending":
                    session.clear()
                    flash("Approval pending", "info")
                    return redirect(url_for("auth.login"))
                if user.company.is_approved == "rejected":
                    session.clear()
                    flash("Company registration rejected", "danger")
                    return redirect(url_for("auth.login"))
                session["comp_id"] = user.company.id
                return redirect(url_for("company.dashboard"))
            elif user.role == "student":
                session["std_id"] = user.student.id
                return redirect(url_for("student.dashboard"))