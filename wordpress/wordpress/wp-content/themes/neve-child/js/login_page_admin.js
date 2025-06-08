// admin.js

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('adminLoginForm');
    const errorMessage = document.getElementById('errorMessage');
    
    const adminUsernameInput = document.getElementById('adminUsername');
    const adminPasswordInput = document.getElementById('adminPassword');

    const ADMIN_LOGIN_URL = 'http://127.0.0.1:8001/admin/login';

    const saveToken = (token) => {
        sessionStorage.setItem('admin_token', token);
    };

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        errorMessage.classList.add('d-none');

        const username = adminUsernameInput.value.trim();
        const password = adminPasswordInput.value.trim();

        // ================================================================
        // ШАГ ДИАГНОСТИКИ: Проверяем, что именно мы отправляем
        // ================================================================
        console.log("ПОПЫТКА ОТПРАВКИ ДАННЫХ:");
        console.log("Username, который мы отправляем:", username);
        console.log("Password, который мы отправляем:", password);
        // ================================================================

        try {
            const response = await fetch(ADMIN_LOGIN_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (response.ok) {
                saveToken(data.token);
                console.log('Успешный вход. Перенаправление...');
                window.location.href = 'http://localhost:7600/admin-panel/';
            } else {
                errorMessage.textContent = `Ошибка от сервера: ${data.detail || 'Неизвестная ошибка'}`;
                errorMessage.classList.remove('d-none');
            }
        } catch (error) {
            errorMessage.textContent = 'Не удалось подключиться к серверу или обработать ответ.';
            errorMessage.classList.remove('d-none');
        }
    });
});