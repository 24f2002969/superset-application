from route.admin import admin_bp
from route.auth import auth_bp
from route.company import company_bp
from route.error import error_bp
from route.public import public_bp
from route.student import student_bp


def init_routes(app):
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(student_bp)