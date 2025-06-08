 <?php
get_header();
/**
* Template Name: admin-panel
*/
?>
 <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Admin Panel</a>
            <button id="logoutButton" class="btn btn-outline-light">Выйти</button>
        </div>
    </nav>

    <main class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h1>Пользователи</h1>
            <button id="addUserBtn" class="btn btn-primary">
                <i class="bi bi-plus-circle"></i> Добавить пользователя
            </button>
        </div>

        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead>
                    <tr>
                        <th scope="col">Логин</th>
                        <th scope="col">Email</th>
                        <th scope="col">Активен</th>
                        <th scope="col" class="text-end">Действия</th>
                    </tr>
                </thead>
                <tbody id="user-table-body">
                    </tbody>
            </table>
        </div>
    </main>

    <div class="modal fade" id="userModal" tabindex="-1" aria-labelledby="userModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="userModalLabel">Добавить пользователя</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="userForm">
                        <input type="hidden" id="userId">
                        
                        <div class="mb-3">
                            <label for="username" class="form-label">Логин</label>
                            <input type="text" class="form-control" id="username" required>
                        </div>
                        <div class="mb-3">
                            <label for="email" class="form-label">Email</label>
                            <input type="email" class="form-control" id="email" required>
                        </div>
                        <div class="mb-3">
                            <label for="password" class="form-label">Пароль</label>
                            <input type="password" class="form-control" id="password" required>
                            <div class="form-text">Введите новый пароль или оставьте пустым, чтобы не менять.</div>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="is_active">
                            <label class="form-check-label" for="is_active">
                                Активен
                            </label>
                        </div>
                        <div id="modalErrorMessage" class="text-danger mt-2 d-none"></div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                    <button type="submit" form="userForm" class="btn btn-primary">Сохранить</button>
                </div>
            </div>
        </div>
    </div>
<?php
get_footer();
