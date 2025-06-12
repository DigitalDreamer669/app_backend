<?php
/**
* Template Name: login_page
*/
get_header();
?>
<div class="container-fluid vh-100 d-flex justify-content-center align-items-center">
    <div class="login-container">
        <div class="text-center mb-4">
            <img src="<?php echo get_stylesheet_directory_uri(); ?>/logo.png" alt="Логотип" class="logo-img mb-3">
            <h1 class="h3 mb-3 fw-normal">С возвращением!</h1>
            <p>Пожалуйста, войдите в свой аккаунт</p>
        </div>
        <form id="loginForm">
            <div class="form-floating mb-3">
                <input type="text" class="form-control" id="floatingUsername" placeholder="Ваш логин" required autocomplete="username">
                <label for="floatingUsername">Логин</label>
            </div>
            <div class="form-floating mb-3">
                <input type="password" class="form-control" id="floatingPassword" placeholder="Пароль" required autocomplete="current-password">
                <label for="floatingPassword">Пароль</label>
            </div>

            <button class="w-100 btn btn-lg btn-primary" type="submit">Войти</button>

            <div class="text-center mt-3">
                <a href="#" class="forgot-password-link">Забыли пароль?</a>
            </div>
        </form>
        <p id="errorMessage" class="text-danger mt-3 text-center d-none"></p>
    </div>
</div>
<?php
get_footer();
?>