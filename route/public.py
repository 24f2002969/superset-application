from flask import Blueprint, render_template

public_bp = Blueprint("public", __name__)


# 🔹 HOME PAGE
@public_bp.route("/")
def home():
    return render_template(
        "Home/index.html",
    )