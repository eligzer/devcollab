from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Message, User, Notification
from utils import log_activity

# import socketio from app
from extensions import socketio

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')


# ----------------------------
# Inbox
# ----------------------------
@messages_bp.route('/inbox')
@login_required
def inbox():

    subquery = db.session.query(
        db.func.max(Message.id).label('max_id')
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
        subquery, Message.id == subquery.c.max_id
    ).order_by(Message.created_at.desc()).all()

    return render_template(
        'messages/inbox.html',
        latest_messages=latest_messages
    )


# ----------------------------
# Conversation Page
# ----------------------------
@messages_bp.route('/conversation/<username>')
@login_required
def conversation(username):

    other_user = User.query.filter_by(username=username).first_or_404()

    if other_user == current_user:
        flash('You cannot message yourself.', 'warning')
        return redirect(url_for('messages.inbox'))

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
        'messages/conversation.html',
        other_user=other_user,
        messages=messages
    )


# ----------------------------
# Send Message (Realtime)
# ----------------------------
@messages_bp.route('/send_message/<username>', methods=['POST'])
@login_required
def send_message(username):

    other_user = User.query.filter_by(username=username).first_or_404()

    content = request.form.get('content', '').strip()

    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('messages.conversation', username=username))

    if other_user == current_user:
        flash('You cannot message yourself.', 'warning')
        return redirect(url_for('messages.inbox'))

    # save message
    msg = Message(
        sender_id=current_user.id,
        receiver_id=other_user.id,
        content=content
    )

    db.session.add(msg)

    notif = Notification(
        user_id=other_user.id,
        message=f'New message from {current_user.username}'
    )

    db.session.add(notif)

    db.session.commit()

    log_activity(
        current_user.id,
        'send_message',
        'message',
        msg.id,
        f'{current_user.username} sent a message to {other_user.username}'
    )

    # 🔥 emit realtime message
    room = f"chat_{min(current_user.id, other_user.id)}_{max(current_user.id, other_user.id)}"

    socketio.emit(
        "receive_message",
        {
            "username": current_user.username,
            "message": content
        },
        room=room
    )

    return redirect(url_for('messages.conversation', username=username))