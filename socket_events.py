from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from models import db, Message, User, Notification, ClassNote, ClassNoteHistory
from utils import log_activity
from extensions import socketio
from datetime import datetime, timezone

# In-memory store for online users. In a production environment with multiple workers,
# you'd use Redis or a database table to track presence.
online_users = set()

# In-memory structures for collaborative editing
active_note_editors = {} # Maps note_id (int) to a list of dicts: [{'user_id': 1, 'username': 'Farhan', 'avatar': 'default.jpg'}]
note_buffers = {} # Maps note_id (int) to current markdown string buffer

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        # Join a room specific to this user so we can send them private notifications/messages
        room_name = f"user_{current_user.id}"
        join_room(room_name)
        
        # Add to online users
        if current_user.id not in online_users:
            online_users.add(current_user.id)
            # Broadcast to all clients that this user is online
            emit('user_online', {'user_id': current_user.id}, broadcast=True)
            
        # Send current online users to the newly connected client
        emit('online_users_list', {'online_users': list(online_users)})

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        room_name = f"user_{current_user.id}"
        leave_room(room_name)
        
        if current_user.id in online_users:
            online_users.remove(current_user.id)
            # Broadcast to all clients that this user is offline
            emit('user_offline', {'user_id': current_user.id}, broadcast=True)
            
        # Clean up from any active note editors
        for note_id, editors in list(active_note_editors.items()):
            if any(u['user_id'] == current_user.id for u in editors):
                # Remove this user
                active_note_editors[note_id] = [u for u in editors if u['user_id'] != current_user.id]
                # Emit update
                room_name = f"note_{note_id}"
                emit('active_editors_update', {'editors': active_note_editors[note_id]}, room=room_name)

@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        return {'status': 'error', 'message': 'Unauthorized'}
        
    receiver_username = data.get('receiver')
    content = data.get('content', '').strip()
    
    if not content or not receiver_username:
        return {'status': 'error', 'message': 'Invalid data'}
        
    other_user = User.query.filter_by(username=receiver_username).first()
    if not other_user or other_user == current_user:
        return {'status': 'error', 'message': 'Invalid receiver'}
        
    # Save to database
    msg = Message(sender_id=current_user.id, receiver_id=other_user.id, content=content)
    db.session.add(msg)
    
    # Notify receiver
    notif = Notification(user_id=other_user.id, message=f'New message from {current_user.username}')
    db.session.add(notif)
    
    db.session.commit()
    log_activity(current_user.id, 'send_message', 'message', msg.id, f'{current_user.username} sent a message to {other_user.username}')
    
    # Emit to receiver
    receiver_room = f"user_{other_user.id}"
    message_data = {
        'id': msg.id,
        'sender_id': current_user.id,
        'sender_username': current_user.username,
        'sender_avatar': current_user.profile_image or 'default.jpg',
        'content': msg.content,
        'created_at': msg.created_at.strftime('%I:%M %p')
    }
    
    emit('new_message', message_data, room=receiver_room)
    
    # Trigger notification ping for the receiver's navbar
    emit('new_notification', {'count_increment': 1}, room=receiver_room)
    
    # Return success to sender
    return {'status': 'success', 'message': message_data}

# --- Collaborative Note Editing Events ---

@socketio.on('note_join')
def handle_note_join(data):
    if not current_user.is_authenticated:
        return {'status': 'error', 'message': 'Unauthorized'}
        
    try:
        note_id = int(data.get('note_id'))
    except (TypeError, ValueError):
        return {'status': 'error', 'message': 'Invalid note ID'}
        
    room_name = f"note_{note_id}"
    join_room(room_name)
    
    if note_id not in active_note_editors:
        active_note_editors[note_id] = []
        
    user_info = {
        'user_id': current_user.id,
        'username': current_user.username,
        'avatar': current_user.profile_image or 'default.jpg'
    }
    
    # Add if not already in list
    if not any(u['user_id'] == current_user.id for u in active_note_editors[note_id]):
        active_note_editors[note_id].append(user_info)
        
    emit('active_editors_update', {'editors': active_note_editors[note_id]}, room=room_name)
    
    log_activity(current_user.id, 'join_note', 'note', note_id, f'{current_user.username} joined editing session for Note ID {note_id}')
    
    # Send current buffer if exists, else load from DB
    current_buffer = note_buffers.get(note_id)
    if current_buffer is None:
        note = ClassNote.query.get(note_id)
        current_buffer = note.content if note else ""
        note_buffers[note_id] = current_buffer
        
    return {'status': 'success', 'content': current_buffer}

@socketio.on('note_leave')
def handle_note_leave(data):
    if not current_user.is_authenticated:
        return
        
    try:
        note_id = int(data.get('note_id'))
    except (TypeError, ValueError):
        return
        
    room_name = f"note_{note_id}"
    leave_room(room_name)
    
    if note_id in active_note_editors:
        active_note_editors[note_id] = [u for u in active_note_editors[note_id] if u['user_id'] != current_user.id]
        emit('active_editors_update', {'editors': active_note_editors[note_id]}, room=room_name)
        if not active_note_editors[note_id]:
            # Optional cleanup: if no one is editing, remove from memory, but maybe leave buffer if needed
            pass

@socketio.on('note_edit')
def handle_note_edit(data):
    """ Broadcasts that someone is typing """
    if not current_user.is_authenticated:
        return
    try:
        note_id = int(data.get('note_id'))
    except (TypeError, ValueError):
        return
        
    room_name = f"note_{note_id}"
    emit('user_editing', {'user_id': current_user.id, 'username': current_user.username}, room=room_name, include_self=False)

@socketio.on('note_update')
def handle_note_update(data):
    """ Broadcasts content changes (deltas) to peers """
    if not current_user.is_authenticated:
        return
    try:
        note_id = int(data.get('note_id'))
    except (TypeError, ValueError):
        return
        
    delta = data.get('delta')
    if not delta:
        return
        
    room_name = f"note_{note_id}"
    emit('note_content_update', {'user_id': current_user.id, 'delta': delta}, room=room_name, include_self=False)

@socketio.on('note_save')
def handle_note_save(data):
    """ Commits buffer to PostgreSQL """
    if not current_user.is_authenticated:
        return {'status': 'error', 'message': 'Unauthorized'}
        
    try:
        note_id = int(data.get('note_id'))
    except (TypeError, ValueError):
        return {'status': 'error', 'message': 'Invalid note ID'}
        
    content = data.get('content', '')
    if not content:
        # Don't save empty if we lost state, or allow it explicitly
        content = note_buffers.get(note_id, '')
        
    note = ClassNote.query.get(note_id)
    if not note:
        return {'status': 'error'}
        
    # Check if content actually changed
    if note.content != content:
        # Record history just like standard route
        history = ClassNoteHistory(
            note_id=note.id,
            previous_content=note.content,
            edited_by=current_user.username,
            action_type='edit (collaborative)'
        )
        db.session.add(history)
        
        note.content = content
        note.updated_at = datetime.now(timezone.utc)
        note_buffers[note_id] = content
        
        db.session.commit()
        
        log_activity(current_user.id, 'edit_note', 'note', note.id, f'{current_user.username} collaboratively edited Note "{note.title}"')
        
        room_name = f"note_{note_id}"
        emit('note_saved', {'message': 'Saved!', 'updated_at': note.updated_at.strftime('%I:%M %p')}, room=room_name)
        
    return {'status': 'success'}
