document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return; // Выходим, если формы нет на странице

    const errorMessage = document.getElementById('errorMessage');
    const usernameInput = document.getElementById('floatingUsername');
    const passwordInput = document.getElementById('floatingPassword');

    // URL вашего FastAPI бэкенда
    const API_URL = 'http://127.0.0.1:8001/login';

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Предотвращаем перезагрузку страницы

        // Скрываем старые ошибки
        errorMessage.classList.add('d-none');
        errorMessage.textContent = '';

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            errorMessage.textContent = 'Пожалуйста, введите логин и пароль.';
            errorMessage.classList.remove('d-none');
            return;
        }

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // --- УСПЕХ ---
                console.log('Вход успешен:', data);

                // ИЗМЕНЕНИЕ: Имя пользователя теперь в data.user_info
                alert(`Добро пожаловать, ${data.user_info.username}!`);
                
                // НОВОЕ: Сохраняем токен в localStorage для дальнейшего использования
                localStorage.setItem('accessToken', data.token);
                
                // НОВОЕ: Перенаправляем пользователя в личный кабинет или на главную
                // Замените '/dashboard' на URL вашей защищенной страницы
                window.location.href = '/dashboard'; 
                
            } else {
                // --- ОШИБКА АУТЕНТИФИКАЦИИ ---
                errorMessage.textContent = data.detail || 'Произошла неизвестная ошибка.';
                errorMessage.classList.remove('d-none');
            }
        } catch (error) {
            // --- ОШИБКА СЕТИ ИЛИ СЕРВЕРА ---
            console.error('Ошибка запроса на вход:', error);
            errorMessage.textContent = 'Не удалось подключиться к серверу. Попробуйте позже.';
            errorMessage.classList.remove('d-none');
        }
    });
});