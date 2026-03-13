from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Message, User, Notification
from utils import log_activity
from extensions import socketio

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')


@messages_bp.route('/inbox')
@login_required
def inbox():
    # Group messages by the other user
    subquery = db.session.query(
        db.func.max(Message.id).label('max_id')
    ).filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).group_by(
        db.case(
            (Message.sender_id == current_user.id, Message.receiver_id),
            else_=Message.sender_id
        )
    ).subquery()

    latest_messages = Message.query.join(
        subquery, Message.id == subquery.c.max_id
    ).order_by(Message.created_at.desc()).all()

    return render_template('messages/inbox.html', latest_messages=latest_messages)


@messages_bp.route('/conversation/<username>')
@login_required
def conversation(username):
    other_user = User.query.filter_by(username=username).first_or_404()
    
    if other_user == current_user:
        flash('You cannot message yourself.', 'warning')
        return redirect(url_for('messages.inbox'))

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    # Mark as read
    unread = [m for m in messages if m.receiver_id == current_user.id and not m.is_read]
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    return render_template('messages/conversation.html', other_user=other_user, messages=messages)


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

    msg = Message(sender_id=current_user.id, receiver_id=other_user.id, content=content)
    db.session.add(msg)
    
    # Notify receiver
    notif = Notification(user_id=other_user.id, message=f'New message from {current_user.username}')
    db.session.add(notif)
    
    db.session.commit()
    
    socketio.emit('new_notification', {'count_increment': 1}, room=f"user_{other_user.id}")
    
    log_activity(current_user.id, 'send_message', 'message', msg.id, f'{current_user.username} sent a message to {other_user.username}')
    
    return redirect(url_for('messages.conversation', username=username))
