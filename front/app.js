/**
 * app.js — Основная логика приложения inVision U
 * ================================================
 *
 * КАК ЭТО РАБОТАЕТ (для начинающих):
 *
 *   Приложение — это SPA (Single Page Application).
 *   Вместо перехода по страницам мы показываем/скрываем «экраны» (sections).
 *
 *   Поток пользователя:
 *     1. Landing (главная) — кликаешь "Подать заявку"
 *     2. Registration (анкета) — заполняешь поля → отправляешь в backend
 *     3. MBTI Test — 40 вопросов, по одному на экране, отвечаешь A или B
 *     4. Language Test — 20 вопросов с таймером (10 минут), контроль вкладки
 *     5. Success — «Заявка отправлена!» + ссылка на Telegram
 *
 *   Зависимости (загружаются ДО этого файла):
 *     - i18n.js → переводы (функция t(), setLanguage())
 *     - api.js  → API клиент (объект API с методами getCities, submitApplication и т.д.)
 */

'use strict';

// ─── Состояние приложения ─────────────────────────────────────────────────────
// Один объект хранит ВСЁ, что нужно знать о текущей сессии пользователя.
const state = {
  applicationId: null,    // ID заявки (приходит от backend после submit)
  mbtiIndex:     0,       // Номер текущего вопроса MBTI (0-39)
  mbtiAnswers:   {},      // Ответы MBTI: { q1: "A", q2: "B", ... }
  langIndex:     0,       // Номер текущего вопроса языкового теста (0-19)
  langAnswers:   {},      // Ответы: { q1: "B", q2: "A", ... }
  langTimer:     600,     // Осталось секунд (600 = 10 минут)
  langTimerId:   null,    // ID таймера (для clearInterval)
  violations:    0,       // Счётчик выходов из вкладки
  langBlocked:   false,   // Заблокирован ли тест
  langStartTime: null,    // Время начала теста (Date)
  selectedLangs: [],      // Выбранные языки в форме
  cities:        [],      // Список городов (с backend)
  languagesList: [],      // Список языков (с backend)
};


