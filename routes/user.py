import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import db, User, ClassNote, UserLink, Follow, Notification
from forms import EditProfileForm, UserLinkForm
from utils import log_activity


user_bp = Blueprint("user", __name__)


# ----------------------------
# User Profile Page
# ----------------------------
@user_bp.route("/user/<username>")
def profile(username):

    user = User.query.filter_by(username=username).first_or_404()

    notes = ClassNote.query.filter_by(
        created_by=user.username
    ).order_by(ClassNote.created_at.desc()).all()

    link_form = UserLinkForm()

    is_following = False

    if current_user.is_authenticated and current_user.id != user.id:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id,
            following_id=user.id
        ).first() is not None

    return render_template(
        "user/profile.html",
        user=user,
        notes=notes,
        link_form=link_form,
        is_following=is_following
    )


# ----------------------------
# Edit Profile
# ----------------------------
@user_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    form = EditProfileForm(current_user.username, obj=current_user)

    if form.validate_on_submit():

        try:

            pic_file = form.profile_image.data

            if pic_file and hasattr(pic_file, "filename") and pic_file.filename != "":

                allowed_extensions = {"png", "jpg", "jpeg", "gif"}

                ext = pic_file.filename.rsplit(".", 1)[1].lower()

                if ext in allowed_extensions:

                    filename = secure_filename(pic_file.filename)

                    unique_filename = f"{uuid.uuid4()}_{filename}"

                    filepath = os.path.join(
                        current_app.config["UPLOAD_FOLDER"],
                        unique_filename
                    )

                    pic_file.save(filepath)

                    current_user.profile_image = unique_filename

                else:
                    flash("Invalid image format.", "danger")
                    return redirect(url_for("user.edit_profile"))

            current_user.username = form.username.data
            current_user.bio = form.bio.data
            current_user.github_link = form.github_link.data

            db.session.commit()

            log_activity(
                current_user.id,
                "update_profile",
                "user",
                current_user.id,
                f"{current_user.username} updated profile"
            )

            flash("Profile updated successfully.", "success")

            return redirect(url_for("user.profile", username=current_user.username))

        except Exception as e:

            db.session.rollback()

            flash("Error updating profile.", "danger")

    return render_template("user/edit_profile.html", form=form)


# ----------------------------
# Add Custom Profile Link
# ----------------------------
@user_bp.route("/user/add_link", methods=["POST"])
@login_required
def add_link():

    form = UserLinkForm()

    if form.validate_on_submit():

        try:

            link = UserLink(
                user_id=current_user.id,
                title=form.title.data,
                url=form.url.data
            )

            db.session.add(link)
            db.session.commit()

            log_activity(
                current_user.id,
                "add_link",
                "user_link",
                link.id,
                f"{current_user.username} added profile link"
            )

            flash("Link added successfully.", "success")

        except Exception:

            db.session.rollback()

            flash("Failed to add link.", "danger")

    return redirect(url_for("user.profile", username=current_user.username))


# ----------------------------
# Delete Profile Link
# ----------------------------
@user_bp.route("/user/<int:user_id>/delete_link/<int:link_id>", methods=["POST"])
@login_required
def delete_link(user_id, link_id):

    if current_user.id != user_id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("user.profile", username=current_user.username))

    link = UserLink.query.get_or_404(link_id)

    try:

        db.session.delete(link)
        db.session.commit()

        flash("Link deleted.", "info")

    except Exception:

        db.session.rollback()
        flash("Error deleting link.", "danger")

    return redirect(url_for("user.profile", username=current_user.username))


# ----------------------------
# Follow User
# ----------------------------
@user_bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):

    user = User.query.filter_by(username=username).first_or_404()

    if user.id == current_user.id:
        flash("You cannot follow yourself.", "warning")
        return redirect(url_for("user.profile", username=username))

    try:

        existing = Follow.query.filter_by(
            follower_id=current_user.id,
            following_id=user.id
        ).first()

        if not existing:

            follow = Follow(
                follower_id=current_user.id,
                following_id=user.id
            )

            db.session.add(follow)

            notification = Notification(
                user_id=user.id,
                message=f"{current_user.username} started following you.",
                link=url_for("user.profile", username=current_user.username)
            )

            db.session.add(notification)

            db.session.commit()

            log_activity(
                current_user.id,
                "follow",
                "user",
                user.id,
                f"{current_user.username} followed {user.username}"
            )

            flash(f"You are now following {username}.", "success")

    except Exception:

        db.session.rollback()
        flash("Follow failed.", "danger")

    return redirect(url_for("user.profile", username=username))


# ----------------------------
# Unfollow User
# ----------------------------
@user_bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):

    user = User.query.filter_by(username=username).first_or_404()

    try:

        follow = Follow.query.filter_by(
            follower_id=current_user.id,
            following_id=user.id
        ).first()

        if follow:

            db.session.delete(follow)
            db.session.commit()

            log_activity(
                current_user.id,
                "unfollow",
                "user",
                user.id,
                f"{current_user.username} unfollowed {user.username}"
            )

            flash(f"You unfollowed {username}.", "info")

    except Exception:

        db.session.rollback()
        flash("Unfollow failed.", "danger")

    return redirect(url_for("user.profile", username=username))


# ----------------------------
# Notifications Page
# ----------------------------
@user_bp.route("/notifications")
@login_required
def notifications():

    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()

    return render_template(
        "user/notifications.html",
        notifications=notifs
    )


# ----------------------------
# Mark Notification Read
# ----------------------------
@user_bp.route("/notifications/read/<int:notif_id>", methods=["POST"])
@login_required
def read_notification(notif_id):

    notif = Notification.query.get_or_404(notif_id)

    if notif.user_id == current_user.id:

        notif.is_read = True
        db.session.commit()

    return redirect(url_for("user.notifications"))


# ----------------------------
# Mark All Notifications Read
# ----------------------------
@user_bp.route("/notifications/read_all", methods=["POST"])
@login_required
def read_all_notifications():

    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({"is_read": True})

    db.session.commit()

    flash("All notifications marked as read.", "success")

    return redirect(url_for("user.notifications"))