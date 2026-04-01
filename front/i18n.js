/**
 * i18n.js — Мультиязычность (RU / KZ / EN)
 * ==========================================
 *
 * КАК ЭТО РАБОТАЕТ (для начинающих):
 *
 *   1. В HTML у текстовых элементов стоит атрибут data-i18n="ключ"
 *      Например: <h2 data-i18n="reg_title">Заявка</h2>
 *
 *   2. В объекте TRANSLATIONS хранятся переводы для каждого языка:
 *      { ru: { reg_title: "Заявка" }, kz: { reg_title: "Өтінім" }, en: { reg_title: "Application" } }
 *
 *   3. Функция setLanguage('kz') находит ВСЕ элементы с data-i18n
 *      и заменяет их текст на перевод из нужного языка.
 *
 *   4. Выбранный язык сохраняется в localStorage → при перезагрузке
 *      страницы язык не сбрасывается.
 */

'use strict';

// ─── Словарь переводов ────────────────────────────────────────────────────────
const TRANSLATIONS = {

  // ═══════════════════════════════════════════════════
  // РУССКИЙ
  // ═══════════════════════════════════════════════════
  ru: {
    // Header
    apply_btn:      'Подать заявку',

    // Landing / Hero
    badge:          '✨ Программа отбора 2026',
    hero_line1:     'Поступи в',
    hero_sub:       'Заполни анкету, пройди MBTI тест и языковой тест. Все данные защищены и отправляются в нашу систему.',
    cta_note:       'Бесплатно · ~15 минут · Данные защищены',
    steps:          'Шага',
    test:           'Тест',
    safe:           'Безопасно',

    // Registration form
    reg_title:      'Заявка',
    reg_sub:        'Заполни все поля для подачи заявки',
    label_name:     'Имя и фамилия *',
    label_city:     'Город *',
    label_region:   'Регион',
    label_langs:    'Знание языков *',
    label_tg:       'Telegram username *',
    label_hobbies:  'Хобби',
    label_sport:    'Спорт',
    choose:         '— выберите —',
    next_btn:       'Далее — MBTI тест →',
    ph_name:        'Иван Иванов',
    ph_region:      'Заполнится автоматически',
    ph_tg:          '@username',
    ph_hobbies:     'Чтение, музыка...',
    ph_sport:       'Плавание, бег...',

    // Validation errors
    err_fill_all:   'Пожалуйста, заполните все обязательные поля',
    err_select_lang:'Выберите хотя бы один язык',
    err_tg_format:  'Введите корректный Telegram username',

    // MBTI test
    mbti_title:     'Психометрический тест',
    back:           '← Назад',
    next_q:         'Далее →',
    finish_mbti:    'Завершить тест →',
    mbti_pick:      'Выберите один из вариантов',

    // Language test
    lang_title:     'Языковой тест',
    violations:     'Выходы из вкладки: 0',
    violation_warn: '⚠ Внимание! Не покидайте вкладку во время теста. Следующий выход приведёт к блокировке.',
    violation_block:'Тест заблокирован из-за повторного выхода из вкладки. Результаты отправлены автоматически.',
    finish_lang:    'Завершить тест →',
    time_up:        'Время вышло! Результаты отправлены автоматически.',

    // Submission
    sending:        'Отправляем...',
    send_error:     'Ошибка при отправке. Попробуйте ещё раз.',

    // Success
    success_title:  'Заявка отправлена!',
    success_sub:    'Все данные сохранены. Спасибо за заявку!',
    tg_redirect:    'Перейдите в Telegram, чтобы отслеживать статус вашей заявки:',
    go_home:        'На главную',

    // Login
    login_btn:      'Войти',
    login_title:    'Вход в панель',
    login_sub:      'Авторизация для администраторов',
    login_user:     'Логин',
    login_pass:     'Пароль',
    login_ok:       'Успешный вход!',
    login_fail:     'Неверный логин или пароль',
    ph_login:       'Введите логин',
  },

  // ═══════════════════════════════════════════════════
  // ҚАЗАҚША
  // ═══════════════════════════════════════════════════
  kz: {
    apply_btn:      'Өтінім беру',

    badge:          '✨ Іріктеу бағдарламасы 2026',
    hero_line1:     'Түсу',
    hero_sub:       'Анкетаны толтырыңыз, MBTI тестін және тіл тестін тапсырыңыз. Барлық деректер қорғалған.',
    cta_note:       'Тегін · ~15 минут · Деректер қорғалған',
    steps:          'Қадам',
    test:           'Тест',
    safe:           'Қауіпсіз',

    reg_title:      'Өтінім',
    reg_sub:        'Өтінім беру үшін барлық өрістерді толтырыңыз',
    label_name:     'Аты-жөні *',
    label_city:     'Қала *',
    label_region:   'Аймақ',
    label_langs:    'Тіл білімі *',
    label_tg:       'Telegram username *',
    label_hobbies:  'Хобби',
    label_sport:    'Спорт',
    choose:         '— таңдаңыз —',
    next_btn:       'Келесі — MBTI тест →',
    ph_name:        'Иван Иванов',
    ph_region:      'Автоматты түрде толтырылады',
    ph_tg:          '@username',
    ph_hobbies:     'Оқу, музыка...',
    ph_sport:       'Жүзу, жүгіру...',

    err_fill_all:   'Барлық міндетті өрістерді толтырыңыз',
    err_select_lang:'Кем дегенде бір тілді таңдаңыз',
    err_tg_format:  'Дұрыс Telegram username енгізіңіз',

    mbti_title:     'Психометриялық тест',
    back:           '← Артқа',
    next_q:         'Келесі →',
    finish_mbti:    'Тестті аяқтау →',
    mbti_pick:      'Нұсқалардың бірін таңдаңыз',

    lang_title:     'Тіл тесті',
    violations:     'Қойындыдан шығу: 0',
    violation_warn: '⚠ Назар аударыңыз! Тест кезінде қойындыдан шықпаңыз. Келесі шығу блоктауға әкеледі.',
    violation_block:'Қойындыдан қайта шыққандықтан тест бұғатталды. Нәтижелер автоматты түрде жіберілді.',
    finish_lang:    'Тестті аяқтау →',
    time_up:        'Уақыт бітті! Нәтижелер автоматты түрде жіберілді.',

    sending:        'Жіберілуде...',
    send_error:     'Жіберу қатесі. Қайта көріңіз.',

    success_title:  'Өтінім жіберілді!',
    success_sub:    'Барлық деректер сақталды. Өтінім үшін рахмет!',
    tg_redirect:    'Өтінім мәртебесін бақылау үшін Telegram-ға өтіңіз:',
    go_home:        'Басты бетке',

    login_btn:      'Кіру',
    login_title:    'Панельге кіру',
    login_sub:      'Әкімшілер үшін авторизация',
    login_user:     'Логин',
    login_pass:     'Құпия сөз',
    login_ok:       'Сәтті кіру!',
    login_fail:     'Логин немесе құпия сөз қате',
    ph_login:       'Логинді енгізіңіз',
  },

  // ═══════════════════════════════════════════════════
  // ENGLISH
  // ═══════════════════════════════════════════════════
  en: {
    apply_btn:      'Apply Now',

    badge:          '✨ Selection Program 2026',
    hero_line1:     'Join',
    hero_sub:       'Fill out the application, take the MBTI test and language test. All data is protected and sent to our system.',
    cta_note:       'Free · ~15 min · Data protected',
    steps:          'Steps',
    test:           'Test',
    safe:           'Secure',

    reg_title:      'Application',
    reg_sub:        'Fill in all fields to submit your application',
    label_name:     'Full name *',
    label_city:     'City *',
    label_region:   'Region',
    label_langs:    'Languages *',
    label_tg:       'Telegram username *',
    label_hobbies:  'Hobbies',
    label_sport:    'Sport',
    choose:         '— select —',
    next_btn:       'Next — MBTI test →',
    ph_name:        'John Smith',
    ph_region:      'Auto-filled',
    ph_tg:          '@username',
    ph_hobbies:     'Reading, music...',
    ph_sport:       'Swimming, running...',

    err_fill_all:   'Please fill in all required fields',
    err_select_lang:'Please select at least one language',
    err_tg_format:  'Please enter a valid Telegram username',

    mbti_title:     'Psychometric Test',
    back:           '← Back',
    next_q:         'Next →',
    finish_mbti:    'Finish test →',
    mbti_pick:      'Select one option',

    lang_title:     'Language Test',
    violations:     'Tab switches: 0',
    violation_warn: '⚠ Warning! Do not leave the tab during the test. Next exit will result in a block.',
    violation_block:'Test blocked due to repeated tab exit. Results submitted automatically.',
    finish_lang:    'Finish test →',
    time_up:        'Time is up! Results submitted automatically.',

    sending:        'Sending...',
    send_error:     'Submission error. Please try again.',

    success_title:  'Application sent!',
    success_sub:    'All data has been saved. Thank you for applying!',
    tg_redirect:    'Go to Telegram to track your application status:',
    go_home:        'Home',

    login_btn:      'Sign In',
    login_title:    'Admin Panel',
    login_sub:      'Authentication for administrators',
    login_user:     'Username',
    login_pass:     'Password',
    login_ok:       'Login successful!',
    login_fail:     'Invalid username or password',
    ph_login:       'Enter username',
  },
};