// ─── MBTI Вопросы (40 штук) ──────────────────────────────────────────────────
// Формат: key, text, optionA, optionB
// Backend ожидает ответы в формате { q1: "A", q2: "B", ... }
// A = первый вариант, B = второй вариант
const MBTI_QUESTIONS = [
  // ── Целеустремлённость (1-8) ──
  { key: 'q1',  text: 'Когда у меня есть важная цель, я...',
    a: 'Сразу составляю план и следую ему', b: 'Действую по ситуации и настроению' },
  { key: 'q2',  text: 'Я ставлю долгосрочные цели (на год+)?',
    a: 'Да, у меня есть чёткий план', b: 'Редко — предпочитаю краткосрочные задачи' },
  { key: 'q3',  text: 'Если я не успеваю в срок, я...',
    a: 'Пересматриваю план и наверстываю', b: 'Расстраиваюсь или прошу перенос' },
  { key: 'q4',  text: 'Моя учёба/работа над проектами...',
    a: 'Всегда структурирована: расписание и дедлайны', b: 'Хаотична, но результат бывает' },
  { key: 'q5',  text: 'Когда у меня несколько задач, я...',
    a: 'Приоритизирую и делаю по очереди', b: 'Переключаюсь по настроению' },
  { key: 'q6',  text: 'Как часто ты достигаешь своих целей?',
    a: 'Почти всегда — ставлю реалистичные цели', b: 'Примерно 50/50 или реже' },
  { key: 'q7',  text: 'Что мешает тебе достигать целей?',
    a: 'Ничего — я справляюсь', b: 'Прокрастинация или страх неудачи' },
  { key: 'q8',  text: 'Когда учишься чему-то новому, ты...',
    a: 'Предпочитаю чёткую структуру: курс, книга', b: 'Учусь на практике, пробуя разное' },

  // ── Мотивация (9-16) ──
  { key: 'q9',  text: 'Что мотивирует тебя работать усердно?',
    a: 'Желание стать профессионалом', b: 'Интерес к процессу обучения' },
  { key: 'q10', text: 'Когда занимаешься интересным делом, ты...',
    a: 'Теряю счёт времени — полностью погружаюсь', b: 'Интересно, но легко отвлекаюсь' },
  { key: 'q11', text: 'Если бы деньги не были проблемой, ты бы...',
    a: 'Продолжал(а) учиться и исследовать', b: 'Путешествовал(а) и отдыхал(а)' },
  { key: 'q12', text: 'Когда скучно в учёбе, ты...',
    a: 'Ищу более глубокий материал сам(а)', b: 'Жду, пока это закончится' },
  { key: 'q13', text: 'Твоя учёбная активность вне школы...',
    a: 'Высокая: онлайн-курсы, книги, проекты', b: 'Низкая: только если задали' },
  { key: 'q14', text: 'Когда достигаешь цели, ты обычно...',
    a: 'Радуюсь и ставлю новую, выше', b: 'Чувствую облегчение или быстро теряю интерес' },
  { key: 'q15', text: 'Насколько важно «быть лучшим»?',
    a: 'Очень — стремлюсь к мастерству', b: 'Мне важнее прогресс, чем сравнение' },
  { key: 'q16', text: 'Когда слышишь об успехе другого, ты...',
    a: 'Вдохновляюсь и думаю, как достичь подобного', b: 'Радуюсь, но иногда чувствую зависть' },

  // ── Стрессоустойчивость (17-24) ──
  { key: 'q17', text: 'Когда что-то пошло не по плану, ты...',
    a: 'Анализирую и ищу новый путь', b: 'Надолго застреваю в негативных мыслях' },
  { key: 'q18', text: 'В стрессовых ситуациях ты...',
    a: 'Концентрируюсь и работаю эффективнее', b: 'Сильно переживаю, что мешает работе' },
  { key: 'q19', text: 'После серьёзной неудачи ты восстанавливаешься...',
    a: 'Быстро — провал это урок', b: 'Долго — трудно прийти в себя' },
  { key: 'q20', text: 'Как воспринимаешь критику?',
    a: 'Как ценную обратную связь', b: 'С трудом — критика выбивает из колеи' },
  { key: 'q21', text: 'Если проект провалился, ты...',
    a: 'Честно анализирую свой вклад в провал', b: 'Предпочитаю не возвращаться к этой теме' },
  { key: 'q22', text: 'Когда тебя отвергают, ты...',
    a: 'Прошу фидбэк и готовлюсь попробовать снова', b: 'Долго переживаю и откладываю попытку' },
  { key: 'q23', text: 'Ты справляешься с неопределённостью...',
    a: 'Хорошо — это возможности', b: 'С трудом — неопределённость тревожит' },
  { key: 'q24', text: 'Когда устал(а) и нет сил, ты...',
    a: 'Отдыхаю осознанно, потом возвращаюсь', b: 'Теряю интерес, с трудом возвращаюсь' },

  // ── Командная работа (25-32) ──
  { key: 'q25', text: 'В групповом проекте ты...',
    a: 'Беру роль лидера и организую', b: 'Выполняю свою часть, не мешая другим' },
  { key: 'q26', text: 'Если партнёр работает плохо, ты...',
    a: 'Честно говорю и предлагаю помощь', b: 'Молчу, но исправляю его ошибки' },
  { key: 'q27', text: 'При конфликте в команде ты...',
    a: 'Инициирую разговор для общего решения', b: 'Держусь в стороне и жду' },
  { key: 'q28', text: 'Умеешь ли объяснять сложное простыми словами?',
    a: 'Очень хорошо — это сильная сторона', b: 'С трудом — проще самому понять' },
  { key: 'q29', text: 'Комфортно ли при публичных выступлениях?',
    a: 'Да — нравится выступать', b: 'Сильно нервничаю или избегаю' },
  { key: 'q30', text: 'Ты предпочитаешь работать...',
    a: 'В команде — вместе продуктивнее', b: 'Самостоятельно' },
  { key: 'q31', text: 'Когда кто-то высказывает другое мнение, ты...',
    a: 'Слушаю внимательно и рассматриваю всерьёз', b: 'Стараюсь переубедить' },
  { key: 'q32', text: 'Поддержка окружающих для твоей продуктивности...',
    a: 'Очень важна — черпаю силы из окружения', b: 'Почти не влияет — я независим(а)' },

  // ── Критическое мышление (33-40) ──
  { key: 'q33', text: 'Если видишь лучший способ, чем предложенный, ты...',
    a: 'Предлагаю свой и объясняю почему', b: 'Делаю как сказано' },
  { key: 'q34', text: 'Берёшься за задачи, которые никто не делал?',
    a: 'Часто — интересно быть первопроходцем', b: 'Редко — слишком рискованно' },
  { key: 'q35', text: 'Если замечаешь проблему в организации, ты...',
    a: 'Предлагаю решение и берусь его делать', b: 'Молчу — не моё дело' },
  { key: 'q36', text: 'Когда тебе дают факт или мнение, ты...',
    a: 'Проверяю источник и ищу подтверждение', b: 'Чаще принимаю на веру' },
  { key: 'q37', text: 'Когда проект идёт хорошо, но можно лучше, ты...',
    a: 'Всегда ищу как улучшить', b: 'Оставляю как есть — зачем рисковать' },
  { key: 'q38', text: 'Твоё отношение к правилам...',
    a: 'Понимаю смысл, следую, но задаю вопросы', b: 'Всегда следую — так безопаснее' },
  { key: 'q39', text: 'Готов(а) взять ответственность за результат команды?',
    a: 'Полностью — готов(а) отвечать за общее', b: 'Только за свою часть' },
  { key: 'q40', text: 'Через 10 лет ты видишь себя...',
    a: 'Профессионалом высокого уровня / предпринимателем', b: 'Пока сложно сказать — фокус на настоящем' },
];


