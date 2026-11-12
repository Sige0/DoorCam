import os

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

bp = Blueprint("auth", __name__)

login_manager = LoginManager()
login_manager.login_view = "auth.login"


class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(user_id):
    if user_id == os.getenv("LOGIN_USER"):
        return User(user_id)
    return None


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        pw_hash = os.getenv("LOGIN_PASSWORD_HASH", "")

        if username == os.getenv("LOGIN_USER") and pw_hash and check_password_hash(pw_hash, password):
            login_user(User(username))
            return redirect(url_for("index"))

        flash("Benutzername oder Passwort falsch")

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
