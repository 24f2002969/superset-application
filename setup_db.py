"""
setup_db.py
-----------
Drops all tables, recreates them, and seeds realistic demo data.

Run once before demo / viva:
    python setup_db.py

Credentials seeded
    Admin   → username: admin        password: admin123
    Company → username: company1..10 password: pass1234
    Student → username: student1..20 password: pass1234
"""

import os
import sys
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from model import db, User, Company, Student, Drive, Application, Log


def _days(n):
    """Return a date n days from today (negative = past)."""
    return date.today() + timedelta(days=n)


def _fake_resume(username):
    return f"static/uploads/demo_{username}_resume.pdf"


def seed():
    # seed=False skips _seed_admin() inside create_app — we seed our own admin below
    app = create_app(seed=False)
    with app.app_context():

        print("Dropping existing tables...")
        db.drop_all()
        print("Creating fresh tables...")
        db.create_all()

        # ── 1. Admin ──────────────────────────────────────────
        admin = User(
            username="admin",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.flush()
        print(f"  [+] Admin created  (id={admin.id})")

        # ── 2. Companies (10 total, 8 approved, 1 pending, 1 rejected) ──
        company_defs = [
            ("Nexora Systems",     "hr@nexora.io",        "https://nexora.io",       "approved"),
            ("Bluewave Analytics", "talent@bluewave.co",  "https://bluewave.co",     "approved"),
            ("Crestline Tech",     "recruit@crestline.in","https://crestline.in",    "approved"),
            ("Orbitron Labs",      "jobs@orbitron.dev",   "https://orbitron.dev",    "approved"),
            ("Pinnacle Software",  "hr@pinnacle.com",     "https://pinnacle.com",    "approved"),
            ("Dawnlight Inc",      "careers@dawnlight.io","https://dawnlight.io",    "approved"),
            ("Stackforge Co",      "hr@stackforge.io",    "https://stackforge.io",   "approved"),
            ("Clarix Solutions",   "hr@clarix.net",       "https://clarix.net",      "approved"),
            ("Vantex Global",      "jobs@vantex.com",     "https://vantex.com",      "pending"),
            ("Redline Corp",       "hr@redline.co",       "https://redline.co",      "rejected"),
        ]

        companies = []
        for idx, (name, hr, website, approval) in enumerate(company_defs, start=1):
            u = User(
                username=f"company{idx}",
                password=generate_password_hash("pass1234"),
                role="company"
            )
            db.session.add(u)
            db.session.flush()
            c = Company(
                user_id=u.id,
                name=name,
                hr_contact=hr,
                website=website,
                is_approved=approval
            )
            db.session.add(c)
            db.session.flush()
            companies.append(c)

        approved_companies = [c for c in companies if c.is_approved == "approved"]
        print(f"  [+] {len(companies)} companies created ({len(approved_companies)} approved)")

        # ── 3. Students (20 total, last 2 blacklisted) ────────
        student_defs = [
            ("Aman Gupta",       "aman@iitm.ac.in",      "9876543201", 8.9, "Python, Flask, SQL",          "B.Tech CSE"),
            ("Priya Sharma",     "priya@iitm.ac.in",     "9876543202", 7.5, "Java, Spring, MySQL",         "B.Tech IT"),
            ("Rohan Mehta",      "rohan@iitm.ac.in",     "9876543203", 9.1, "ML, Python, TensorFlow",      "B.Tech AI"),
            ("Sneha Iyer",       "sneha@iitm.ac.in",     "9876543204", 6.8, "HTML, CSS, JavaScript",       "B.Tech CSE"),
            ("Karan Patel",      "karan@iitm.ac.in",     "9876543205", 8.2, "C++, DSA, Competitive",       "B.Tech ECE"),
            ("Divya Nair",       "divya@iitm.ac.in",     "9876543206", 7.9, "Data Analysis, SQL, Power BI","B.Sc DS"),
            ("Arjun Singh",      "arjun@iitm.ac.in",     "9876543207", 8.5, "Flask, REST, PostgreSQL",     "B.Tech CSE"),
            ("Meera Reddy",      "meera@iitm.ac.in",     "9876543208", 7.1, "React, Node.js, MongoDB",     "B.Tech IT"),
            ("Vikram Joshi",     "vikram@iitm.ac.in",    "9876543209", 9.4, "Research, Python, LaTeX",     "M.Tech CSE"),
            ("Pooja Verma",      "pooja@iitm.ac.in",     "9876543210", 6.5, "QA, Selenium, Jira",          "B.Tech CSE"),
            ("Rahul Das",        "rahul@iitm.ac.in",     "9876543211", 8.0, "DevOps, Docker, AWS",         "B.Tech IT"),
            ("Ananya Bose",      "ananya@iitm.ac.in",    "9876543212", 7.6, "UI/UX, Figma, CSS",           "B.Design"),
            ("Siddharth Rao",    "siddharth@iitm.ac.in", "9876543213", 8.8, "Android, Kotlin, Firebase",   "B.Tech CSE"),
            ("Lakshmi Pillai",   "lakshmi@iitm.ac.in",   "9876543214", 7.3, "Networking, Linux, Shell",    "B.Tech ECE"),
            ("Nikhil Agarwal",   "nikhil@iitm.ac.in",    "9876543215", 9.0, "Blockchain, Solidity, Web3",  "B.Tech CSE"),
            ("Tanvi Kulkarni",   "tanvi@iitm.ac.in",     "9876543216", 6.9, "Python, Django, SQLite",      "B.Tech IT"),
            ("Harsh Gupta",      "harsh@iitm.ac.in",     "9876543217", 8.3, "Cloud, GCP, Terraform",       "B.Tech CSE"),
            ("Ishaan Kapoor",    "ishaan@iitm.ac.in",    "9876543218", 7.8, "Data Science, R, SPSS",       "B.Sc Stats"),
            ("Blocked Student",  "blocked1@iitm.ac.in",  "9000000001", 5.0, "None",                        "B.Tech CSE"),
            ("Banned Student",   "blocked2@iitm.ac.in",  "9000000002", 4.5, "None",                        "B.Tech IT"),
        ]

        students = []
        for idx, (name, email, contact, cgpa, skills, course) in enumerate(student_defs, start=1):
            blacklisted = idx >= 19
            u = User(
                username=f"student{idx}",
                password=generate_password_hash("pass1234"),
                role="student",
                is_blacklisted=blacklisted
            )
            db.session.add(u)
            db.session.flush()
            s = Student(
                user_id=u.id,
                name=name,
                email=email,
                contact_number=contact,
                cgpa=cgpa,
                skills=skills,
                course=course,
                resume=_fake_resume(f"student{idx}")
            )
            db.session.add(s)
            db.session.flush()
            students.append(s)

        active_students = students[:18]
        print(f"  [+] {len(students)} students created (2 blacklisted)")

        # ── 4. Drives ─────────────────────────────────────────
        drive_defs = [
            # (company_idx, job_title, vacancies, description, eligibility, cgpa, deadline_days, status)
            (0, "Software Engineer",      5, "Build scalable backend services.",       "B.Tech CSE/IT",  7.0,  30, "active"),
            (0, "Data Analyst",           3, "Analyse product and business metrics.",  "Any branch",     6.5,  25, "active"),
            (1, "ML Engineer",            2, "Develop and deploy ML models.",          "B.Tech CSE/AI",  8.0,  40, "active"),
            (1, "Business Analyst",       4, "Translate data to business strategy.",   "Any branch",     6.0,  15, "active"),
            (2, "Full Stack Developer",   6, "React + Flask end-to-end development.",  "B.Tech CSE/IT",  7.5,  35, "active"),
            (2, "QA Engineer",            3, "Test automation and manual QA.",         "Any branch",     6.0,  20, "active"),
            (3, "DevOps Engineer",        2, "CI/CD pipelines and cloud infra.",       "B.Tech CSE/ECE", 7.0,  50, "active"),
            (3, "Research Intern",        4, "AI/ML research assistant role.",         "M.Tech/B.Tech",  8.5,  45, "pending"),
            (4, "Android Developer",      3, "Native Android apps using Kotlin.",      "B.Tech CSE/IT",  7.0,  28, "active"),
            (4, "Cloud Architect",        1, "GCP/AWS cloud solutions design.",        "B.Tech CSE",     8.0,  60, "pending"),
            (5, "UI/UX Designer",         2, "Figma prototyping and front-end.",       "Any branch",     6.0,  22, "active"),
            (5, "Blockchain Developer",   2, "Smart contracts and DApp development.",  "B.Tech CSE",     7.5, -10, "closed"),
            (6, "Backend Developer",      4, "Django/Flask REST API development.",     "B.Tech CSE/IT",  7.0,  33, "active"),
            (6, "Product Manager Intern", 2, "Product roadmap and sprint planning.",   "Any branch",     6.5,  18, "rejected"),
            (7, "Network Engineer",       3, "LAN/WAN infrastructure and support.",    "B.Tech ECE/CSE", 6.5,  -5, "closed"),
        ]

        drives = []
        for (c_idx, title, vac, desc, elig, cgpa, days, status) in drive_defs:
            d = Drive(
                company_id=approved_companies[c_idx].id,
                job_title=title,
                vacancies=vac,
                description=desc,
                eligibility=elig,
                eligibility_cgpa=cgpa,
                deadline=_days(days),
                status=status
            )
            db.session.add(d)
            db.session.flush()
            drives.append(d)

        approved_drives = [d for d in drives if d.status == "active"]
        print(f"  [+] {len(drives)} drives created ({len(approved_drives)} approved)")

        # ── 5. Applications ───────────────────────────────────
        status_cycle = ["applied", "shortlisted", "placed", "rejected", "applied", "shortlisted", "applied"]
        application_count = 0
        used_pairs = set()

        for i, student in enumerate(active_students):
            for j in range(min(3, len(approved_drives))):
                drive_idx = (i + j) % len(approved_drives)
                drive = approved_drives[drive_idx]
                pair = (student.id, drive.id)
                if pair in used_pairs:
                    continue
                if drive.eligibility_cgpa > student.cgpa:
                    continue
                used_pairs.add(pair)
                status = status_cycle[(i + j) % len(status_cycle)]
                app_obj = Application(
                    student_id=student.id,
                    drive_id=drive.id,
                    status=status
                )
                db.session.add(app_obj)
                application_count += 1

        db.session.flush()
        print(f"  [+] {application_count} applications created")

        # ── 6. Logs ───────────────────────────────────────────
        sample_logs = [
            Log(user_id=admin.id, action="Approved",    target_type="company", target_id=companies[0].id),
            Log(user_id=admin.id, action="Approved",    target_type="company", target_id=companies[1].id),
            Log(user_id=admin.id, action="Rejected",    target_type="company", target_id=companies[9].id),
            Log(user_id=admin.id, action="Approved",    target_type="drive",   target_id=drives[0].id),
            Log(user_id=admin.id, action="Approved",    target_type="drive",   target_id=drives[2].id),
            Log(user_id=admin.id, action="Rejected",    target_type="drive",   target_id=drives[13].id),
            Log(user_id=admin.id, action="Blacklisted", target_type="student", target_id=students[18].id),
            Log(user_id=admin.id, action="Blacklisted", target_type="student", target_id=students[19].id),
        ]
        db.session.add_all(sample_logs)

        db.session.commit()
        print("\n✓ Database seeded successfully!\n")
        print("  Login credentials:")
        print("  ┌─────────────┬──────────────┬──────────────┐")
        print("  │ Role        │ Username     │ Password     │")
        print("  ├─────────────┼──────────────┼──────────────┤")
        print("  │ Admin       │ admin        │ admin123     │")
        print("  │ Company     │ company1     │ pass1234     │")
        print("  │ Student     │ student1     │ pass1234     │")
        print("  └─────────────┴──────────────┴──────────────┘")


if __name__ == "__main__":
    seed()