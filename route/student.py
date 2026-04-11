from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from model import db, User, Student, Drive, Application, Log
from datetime import date
from werkzeug.utils import secure_filename
import os, time

student_bp = Blueprint("student", __name__, url_prefix="/student")

#DONE
@student_bp.before_request
def restrict_student():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    if session.get("role") != "student":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(session["user_id"])
    if user.is_blacklisted:
        flash("Account Blacklisted", "danger")
        return redirect(url_for("auth.login"))

#DONE
@student_bp.route("/dashboard", methods=["GET"])
def dashboard():
    student = Student.query.get_or_404(session["std_id"])
    applications = Application.query.filter_by(student_id=student.id).all()
    applied_drive_ids = [a.drive_id for a in applications]

    total_applications = len(applications)
    applied = len([a for a in applications if a.status == "applied"])
    shortlisted = len([a for a in applications if a.status == "shortlisted"])
    placed = len([a for a in applications if a.status == "placed"])
    rejected = len([a for a in applications if a.status == "rejected"])
    withdrawn = len([a for a in applications if a.status == "withdrawn"])

    recommended_drives = Drive.query.filter(
    Drive.status == "active",
    Drive.eligibility_cgpa <= student.cgpa,
    ~Drive.id.in_(applied_drive_ids),
    Drive.deadline >= date.today()).order_by(Drive.deadline.asc()).limit(6).all()
    priority = {
        "placed": 1,
        "shortlisted": 2,
        "applied": 3,
        "rejected": 4,
        "withdrawn": 5
    }
    top_applications = sorted(applications,key=lambda x: priority.get(x.status, 6))[:5]

    return render_template("student/dashboard.html", student=student,
                           total_applications=total_applications,
                           applied=applied, shortlisted=shortlisted,
                           placed=placed, rejected=rejected,
                           withdrawn=withdrawn,
                           recommended_drives=recommended_drives,
                           top_applications=top_applications, active_tab="dashboard")

#DONE
@student_bp.route("/profile", methods=["GET"])
def profile():
    student = Student.query.get_or_404(session["std_id"])
    return render_template("student/profile.html", student=student, active_tab="profile")

#DONE
@student_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    student = Student.query.get_or_404(session["std_id"])
    if request.method == "POST":
        try:
            student.cgpa = float(request.form.get("cgpa").strip())
        except:
            flash("Invalid CGPA. Please enter a valid CGPA.", "danger")
            return redirect(url_for("student.edit_profile"))
        if student.cgpa < 0.0 or student.cgpa > 10.0:
            flash("Invalid CGPA. Please enter a CGPA between 0.0 and 10.0.", "danger")
            return redirect(url_for("student.edit_profile"))
        student.name = request.form.get("name", "").strip()
        student.email = request.form.get("email", "").strip()
        student.contact_number = request.form.get("contact_number", "").strip()
        student.skills = request.form.get("skills", "").strip()
        student.course = request.form.get("course", "").strip()
        if not student.name or not student.email or not student.contact_number:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("student.edit_profile"))
        file = request.files.get("resume")
        if file and file.filename:
            filename = secure_filename(file.filename)
            if not filename.lower().endswith(".pdf"):
                flash("Only PDF files allowed", "danger")
                return redirect(url_for("student.edit_profile"))
            if student.resume and os.path.exists(student.resume):
                os.remove(student.resume)
            filename = str(time.time()) + "_" + filename
            filepath = os.path.join("static/uploads", filename)
            file.save(filepath)
            
            student.resume = filepath
        db.session.commit()
        stdlog("Details Updated", "student", student.id)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("student.profile"))
    return render_template("student/edit_profile.html",student=student,active_tab="profile")

#DONE
@student_bp.route("/drives", methods=["GET"])
def drives():
    drives = Drive.query.filter(Drive.status == "active").all()
    student = Student.query.get(session["std_id"])
    applied = Application.query.filter_by(student_id=session["std_id"]).all()
    applied_drive_ids = [app.drive_id for app in applied]
    return render_template("student/drives.html", student=student, drives=drives, applied=applied,applied_drive=applied_drive_ids, active_tab="drives")

#Done
@student_bp.route("/notifications", methods=["GET"])
def notifications():
    student = Student.query.get_or_404(session["std_id"])
    applications = Application.query.filter_by(student_id=session["std_id"]).all()
    app_id = [a.id for a in applications]
    logs = Log.query.filter(Log.target_type=='application', Log.target_id.in_(app_id)).order_by(Log.timestamp.desc()).all()
    return render_template("student/notification.html", logs=logs, student=student, active_tab="log")

# Done 
@student_bp.route("/applications", methods=["GET"])
def applications():
    student = Student.query.get_or_404(session["std_id"])
    priority = {
        "placed": 1,
        "shortlisted": 2,
        "applied": 3,
        "rejected": 4
    }
    applications = Application.query.filter_by(student_id=student.id).all()
    app = sorted(applications,key=lambda x: priority.get(x.status, 5))
    return render_template("student/application.html", applications=app, student=student, active_tab="applications")


# DONE
@student_bp.route("/drive/view/<int:id>", methods=["GET"])
def view_drive(id):
    drive = Drive.query.get_or_404(id)
    student = Student.query.get(session["std_id"])
    return render_template("student/view_drive.html", drive=drive, student=student, active_tab="drives")

#DONE
@student_bp.route("/application/view/<int:id>", methods=["GET"])
def view_application(id):
    application = Application.query.get_or_404(id)
    student = Student.query.get(session["std_id"])
    if application.student_id != session.get("std_id"):
        flash("Unauthorized access!", "danger")
        return redirect(url_for("student.dashboard"))
    return render_template("student/view_application.html", application=application, student=student, active_tab="applications")


#DONE
@student_bp.route("/drive/apply/<int:id>", methods=["POST"])
def apply_drive(id):
    drive = Drive.query.get_or_404(id)
    student = Student.query.get_or_404(session["std_id"])

    # Check if already applied
    existing_application = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if existing_application:
        flash("You have already applied for this drive.", "warning")
        return redirect(request.referrer or url_for("student.drives"))

    # Check eligibility
    if drive.eligibility_cgpa > student.cgpa:
        flash("You do not meet the CGPA requirement for this drive.", "danger")
        return redirect(request.referrer or url_for("student.drives"))

    # Create application
    application = Application(student_id=student.id, drive_id=drive.id)
    db.session.add(application)
    db.session.commit()
    stdlog("Applied", "application", application.id)
    stdlog("Applied", "drive", drive.id)
    flash("Application submitted successfully!", "success")
    return redirect(request.referrer or url_for("student.applications"))
#DONE
@student_bp.route("/application/withdraw/<int:id>", methods=["POST"])
def withdraw_application(id):
    application = Application.query.get_or_404(id)
    if application.student_id != session.get("std_id"):
        flash("Unauthorized access!", "danger")
        return redirect(url_for("student.dashboard"))
    application.status = "withdrawn"
    db.session.commit()
    stdlog("Withdrawn", "application", application.id)
    stdlog("Withdrawn", "drive", application.drive_id)
    flash("Application withdrawn successfully!", "success")
    return redirect(request.referrer or url_for("student.applications"))


# Log
def stdlog(action, target_type, target_id):
    log = Log(
        user_id=session["user_id"],
        action=action,
        target_type=target_type,
        target_id=target_id
    )
    db.session.add(log)
    db.session.commit()