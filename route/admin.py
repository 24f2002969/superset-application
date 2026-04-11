from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from model import db, User, Student, Company, Drive, Application, Log
from sqlalchemy import or_, func

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
def restrict_admin():
    if not session.get("user_id"):
        flash("Admin Login Required!", "danger")
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Access denied!, You are not Admin", "danger")
        return redirect(url_for("auth.login"))


#will do little change here on recent application
# Will change it to log version
@admin_bp.route("/dashboard", methods=["GET"])
def dashboard():
    # Total counts of Entities
    total_students = Student.query.count()
    total_jobs = db.session.query(func.sum(Drive.vacancies)).scalar()
    total_companies = Company.query.count()
    total_drives = Drive.query.count()
    total_apps = Application.query.count()
    active_students = Student.query.join(User).filter(User.is_blacklisted == False).count()
    active_companies = Company.query.join(User).filter(User.is_blacklisted == False).count()
    active_drives = Drive.query.filter(Drive.status == "active").count()
    pending_drives = Drive.query.filter(Drive.status == "pending").count()
    rejected_drives = Drive.query.filter(Drive.status == "rejected").count()
    closed_drives = Drive.query.filter(Drive.status == "closed").count()
    applied = Application.query.filter(Application.status == "applied").count()
    shortlisted = Application.query.filter(Application.status == "shortlisted").count()
    placed = Application.query.filter(Application.status == "placed").count()
    withdrawn = Application.query.filter(Application.status == "withdrawn").count()
    rejected = Application.query.filter(Application.status == "rejected").count()
    blacklisted_students = Student.query.join(User).filter(User.is_blacklisted == True).count()
    blacklisted_companies = Company.query.join(User).filter(User.is_blacklisted == True).count()
    recent_apps = Application.query.order_by(Application.applied_on.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        # totals
        students=total_students,
        companies=total_companies,
        drives=total_drives,
        jobs=total_jobs,
        applications=total_apps,
        # active
        active_students=active_students,
        active_companies=active_companies,
        active_drives=active_drives,
        # drive stats
        pending_drives=pending_drives,
        closed_drives=closed_drives,
        rejected_drives=rejected_drives,
        # application stats
        applied=applied,
        shortlisted=shortlisted,
        placed=placed,
        rejected=rejected,
        withdrawn=withdrawn,
        # extra
        completed_drives=closed_drives,
        placed_students=placed,
        # blacklist
        blacklisted_students=blacklisted_students,
        blacklisted_companies=blacklisted_companies,
        # recent
        recent_apps=recent_apps,
        active_tab="dashboard"
    )

@admin_bp.route("/students", methods=["GET"])
def students():
    query = request.args.get("q", "").strip()
    students_query = Student.query
    if query:
        filters = [
            Student.name.ilike(f"%{query}%"),
            Student.email.ilike(f"%{query}%"),
            Student.contact_number.ilike(f"%{query}%")
        ]
        if query.isdigit():
            filters.append(Student.id == int(query))
        students_query = students_query.filter(or_(*filters))

    students = students_query.all()

    return render_template(
        "admin/students.html",
        students=students,
        active_tab="students",
        search=query
    )

@admin_bp.route("/companies", methods=["GET"])
def companies():
    query = request.args.get("q", "").strip()
    companies_query = Company.query
    pending_companies = companies_query.filter_by(is_approved="pending").all()
    if query:
        filters = [
            Company.name.ilike(f"%{query}%"),
            Company.website.ilike(f"%{query}%"),
            Company.hr_contact.ilike(f"%{query}%")
        ]
        if query.isdigit():
            filters.append(Company.id == int(query))
        companies_query = companies_query.filter(or_(*filters))

    companies = companies_query.all()

    return render_template(
        "admin/companies.html",
        companies=companies,
        pending_companies=pending_companies,
        active_tab="companies",
        search=query
    )

@admin_bp.route("/blacklisted", methods=["GET"])
def black():
    blacklisted_students = User.query.filter_by(is_blacklisted=True, role='student').all()
    blacklisted_companies = User.query.filter_by(is_blacklisted=True, role='company').all()
    student_count = len(blacklisted_students)
    company_count = len(blacklisted_companies)
    return render_template(
        "admin/blacklisted.html",
        students=blacklisted_students,
        companies=blacklisted_companies,
        count_std=student_count,
        count_comp=company_count,
        active_tab="black"
    )

@admin_bp.route("/drives", methods=["GET"])
def drives():

    drives = Drive.query.all()
    pending = Drive.query.filter_by(status="pending").all()

    return render_template(
        "admin/drives.html",
        drives=drives,
        pending_drives=pending,
        active_tab="drives"
    )

@admin_bp.route("/application", methods=["GET"])
def applications():

    applications = Application.query.all()

    return render_template(
        "admin/applications.html",
        applications=applications,
        active_tab="applications"
    )

@admin_bp.route("/logs", methods=["GET"])
def logs():

    logs = Log.query.all()

    return render_template(
        "admin/log.html",
        logs=logs,
        active_tab="logs"
    )

