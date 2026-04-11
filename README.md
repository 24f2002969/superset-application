# SuperSet — Campus Placement Portal

SuperSet is a role-based campus placement management web application built for **IIT Madras — Modern Application Development 1**. It supports company onboarding, placement drive publishing, student applications, resume management, and audit logging across three roles: **Admin**, **Company**, and **Student**.

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite (via Flask-SQLAlchemy)
- **Frontend:** Jinja2, HTML/CSS, Bootstrap 5, Chart.js
- **File Handling:** Werkzeug (`secure_filename`) for PDF resume uploads

## Repository Structure

```text
SuperSet/
├── app.py                  # App factory, config, admin seeding
├── model.py                # SQLAlchemy models
├── setup_db.py             # DB reset + demo data seeding
├── extra_services.py       # Live schema migration (ensure_schema)
├── requirements.txt
├── route/
│   ├── init_route.py       # Blueprint registration
│   ├── auth.py             # Login, logout, registration
│   ├── admin.py            # Admin panel routes
│   ├── company.py          # Company routes
│   ├── student.py          # Student routes
│   ├── public.py           # Landing page
│   └── error.py            # 404 / 500 handlers
├── static/
│   ├── app.css
│   └── uploads/            # Runtime resume upload target
└── templates/
    ├── Home/
    │   └── index.html
    ├── auth/
    │   ├── base.html
    │   ├── login.html
    │   ├── register_student.html
    │   └── register_company.html
    ├── admin/
    │   ├── base.html
    │   ├── dashboard.html
    │   ├── students.html
    │   ├── companies.html
    │   ├── drives.html
    │   ├── applications.html
    │   ├── blacklisted.html
    │   ├── log.html
    │   ├── view_student.html
    │   ├── view_company.html
    │   ├── view_drive.html
    │   ├── view_application.html
    │   ├── edit_student.html
    │   └── edit_company.html
    ├── company/
    │   ├── base.html
    │   ├── dashboard.html
    │   ├── profile.html
    │   ├── edit_profile.html
    │   ├── drives.html
    │   ├── create_drive.html
    │   ├── edit_drive.html
    │   ├── view_drive.html
    │   ├── applications.html
    │   ├── view_application.html
    │   └── notification.html
    ├── student/
    │   ├── base.html
    │   ├── dashboard.html
    │   ├── profile.html
    │   ├── edit_profile.html
    │   ├── drives.html
    │   ├── view_drive.html
    │   ├── application.html
    │   ├── view_application.html
    │   └── notification.html
    └── errors/
        ├── 404.html
        └── 500.html
```

## Data Model

| Model | Description |
|---|---|
| `User` | Auth credentials, role (`admin`/`company`/`student`), blacklist flag |
| `Company` | Company profile, approval status, linked to `User` |
| `Student` | Student profile, CGPA, skills, resume path, linked to `User` |
| `Drive` | Placement drive posted by a company with lifecycle status |
| `Application` | Student–Drive mapping with unique constraint on `(student_id, drive_id)` |
| `Log` | Audit log of every action across all roles |

Drive lifecycle: `pending → active / rejected → closed`

Application pipeline: `applied → shortlisted → placed / rejected / withdrawn`

## Getting Started

### 1. Create and activate virtual environment

```bash
python -m venv .venv
or
python3 -m venv .venv   // for Mac / Linux

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```
or 

```bash
pip install flask flask-sqlalchemy sqlalchemy 
```

### 3. Seed the database (recommended for first run)

```bash
python setup_db.py
```

Drops and recreates the DB, then inserts demo data: 10 companies, 20 students, 15 drives, and realistic applications.

### 4. Run the application

```bash
python app.py
```

Open: `http://127.0.0.1:5000`

## Seeded Login Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Company | `company1` – `company10` | `pass1234` |
| Student | `student1` – `student20` | `pass1234` |

- `company9` is pending approval, `company10` is rejected — for testing the approval flow.
- `student19`, `student20` are blacklisted — for testing access control.
- Mix of active, pending, closed, and rejected drives seeded.

## Role Capabilities

### Admin
- Approve or reject company registrations
- Approve, reject, or close placement drives
- View, edit, search, and blacklist students and companies
- View all applications and full audit logs

### Company
- Login only after admin approval
- Create and manage placement drives (submitted as pending)
- View student applications per drive
- Shortlist, place, or reject applicants

### Student
- Register, login, and manage profile with PDF resume upload
- Browse active approved drives (filtered by eligibility CGPA)
- Apply to drives (one application per drive enforced)
- Track application status and view notifications

## Notes

- Admin account is pre-seeded — no admin registration route exists.
- `extra_services.py` runs safe `ALTER TABLE` migrations on startup so existing local databases stay compatible without a full reset.
- Passwords are hashed using `werkzeug.security`.
- Resume uploads are PDF-only, max 5 MB.

## Built By

**Aman Gupta** · `24f2002969@ds.study.iitm.ac.in`  
Modern Application Development 1 · IIT Madras Online Degree
