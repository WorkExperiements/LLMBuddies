// Chat history storage
let chatHistory = [];
let currentSessionId = null;
let urlEnabled = false;

// Load available models and setup collapsible when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadAvailableModels();
    setupCollapsible();
    setupUrlToggle();
});

function setupCollapsible() {
    const collapsibles = document.getElementsByClassName('collapsible');
    for (let i = 0; i < collapsibles.length; i++) {
        collapsibles[i].addEventListener('click', function() {
            this.classList.toggle('collapsed');
            const content = this.nextElementSibling;
            content.classList.toggle('collapsed');
        });
    }
}

function setupUrlToggle() {
    const urlToggle = document.getElementById('url-toggle');
    const urlInputContainer = document.getElementById('url-input-container');
    
    urlToggle.addEventListener('change', function() {
        urlEnabled = this.checked;
        urlInputContainer.style.display = urlEnabled ? 'block' : 'none';
    });
}

async function loadAvailableModels() {
    try {
        const response = await fetch('/models/configured');
        const data = await response.json();
        const modelSelect = document.getElementById('model-select');
        
        // Clear existing options except the first one
        while (modelSelect.options.length > 1) {
            modelSelect.remove(1);
        }

        // Add new options
        for (const [modelId, modelInfo] of Object.entries(data)) {
            const option = document.createElement('option');
            option.value = modelId;
            option.textContent = modelInfo.display_name;
            modelSelect.appendChild(option);
        }
    } catch (error) {
        alert('Error loading available models: ' + error.message);
    }
}

function clearSession() {
    currentSessionId = null;
    chatHistory = [];
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    document.getElementById('session-id').value = '';
    alert('Session cleared');
}

async function loadSession() {
    const sessionId = document.getElementById('session-id').value.trim();
    if (!sessionId) {
        alert('Please enter a session ID');
        return;
    }

    try {
        const response = await fetch(`/chat/session/${sessionId}`);
        const data = await response.json();
        
        // Clear existing chat
        chatHistory = [];
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';
        
        // Load history from session
        if (data.history && data.history.length > 0) {
            chatHistory = data.history;
            for (const msg of data.history) {
                const prefix = msg.role === 'user' ? 'You: ' : 'Assistant: ';
                addMessageToChat(prefix + msg.content, msg.role + '-message');
            }
        }
        
        currentSessionId = sessionId;
        alert('Session loaded successfully');
    } catch (error) {
        alert('Error loading session: ' + error.message);
    }
}

async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const modelSelect = document.getElementById('model-select');
    const sendButton = document.getElementById('send-button');
    const message = messageInput.value.trim();
    const modelId = modelSelect.value;
    
    if (!message) return;
    
    if (!modelId) {
        alert('Please select a model first');
        return;
    }
    
    // Disable send button and change text
    sendButton.disabled = true;
    sendButton.textContent = 'Sending...';
    
    // Add user message to chat and history
    addMessageToChat('You: ' + message, 'user-message');
    chatHistory.push({ role: 'user', content: message });
    messageInput.value = '';

    try {
        // Filter out any history items that don't have both role and content
        const validHistory = chatHistory.filter(msg => msg.role && msg.content);
        
        const payload = { 
            message: message,
            model_id: modelId,
            history: validHistory,
            session_id: currentSessionId,
            url_enabled: urlEnabled
        };

        // Add URL if enabled and provided
        if (urlEnabled) {
            const urlInput = document.getElementById('url-input');
            if (urlInput.value.trim()) {
                payload.url = urlInput.value.trim();
            }
        }

        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        // Only add assistant message to history if it has content
        if (data.response) {
            // Add assistant response to chat and history
            addMessageToChat('Assistant: ' + data.response, 'assistant-message');
            chatHistory.push({ role: 'assistant', content: data.response });
        }
    } catch (error) {
        addMessageToChat('Error: ' + error.message, 'error-message');
        console.log('Error:', error);
    } finally {
        // Re-enable send button and restore text
        sendButton.disabled = false;
        sendButton.textContent = 'Send';
    }
}

function addMessageToChat(message, className) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', className);
    messageElement.textContent = message;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle Enter key in message input
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});