// ─── Языковой тест — 20 вопросов ─────────────────────────────────────────────
// Каждый вопрос: text, 4 варианта (A/B/C/D), correct — правильный ответ
const LANG_QUESTIONS = [
  { key: 'q1',  text: 'Choose the correct sentence:',
    options: ['She go to school every day.', 'She goes to school every day.', 'She going to school every day.', 'She are go to school every day.'], correct: 'B' },
  { key: 'q2',  text: 'What is the past tense of "buy"?',
    options: ['buyed', 'bought', 'buied', 'boughted'], correct: 'B' },
  { key: 'q3',  text: '"I ___ to the cinema yesterday."',
    options: ['go', 'goes', 'went', 'gone'], correct: 'C' },
  { key: 'q4',  text: 'Choose the synonym for "happy":',
    options: ['sad', 'joyful', 'angry', 'tired'], correct: 'B' },
  { key: 'q5',  text: '"She has been studying ___ 3 hours."',
    options: ['since', 'for', 'during', 'while'], correct: 'B' },
  { key: 'q6',  text: 'Which sentence is correct?',
    options: ['I have went there.', 'I have gone there.', 'I has gone there.', 'I have go there.'], correct: 'B' },
  { key: 'q7',  text: '"If I ___ rich, I would travel the world."',
    options: ['am', 'was', 'were', 'be'], correct: 'C' },
  { key: 'q8',  text: 'Choose the antonym of "ancient":',
    options: ['old', 'modern', 'historic', 'traditional'], correct: 'B' },
  { key: 'q9',  text: '"By the time she arrived, the movie ___."',
    options: ['started', 'has started', 'had started', 'was starting'], correct: 'C' },
  { key: 'q10', text: '"I wish I ___ more time to study."',
    options: ['have', 'has', 'had', 'having'], correct: 'C' },
  { key: 'q11', text: 'Choose the correct word: "He speaks English ___."',
    options: ['fluent', 'fluently', 'fluence', 'fluid'], correct: 'B' },
  { key: 'q12', text: '"The book ___ by many students."',
    options: ['is reading', 'is read', 'are read', 'reads'], correct: 'B' },
  { key: 'q13', text: '"She asked me where I ___."',
    options: ['live', 'lived', 'living', 'lives'], correct: 'B' },
  { key: 'q14', text: 'Choose the correct form: "___ you ever been to London?"',
    options: ['Do', 'Did', 'Have', 'Are'], correct: 'C' },
  { key: 'q15', text: '"I\'m looking forward ___ you again."',
    options: ['to see', 'to seeing', 'seeing', 'see'], correct: 'B' },
  { key: 'q16', text: '"He ___ have left already; the office is empty."',
    options: ['must', 'can', 'should', 'would'], correct: 'A' },
  { key: 'q17', text: '"Despite ___ tired, she continued working."',
    options: ['be', 'being', 'been', 'was'], correct: 'B' },
  { key: 'q18', text: '"The more you practice, the ___ you get."',
    options: ['good', 'better', 'best', 'well'], correct: 'B' },
  { key: 'q19', text: '"I\'d rather you ___ to the meeting tomorrow."',
    options: ['come', 'came', 'coming', 'will come'], correct: 'B' },
  { key: 'q20', text: '"Not until the rain stopped ___ go outside."',
    options: ['we could', 'could we', 'we can', 'can we'], correct: 'B' },
];


