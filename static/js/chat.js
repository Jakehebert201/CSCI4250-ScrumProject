class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.init();
    }

    init() {
        this.createWidget();
        this.bindEvents();
        this.showWelcomeMessage();
    }

    createWidget() {
        const widget = document.createElement('div');
        widget.className = 'chat-widget';
        widget.innerHTML = `
            <button class="chat-button" id="chat-toggle">
                💬
            </button>
            <div class="chat-window" id="chat-window">
                <div class="chat-header">
                    <h3>🤖 Student Tracker Assistant</h3>
                    <button class="chat-close" id="chat-close">×</button>
                </div>
                <div class="chat-messages" id="chat-messages">
                    <!-- Messages will be added here -->
                </div>
                <div class="chat-input-container">
                    <form class="chat-input-form" id="chat-form">
                        <input 
                            type="text" 
                            class="chat-input" 
                            id="chat-input" 
                            placeholder="Ask me anything..."
                            autocomplete="off"
                        >
                        <button type="submit" class="chat-send" id="chat-send">
                            ➤
                        </button>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(widget);
    }

    bindEvents() {
        const toggleBtn = document.getElementById('chat-toggle');
        const closeBtn = document.getElementById('chat-close');
        const form = document.getElementById('chat-form');
        const input = document.getElementById('chat-input');

        toggleBtn.addEventListener('click', () => this.toggle());
        closeBtn.addEventListener('click', () => this.close());
        form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        const window = document.getElementById('chat-window');
        const button = document.getElementById('chat-toggle');
        
        window.classList.add('open');
        button.classList.add('active');
        button.innerHTML = '×';
        this.isOpen = true;
        
        // Focus input
        setTimeout(() => {
            document.getElementById('chat-input').focus();
        }, 100);
    }

    close() {
        const window = document.getElementById('chat-window');
        const button = document.getElementById('chat-toggle');
        
        window.classList.remove('open');
        button.classList.remove('active');
        button.innerHTML = '💬';
        this.isOpen = false;
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || this.isTyping) return;
        
        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        
        // Show typing indicator
        this.showTyping();
        
        try {
            const response = await fetch('/app/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Simulate typing delay
                setTimeout(() => {
                    this.hideTyping();
                    this.addMessage(data.response.message, 'bot', data.response.actions);
                }, 800);
            } else {
                this.hideTyping();
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTyping();
            this.addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'bot');
        }
    }

    addMessage(content, sender, actions = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message message-${sender}`;
        
        if (sender === 'bot') {
            messageDiv.innerHTML = `
                <div class="message-bot">
                    <div class="bot-avatar">🤖</div>
                    <div>
                        <div class="message-content">${this.formatMessage(content)}</div>
                        ${actions ? this.createActionButtons(actions) : ''}
                    </div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-user">
                    <div class="message-content">${this.escapeHtml(content)}</div>
                </div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    createActionButtons(actions) {
        if (!actions || actions.length === 0) return '';
        
        const buttonsHtml = actions.map(action => {
            if (action.url) {
                return `<a href="${action.url}" class="action-button">${action.text}</a>`;
            } else if (action.action) {
                return `<button class="action-button" onclick="chatWidget.handleAction('${action.action}')">${action.text}</button>`;
            }
            return '';
        }).join('');
        
        return `<div class="message-actions">${buttonsHtml}</div>`;
    }

    async handleAction(action) {
        // Show typing indicator
        this.showTyping();
        
        try {
            const response = await fetch('/app/chat/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify({ action })
            });
            
            const data = await response.json();
            
            if (data.success) {
                setTimeout(() => {
                    this.hideTyping();
                    this.addMessage(data.response.message, 'bot', data.response.actions);
                }, 500);
            } else {
                this.hideTyping();
                this.addMessage('Sorry, I couldn\'t complete that action.', 'bot');
            }
        } catch (error) {
            console.error('Action error:', error);
            this.hideTyping();
            this.addMessage('Sorry, something went wrong.', 'bot');
        }
    }

    showTyping() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        const messagesContainer = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="bot-avatar">🤖</div>
            <div>
                Assistant is typing
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
        
        // Disable input
        document.getElementById('chat-send').disabled = true;
    }

    hideTyping() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        // Enable input
        document.getElementById('chat-send').disabled = false;
    }

    showWelcomeMessage() {
        setTimeout(() => {
            this.addMessage(
                "Hi! 👋 I'm your Student Tracker assistant. I can help you with:\n\n• Location sharing\n• Class enrollment\n• Navigation\n• General questions\n\nJust ask me anything!",
                'bot',
                [
                    { text: 'Location Help', action: 'location' },
                    { text: 'Class Help', action: 'classes' },
                    { text: 'General Help', action: 'help' }
                ]
            );
        }, 1000);
    }

    formatMessage(message) {
        // Convert markdown-style formatting to HTML
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/• /g, '• ');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
}

// Initialize chat widget when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user is logged in
    if (document.body.classList.contains('layout')) {
        window.chatWidget = new ChatWidget();
    }
});