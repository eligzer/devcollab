import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from models import db, User, ClassNote, UserLink, Follow, Notification
from forms import EditProfileForm, UserLinkForm
from utils import log_activity
from extensions import socketio


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
    if current_user.is_authenticated:
        is_following = (
            Follow.query.filter_by(
                follower_id=current_user.id,
                following_id=user.id
            ).first()
            is not None
        )

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

        # ---- Profile Image Upload (SAFE VERSION) ----
        pic_file = form.profile_image.data

        if pic_file and hasattr(pic_file, "filename") and pic_file.filename != "":
            filename = secure_filename(pic_file.filename)

            unique_filename = f"{uuid.uuid4()}_{filename}"

            pic_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                unique_filename
            )

            pic_file.save(pic_path)

            current_user.profile_image = unique_filename

        # ---- Update Profile Fields ----
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.github_link = form.github_link.data

        db.session.commit()

        log_activity(
            current_user.id,
            "update_profile",
            "user",
            current_user.id,
            f"{current_user.username} updated their profile"
        )

        flash("Your profile has been updated!", "success")

        return redirect(url_for("user.profile", username=current_user.username))

    elif request.method == "GET":

        form.username.data = current_user.username
        form.bio.data = current_user.bio
        form.github_link.data = current_user.github_link

    return render_template("user/edit_profile.html", form=form)


# ----------------------------
# Add Custom Profile Link
# ----------------------------
@user_bp.route("/user/add_link", methods=["POST"])
@login_required
def add_link():

    form = UserLinkForm()

    if form.validate_on_submit():

        link = UserLink(
            user_id=current_user.id,
            title=form.title.data,
            url=form.url.data
        )

        db.session.add(link)
        db.session.commit()

        flash("Link added to your profile.", "success")

        log_activity(
            current_user.id,
            "add_link",
            "user_link",
            link.id,
            f"{current_user.username} added a custom link"
        )

    else:
        flash("Failed to add link. Please check your inputs.", "danger")

    return redirect(url_for("user.profile", username=current_user.username))


# ----------------------------
# Delete Profile Link
# ----------------------------
@user_bp.route("/user/<int:user_id>/delete_link/<int:link_id>", methods=["POST"])
@login_required
def delete_link(user_id, link_id):

    if current_user.id != user_id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("user.profile", username=current_user.username))

    link = UserLink.query.get_or_404(link_id)

    if link.user_id == current_user.id:
        db.session.delete(link)
        db.session.commit()
        flash("Link removed.", "info")

    return redirect(url_for("user.profile", username=current_user.username))


# ----------------------------
# Follow User
# ----------------------------
@user_bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):

    user = User.query.filter_by(username=username).first_or_404()

    if user == current_user:
        flash("You cannot follow yourself!", "warning")
        return redirect(url_for("user.profile", username=username))

    existing_follow = Follow.query.filter_by(
        follower_id=current_user.id,
        following_id=user.id
    ).first()

    if not existing_follow:

        follow_rel = Follow(
            follower_id=current_user.id,
            following_id=user.id
        )

        db.session.add(follow_rel)

        notif = Notification(
            user_id=user.id,
            message=f"{current_user.username} started following you."
        )

        db.session.add(notif)

        db.session.commit()

        socketio.emit(
            "new_notification",
            {"count_increment": 1},
            room=f"user_{user.id}"
        )

        log_activity(
            current_user.id,
            "follow",
            "user",
            user.id,
            f"{current_user.username} followed {user.username}"
        )

        flash(f"You are now following {username}!", "success")

    return redirect(url_for("user.profile", username=username))


# ----------------------------
# Unfollow User
# ----------------------------
@user_bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):

    user = User.query.filter_by(username=username).first_or_404()

    if user == current_user:
        flash("You cannot unfollow yourself!", "warning")
        return redirect(url_for("user.profile", username=username))

    existing_follow = Follow.query.filter_by(
        follower_id=current_user.id,
        following_id=user.id
    ).first()

    if existing_follow:

        db.session.delete(existing_follow)
        db.session.commit()

        log_activity(
            current_user.id,
            "unfollow",
            "user",
            user.id,
            f"{current_user.username} unfollowed {user.username}"
        )

        flash(f"You have unfollowed {username}.", "info")

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