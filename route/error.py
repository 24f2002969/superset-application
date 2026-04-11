# Done

from flask import Blueprint, render_template
import traceback

error_bp = Blueprint("error", __name__)

@error_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404

@error_bp.app_errorhandler(500)
def internal_error(error):
    print(traceback.format_exc())
    return render_template("errors/500.html"), 500