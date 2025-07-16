// 现代化AI助手交互脚本

class ChatApp {
    constructor() {
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.chatMessages = document.getElementById('chat-messages');
        this.charCount = document.getElementById('char-count');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.clearButton = document.getElementById('clear-chat');
        this.chatForm = document.getElementById('chat-form');

        this.initEventListeners();
        this.updateSendButton();
    }

    initEventListeners() {
        // 表单提交事件
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // 输入框事件
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.updateSendButton();
            this.autoResize();
        });

        // 键盘事件
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.shiftKey) {
                    // Shift + Enter: 允许换行
                    return;
                } else {
                    // Enter: 发送消息
                    e.preventDefault();
                    this.sendMessage();
                }
            }
        });

        // 清空对话
        this.clearButton.addEventListener('click', () => {
            this.clearChat();
        });

        // 滚动到底部
        this.chatMessages.addEventListener('DOMNodeInserted', () => {
            this.scrollToBottom();
        });
    }

    // 自动调整输入框高度
    autoResize() {
        this.messageInput.style.height = 'auto';
        const maxHeight = 150;
        const newHeight = Math.min(this.messageInput.scrollHeight, maxHeight);
        this.messageInput.style.height = newHeight + 'px';
    }

    // 更新字符计数
    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = count;

        if (count > 1800) {
            this.charCount.style.color = 'var(--danger-color)';
        } else if (count > 1500) {
            this.charCount.style.color = 'var(--warning-color)';
        } else {
            this.charCount.style.color = 'var(--secondary-color)';
        }
    }

    // 更新发送按钮状态
    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText;
    }

    // 显示打字指示器
    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.scrollToBottom();
    }

    // 隐藏打字指示器
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    // 滚动到底部
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    // 添加消息到聊天区域
    addMessage(content, isUser = false) {
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message-container mb-4';

        const message = document.createElement('div');
        message.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';

        if (isUser) {
            messageText.textContent = content;
        } else {
            // 支持简单的Markdown渲染
            messageText.innerHTML = this.formatBotMessage(content);
        }

        messageContent.appendChild(messageText);
        message.appendChild(avatar);
        message.appendChild(messageContent);
        messageContainer.appendChild(message);

        this.chatMessages.appendChild(messageContainer);
        this.scrollToBottom();

        return messageContainer;
    }

    // 格式化机器人消息（简单的Markdown支持）
    formatBotMessage(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    // 发送消息
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // 禁用输入和发送按钮
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;

        // 添加用户消息
        this.addMessage(message, true);

        // 清空输入框
        this.messageInput.value = '';
        this.updateCharCount();
        this.autoResize();

        // 显示打字指示器
        this.showTypingIndicator();

        try {
            const response = await fetch('/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // 隐藏打字指示器
            this.hideTypingIndicator();

            // 添加机器人回复
            if (data.status === 'success') {
                this.addMessage(data.response);
            } else {
                this.addMessage('抱歉，处理您的请求时出现了问题。请稍后再试。');
            }

        } catch (error) {
            console.error('Error:', error);
            this.hideTypingIndicator();
            this.addMessage('网络连接错误，请检查网络连接后重试。');
        } finally {
            // 重新启用输入
            this.messageInput.disabled = false;
            this.messageInput.focus();
            this.updateSendButton();
        }
    }

    // 清空对话
    clearChat() {
        if (confirm('确定要清空所有对话吗？此操作无法撤销。')) {
            // 保留欢迎消息，清除其他消息
            const messages = this.chatMessages.querySelectorAll('.message-container');
            for (let i = 1; i < messages.length; i++) {
                messages[i].remove();
            }
        }
    }

    // 添加错误处理
    handleError(error) {
        console.error('Chat error:', error);
        this.hideTypingIndicator();
        this.addMessage('抱歉，发生了意外错误。请刷新页面后重试。');

        // 重新启用输入
        this.messageInput.disabled = false;
        this.sendButton.disabled = false;
        this.updateSendButton();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    const chatApp = new ChatApp();

    // 添加一些快捷功能

    // 双击输入框清空内容
    chatApp.messageInput.addEventListener('dblclick', () => {
        chatApp.messageInput.value = '';
        chatApp.updateCharCount();
        chatApp.updateSendButton();
        chatApp.autoResize();
    });

    // 页面可见性变化时的处理
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            chatApp.messageInput.focus();
        }
    });

    // 初始焦点
    chatApp.messageInput.focus();
});

// 全局错误处理
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// 未捕获的Promise错误处理
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});