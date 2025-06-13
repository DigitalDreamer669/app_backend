// admin-panel.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Get references to all necessary DOM elements ---
    const userTableBody = document.getElementById('user-table-body');
    const addUserBtn = document.getElementById('addUserBtn');
    const logoutButton = document.getElementById('logoutButton');

    // Modal window elements
    const userModalEl = document.getElementById('userModal');
    const userModal = userModalEl ? new bootstrap.Modal(userModalEl) : null;
    const userModalLabel = document.getElementById('userModalLabel');
    const userForm = document.getElementById('userForm');
    const userIdInput = document.getElementById('userId');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const isActiveInput = document.getElementById('is_active');
    const typeOfUserInput = document.getElementById('type_of_user'); // <<< NEW ELEMENT
    const modalErrorMessage = document.getElementById('modalErrorMessage');
    const passwordHelpText = document.querySelector('#password + .form-text');

    // --- API and Token Settings ---
    const API_BASE_URL = 'http://127.0.0.1:8001/admin/users';
    const token = sessionStorage.getItem('admin_token');

    // --- Main function: check authorization and initialize ---
    const initialize = () => {
        if (!token) {
            alert('Вы не авторизованы. Пожалуйста, войдите.');
            window.location.href = '/login-admin';
            return;
        }
        if (userTableBody) {
             fetchUsers();
        }
    };

    // --- Function to fetch and display users ---
    const fetchUsers = async () => {
        if (!userTableBody) return;
        // CHANGED: colspan is now 5
        userTableBody.innerHTML = `<tr><td colspan="5" class="text-center">Загрузка...</td></tr>`;

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

            const users = await response.json();
            renderTable(users);

        } catch (error) {
            console.error("Error in fetchUsers:", error);
            userTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Не удалось загрузить данные: ${error.message}</td></tr>`;
        }
    };

    // --- Function to render the table ---
    const renderTable = (users) => {
        userTableBody.innerHTML = '';
        if (!users || users.length === 0) {
            // CHANGED: colspan is now 5
            userTableBody.innerHTML = '<tr><td colspan="5" class="text-center">Пользователи не найдены.</td></tr>';
            return;
        }

        users.forEach(user => {
            const row = document.createElement('tr');
            // CHANGED: Added a new cell for type_of_user
            row.innerHTML = `
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>${user.type_of_user || '<span class="text-muted">Не указан</span>'}</td>
                <td>
                    <span class="badge ${user.is_active ? 'bg-success' : 'bg-secondary'}">
                        ${user.is_active ? 'Да' : 'Нет'}
                    </span>
                </td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-sm btn-primary edit-btn" data-user='${JSON.stringify(user)}' title="Редактировать">
                            <i class="bi bi-pencil-square"></i>
                        </button>
                        <button class="btn btn-sm btn-danger delete-btn" data-id="${user.id}" data-username="${user.username}" title="Удалить">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            userTableBody.appendChild(row);
        });
    };

    // --- Event Handlers ---

    // Click "Add User"
    if (addUserBtn) {
        addUserBtn.addEventListener('click', () => {
            userForm.reset();
            userIdInput.value = '';
            userModalLabel.textContent = 'Добавить нового пользователя';
            passwordInput.required = true;
            passwordHelpText.textContent = 'Пароль должен содержать минимум 6 символов.';
            modalErrorMessage.classList.add('d-none');
            if (userModal) userModal.show();
        });
    }

    // Use event delegation for buttons in the table
    if (userTableBody) {
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
                isActiveInput.checked = userData.is_active;
                typeOfUserInput.value = userData.type_of_user || ''; // <<< CHANGED
                passwordInput.required = false; 
                passwordHelpText.textContent = 'Введите новый пароль, чтобы изменить его. Иначе оставьте пустым.';
                modalErrorMessage.classList.add('d-none');
                if (userModal) userModal.show();
            }

            if (target.classList.contains('delete-btn')) {
                const userId = target.dataset.id;
                const username = target.dataset.username;
                if (confirm(`Вы уверены, что хотите удалить пользователя "${username}"?`)) {
                    deleteUser(userId);
                }
            }
        });
    }

    // Form submission (for both create and update)
    if (userForm) {
        userForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            
            const userId = userIdInput.value;
            const isUpdate = !!userId;
            
            const url = isUpdate ? `${API_BASE_URL}/${userId}` : API_BASE_URL;
            const method = isUpdate ? 'PUT' : 'POST';

            // CHANGED: Added type_of_user to the data object
            const userData = {
                username: usernameInput.value,
                email: emailInput.value,
                is_active: isActiveInput.checked,
                type_of_user: typeOfUserInput.value.trim(),
            };

            if (passwordInput.value) {
                userData.password = passwordInput.value;
            } else if (!isUpdate) {
                modalErrorMessage.textContent = 'Пароль обязателен для нового пользователя.';
                modalErrorMessage.classList.remove('d-none');
                return;
            }
            
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

                if (userModal) userModal.hide();
                fetchUsers();
            } catch (error) {
                 modalErrorMessage.textContent = error.message;
                 modalErrorMessage.classList.remove('d-none');
            }
        });
    }

    // --- Delete User Function ---
    const deleteUser = async (userId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.status === 204) {
                fetchUsers();
            } else {
                const data = await response.json();
                throw new Error(data.detail || 'Ошибка удаления');
            }
        } catch (error) {
            alert(`Не удалось удалить пользователя: ${error.message}`);
        }
    };
    
    // --- Logout Logic ---
    const handleLogout = () => {
        sessionStorage.removeItem('admin_token');
        window.location.href = '/login-admin';
    };

    if(logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }

    // --- Initialize the application ---
    initialize();
});
