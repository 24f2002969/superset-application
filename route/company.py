from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from model import db, User, Company, Drive, Application, Log
from datetime import datetime, date

company_bp = Blueprint("company", __name__, url_prefix="/company")

@company_bp.before_request
def restrict_company():
 
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    if session.get("role") != "company":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(session["user_id"])
    if user.is_blacklisted:
        flash("Account Blacklisted", "danger")
        return redirect(url_for("auth.login"))

#DONE
@company_bp.route("/dashboard")
def dashboard():
    comp_id = session.get("comp_id")
    company = Company.query.get(comp_id)
    drives = company.drives
    total_drives = len(drives)
    all_applications = []
    for d in drives:
        all_applications.extend(d.applications)
    total_applications = len(all_applications)
    applied = sum(1 for a in all_applications if a.status == "applied")
    shortlisted = sum(1 for a in all_applications if a.status == "shortlisted")
    placed = sum(1 for a in all_applications if a.status == "placed")
    rejected = sum(1 for a in all_applications if a.status == "rejected")
    withdrawn = sum(1 for a in all_applications if a.status == "withdrawn")
    pending = sum(1 for d in drives if d.status == "pending")
    approved = sum(1 for d in drives if d.status == "active")
    closed = sum(1 for d in drives if d.status == "closed")
    rejected_drives = sum(1 for d in drives if d.status == "rejected")
    recent_drives = sorted(drives, key=lambda d: d.id, reverse=True)[:5]
    recent_applications = sorted(all_applications, key=lambda a: a.id, reverse=True)[:5]
    return render_template("company/dashboard.html",
        company=company,
        total_drives=total_drives,
        total_applications=total_applications,
        applied=applied,
        shortlisted=shortlisted,
        placed=placed,
        rejected=rejected,
        withdrawn=withdrawn,
        pending=pending,
        approved=approved,
        closed=closed,
        rejected_drives=rejected_drives,
        recent_drives=recent_drives,
        recent_applications=recent_applications,
        active_tab="dashboard"
    )

#DONE
@company_bp.route("/profile", methods=["GET"])
def profile():
    company = Company.query.get_or_404(session["comp_id"])
    return render_template("company/profile.html", company=company, active_tab="profile")

#DONE
@company_bp.route("/drive", methods=["GET"])
def drives():
    comp_id = session.get("comp_id")
    company = Company.query.get(comp_id)
    # Fetch drives by status
    pending_drives = Drive.query.filter_by(company_id=comp_id, status="pending").all()
    approved_drives = Drive.query.filter_by(company_id=comp_id, status="active").all()
    closed_drives = Drive.query.filter_by(company_id=comp_id, status="closed").all()
    rejected_drives = Drive.query.filter_by(company_id=comp_id, status="rejected").all()

    return render_template(
        "company/drives.html",
        company=company,
        pending_drives=pending_drives,
        approved_drives=approved_drives,
        closed_drives=closed_drives,
        rejected_drives=rejected_drives,
        active_tab="drives"
    )

#DONE
@company_bp.route("/applications", methods=["GET"])
def applications():
    comp_id = session.get("comp_id")
    company = Company.query.get(comp_id)
    status = ['active', 'closed']
    drives = Drive.query.filter(Drive.company_id == comp_id, Drive.status.in_(status)).all()
    return render_template("company/applications.html", company = company,drives=drives , active_tab="applications")

@company_bp.route("/notifications", methods=["GET"])
def notifications():
    comp = Company.query.get(session.get("comp_id"))
    drive_id = [d.id for d in comp.drives]
    notifications = Log.query.filter(Log.target_id.in_(drive_id), Log.target_type == "drive").all()
    return render_template("company/notification.html", company=comp, logs=notifications, active_tab="logs")

#Done
@company_bp.route("/drive/create", methods=["GET", "POST"])
def create_drive():
    company = Company.query.get(session["comp_id"])
    if request.method == "POST":
        date_str = request.form.get("deadline","").strip()
        if not date_str:
            flash("Deadline is required", "warning")
            return redirect(url_for("company.create_drive"))
        deadline = datetime.strptime(date_str, "%Y-%m-%d").date()
        if deadline <= date.today():
            flash("Deadline must be a future date", "danger")
            return redirect(url_for("company.create_drive"))
        try:
            vacancy = int(request.form.get("vacancies", "1").strip())
        except:
            vacancy =1
        try :
            cgpa = float(request.form.get("eligibility_cgpa", "0.0").strip())
        except:
            cgpa = 0.0

        drive = Drive(
            company_id=session["comp_id"],
            job_title=request.form.get("job_title").strip(),
            vacancies=vacancy,
            description=request.form.get("description", "No Description").strip(),
            eligibility=request.form.get("eligibility", "None").strip(),
            deadline=deadline,
            eligibility_cgpa=cgpa
        )
        if not drive.job_title:
            flash("All fields are required", "warning")
            return redirect(url_for("company.create_drive"))
        if vacancy <1 :
            flash("Vacancy can't be negative", "warning")
            return redirect(url_for("company.create_drive"))
        if drive.eligibility_cgpa < 0.0 or drive.eligibility_cgpa > 10.0:
            flash("Eligibility CGPA must be between 0.0 and 10.0", "warning")
            return redirect(url_for("company.create_drive"))
        db.session.add(drive)
        db.session.commit()
        complog("Created", "drive", drive.id)
        flash("Drive created (pending approval)", "info")
        return redirect(url_for("company.drives"))
    return render_template("company/create_drive.html", company = company, active_tab="create_drive")

