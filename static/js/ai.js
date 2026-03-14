class AIAssistant {
    constructor(config) {
        this.csrfToken = config.csrfToken;
        this.endpoints = config.endpoints;
        this.easymde = config.easymde;
        
        this.sidebarContainer = document.querySelector('.ai-sidebar-container');
        this.isMobile = window.innerWidth <= 1024;
        
        this.initEventListeners();
    }

    // Modern Toast Notification
    showToast(message) {
        let container = document.getElementById('ai-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'ai-toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const msg = document.createElement('div');
        msg.className = 'toast-msg';
        msg.textContent = message;
        container.appendChild(msg);

        // trigger reflow
        void msg.offsetWidth;
        msg.classList.add('show');

        setTimeout(() => {
            msg.classList.remove('show');
            setTimeout(() => {
                msg.remove();
            }, 300);
        }, 3000);
    }

    async runAiRequest(endpoint, payload, loaderId, resultBoxId, onSuccess) {
        const loader = document.getElementById(loaderId);
        const resultBox = resultBoxId ? document.getElementById(resultBoxId) : null;
        
        loader.style.display = 'flex';
        if(resultBox) {
            resultBox.style.display = 'none';
            resultBox.innerHTML = '';
        }
        
        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            loader.style.display = 'none';
            
            if (!res.ok) {
                this.showToast(data.error || 'Something went wrong.');
                return;
            }
            
            if (onSuccess) {
                onSuccess(data.result);
            } else if (resultBox) {
                resultBox.style.display = 'block';
                let formatted = data.result.replace(/\n/g, '<br>');
                formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                resultBox.innerHTML = formatted;
            }
            
        } catch(e) {
            loader.style.display = 'none';
            this.showToast("Network error processing AI request. Please try again.");
            console.error("AI Request Error: ", e);
        }
    }

    initEventListeners() {
        // 1. Generate Notes
        const btnGenerate = document.getElementById('btn-ai-generate');
        if (btnGenerate) {
            btnGenerate.addEventListener('click', () => {
                const topic = document.getElementById('ai-topic-input').value.trim();
                if (!topic) return this.showToast('Please enter a topic.');
                
                this.runAiRequest(this.endpoints.generate, { topic: topic }, 'loader-generate', null, (result) => {
                    const cm = this.easymde.codemirror;
                    const currentVal = cm.getValue();
                    const newVal = currentVal + (currentVal ? '\n\n' : '') + result;
                    cm.setValue(newVal);
                    document.getElementById('ai-topic-input').value = '';
                });
            });
        }

        // 2. Context Actions
        const ctxResult = document.getElementById('ai-context-result');
        if (ctxResult) {
            ctxResult.addEventListener('click', (e) => {
                if(e.target.tagName === 'BUTTON' && e.target.hasAttribute('data-raw')) {
                    const raw = decodeURIComponent(e.target.getAttribute('data-raw'));
                    this.easymde.codemirror.setValue(this.easymde.value() + "\n\n" + raw);
                }
            });
        }

        document.getElementById('btn-ai-summarize')?.addEventListener('click', () => {
            const content = this.easymde.value();
            if (!content.trim()) return this.showToast("Editor is empty.");
            this.runAiRequest(this.endpoints.summarize, { content: content }, 'loader-context', 'ai-context-result');
        });

        document.getElementById('btn-ai-questions')?.addEventListener('click', () => {
            const content = this.easymde.value();
            if (!content.trim()) return this.showToast("Editor is empty.");
            this.runAiRequest(this.endpoints.questions, { content: content }, 'loader-context', 'ai-context-result', (result) => {
                ctxResult.style.display = 'block';
                const mapped = result.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                ctxResult.innerHTML = mapped + `<br><br><button class="btn btn-sm btn-outline mt-2" data-raw="${encodeURIComponent(result)}">Insert into note</button>`;
            });
        });

        document.getElementById('btn-ai-explain')?.addEventListener('click', () => {
            const text = this.easymde.codemirror.getSelection();
            if(!text) return this.showToast("Please highlight text in the editor first.");
            this.runAiRequest(this.endpoints.explain, { text: text, is_code: false }, 'loader-context', 'ai-context-result');
        });

        document.getElementById('btn-ai-explain-code')?.addEventListener('click', () => {
            const text = this.easymde.codemirror.getSelection();
            if(!text) return this.showToast("Please highlight code snippet in the editor first.");
            this.runAiRequest(this.endpoints.explain, { text: text, is_code: true }, 'loader-context', 'ai-context-result');
        });

        // 3. Chat Logic
        const btnChat = document.getElementById('btn-ai-chat');
        const chatInput = document.getElementById('ai-chat-input');
        if (btnChat && chatInput) {
            btnChat.addEventListener('click', () => {
                const query = chatInput.value.trim();
                const content = this.easymde.value();
                const historyBox = document.getElementById('ai-chat-history');
                
                if (!query) return;
                
                historyBox.innerHTML += `<div style="margin-bottom: 8px;"><b>You:</b> ${query}</div>`;
                historyBox.scrollTop = historyBox.scrollHeight;
                chatInput.value = '';
                
                this.runAiRequest(this.endpoints.chat, { query: query, context: content }, 'loader-chat', null, (result) => {
                     const mapped = result.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                     historyBox.innerHTML += `<div style="margin-bottom: 12px; color: var(--accent-secondary);"><b>AI:</b> ${mapped}</div>`;
                     historyBox.scrollTop = historyBox.scrollHeight;
                });
            });

            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    btnChat.click();
                }
            });
        }
        
    }
}

// Attach to window so it can be initialized when lazy loaded
window.AIAssistant = AIAssistant;
