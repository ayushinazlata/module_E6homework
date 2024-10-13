let chatSocket; 

function initializeChat(chatType, roomName, username) {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsURL = `${protocol}://${window.location.host}/ws/chat/${chatType}/${roomName}/`;
    
    chatSocket = new WebSocket(wsURL); // Используем глобальную переменную chatSocket

    chatSocket.onopen = function() {
        console.log('WebSocket connected');
        addMessageToChat('System', `${username} has joined the chat.`);
        updateConnectionStatus('CONNECTED');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        addMessageToChat(data.username, data.message);
    };

    chatSocket.onclose = function() {
        console.log('WebSocket closed');
        updateConnectionStatus('DISCONNECTED');
        document.getElementById('open-button').disabled = false;
    };

    chatSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateConnectionStatus('ERROR: WebSocket failed');
    };
}


// Функция для добавления сообщения в чат
function addMessageToChat(username, message) {
    const chatLog = document.getElementById('chat-log');
    const shouldScroll = chatLog.scrollTop + chatLog.clientHeight === chatLog.scrollHeight;

    const messageElement = document.createElement('div');
    messageElement.innerHTML = `<strong>${escapeHTML(username)}</strong>: ${escapeHTML(message)}`;
    chatLog.appendChild(messageElement);

    if (shouldScroll) {
        chatLog.scrollTop = chatLog.scrollHeight;
    }
}

// Функция для отправки сообщения
function sendMessage(event) {
    event.preventDefault();
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        const messageInput = document.getElementById('chat-message-input');
        const message = messageInput.value;
        const username = document.getElementById('username').value;

        chatSocket.send(JSON.stringify({
            'message': message,
            'username': username
        }));

        messageInput.value = ''; // Очистка поля ввода
    } else {
        alert('Cannot send message, WebSocket is not open.');
    }
}

// Функция для открытия соединения
function openConnection() {
    const chatType = document.getElementById('chat-type').value; // Получаем тип чата
    const roomName = document.getElementById('room-name').value; // Получаем имя комнаты
    const username = document.getElementById('username').value;

    if (!chatSocket || chatSocket.readyState === WebSocket.CLOSED) {
        initializeChat(chatType, roomName, username); // Вызов инициализации
        document.getElementById('open-button').disabled = true; // Отключаем кнопку после открытия соединения
    }
}

// Функция для закрытия соединения
function closeConnection() {
    if (chatSocket) {
        chatSocket.close();
        chatSocket = null; // Сбросить переменную
    }
}

// Функция для обновления статуса соединения
function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.innerText = status;
        statusElement.className = ''; // Сбросить предыдущие классы статуса
        if (status === 'CONNECTED') {
            statusElement.classList.add('text-success');
        } else if (status === 'DISCONNECTED') {
            statusElement.classList.add('text-danger');
        } else if (status === 'ERROR') {
            statusElement.classList.add('text-warning');
        }
    }
}

// Привязываем события к форме и кнопкам
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form'); // Убедитесь, что у вас есть этот элемент
    const closeButton = document.getElementById('close-button'); // Получаем кнопку закрытия

    if (chatForm) {
        chatForm.onsubmit = sendMessage; // Обработчик отправки сообщения
    }

    const openButton = document.getElementById('open-button');
    if (openButton) {
        openButton.addEventListener('click', openConnection); // Открытие соединения
    }

    if (closeButton) {
        closeButton.addEventListener('click', closeConnection); // Закрытие соединения
    }
});

// Экранирование HTML
function escapeHTML(unsafe) {
    return unsafe.replace(/[&<>"']/g, function(match) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return map[match];
    });
}