# Methods
@admin_bp.route("/blacklist/<int:id>", methods=["POST"])
def toggle_blacklist_user(id):

    user = User.query.get_or_404(id)
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    if user.is_blacklisted:
        flash(f"User {user.username} blacklisted", "info")
        if user.role == "student":
            adminlog("Blacklisted", "student", user.student.id)
        else:
            Drive.query.filter_by(company_id=user.company.id).update({"status": "closed"})
            db.session.commit()
            adminlog("Blacklisted", "company", user.company.id)
    else:
        flash(f"User {user.username} Activated", "info")
        if user.role == "student":
            adminlog("Activated", "student", user.student.id)
        else:
            adminlog("Activated", "company", user.company.id)
            Drive.query.filter_by(company_id=user.company.id).update({"status": "pending"})
            db.session.commit()
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/company/approve/<int:id>", methods=["POST"])
def approve_company(id):
    company = Company.query.get_or_404(id)
    company.is_approved = "approved"
    db.session.commit()
    adminlog("Approved", "company", company.id)
    flash("Company approved", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/company/reject/<int:id>", methods=["POST"])
def reject_company(id):

    company = Company.query.get_or_404(id)
    company.is_approved = "rejected"
    db.session.commit()
    adminlog("Rejected", "company", company.id)
    flash("Company rejected", "danger")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/drive/approve/<int:id>", methods=["POST"])
def approve_drive(id):
    drive = Drive.query.get_or_404(id)
    drive.status = "active"
    db.session.commit()
    adminlog("Approved", "drive", drive.id)
    flash("Drive approved", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/drive/reject/<int:id>", methods=["POST"])
def reject_drive(id):
    drive = Drive.query.get_or_404(id)
    drive.status = "rejected"
    db.session.commit()
    adminlog("Rejected", "drive", drive.id)
    flash("Drive rejected", "danger")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/drive/close/<int:id>", methods=["POST"])
def close_drive(id):
    drive = Drive.query.get_or_404(id)
    drive.status = "closed"
    db.session.commit()
    adminlog("Closed", "drive", drive.id)
    flash("Drive closed", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/application/view/<int:id>", methods=["GET"])
def view_application(id):

    application = Application.query.get_or_404(id)

    return render_template(
        "admin/view_application.html",
        application=application,
        active_tab="applicants"
    )

@admin_bp.route("/drive/view/<int:id>", methods=["GET"])
def view_drive(id):

    drive = Drive.query.get_or_404(id)

    return render_template(
        "admin/view_drive.html",
        drive=drive,
        active_tab="drives"
    )

@admin_bp.route("/company/view/<int:id>", methods=["GET"])
def view_company(id):

    company = Company.query.get_or_404(id)

    return render_template(
        "admin/view_company.html",
        company=company
    )

@admin_bp.route("/student/view/<int:id>", methods=["GET"])
def view_student(id):

    student = Student.query.get_or_404(id)

    return render_template(
        "admin/view_student.html",
        student=student
    )

@admin_bp.route("/company/edit/<int:id>", methods=["GET", "POST"])
def edit_company(id):

    company = Company.query.get_or_404(id)

    if request.method == "POST":
        company.name = request.form.get("name").strip()
        company.website = request.form.get("website").strip()
        company.hr_contact = request.form.get("hr_contact").strip()

        if not company.name or not company.website or not company.hr_contact:
            flash("All fields are required.", "danger")
            return redirect(url_for("admin.edit_company", id=id))

        db.session.commit()
        flash("Company updated successfully", "success")
        adminlog("Details Updated", "company", company.id)
        return redirect(url_for("admin.view_company", id=id))

    return render_template(
        "admin/edit_company.html",
        company=company
    )

@admin_bp.route("/student/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    student = Student.query.get_or_404(id)

    if request.method == "POST":
        student.name = request.form.get("name").strip()
        student.course = request.form.get("course").strip()
        student.skills = request.form.get("skills").strip()
        student.contact_number = request.form.get("contact_number").strip()
        student.email = request.form.get("email").strip()
        try :
            student.cgpa = float(request.form.get("cgpa").strip())
        except:
            flash("Invalid CGPA.", "danger")
            return redirect(url_for("admin.edit_student", id=id))
        if student.cgpa < 0.0 or student.cgpa > 10.0:
            flash("Invalid CGPA. Please enter a CGPA between 0.0 and 10.0.", "danger")
            return redirect(url_for("admin.edit_student", id=id))
        if not student.contact_number or not student.email or not student.name or not student.course:
            flash("All fields are required.", "danger")
            return redirect(url_for("admin.edit_student", id=id))
        db.session.commit()
        adminlog("Details Updated", "student", student.id)
        flash("Student updated successfully", "success")
        return redirect(url_for("admin.view_student", id=id))
    return render_template(
        "admin/edit_student.html",
        student=student
    )


#LOG FUNCTION
def adminlog( action, target_type, target_id):
    new_log = Log(
        user_id=session.get("user_id"),
        action=action,
        target_type=target_type,
        target_id=target_id
    )
    db.session.add(new_log)
    db.session.commit()