from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user

from models import db, User, InviteCode
from forms import LoginForm, RegisterForm


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# -----------------------------
# REGISTER
# -----------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()

    if form.validate_on_submit():

        invite = InviteCode.query.filter_by(
            code=form.invite_code.data.strip()
        ).first()

        if not invite:
            flash("Invalid invite code.", "danger")
            return render_template("auth/register.html", form=form)

        if invite.used_by:
            flash("This invite code has already been used.", "danger")
            return render_template("auth/register.html", form=form)

        # mark invite as used
        invite.used_by = form.username.data
        invite.used_at = datetime.now(timezone.utc)

        user = User(
            username=form.username.data,
            email=form.email.data
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please sign in.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


# -----------------------------
# LOGIN
# -----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(
            username=form.username.data.strip()
        ).first()

        if user is None:
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html", form=form)

        # verify password
        if not user.check_password(form.password.data):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html", form=form)

        # account suspension protection
        if hasattr(user, "is_active") and user.is_active is False:
            flash(
                "Your account has been suspended. Please contact an administrator.",
                "danger",
            )
            return redirect(url_for("auth.login"))

        login_user(user)

        flash("Welcome back!", "success")

        next_page = request.args.get("next")

        if not next_page:
            next_page = url_for("main.index")

        return redirect(next_page)

    return render_template("auth/login.html", form=form)


# -----------------------------
# LOGOUT
# -----------------------------
@auth_bp.route("/logout")
def logout():

    logout_user()

    flash("You have been signed out.", "info")

    return redirect(url_for("main.index"))