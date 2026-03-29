document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('chatbot-toggle');
    const chatContainer = document.querySelector('.chatbot-container');
    const messageForm = document.getElementById('chatbot-form');
    const messageInput = document.getElementById('chatbot-input-field');
    const messagesDisplay = document.querySelector('.chatbot-messages');
    const typingIndicator = document.querySelector('.typing-indicator');

    // Toggle chat window
    toggleBtn.addEventListener('click', () => {
        chatContainer.classList.toggle('active');
        toggleBtn.classList.toggle('active');
        const icon = toggleBtn.querySelector('i');
        if (chatContainer.classList.contains('active')) {
            icon.classList.remove('bi-chat-dots-fill');
            icon.classList.add('bi-x-lg');
            messageInput.focus();
        } else {
            icon.classList.remove('bi-x-lg');
            icon.classList.add('bi-chat-dots-fill');
        }
    });

    // Initial welcome message
    setTimeout(() => {
        if (messagesDisplay.children.length === 1) { // Only welcome if empty (except typing)
            addMessage("Hi! 👋 I'm your EventHub assistant. How can I help you today?", 'bot', null, ["Upcoming Events", "How to Register", "Contact Support"]);
        }
    }, 1000);

    // Handle message submission
    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;
        submitMessage(message);
    });

    async function submitMessage(message) {
        // Add user message to UI
        addMessage(message, 'user');
        messageInput.value = '';

        // Show typing indicator
        showTyping(true);

        try {
            const response = await fetch('/chatbot/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            showTyping(false);

            if (data.error) {
                addMessage("Sorry, I encountered an error. Please try again.", 'bot');
            } else {
                addMessage(data.text, 'bot', data.events, data.chips);
            }
        } catch (error) {
            showTyping(false);
            addMessage("Unable to connect to the assistant.", 'bot');
            console.error('Chatbot error:', error);
        }
    }

    function addMessage(text, side, events = null, chips = null) {
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `chat-message-wrapper ${side}`;

        const div = document.createElement('div');
        div.className = `chat-message ${side}`;

        // Basic markdown formatting for bold text and newlines
        let formattedText = text
            .replace(/\*\*([\s\S]*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        div.innerHTML = formattedText;

        if (events && events.length > 0) {
            const eventListDiv = document.createElement('div');
            eventListDiv.className = 'chat-event-list';

            events.forEach(event => {
                const a = document.createElement('a');
                a.className = 'chat-event-card';
                a.href = event.url;
                a.innerHTML = `
                    <h5>${event.title}</h5>
                    <p><i class="bi bi-calendar-event me-1"></i>${event.date}</p>
                    <p><i class="bi bi-geo-alt me-1"></i>${event.location} • ${event.price}</p>
                `;
                eventListDiv.appendChild(a);
            });
            div.appendChild(eventListDiv);
        }

        messageWrapper.appendChild(div);

        // Add Chips/Quick Replies
        if (chips && chips.length > 0) {
            const chipsDiv = document.createElement('div');
            chipsDiv.className = 'chat-chips';
            chips.forEach(chipText => {
                const chip = document.createElement('button');
                chip.className = 'chat-chip';
                chip.innerText = chipText;
                chip.onclick = () => submitMessage(chipText);
                chipsDiv.appendChild(chip);
            });
            messageWrapper.appendChild(chipsDiv);
        }

        messagesDisplay.appendChild(messageWrapper);
        messagesDisplay.scrollTop = messagesDisplay.scrollHeight;
    }

    function showTyping(show) {
        typingIndicator.style.display = show ? 'block' : 'none';
        if (show) {
            messagesDisplay.scrollTop = messagesDisplay.scrollHeight;
        }
    }

    // Helper to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
