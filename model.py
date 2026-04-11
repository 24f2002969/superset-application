from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin / company / student
    is_blacklisted = db.Column(db.Boolean, default=False)
    company = db.relationship('Company', backref='user', uselist=False)
    student = db.relationship('Student', backref='user', uselist=False)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    hr_contact = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(200), nullable=False)
    is_approved = db.Column(db.String(20), default="pending", nullable=False)  # pending / approved / rejected
    drives = db.relationship('Drive', backref='company')

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    resume = db.Column(db.String(200), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    skills = db.Column(db.String(200))
    course = db.Column(db.String(100))
    applications = db.relationship('Application', backref='student')

class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    job_title = db.Column(db.String(100), nullable=False)
    vacancies = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, default="No Description")
    eligibility = db.Column(db.String(200), nullable=False, default="None")
    eligibility_cgpa = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending / approved / closed
    applications = db.relationship('Application', backref='drive')

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    drive_id = db.Column(db.Integer, db.ForeignKey('drive.id'))
    applied_on = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    status = db.Column(db.String(20), default="applied")  
    # applied / shortlisted / placed / rejected

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(200))
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    user = db.relationship('User', backref='logs')
    def __repr__(self):
        return f"<Log {self.id} - {self.user.role}:{self.user_id} {self.action} {self.target_type}:{self.target_id} at {self.timestamp}>"