// ─── Текущий язык ─────────────────────────────────────────────────────────────
let currentLang = localStorage.getItem('lang') || 'ru';


// ─── Получить перевод по ключу ────────────────────────────────────────────────
function t(key) {
  const dict = TRANSLATIONS[currentLang] || TRANSLATIONS['ru'];
  return dict[key] || TRANSLATIONS['ru'][key] || key;
}


// ─── Применить язык ко всей странице ──────────────────────────────────────────
function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('lang', lang);

  // 1. Обновить все элементы с data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const translation = t(key);
    if (translation) {
      el.textContent = translation;
    }
  });

  // 2. Обновить placeholder'ы
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.getAttribute('data-i18n-ph');
    const translation = t(key);
    if (translation) {
      el.placeholder = translation;
    }
  });

  // 3. Обновить кнопки языков в header
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  // 4. Обновить title страницы
  const titles = { ru: 'inVision U — Подать заявку', kz: 'inVision U — Өтінім беру', en: 'inVision U — Apply Now' };
  document.title = titles[lang] || titles['ru'];

  // 5. Оповестить другие модули о смене языка
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
}


// ─── Инициализация ────────────────────────────────────────────────────────────
function initI18n() {
  // Применить сохранённый язык
  setLanguage(currentLang);

  // Слушаем клики на кнопки языков
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      setLanguage(btn.dataset.lang);
    });
  });
}

// Запускаем при загрузке DOM
document.addEventListener('DOMContentLoaded', initI18n);