// ─── Вспомогательные функции ──────────────────────────────────────────────────

// Короткий доступ к document.getElementById
const $ = (id) => document.getElementById(id);

// Показать toast-уведомление
function showToast(message, type = 'success') {
  const container = $('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  // Удалить через 4 секунды
  setTimeout(() => {
    toast.classList.add('out');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Показать / скрыть loader
function setLoader(visible) {
  $('loader-overlay').classList.toggle('hidden', !visible);
}


// ═══════════════════════════════════════════════════
// 1. ЭКРАНЫ — маршрутизация
// ═══════════════════════════════════════════════════

function showScreen(name) {
  /*
   * Как работает:
   * 1. Убираем класс active у всех .screen элементов → они скрываются (display:none)
   * 2. Добавляем active к нужному → он появляется с анимацией (fadeSlideIn)
   */
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const target = $(`screen-${name}`);
  if (target) target.classList.add('active');

  // Прокрутка наверх при смене экрана
  window.scrollTo({ top: 0, behavior: 'smooth' });
}


// ═══════════════════════════════════════════════════
// 2. ТЕМА — тёмная / светлая
// ═══════════════════════════════════════════════════

function initTheme() {
  /*
   * Как работает:
   * - <html data-theme="dark"> — CSS переменные для тёмной темы
   * - <html data-theme="light"> — CSS переменные для светлой темы
   * - Все цвета в CSS используют var(--clr-*) → мгновенное переключение
   * - Выбор сохраняется в localStorage
   */
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);

  $('theme-toggle').addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcon(next);
  });
}

function updateThemeIcon(theme) {
  $('theme-icon').textContent = theme === 'dark' ? '🌙' : '☀️';
}


// ═══════════════════════════════════════════════════
// 3. РЕГИСТРАЦИЯ — форма заявки
// ═══════════════════════════════════════════════════

// --- 3.1: Загрузка городов ---

async function loadCities() {
  /*
   * Алгоритм:
   * 1. Запрашиваем GET /api/cities/ через API клиент
   * 2. Получаем { cities: [...], languages: [...] }
   * 3. Заполняем <select id="f-city"> опциями
   * 4. Создаём чипсы (chips) для языков
   *
   * Fallback: если backend недоступен, используем встроенный список
   */
  try {
    const data = await API.getCities();
    state.cities = data.cities || [];
    state.languagesList = data.languages || [];
  } catch (e) {
    // Fallback — встроенный список (работает без backend)
    state.cities = [
      'Алматы','Астана','Шымкент','Актобе','Караганда','Тараз',
      'Павлодар','Усть-Каменогорск','Семей','Костанай','Петропавловск',
      'Кызылорда','Атырау','Актау','Уральск','Кокшетау','Талдыкорган',
      'Конаев','Туркестан','Темиртау','Экибастуз','Рудный',
      'Жанаозен','Балхаш','Кентау','Каскелен','Талгар','Риддер',
    ].sort();
    state.languagesList = [
      'Казахский','Русский','Английский','Турецкий','Китайский',
      'Немецкий','Французский','Корейский','Арабский','Испанский','Другой',
    ];
    console.warn('Backend недоступен, используем встроенный список городов');
  }

  // Заполняем dropdown городов
  const select = $('f-city');
  state.cities.forEach(city => {
    const opt = document.createElement('option');
    opt.value = city;
    opt.textContent = city;
    select.appendChild(opt);
  });

  // Создаём чипсы языков
  renderLanguageChips();
}

// --- 3.2: Чипсы языков (multi-select) ---

function renderLanguageChips() {
  /*
   * Чипсы — это кнопки-тоглы. Клик → selected/deselected.
   * state.selectedLangs хранит массив выбранных языков.
   */
  const container = $('lang-chips');
  container.innerHTML = '';

  state.languagesList.forEach(lang => {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = lang;
    chip.dataset.lang = lang;

    chip.addEventListener('click', () => {
      chip.classList.toggle('selected');
      if (chip.classList.contains('selected')) {
        state.selectedLangs.push(lang);
      } else {
        state.selectedLangs = state.selectedLangs.filter(l => l !== lang);
      }
    });

    container.appendChild(chip);
  });
}

// --- 3.3: Город → Регион ---

function initCityRegion() {
  /*
   * Логика:
   * 1. Пользователь выбирает город
   * 2. Отправляем GET /api/cities/<город>/regions/
   * 3. Получаем { city: "Алматы", region: "город Алматы" }
   * 4. Вставляем регион в readonly поле
   */
  $('f-city').addEventListener('change', async (e) => {
    const city = e.target.value;
    const regionInput = $('f-region');

    if (!city) {
      regionInput.value = '';
      return;
    }

    try {
      const data = await API.getRegion(city);
      regionInput.value = data.region || '';
    } catch {
      // Fallback — простой маппинг
      regionInput.value = city + ' (регион)';
    }
  });
}

// --- 3.4: Валидация и отправка формы ---

function initRegistrationForm() {
  $('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Собираем данные из полей
    const name     = $('f-name').value.trim();
    const city     = $('f-city').value;
    const region   = $('f-region').value.trim();
    const telegram = $('f-telegram').value.trim();
    const hobbies  = $('f-hobbies').value.trim();
    const sport    = $('f-sport').value.trim();
    const langs    = state.selectedLangs;

    // Валидация
    const errorEl = $('reg-error');
    errorEl.classList.add('hidden');

    if (!name || !city || !telegram) {
      errorEl.textContent = t('err_fill_all');
      errorEl.classList.remove('hidden');
      return;
    }
    if (langs.length === 0) {
      errorEl.textContent = t('err_select_lang');
      errorEl.classList.remove('hidden');
      return;
    }
    if (telegram.length < 3) {
      errorEl.textContent = t('err_tg_format');
      errorEl.classList.remove('hidden');
      return;
    }

    // Формируем JSON для отправки
    const payload = {
      name:               name,
      city:               city,
      region:             region,
      languages:          langs,
      telegram_username:  telegram.startsWith('@') ? telegram : `@${telegram}`,
      hobbies:            hobbies,
      sport:              sport,
    };

    // Отправляем в backend
    const submitBtn = $('reg-submit');
    const spinner   = $('reg-spinner');
    const btnText   = submitBtn.querySelector('.btn-text');

    submitBtn.disabled = true;
    spinner.classList.remove('hidden');
    if (btnText) btnText.style.opacity = '0.5';

    try {
      const result = await API.submitApplication(payload);
      state.applicationId = result.id;
      showToast('Анкета сохранена! Переходим к MBTI тесту.', 'success');

      // Переходим к MBTI тесту
      startMBTI();
    } catch (err) {
      errorEl.textContent = err.message || t('send_error');
      errorEl.classList.remove('hidden');
      showToast(err.message || t('send_error'), 'error');
    } finally {
      submitBtn.disabled = false;
      spinner.classList.add('hidden');
      if (btnText) btnText.style.opacity = '1';
    }
  });
}


