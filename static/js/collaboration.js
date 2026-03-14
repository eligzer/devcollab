class CollaborationManager {
    constructor(config) {
        this.socket = config.socket;
        this.noteId = config.noteId;
        this.easymde = config.easymde;
        this.ui = {
            editorsList: document.getElementById('active-editors-list'),
            statusText: document.getElementById('edit-conflict-status')
        };
        
        this.isRemoteUpdate = false;
        this.isDirty = false;
        this.typingTimeout = null;

        if (this.socket) {
            this.initSocketEvents();
            this.initEditorEvents();
            this.initAutoSave();
        }
    }

    initSocketEvents() {
        // 1. Join room
        this.socket.emit('note_join', { note_id: this.noteId }, (response) => {
            if (response && response.status === 'success' && response.content) {
                // Initial load: full document
                this.isRemoteUpdate = true;
                this.easymde.value(response.content);
                this.isRemoteUpdate = false;
            }
        });

        // 2. Receive delta changes from others
        this.socket.on('note_content_update', (data) => {
            if (!data.delta) return;
            
            this.isRemoteUpdate = true;
            
            // Apply delta using CodeMirror doc
            const doc = this.easymde.codemirror.getDoc();
            doc.replaceRange(data.delta.text, data.delta.from, data.delta.to, data.delta.origin);
            
            this.isRemoteUpdate = false;
        });

        // 3. Handle Typing / Conflict Ribbon
        this.socket.on('user_editing', (data) => {
            if (!this.ui.statusText) return;
            
            this.ui.statusText.textContent = data.username + ' is editing...';
            this.ui.statusText.style.opacity = '1';
            
            clearTimeout(this.typingTimeout);
            this.typingTimeout = setTimeout(() => {
                this.ui.statusText.style.opacity = '0';
            }, 2500);
        });

        // 4. Active Editors UI
        this.socket.on('active_editors_update', (data) => {
            if (!this.ui.editorsList) return;
            
            this.ui.editorsList.innerHTML = '';
            const editors = data.editors || [];
            
            if (editors.length === 0) {
                this.ui.editorsList.innerHTML = '<span class="text-muted text-sm" style="font-style: italic;">Just you</span>';
            } else {
                let html = '';
                editors.forEach(ed => {
                    const avatarUrl = "/static/profile_pics/" + ed.avatar;
                    html += `<div style="display: flex; align-items: center; gap: 4px; background: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 12px; margin-right: 5px;">
                                <img src="${avatarUrl}" alt="Avatar" style="width: 20px; height: 20px; border-radius: 50%; object-fit: cover;">
                                <span class="text-sm font-weight-bold" style="line-height: 1;">${ed.username}</span>
                             </div>`;
                });
                this.ui.editorsList.innerHTML = html;
            }
        });

        // 5. Saved confirmation
        this.socket.on('note_saved', (data) => {
            if (!this.ui.statusText) return;
            
            this.ui.statusText.textContent = 'Auto-saved at ' + data.updated_at;
            this.ui.statusText.style.opacity = '0.7';
            clearTimeout(this.typingTimeout);
            this.typingTimeout = setTimeout(() => {
                this.ui.statusText.style.opacity = '0';
            }, 3000);
        });

        // 6. Leave Room on Unload
        window.addEventListener('beforeunload', () => {
            this.socket.emit('note_leave', { note_id: this.noteId });
        });
    }

    initEditorEvents() {
        // Transmit changes as they happen
        this.easymde.codemirror.on('change', (cm, changeObj) => {
            if (!this.isRemoteUpdate) {
                this.isDirty = true;
                
                // Broadcast that user is typing
                this.socket.emit('note_edit', { note_id: this.noteId });
                
                // Broadcast the specific change
                this.socket.emit('note_update', { 
                    note_id: this.noteId, 
                    delta: {
                        from: changeObj.from,
                        to: changeObj.to,
                        text: changeObj.text,
                        origin: changeObj.origin
                    }
                });
            }
        });
    }

    initAutoSave() {
        // Auto-save Loop every 5 seconds
        setInterval(() => {
            if (this.isDirty) {
                this.socket.emit('note_save', { 
                    note_id: this.noteId, 
                    content: this.easymde.value() // Save full final document
                }, (res) => {
                    if (res && res.status === 'success') {
                        this.isDirty = false;
                    }
                });
            }
        }, 5000);
    }
}

// Attach to window so it can be initialized by edit.html
window.CollaborationManager = CollaborationManager;