#DONE
@company_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    company = Company.query.get_or_404(session["comp_id"])
    if request.method == "POST":
        company.name = request.form.get("name").strip()
        company.hr_contact = request.form.get("hr_contact").strip()
        company.website = request.form.get("website").strip()
        if not company.name or not company.hr_contact or not company.website:
            flash("All fields are required", "warning")
            return redirect(url_for("company.edit_profile"))
        db.session.commit()
        flash("Profile updated", "success")
        complog("Details Updated", "company", company.id)
        return redirect(url_for("company.profile"))
    
    return render_template("company/edit_profile.html", company=company, active_tab="profile")


#DONE
@company_bp.route("/drive/view/<int:id>", methods=["GET"])
def view_drive(id):
    drive = Drive.query.get_or_404(id)
    company = Company.query.get(session["comp_id"])
    if drive.company_id != session["comp_id"]:
        flash("Unauthorized", "danger")
        return redirect(url_for("company.dashboard"))
    return render_template("company/view_drive.html", company=company, drive=drive)

#done
@company_bp.route("/drive/edit/<int:id>", methods=["GET", "POST"])
def edit_drive(id):
    company = Company.query.get(session["comp_id"])
    drive = Drive.query.get_or_404(id)
    if drive.company_id != session["comp_id"]:
        flash("Unauthorized", "danger")
        return redirect(url_for("company.dashboard"))
    if request.method == "GET":
        return render_template("company/edit_drive.html", company=company, drive=drive, active_tab="drives")
    date_str = request.form.get("deadline","").strip()
    if not date_str:
        flash("Deadline is required", "warning")
        return redirect(url_for("company.edit_drive", id=drive.id))
    deadline = datetime.strptime(date_str, "%Y-%m-%d").date()
    if deadline <= date.today():
            flash("Deadline must be a future date", "danger")
            return redirect(url_for("company.edit_drive", id=drive.id))
    drive.deadline = deadline
    drive.job_title = request.form.get("job_title").strip()

    drive.description = request.form.get("description", "No Description").strip()
    drive.eligibility = request.form.get("eligibility", "None").strip()
    try:
        drive.eligibility_cgpa = float(request.form.get("eligibility_cgpa", "0.0").strip())
    except:
        drive.eligibility_cgpa = 0.0
    try:
        drive.vacancies = int(request.form.get("vacancies", "1").strip())
    except:
        drive.vacancies = 1
    if not drive.job_title:
        flash("All fields are required", "warning")
        return redirect(url_for("company.edit_drive", id=drive.id))
    if drive.eligibility_cgpa < 0.0 or drive.eligibility_cgpa > 10.0:
        flash("Eligibility CGPA must be between 0.0 and 10.0", "warning")
        return redirect(url_for("company.edit_drive", id=drive.id))
    if drive.vacancies < 1 :
        flash("Vacancy can't be negative", "warning")
        return redirect(url_for("company.edit_drive", id = drive.id))

    db.session.add(drive)
    db.session.commit()

    flash("Drive updated", "success")
    complog("Details Updated", "drive", drive.id)
    return redirect(url_for("company.view_drive", id=drive.id))

#DONE
@company_bp.route("/drive/close/<int:id>", methods=["POST"])
def close_drive(id):

    drive = Drive.query.get_or_404(id)
    if drive.company_id != session["comp_id"]:
        flash("Unauthorized", "danger")
        return redirect(url_for("company.dashboard"))
    drive.status = "closed"
    db.session.commit()
    complog("Closed", "drive", drive.id)
    flash("Drive closed", "info")
    return redirect(request.referrer or url_for("company.dashboard"))




#DONE
@company_bp.route("/application/shortlist/<int:id>", methods=["POST"])
def shortlist_application(id):
    app = Application.query.get_or_404(id)
    if app.drive.company_id != session["comp_id"]:
        flash("Unauthorized", "danger")
        return redirect(url_for("company.dashboard"))
    app.status = "shortlisted"
    db.session.commit()
    complog("Shortlisted", "application", app.id)
    flash("Application shortlisted", "success")
    return redirect(request.referrer or url_for("company.dashboard"))

#DONE
@company_bp.route("/application/reject/<int:id>", methods=["POST"])
def reject_application(id):
    app = Application.query.get_or_404(id)
    if app.drive.company_id != session["comp_id"]:
        flash("Unauthorized", "danger")
        return redirect(url_for("company.dashboard"))
    app.status = "rejected"
    db.session.commit()
    complog("Rejected", "application", app.id)
    flash("Application rejected", "success")
    return redirect(request.referrer or url_for("company.dashboard"))

#DONE
@company_bp.route("/application/place/<int:id>", methods=["POST"])
def hire_application(id):
    app = Application.query.get_or_404(id)
    if app.drive.company_id != session["comp_id"]:
        flash("Unauthorized", "danger")
        return redirect(url_for("company.dashboard"))
    app.status = "placed"
    db.session.commit()
    complog("Placed", "application", app.id)
    flash("Application placed", "success")
    return redirect(request.referrer or url_for("company.dashboard"))

#DONE
@company_bp.route("/application/view/<int:id>", methods=["GET"])
def view_application(id):
    app = Application.query.get_or_404(id)
    company = Company.query.get(session["comp_id"])
    if app.drive.company_id != session["comp_id"]:
        flash("Unauthorized", "danger")
        return redirect(url_for("company.dashboard"))
    return render_template("company/view_application.html", application=app, company=company, active_tab="applications")


#LOG
def complog(action, target_type, target_id):
    log = Log(
        user_id=session["user_id"],
        action=action,
        target_type=target_type,
        target_id=target_id
    )
    db.session.add(log)
    db.session.commit()