// ═══════════════════════════════════════════════════
// 4. MBTI ТЕСТ — 40 вопросов по одному
// ═══════════════════════════════════════════════════

function startMBTI() {
  state.mbtiIndex = 0;
  state.mbtiAnswers = {};
  renderMBTIQuestion();
  showScreen('mbti');
}

function renderMBTIQuestion() {
  /*
   * Как работает пошаговый тест:
   * 1. Берём текущий вопрос по индексу state.mbtiIndex
   * 2. Обновляем текст, номер, прогресс-бар
   * 3. Рендерим 2 кнопки-варианта (A и B)
   * 4. При клике → запоминаем ответ и подсвечиваем
   * 5. Кнопка «Далее» → следующий вопрос
   */
  const q = MBTI_QUESTIONS[state.mbtiIndex];
  const total = MBTI_QUESTIONS.length;
  const idx = state.mbtiIndex;

  // Прогресс
  const pct = ((idx + 1) / total) * 100;
  $('mbti-progress-fill').style.width = `${pct}%`;
  $('mbti-progress-label').textContent = `${idx + 1} / ${total}`;

  // Номер и текст вопроса
  $('mbti-q-num').textContent = idx + 1;
  $('mbti-q-text').textContent = q.text;

  // Варианты ответов
  const container = $('mbti-options');
  container.innerHTML = '';

  ['A', 'B'].forEach(letter => {
    const text = letter === 'A' ? q.a : q.b;
    const option = document.createElement('div');
    option.className = 'test-option';
    if (state.mbtiAnswers[q.key] === letter) option.classList.add('selected');

    option.innerHTML = `
      <div class="test-option-circle"></div>
      <span class="test-option-text">${text}</span>
    `;

    option.addEventListener('click', () => {
      state.mbtiAnswers[q.key] = letter;
      container.querySelectorAll('.test-option').forEach(o => o.classList.remove('selected'));
      option.classList.add('selected');
    });

    container.appendChild(option);
  });

  // Навигация
  $('mbti-prev').disabled = idx === 0;

  const nextBtn = $('mbti-next');
  const isLast = idx === total - 1;
  nextBtn.textContent = isLast ? t('finish_mbti') : t('next_q');
}

