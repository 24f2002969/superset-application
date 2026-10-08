import os
from flask import Flask
from model import db
from route.init_route import init_routes
from extra_services import ensure_schema


def _seed_admin():
    from model import User
    from werkzeug.security import generate_password_hash
    if not User.query.filter_by(role="admin").first():
        admin = User(
            username="admin",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("[SuperSet] Admin account created — username: admin / password: admin123")
        print("[SuperSet] Change the admin password before submitting!")

def create_app(seed=True):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "superset-dev-secret-change-in-prod")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///superset.sqlite3"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.init_app(app)
    init_routes(app)
    with app.app_context():
        db.create_all()
        if seed:
            _seed_admin()
    ensure_schema(app)

    return app





app = create_app()


if __name__ == "__main__":
    app.run(debug=True)