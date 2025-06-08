document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    
    // ИЗМЕНЕНО: Получаем поле по новому ID
    const usernameInput = document.getElementById('floatingUsername'); 
    const passwordInput = document.getElementById('floatingPassword');

    // URL вашего FastAPI бэкенда
    const API_URL = 'http://127.0.0.1:8001/login';

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Предотвращаем перезагрузку страницы

        errorMessage.classList.add('d-none');
        errorMessage.textContent = '';

        // Получаем значения из полей
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            errorMessage.textContent = 'Пожалуйста, введите логин и пароль.';
            errorMessage.classList.remove('d-none');
            return;
        }

        // Выполняем вызов API
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username, // Бэкенд ожидает именно поле 'username'
                    password: password
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // УСПЕХ
                console.log('Вход успешен:', data);
                alert(`Добро пожаловать, ${data.username}!`);
                
            } else {
                // ОШИБКА
                errorMessage.textContent = data.detail || 'Произошла неизвестная ошибка.';
                errorMessage.classList.remove('d-none');
            }
        } catch (error) {
            // ОШИБКА СЕТИ
            console.error('Ошибка запроса на вход:', error);
            errorMessage.textContent = 'Не удалось подключиться к серверу. Попробуйте позже.';
            errorMessage.classList.remove('d-none');
        }
    });
});