function initMBTINav() {
  // Кнопка «Далее»
  $('mbti-next').addEventListener('click', async () => {
    const q = MBTI_QUESTIONS[state.mbtiIndex];

    // Проверяем что ответ выбран
    if (!state.mbtiAnswers[q.key]) {
      showToast(t('mbti_pick'), 'warning');
      return;
    }

    const isLast = state.mbtiIndex === MBTI_QUESTIONS.length - 1;

    if (isLast) {
      // Все 40 вопросов отвечены → отправляем
      await submitMBTI();
    } else {
      state.mbtiIndex++;
      renderMBTIQuestion();
    }
  });

  // Кнопка «Назад»
  $('mbti-prev').addEventListener('click', () => {
    if (state.mbtiIndex > 0) {
      state.mbtiIndex--;
      renderMBTIQuestion();
    }
  });
}

async function submitMBTI() {
  setLoader(true);
  try {
    await API.submitMBTI(state.applicationId, state.mbtiAnswers);
    showToast('MBTI тест завершён! Переходим к языковому тесту.', 'success');
    startLangTest();
  } catch (err) {
    showToast(err.message || t('send_error'), 'error');
  } finally {
    setLoader(false);
  }
}


// ═══════════════════════════════════════════════════
// 5. ЯЗЫКОВОЙ ТЕСТ — 20 вопросов + таймер + вкладка
// ═══════════════════════════════════════════════════

function startLangTest() {
  state.langIndex = 0;
  state.langAnswers = {};
  state.langTimer = 600; // 10 минут
  state.violations = 0;
  state.langBlocked = false;
  state.langStartTime = new Date();

  $('violation-badge').classList.add('hidden');

  renderLangQuestion();
  startTimer();
  startTabDetection();
  showScreen('lang-test');
}

