// admin-panel.js - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ

document.addEventListener('DOMContentLoaded', () => {
    // --- Получение ссылок на все нужные элементы DOM ---
    const userTableBody = document.getElementById('user-table-body');
    const addUserBtn = document.getElementById('addUserBtn');
    const logoutButton = document.getElementById('logoutButton');
    
    // Элементы модального окна
    const userModalEl = document.getElementById('userModal');
    const userModal = new bootstrap.Modal(userModalEl);
    const userModalLabel = document.getElementById('userModalLabel');
    const userForm = document.getElementById('userForm');
    const userIdInput = document.getElementById('userId');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const isActiveInput = document.getElementById('is_active');
    const modalErrorMessage = document.getElementById('modalErrorMessage');
    const passwordHelpText = document.querySelector('#password + .form-text');

    // --- Настройки API и токена ---
    const API_BASE_URL = 'http://127.0.0.1:8001/admin/users';
    const token = sessionStorage.getItem('admin_token');

    // --- Главная функция: проверка авторизации и запуск ---
    const initialize = () => {
        if (!token) {
            alert('Вы не авторизованы. Пожалуйста, войдите.');
            window.location.href = 'admin.html'; // Убедитесь, что у вас есть эта страница
            return;
        }
        fetchUsers();
    };

    // --- Функция для загрузки и отображения пользователей ---
    const fetchUsers = async () => {
        try {
            const response = await fetch(API_BASE_URL, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                alert('Ваша сессия истекла или недействительна. Пожалуйста, войдите снова.');
                handleLogout();
                return;
            }

            if (!response.ok) {
                throw new Error(`Ошибка при загрузке пользователей: ${response.statusText}`);
            }

            // API возвращает массив напрямую, без ключа "data"
            const users = await response.json();
            renderTable(users);

        } catch (error) {
            console.error("Ошибка в fetchUsers:", error);
            userTableBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Не удалось загрузить данные: ${error.message}</td></tr>`;
        }
    };

    // --- Функция для отрисовки таблицы ---
    const renderTable = (users) => {
        userTableBody.innerHTML = '';
        if (!users || users.length === 0) {
            userTableBody.innerHTML = '<tr><td colspan="4" class="text-center">Пользователи не найдены.</td></tr>';
            return;
        }
        
        users.forEach(user => {
            const row = document.createElement('tr');
            
            // ================================================================
            // ИЗМЕНЕНИЯ ЗДЕСЬ:
            // 1. Убрали <div class="btn-group">.
            // 2. Добавили текст рядом с иконками.
            // 3. Обернули текст в <span class="d-none d-sm-inline"> для адаптивности.
            //    Текст будет скрыт на самых маленьких экранах (портрет телефона).
            // 4. Добавили класс `action-buttons` для стилизации.
            // ================================================================
            row.innerHTML = `
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>
                    <span class="badge ${user.is_active ? 'bg-success' : 'bg-secondary'}">
                        ${user.is_active ? 'Да' : 'Нет'}
                    </span>
                </td>
                <td class="text-end action-buttons">
                    <button class="btn btn-primary edit-btn" 
                            data-user='${JSON.stringify(user)}' 
                            data-bs-toggle="tooltip" 
                            title="Редактировать">
                        <i class="bi bi-pencil-square"></i>
                        <span class="d-none d-sm-inline">Редактировать</span>
                    </button>
                    <button class="btn btn-danger delete-btn" 
                            data-id="${user.id}" 
                            data-username="${user.username}" 
                            data-bs-toggle="tooltip" 
                            title="Удалить">
                        <i class="bi bi-trash"></i>
                        <span class="d-none d-sm-inline">Удалить</span>
                    </button>
                </td>
            `;
            userTableBody.appendChild(row);
        });

        // Инициализация всплывающих подсказок Bootstrap (остается без изменений)
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    };

    // --- Обработка событий ---
    
    // Клик на "Добавить пользователя"
    addUserBtn.addEventListener('click', () => {
        userForm.reset();
        userIdInput.value = '';
        userModalLabel.textContent = 'Добавить нового пользователя';
        passwordInput.required = true;
        passwordHelpText.textContent = 'Пароль должен содержать минимум 6 символов.';
        modalErrorMessage.classList.add('d-none');
        userModal.show();
    });

    // Делегирование событий для кнопок в таблице
    userTableBody.addEventListener('click', (event) => {
        const target = event.target.closest('button');
        if (!target) return;

        if (target.classList.contains('edit-btn')) {
            const userData = JSON.parse(target.dataset.user);
            userForm.reset();
            userModalLabel.textContent = `Редактировать: ${userData.username}`;
            userIdInput.value = userData.id;
            usernameInput.value = userData.username;
            emailInput.value = userData.email;
            passwordInput.value = userData.password;
            isActiveInput.checked = userData.is_active;
            passwordInput.required = true; // Пароль всегда обязателен, согласно Pydantic модели
            passwordHelpText.textContent = 'Вы должны подтвердить старый или ввести новый пароль.';
            modalErrorMessage.classList.add('d-none');
            userModal.show();
        }

        if (target.classList.contains('delete-btn')) {
            const userId = target.dataset.id;
            const username = target.dataset.username;
            if (confirm(`Вы уверены, что хотите удалить пользователя "${username}"?`)) {
                deleteUser(userId);
            }
        }
    });

    // Сохранение формы (создание или обновление)
    userForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        const userId = userIdInput.value;
        const isUpdate = !!userId;
        
        const url = isUpdate ? `${API_BASE_URL}/${userId}` : API_BASE_URL;
        const method = isUpdate ? 'PUT' : 'POST';

        const userData = {
            username: usernameInput.value,
            email: emailInput.value,
            password: passwordInput.value,
            is_active: isActiveInput.checked,
        };
        
        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Произошла ошибка при сохранении');
            }

            userModal.hide();
            fetchUsers(); // Обновляем таблицу после успешного действия
        } catch (error) {
             modalErrorMessage.textContent = error.message;
             modalErrorMessage.classList.remove('d-none');
        }
    });

    // --- Функция удаления пользователя ---
    const deleteUser = async (userId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.status === 204) {
                fetchUsers(); // Успешно удалено
            } else {
                const data = await response.json();
                throw new Error(data.detail || 'Ошибка удаления');
            }
        } catch (error) {
            alert(`Не удалось удалить пользователя: ${error.message}`);
        }
    };
    
    // --- Логика выхода ---
    const handleLogout = () => {
        sessionStorage.removeItem('admin_token');
        window.location.href = 'admin.html'; // или ваша страница входа
    };

    logoutButton.addEventListener('click', handleLogout);

    // --- Запуск приложения ---
    initialize();
});