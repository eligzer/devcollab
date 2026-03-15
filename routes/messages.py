from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Message, User, Notification
from utils import log_activity

from extensions import socketio
from flask_socketio import join_room, emit
from app import online_users


messages_bp = Blueprint(
    "messages",
    __name__,
    url_prefix="/messages"
)


# =====================================================
# Inbox
# =====================================================

@messages_bp.route("/inbox")
@login_required
def inbox():

    subquery = db.session.query(
        db.func.max(Message.id).label("max_id")
    ).filter(
        (Message.sender_id == current_user.id) |
        (Message.receiver_id == current_user.id)
    ).group_by(
        db.case(
            (Message.sender_id == current_user.id, Message.receiver_id),
            else_=Message.sender_id
        )
    ).subquery()

    latest_messages = Message.query.join(
        subquery,
        Message.id == subquery.c.max_id
    ).order_by(Message.created_at.desc()).all()

    return render_template(
        "messages/inbox.html",
        latest_messages=latest_messages
    )


# =====================================================
# Conversation Page
# =====================================================

@messages_bp.route("/conversation/<username>")
@login_required
def conversation(username):

    other_user = User.query.filter_by(
        username=username
    ).first_or_404()

    if other_user == current_user:

        flash("You cannot message yourself.", "warning")

        return redirect(url_for("messages.inbox"))

    messages = Message.query.filter(

        ((Message.sender_id == current_user.id) &
         (Message.receiver_id == other_user.id)) |

        ((Message.sender_id == other_user.id) &
         (Message.receiver_id == current_user.id))

    ).order_by(Message.created_at.asc()).all()

    # mark messages as read

    unread = [
        m for m in messages
        if m.receiver_id == current_user.id and not m.is_read
    ]

    for m in unread:
        m.is_read = True

    if unread:
        db.session.commit()

    return render_template(
    "messages/conversation.html",
    other_user=other_user,
    messages=messages,
    is_online=other_user.id in online_users
)


# =====================================================
# SOCKET.IO EVENTS
# =====================================================


# ----------------------------
# Join Chat Room
# ----------------------------

@socketio.on("join_chat")
def join_chat(data):

    room = data["room"]

    join_room(room)


# ----------------------------
# Send Message
# ----------------------------

@socketio.on("send_message")
def handle_send_message(data):

    room = data["room"]
    content = data["message"]

    sender = current_user

    # extract receiver id

    ids = room.replace("chat_", "").split("_")

    user1 = int(ids[0])
    user2 = int(ids[1])

    receiver_id = user2 if sender.id == user1 else user1


    # save message

    msg = Message(
        sender_id=sender.id,
        receiver_id=receiver_id,
        content=content
    )

    db.session.add(msg)


    # notification

    notif = Notification(
        user_id=receiver_id,
        message=f"New message from {sender.username}"
    )

    db.session.add(notif)

    db.session.commit()


    # emit realtime message

    emit(
        "receive_message",
        {
            "username": sender.username,
            "sender_id": sender.id,
            "message": content,
            "timestamp": msg.created_at.strftime("%H:%M")
        },
        room=room
    )


    log_activity(
        sender.id,
        "send_message",
        "message",
        msg.id,
        f"{sender.username} sent a message"
    )