function renderLangQuestion() {
  const q = LANG_QUESTIONS[state.langIndex];
  const total = LANG_QUESTIONS.length;
  const idx = state.langIndex;

  // Прогресс
  const pct = ((idx + 1) / total) * 100;
  $('lang-progress-fill').style.width = `${pct}%`;
  $('lang-progress-label').textContent = `${idx + 1} / ${total}`;

  // Номер и текст
  $('lang-q-num').textContent = idx + 1;
  $('lang-q-text').textContent = q.text;

  // Варианты (A, B, C, D)
  const container = $('lang-options');
  container.innerHTML = '';

  const letters = ['A', 'B', 'C', 'D'];
  q.options.forEach((text, i) => {
    const letter = letters[i];
    const option = document.createElement('div');
    option.className = 'test-option';
    if (state.langAnswers[q.key] === letter) option.classList.add('selected');

    option.innerHTML = `
      <div class="test-option-circle"></div>
      <span class="test-option-text">${letter}. ${text}</span>
    `;

    option.addEventListener('click', () => {
      if (state.langBlocked) return;
      state.langAnswers[q.key] = letter;
      container.querySelectorAll('.test-option').forEach(o => o.classList.remove('selected'));
      option.classList.add('selected');
    });

    container.appendChild(option);
  });

  // Навигация
  $('lang-prev').disabled = idx === 0;

  const nextBtn = $('lang-next');
  const isLast = idx === total - 1;
  nextBtn.textContent = isLast ? t('finish_lang') : t('next_q');
}

function initLangNav() {
  $('lang-next').addEventListener('click', async () => {
    if (state.langBlocked) return;

    const isLast = state.langIndex === LANG_QUESTIONS.length - 1;

    if (isLast) {
      await submitLangTest();
    } else {
      state.langIndex++;
      renderLangQuestion();
    }
  });

  $('lang-prev').addEventListener('click', () => {
    if (state.langBlocked) return;
    if (state.langIndex > 0) {
      state.langIndex--;
      renderLangQuestion();
    }
  });
}


// --- 5.1: Таймер ---

