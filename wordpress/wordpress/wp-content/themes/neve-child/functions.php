<?php
/**
 * neve Theme functions and definitions.
 *
 * @link https://developer.wordpress.org/themes/basics/theme-functions/
 *
 * @package neve
 */


add_action( 'wp_enqueue_scripts', 'neve_child_parent_theme_enqueue_styles' );

/**
 * Enqueue scripts and styles.
 */
function neve_child_parent_theme_enqueue_styles() {
        $version = "3.1";
        wp_enqueue_style( 'neve-style', get_template_directory_uri() . '/style.css', $version);
        wp_enqueue_style( 'neve-child-style',
        get_stylesheet_directory_uri() . '/style.css', [ 'neve-style' ], $version);
        wp_enqueue_script('login-page', get_stylesheet_directory_uri() . '/js/login-page.js', array('jquery'), $version, true);
        wp_enqueue_script('login_page_admin', get_stylesheet_directory_uri() . '/js/login_page_admin.js', array('jquery'), $version, true);
        wp_enqueue_script('admin-panel', get_stylesheet_directory_uri() . '/js/admin-panel.js', array('jquery'), $version, true);

}






































// // Регистрация Custom Post Type "Фронтальные погрузчики"
// function register_cpt_front_loaders() {
//         $labels = array(
//             'name' => 'Фронтальные погрузчики',
//             'singular_name' => 'Фронтальный погрузчик',
//             'add_new' => 'Добавить погрузчик',
//             'add_new_item' => 'Добавить новый погрузчик',
//             'edit_item' => 'Редактировать погрузчик',
//             'new_item' => 'Новый погрузчик',
//             'view_item' => 'Просмотреть погрузчик',
//             'search_items' => 'Найти погрузчики',
//             'not_found' => 'Погрузчики не найдены',
//             'not_found_in_trash' => 'В корзине погрузчиков не найдено',
//             'all_items' => 'Все погрузчики',
//         );
    
//         $args = array(
//             'labels' => $labels,
//             'public' => true,
//             'has_archive' => true,
//             'menu_position' => 5,
//             'menu_icon' => 'dashicons-hammer',
//             'supports' => array('title', 'editor', 'thumbnail', 'excerpt', 'custom-fields'),
//             'rewrite' => array('slug' => 'neve-child/page-templates/catalog/Front_loaders'), // Измененный путь
//         );
    
//         register_post_type('front_loaders', $args);
//     }
//     add_action('init', 'register_cpt_front_loaders');
    
//     // Регистрация таксономии с обновленным ЧПУ
//     function register_taxonomy_front_loader_categories() {
//         register_taxonomy(
//             'front_loader_categories',
//             'front_loaders',
//             array(
//                 'labels' => array(
//                     'name' => 'Категории',
//                     'singular_name' => 'Категория',
//                     'search_items' => 'Найти категории',
//                     'all_items' => 'Все категории',
//                     'edit_item' => 'Редактировать категорию',
//                     'add_new_item' => 'Добавить новую категорию',
//                 ),
//                 'hierarchical' => true,
//                 'show_admin_column' => true,
//                 'rewrite' => array('slug' => 'neve-child/page-templates/catalog/Front_loaders'), // Измененный путь
//             )
//         );
//     }
//     add_action('init', 'register_taxonomy_front_loader_categories');

//     // Добавляем метабоксы для "Фронтальных погрузчиков"
// function front_loaders_add_meta_boxes() {
//         add_meta_box(
//             'front_loaders_tech_specs', // ID метабокса
//             'Технические характеристики', // Название метабокса
//             'front_loaders_tech_specs_callback', // Функция отображения
//             'front_loaders', // Кастомный тип записи
//             'normal', // Расположение
//             'high' // Приоритет
//         );
    
//         add_meta_box(
//             'front_loaders_additional_image', // ID метабокса
//             'Дополнительное изображение', // Название метабокса
//             'front_loaders_additional_image_callback', // Функция отображения
//             'front_loaders', // Кастомный тип записи
//             'side', // Расположение
//             'low' // Приоритет
//         );
//     }
//     add_action('add_meta_boxes', 'front_loaders_add_meta_boxes');

//     // Функция отображения метабокса для технических характеристик
// function front_loaders_tech_specs_callback($post) {
//         // Получаем текущее значение из метаполя
//         $tech_specs = get_post_meta($post->ID, '_tech_specs', true);
//         wp_nonce_field('front_loaders_save_meta_box_data', 'front_loaders_meta_box_nonce'); // Нонcе-поле для безопасности
    
//         echo '<textarea style="width:100%; height:150px;" name="front_loaders_tech_specs">' . esc_textarea($tech_specs) . '</textarea>';
//         echo '<p>Введите технические характеристики для данного погрузчика.</p>';
//     }
    
//     // Функция отображения метабокса для дополнительного изображения
//     function front_loaders_additional_image_callback($post) {
//         // Получаем текущее значение из метаполя
//         $additional_image = get_post_meta($post->ID, '_additional_image', true);
//         wp_nonce_field('front_loaders_save_meta_box_data', 'front_loaders_meta_box_nonce'); // Нонcе-поле для безопасности
    
//         echo '<input type="text" style="width:100%;" name="front_loaders_additional_image" id="front_loaders_additional_image" value="' . esc_url($additional_image) . '">';
//         echo '<button type="button" class="button" id="upload_image_button">Загрузить изображение</button>';
//         echo '<p>Вставьте URL изображения или загрузите новое.</p>';
//     }

    


//     // Сохраняем данные из метабоксов
// function front_loaders_save_meta_box_data($post_id) {
//         // Проверяем nonce для безопасности
//         if (!isset($_POST['front_loaders_meta_box_nonce']) || !wp_verify_nonce($_POST['front_loaders_meta_box_nonce'], 'front_loaders_save_meta_box_data')) {
//             return;
//         }
    
//         // Проверяем, является ли это автосохранением
//         if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
//             return;
//         }
    
//         // Проверяем тип записи
//         if (!isset($_POST['post_type']) || $_POST['post_type'] !== 'front_loaders') {
//             return;
//         }
    
//         // Сохраняем технические характеристики
//         if (isset($_POST['front_loaders_tech_specs'])) {
//             update_post_meta($post_id, '_tech_specs', sanitize_textarea_field($_POST['front_loaders_tech_specs']));
//         }
    
//         // Сохраняем дополнительное изображение
//         if (isset($_POST['front_loaders_additional_image'])) {
//             update_post_meta($post_id, '_additional_image', esc_url_raw($_POST['front_loaders_additional_image']));
//         }
//     }
//     add_action('save_post', 'front_loaders_save_meta_box_data');

//     function enqueue_media_uploader() {
//         wp_enqueue_media();
//         wp_enqueue_script('custom-upload', get_template_directory_uri() . '/js/custom-upload.js', array('jquery'), null, true);
//     }
//     add_action('admin_enqueue_scripts', 'enqueue_media_uploader');
    



    












   

    






    
    
    
    

    

    