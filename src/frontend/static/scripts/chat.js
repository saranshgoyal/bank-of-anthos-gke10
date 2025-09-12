/*
 * Copyright 2024 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

document.addEventListener("DOMContentLoaded", function() {
    const chatBubble = document.getElementById('chat-bubble');
    const chatWindow = document.getElementById('chat-window');
    const openButton = document.getElementById('chat-open-button');
    const closeButton = document.getElementById('chat-close-button');
    const sendButton = document.getElementById('chat-send-button');
    const chatInput = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');

    function toggleChatWindow() {
        chatBubble.classList.toggle('hidden');
        chatWindow.classList.toggle('hidden');
        if (!chatWindow.classList.contains('hidden')) {
            chatInput.focus();
        }
    }

    openButton.addEventListener('click', toggleChatWindow);
    closeButton.addEventListener('click', toggleChatWindow);

    function addMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', `${sender}-message`);
        messageElement.textContent = text;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return messageElement;
    }

    async function sendMessage() {
        const messageText = chatInput.value.trim();
        if (messageText === '') return;

        addMessage(messageText, 'user');
        chatInput.value = '';
        chatInput.disabled = true;
        sendButton.disabled = true;

        const loadingElement = addMessage('...', 'assistant');
        loadingElement.classList.add('loading');

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }),
            });

            messagesContainer.removeChild(loadingElement);

            if (!response.ok) {
                addMessage('Sorry, I had trouble connecting. Please try again.', 'assistant');
                return;
            }

            const data = await response.json();
            if (data.error) {
                addMessage(data.error, 'assistant');
            } else {
                addMessage(data.response, 'assistant');
            }
        } catch (error) {
            console.error('Chat error:', error);
            messagesContainer.removeChild(loadingElement);
            addMessage('An unexpected error occurred. Please check the console.', 'assistant');
        } finally {
            chatInput.disabled = false;
            sendButton.disabled = false;
            chatInput.focus();
        }
    }

    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Initial greeting
    addMessage("Hello! How can I help you today?", 'assistant');
});