function startTimer() {
  /*
   * Как работает таймер:
   * 1. state.langTimer = 600 (10 минут в секундах)
   * 2. Каждую секунду уменьшаем на 1
   * 3. Обновляем отображение (MM:SS)
   * 4. Меняем цвет: зелёный → жёлтый (<3мин) → красный (<1мин)
   * 5. Когда 0 → автоматически отправляем тест
   */
  updateTimerDisplay();

  state.langTimerId = setInterval(() => {
    state.langTimer--;
    updateTimerDisplay();

    if (state.langTimer <= 0) {
      clearInterval(state.langTimerId);
      showToast(t('time_up'), 'warning');
      submitLangTest();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const minutes = Math.floor(state.langTimer / 60);
  const seconds = state.langTimer % 60;
  const display = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  const timerEl = $('lang-timer');
  timerEl.textContent = display;

  // Изменяем стиль в зависимости от оставшегося времени
  timerEl.classList.remove('warning', 'danger');
  if (state.langTimer <= 60) {
    timerEl.classList.add('danger');       // < 1 мин — красный, мигающий
  } else if (state.langTimer <= 180) {
    timerEl.classList.add('warning');      // < 3 мин — жёлтый
  }
}


// --- 5.2: Контроль выхода из вкладки ---

function startTabDetection() {
  /*
   * Как работает проверка вкладки:
   *
   * document.visibilitychange — событие браузера, которое срабатывает когда:
   *   - Пользователь переключается на другую вкладку
   *   - Пользователь сворачивает окно
   *   - Пользователь alt-tab в другое приложение
   *
   * document.hidden === true  → вкладка НЕ видна
   * document.hidden === false → вкладка видна (вернулся)
   *
   * Логика:
   *   1-й раз (violations === 1): показываем предупреждение (toast)
   *   2-й раз (violations === 2): блокируем тест и автоматически отправляем
   */
  const handler = () => {
    if (document.hidden && !state.langBlocked) {
      state.violations++;

      // Обновляем badge
      $('violation-badge').classList.remove('hidden');
      $('violation-text').textContent = `${t('violations').split(':')[0]}: ${state.violations}`;

      if (state.violations === 1) {
        // Первый раз — предупреждение
        showToast(t('violation_warn'), 'warning');
      } else if (state.violations >= 2) {
        // Второй раз — блокировка
        state.langBlocked = true;
        showToast(t('violation_block'), 'error');
        // Автоматическая отправка через 2 секунды
        setTimeout(() => submitLangTest(), 2000);
      }
    }
  };

  document.addEventListener('visibilitychange', handler);

  // Сохраняем ссылку на handler чтобы можно было удалить
  state._tabHandler = handler;
}

function stopTabDetection() {
  if (state._tabHandler) {
    document.removeEventListener('visibilitychange', state._tabHandler);
    state._tabHandler = null;
  }
}


// --- 5.3: Подсчёт и отправка ---

function calculateLangScore() {
  let score = 0;
  LANG_QUESTIONS.forEach(q => {
    if (state.langAnswers[q.key] === q.correct) {
      score++;
    }
  });
  return score;
}

async function submitLangTest() {
  // Останавливаем таймер и детекцию вкладки
  if (state.langTimerId) clearInterval(state.langTimerId);
  stopTabDetection();

  const timeSpent = Math.round((new Date() - state.langStartTime) / 1000);
  const score = calculateLangScore();

  const payload = {
    application_id:     state.applicationId,
    language:           'Английский',
    answers:            state.langAnswers,
    score:              score,
    max_score:          LANG_QUESTIONS.length,
    time_spent_seconds: timeSpent,
    violation_count:    state.violations,
  };

  setLoader(true);
  try {
    await API.submitLanguageTest(payload);
    showToast(t('success_title'), 'success');
    showScreen('success');
  } catch (err) {
    showToast(err.message || t('send_error'), 'error');
    // Всё равно показываем success — данные могли сохраниться
    showScreen('success');
  } finally {
    setLoader(false);
  }
}


// ═══════════════════════════════════════════════════
// 6. НАВИГАЦИЯ — кнопки и ссылки
// ═══════════════════════════════════════════════════

function initNavigation() {
  // Кнопка «Подать заявку» на Hero экране
  $('hero-start-btn').addEventListener('click', () => showScreen('register'));

  // Кнопка «Подать заявку» в header
  $('btn-start-header').addEventListener('click', () => showScreen('register'));

  // Кнопка «Войти» → login экран
  $('btn-login').addEventListener('click', () => showScreen('login'));

  // Логотип → на главную
  $('logo').addEventListener('click', () => showScreen('landing'));

  // Кнопка «На главную» на success экране
  $('btn-home').addEventListener('click', () => showScreen('landing'));

  // Ссылка «На главную» на login экране
  $('login-back').addEventListener('click', (e) => {
    e.preventDefault();
    showScreen('landing');
  });
}


// ═══════════════════════════════════════════════════
// 7. ЛОГИН АДМИНА
// ═══════════════════════════════════════════════════

function initLogin() {
  $('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = $('login-username').value.trim();
    const password = $('login-password').value.trim();
    const errorEl  = $('login-error');
    const submitBtn = $('login-submit');
    const spinner   = $('login-spinner');

    errorEl.classList.add('hidden');

    if (!username || !password) {
      errorEl.textContent = t('err_fill_all');
      errorEl.classList.remove('hidden');
      return;
    }

    submitBtn.disabled = true;
    spinner.classList.remove('hidden');

    try {
      const response = await fetch('/panel/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.success) {
        showToast(t('login_ok'), 'success');
        // Redirect to admin panel
        window.location.href = '/panel/';
      } else {
        errorEl.textContent = data.error || t('login_fail');
        errorEl.classList.remove('hidden');
      }
    } catch (err) {
      errorEl.textContent = t('login_fail');
      errorEl.classList.remove('hidden');
    } finally {
      submitBtn.disabled = false;
      spinner.classList.add('hidden');
    }
  });
}


// ═══════════════════════════════════════════════════
// 8. ИНИЦИАЛИЗАЦИЯ — запуск всего
// ═══════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavigation();
  initLogin();
  initRegistrationForm();
  initCityRegion();
  initMBTINav();
  initLangNav();
  loadCities();
  showScreen('landing');
});
