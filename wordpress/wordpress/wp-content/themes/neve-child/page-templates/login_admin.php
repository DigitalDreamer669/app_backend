<?php
get_header();
/**
* Template Name: login_page_admin
*/
?>


    <div class="container-fluid vh-100 d-flex justify-content-center align-items-center">
        <div class="login-container">
            
            <div id="welcomePanel" class="text-center d-none">
                <h1 class="h3 mb-3 fw-normal">Админ-панель</h1>
                <p>Вы успешно вошли в систему.</p>
                <p>Ваш токен сохранен для этой сессии.</p>
                <button id="logoutButton" class="w-100 btn btn-lg btn-danger mt-3">Выйти</button>
            </div>

            <form id="adminLoginForm">
                <div class="text-center mb-4">
                    <img src="logo.png" alt="Логотип" class="logo-img mb-3">
                    <h1 class="h3 mb-3 fw-normal">Панель администратора</h1>
                    <p>Пожалуйста, войдите для продолжения</p>
                </div>

                <div class="form-floating mb-3">
                    <input type="text" class="form-control" id="adminUsername" placeholder="Логин администратора" required autocomplete="username">
                    <label for="adminUsername">Логин администратора</label>
                </div>
                
                <div class="form-floating mb-3">
                    <input type="password" class="form-control" id="adminPassword" placeholder="Пароль" required autocomplete="current-password">
                    <label for="adminPassword">Пароль</label>
                </div>

                <button class="w-100 btn btn-lg btn-primary" type="submit">Войти</button>

                <p id="errorMessage" class="text-danger mt-3 text-center d-none"></p>
            </form>
        </div>
    </div>

<?php
get_footer();
