"""
services.py
Central utility module for SuperSet.

What lives here:
  1. ensure_schema()      — live DB migration (safe ALTER TABLE on startup)

Where to use this:
  - app.py           → call ensure_schema(app) inside create_app() after db.create_all()
"""

import os
from datetime import datetime, timezone

from flask import session
from sqlalchemy import inspect, text

from model import db, User, Company, Student, Drive, Application, Log



# 1. LIVE DB MIGRATION
# Maps each table to the new columns that should exist.
# Format: { "table_name": [ (column_name, sql_definition), ... ] }
#
# Add a new entry here whenever you add a column to model.py —
# existing local databases will get the column on next startup
# without needing a full reset.
_REQUIRED_COLUMNS = {
    "user": [
        ("username", "VARCHAR(100) NOT NULL"),
        ("password", "VARCHAR(200) NOT NULL"),
        ("role", "VARCHAR(20) NOT NULL"),
        ("is_blacklisted", "BOOLEAN DEFAULT 0"),
    ],

    "company": [
        ("user_id", "INTEGER"),
        ("name", "VARCHAR(100) NOT NULL"),
        ("hr_contact", "VARCHAR(100) NOT NULL"),
        ("website", "VARCHAR(200) NOT NULL"),
        ("is_approved", "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
    ],

    "student": [
        ("user_id", "INTEGER"),
        ("name", "VARCHAR(100) NOT NULL"),
        ("email", "VARCHAR(100) NOT NULL"),
        ("contact_number", "VARCHAR(15) NOT NULL"),
        ("resume", "VARCHAR(200) NOT NULL"),
        ("cgpa", "FLOAT NOT NULL"),
        ("skills", "VARCHAR(200)"),
        ("course", "VARCHAR(100)"),
    ],

    "drive": [
        ("company_id", "INTEGER"),
        ("job_title", "VARCHAR(100) NOT NULL"),
        ("vacancies", "INTEGER DEFAULT 1"),
        ("description", "TEXT DEFAULT 'No Description'"),
        ("eligibility", "VARCHAR(200) NOT NULL DEFAULT 'None'"),
        ("eligibility_cgpa", "FLOAT DEFAULT 0.0"),
        ("deadline", "DATE NOT NULL"),
        ("status", "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
    ],

    "application": [
        ("student_id", "INTEGER"),
        ("drive_id", "INTEGER"),
        ("applied_on", "DATETIME"),
        ("status", "VARCHAR(20) DEFAULT 'applied'"),
    ],

    "log": [
        ("user_id", "INTEGER"),
        ("action", "VARCHAR(200)"),
        ("target_type", "VARCHAR(50)"),
        ("target_id", "INTEGER"),
        ("timestamp", "DATETIME"),
    ],
}

# Maps each table to indexes that must exist.
# Format: { "index_name": (table, sql) }
_REQUIRED_INDEXES = {
    "uq_application_student_drive": (
        "application",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_application_student_drive "
        "ON application(student_id, drive_id)"
    ),
}


def ensure_schema(app):
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        # ── Column migrations ──────────────────────────────────
        altered = []
        for table, columns in _REQUIRED_COLUMNS.items():
            if table not in existing_tables:
                continue  # table doesn't exist yet — db.create_all() will handle it
            existing_cols = {col["name"] for col in inspector.get_columns(table)}
            for col_name, col_def in columns:
                if col_name not in existing_cols:
                    stmt = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"
                    try:
                        db.session.execute(text(stmt))
                        altered.append(f"{table}.{col_name}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"[SuperSet] Migration warning: could not add {table}.{col_name} — {e}")

        if altered:
            db.session.commit()
            for col in altered:
                print(f"[SuperSet] Migrated: added column '{col}'")
        else:
            print("[SuperSet] Schema up to date — no migrations needed.")

        # ── Index migrations ───────────────────────────────────
        for index_name, (table, sql) in _REQUIRED_INDEXES.items():
            if table not in existing_tables:
                continue
            existing_indexes = {idx["name"] for idx in inspector.get_indexes(table)}
            if index_name not in existing_indexes:
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"[SuperSet] Migrated: created index '{index_name}'")
                except Exception as e:
                    db.session.rollback()
                    print(f"[SuperSet] Migration warning: could not create index '{index_name}' — {e}")






