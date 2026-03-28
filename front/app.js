/**
 * app.js — UniAdmit / inVision U Frontend Logic
 * ================================================
 * Handles:
 *   - SPA screen routing (landing → register → login → form → results)
 *   - Auth (register / login via API)
 *   - Multi-block application form (5 blocks)
 *   - JSON submission to backend
 *   - Results display (raw JSON from server)
 */

'use strict';

// ─── API base URL ─────────────────────────────────────────────────────────────
// All backend calls go to /api/...
const API = '/api';

// ─── Application state ───────────────────────────────────────────────────────
// This object holds everything we need across screens.
const state = {
  user:         null,  // { id, username, email } set after login/register
  token:        null,  // session token (not used for auth headers yet)
  currentBlock: 0,     // which of the 5 blocks is currently shown (0-indexed)
};

// ─── Block definitions ────────────────────────────────────────────────────────
// Each block has a title, subtitle, and a type.
// The actual fields/questions are rendered separately.
const BLOCKS = [
  { title: 'Блок 1',  subtitle: 'Базовая информация',        type: 'basic_info' },
  { title: 'Блок 2',  subtitle: 'Опыт и активности',         type: 'experience' },
  { title: 'Блок 3',  subtitle: 'Мотивация и эссе',          type: 'motivation' },
  { title: 'Блок 4',  subtitle: 'Психометрический тест',     type: 'psychometric' },
  { title: 'Блок 5',  subtitle: 'Согласия и подтверждения',  type: 'consents' },
];

// ─── 40 Psychometric questions ────────────────────────────────────────────────
// Each question has a key (used in the JSON), the question text,
// and exactly 4 answer options (the selected text goes into the JSON).
const PSYCHO_QUESTIONS = [
  // ── Целеустремлённость и планирование (1–8) ───────────────────────────────
  {
    key: 'q1',
    text: 'Когда у меня есть важная цель, я...',
    options: [
      'Сразу составляю план и строго следую ему',
      'Держу цель в уме и действую по ситуации',
      'Мотивируюсь, но часто откладываю на потом',
      'Жду подходящего момента и вдохновения',
    ],
  },
  {
    key: 'q2',
    text: 'Я склонен(на) ставить долгосрочные цели (на год и более)...',
    options: [
      'Да, всегда — у меня есть чёткий план на несколько лет',
      'Иногда — если ситуация требует',
      'Редко — предпочитаю краткосрочные задачи',
      'Почти никогда — будущее слишком непредсказуемо',
    ],
  },
  {
    key: 'q3',
    text: 'Если я не успеваю выполнить задачу в срок, я...',
    options: [
      'Пересматриваю план и нахожу способ наверстать',
      'Расстраиваюсь, но продолжаю работу',
      'Прошу помощи или переноса дедлайна',
      'Бросаю задачу и перехожу к другой',
    ],
  },
  {
    key: 'q4',
    text: 'Моя учёба или работа над проектами...',
    options: [
      'Всегда структурирована: расписание, задачи, дедлайны',
      'Частично структурирована — по необходимости',
      'Хаотична, но результат всё равно есть',
      'Без системы, работаю только когда хочется',
    ],
  },
  {
    key: 'q5',
    text: 'Когда у меня несколько задач одновременно, я...',
    options: [
      'Приоритизирую и делаю по очереди',
      'Переключаюсь между задачами в зависимости от настроения',
      'Берусь за всё сразу и часто не заканчиваю',
      'Испытываю стресс и прокрастинирую',
    ],
  },
  {
    key: 'q6',
    text: 'Как часто ты достигаешь целей, которые сам(а) себе ставишь?',
    options: [
      'Почти всегда — я ставлю реалистичные цели и выполняю их',
      'Чаще да, чем нет',
      'Примерно 50 на 50',
      'Редко — цели часто остаются невыполненными',
    ],
  },
  {
    key: 'q7',
    text: 'Что мешает тебе достигать целей чаще всего?',
    options: [
      'Ничего — я справляюсь со своими целями',
      'Нехватка времени или ресурсов',
      'Прокрастинация и отвлекающие факторы',
      'Страх неудачи или неуверенность в себе',
    ],
  },
  {
    key: 'q8',
    text: 'Когда ты учишься чему-то новому, ты предпочитаешь...',
    options: [
      'Чёткую структуру: курс, книга, шаги',
      'Смешанный подход: теория + практика',
      'Учиться на практике, методом проб и ошибок',
      'Смотреть, как делают другие, и потом повторять',
    ],
  },

  // ── Мотивация и страсть (9–16) ────────────────────────────────────────────
  {
    key: 'q9',
    text: 'Что больше всего мотивирует тебя работать усердно?',
    options: [
      'Желание стать профессионалом в своём деле',
      'Признание и похвала со стороны других',
      'Финансовое вознаграждение и стабильность',
      'Интерес к самому процессу обучения',
    ],
  },
  {
    key: 'q10',
    text: 'Как ты чувствуешь себя, когда занимаешься чем-то интересным?',
    options: [
      'Теряю счёт времени — полностью погружаюсь',
      'Работаю с удовольствием, но слежу за временем',
      'Мне интересно, но я легко отвлекаюсь',
      'Интерес быстро проходит',
    ],
  },
  {
    key: 'q11',
    text: 'Если бы тебе не нужно было думать о деньгах, ты бы...',
    options: [
      'Продолжал(а) учиться и исследовать интересные области',
      'Занялся(ась) любимым делом, которое сейчас не приносит доход',
      'Путешествовал(а) и отдыхал(а)',
      'Помогал(а) другим людям / волонтёрство',
    ],
  },
  {
    key: 'q12',
    text: 'Когда тебе скучно в учёбе, ты...',
    options: [
      'Ищу более глубокий материал по теме сам(а)',
      'Стараюсь найти практическое применение теории',
      'Просто жду, пока это закончится',
      'Перестаю вникать и переключаюсь на другое',
    ],
  },
  {
    key: 'q13',
    text: 'Твоя учёбная активность вне школы/колледжа...',
    options: [
      'Высокая: онлайн-курсы, книги, проекты',
      'Средняя: занимаюсь при наличии времени',
      'Низкая: только если задали',
      'Почти нулевая: хватает школы',
    ],
  },
  {
    key: 'q14',
    text: 'Когда ты достигаешь цели, ты обычно...',
    options: [
      'Радуюсь и сразу ставлю новую, более высокую цель',
      'Радуюсь и отдыхаю какое-то время',
      'Чувствую облегчение, а не радость',
      'Быстро теряю интерес к результату',
    ],
  },
  {
    key: 'q15',
    text: 'Насколько тебе важно "быть лучшим" в своём деле?',
    options: [
      'Очень важно — я стремлюсь к мастерству',
      'Важно, но не любой ценой',
      'Мне важнее прогресс, чем сравнение с другими',
      'Не особо важно — главное делать "достаточно хорошо"',
    ],
  },
  {
    key: 'q16',
    text: 'Когда ты слышишь об успехе другого человека, ты...',
    options: [
      'Вдохновляюсь и думаю, как тоже достичь подобного',
      'Искренне радуюсь за него/неё',
      'Чувствую лёгкую зависть, но стараюсь с этим работать',
      'Сравниваю себя с этим человеком и расстраиваюсь',
    ],
  },

  // ── Стрессоустойчивость и resilience (17–24) ─────────────────────────────
  {
    key: 'q17',
    text: 'Когда что-то пошло не по плану, ты первым делом...',
    options: [
      'Анализирую ситуацию и ищу новый путь',
      'Позволяю себе расстроиться, потом собираюсь',
      'Обсуждаю с кем-то близким, чтобы получить поддержку',
      'Надолго застреваю в негативных мыслях',
    ],
  },
  {
    key: 'q18',
    text: 'В стрессовых ситуациях (экзамен, конкурс, дедлайн) ты...',
    options: [
      'Концентрируюсь и работаю эффективнее обычного',
      'Немного нервничаю, но справляюсь',
      'Сильно переживаю, что мешает работе',
      'Теряюсь и не могу продуктивно действовать',
    ],
  },
  {
    key: 'q19',
    text: 'После серьёзной неудачи ты возвращаешься к нормальному состоянию...',
    options: [
      'Быстро — провал для меня это урок',
      'Через несколько дней',
      'Через несколько недель',
      'Долго не могу прийти в себя',
    ],
  },
  {
    key: 'q20',
    text: 'Как ты воспринимаешь критику своей работы?',
    options: [
      'Как ценную обратную связь для роста',
      'Нейтрально — слушаю, фильтрую, применяю',
      'С трудом — внутри обида, но стараюсь учесть',
      'Болезненно — критика выбивает из колеи',
    ],
  },
  {
    key: 'q21',
    text: 'Если проект провалился, ты...',
    options: [
      'Честно анализирую свой вклад в провал и делаю выводы',
      'Ищу причины со стороны — обстоятельства, команда',
      'Предпочитаю не возвращаться к этой теме',
      'Сдаюсь и не пробую снова',
    ],
  },
  {
    key: 'q22',
    text: 'Когда тебя отвергают (конкурс, программа, работа), ты...',
    options: [
      'Прошу фидбэк и готовлюсь попробовать снова',
      'Расстраиваюсь, но продолжаю искать похожие возможности',
      'Долго переживаю и откладываю следующую попытку',
      'Отказываюсь от этого направления',
    ],
  },
  {
    key: 'q23',
    text: 'Ты справляешься с неопределённостью...',
    options: [
      'Хорошо — неопределённость это возможности',
      'Нормально — могу действовать без гарантий',
      'С трудом — предпочитаю знать ответы заранее',
      'Плохо — неопределённость сильно тревожит',
    ],
  },
  {
    key: 'q24',
    text: 'Когда ты устал(а) и нет сил, ты...',
    options: [
      'Отдыхаю осознанно, потом возвращаюсь с новыми силами',
      'Заставляю себя продолжать через силу',
      'Откладываю всё и отдыхаю столько, сколько нужно',
      'Теряю интерес и с трудом возвращаюсь',
    ],
  },

  // ── Командная работа и коммуникация (25–32) ──────────────────────────────
  {
    key: 'q25',
    text: 'В групповом проекте ты чаще всего...',
    options: [
      'Беру на себя роль лидера и организую команду',
      'Участвую активно, но не претендую на лидерство',
      'Выполняю свою часть и стараюсь не мешать другим',
      'Предпочитаю работать в одиночку',
    ],
  },
  {
    key: 'q26',
    text: 'Если партнёр по команде делает свою часть плохо, ты...',
    options: [
      'Честно говорю ему об этом и предлагаю помощь',
      'Молчу, но исправляю его ошибки сам(а)',
      'Сообщаю куратору или организатору',
      'Делаю свою часть и отпускаю ситуацию',
    ],
  },
  {
    key: 'q27',
    text: 'При конфликте в команде ты...',
    options: [
      'Инициирую разговор, чтобы найти общее решение',
      'Стараюсь сгладить конфликт и помирить стороны',
      'Держусь в стороне и жду, пока само разрешится',
      'Принимаю одну из сторон, если считаю её правой',
    ],
  },
  {
    key: 'q28',
    text: 'Насколько хорошо ты умеешь объяснять сложные вещи простыми словами?',
    options: [
      'Очень хорошо — это одна из моих сильных сторон',
      'Неплохо, хотя иногда приходится упрощать чересчур',
      'С трудом — мне проще самому понять, чем объяснить',
      'Плохо — объяснение даётся с большим усилием',
    ],
  },
  {
    key: 'q29',
    text: 'Ты комфортно чувствуешь себя при публичных выступлениях?',
    options: [
      'Да — мне нравится выступать перед аудиторией',
      'Волнуюсь, но справляюсь',
      'Сильно нервничаю, но выступаю',
      'Стараюсь избегать публичных выступлений',
    ],
  },
  {
    key: 'q30',
    text: 'Ты предпочитаешь работать...',
    options: [
      'В команде — вместе интереснее и продуктивнее',
      'В паре или маленькой группе',
      'Самостоятельно, но с возможностью обсудить',
      'Только самостоятельно',
    ],
  },
  {
    key: 'q31',
    text: 'Когда кто-то выражает другую точку зрения, ты...',
    options: [
      'Слушаю внимательно и рассматриваю её всерьёз',
      'Слушаю, но остаюсь при своём мнении',
      'Стараюсь переубедить его(её)',
      'Теряюсь и не знаю, чью сторону принять',
    ],
  },
  {
    key: 'q32',
    text: 'Поддержка людей вокруг тебя для твоей продуктивности...',
    options: [
      'Очень важна — черпаю силы из окружения',
      'Полезна, но я могу работать и без неё',
      'Почти не влияет — я независим(а)',
      'Иногда мешает — отвлекают',
    ],
  },

  // ── Критическое мышление и инициатива (33–40) ────────────────────────────
  {
    key: 'q33',
    text: 'Когда тебя просят что-то сделать определённым способом, а ты видишь лучший способ, ты...',
    options: [
      'Предлагаю свой способ и объясняю почему',
      'Делаю как сказано, но уточняю на будущее',
      'Делаю как сказано, ничего не говоря',
      'Делаю по-своему, не спрашивая',
    ],
  },
  {
    key: 'q34',
    text: 'Ты берёшься за задачи, которые ещё никто не делал в твоём окружении...',
    options: [
      'Часто — мне интересно быть первопроходцем',
      'Иногда, если чувствую, что справлюсь',
      'Редко — предпочитаю проверенные пути',
      'Почти никогда — слишком рискованно',
    ],
  },
  {
    key: 'q35',
    text: 'Если ты замечаешь проблему в организации (школе, клубе, проекте), ты...',
    options: [
      'Предлагаю конкретное решение и берусь его реализовать',
      'Говорю об этом ответственному человеку',
      'Жалуюсь другим, но ничего не делаю',
      'Молчу — не моё дело',
    ],
  },
  {
    key: 'q36',
    text: 'Когда тебе дают факт или мнение, ты...',
    options: [
      'Проверяю источник и ищу подтверждение',
      'Принимаю, если источник кажется надёжным',
      'Чаще всего принимаю на веру',
      'Принимаю, если это совпадает с моим мнением',
    ],
  },
  {
    key: 'q37',
    text: 'Когда проект идёт хорошо, но можно сделать его лучше, ты...',
    options: [
      'Всегда ищу, как улучшить — "достаточно хорошо" не для меня',
      'Улучшаю, если есть время и ресурсы',
      'Оставляю как есть — зачем рисковать?',
      'Не вижу смысла что-то менять в работающем',
    ],
  },
  {
    key: 'q38',
    text: 'Твоё отношение к правилам...',
    options: [
      'Понимаю их смысл и следую им, но задаю вопросы',
      'Следую правилам, если это разумно',
      'Всегда следую правилам — так безопаснее',
      'Правила для меня скорее ориентир, чем обязательство',
    ],
  },
  {
    key: 'q39',
    text: 'Насколько ты готов(а) взять на себя ответственность за результат команды?',
    options: [
      'Полностью — я готов(а) отвечать за общий результат',
      'За свою часть — и немного за общее',
      'Только за свою часть',
      'Предпочитаю, чтобы ответственность нёс кто-то другой',
    ],
  },
  {
    key: 'q40',
    text: 'Через 10 лет ты видишь себя...',
    options: [
      'Профессионалом высокого уровня в конкретной области',
      'Предпринимателем или основателем своего дела',
      'Человеком с положительным влиянием на общество',
      'Пока сложно сказать — я сосредоточен(а) на настоящем',
    ],
  },
];

// ─── DOM References ───────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);  // shortcut for getElementById

// All 5 screen elements
const screens = {
  landing:  $('screen-landing'),
  register: $('screen-register'),
  login:    $('screen-login'),
  form:     $('screen-form'),
  results:  $('screen-results'),
};

// ─── Screen routing ───────────────────────────────────────────────────────────
// Hides all screens, shows only the target one.
function showScreen(name) {
  Object.values(screens).forEach(s => s.classList.remove('active'));
  if (screens[name]) screens[name].classList.add('active');
}

// ─── Header update ────────────────────────────────────────────────────────────
// Shows "Hi, Name" + Logout button when logged in.
function updateHeader() {
  if (state.user) {
    $('header-actions').classList.add('hidden');
    $('header-user').classList.remove('hidden');
    $('greeting-name').textContent = `${state.user.username}`;
  } else {
    $('header-actions').classList.remove('hidden');
    $('header-user').classList.add('hidden');
  }
}

// ─── API helper ───────────────────────────────────────────────────────────────
// Makes a POST request to the backend and parses the JSON response.
async function apiPost(endpoint, body) {
  const res  = await fetch(`${API}${endpoint}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

// ─── Form utilities ───────────────────────────────────────────────────────────
// Show/hide loading spinner inside a button
function setLoading(btnId, spinnerId, loading) {
  const btn    = $(btnId);
  const spin   = $(spinnerId);
  const text   = btn.querySelector('.btn-text');
  btn.disabled = loading;
  spin.classList.toggle('hidden', !loading);
  if (text) text.style.opacity = loading ? '0.5' : '1';
}

// Show an error message box
function showError(elId, msg) {
  const el      = $(elId);
  el.textContent = msg;
  el.classList.remove('hidden');
}

function clearError(elId) {
  $(elId).classList.add('hidden');
}

// ─── AUTH: Register ───────────────────────────────────────────────────────────
$('register-form').addEventListener('submit', async e => {
  e.preventDefault();
  clearError('register-error');

  const username = $('reg-username').value.trim();
  const email    = $('reg-email').value.trim();
  const password = $('reg-password').value;

  if (!username || !email || !password)
    return showError('register-error', 'Заполните все поля.');
  if (password.length < 6)
    return showError('register-error', 'Пароль — минимум 6 символов.');

  setLoading('register-submit', 'register-spinner', true);
  try {
    const data  = await apiPost('/register', { username, email, password });
    state.user  = data.user;
    state.token = data.token;
    updateHeader();
    startForm();
  } catch (err) {
    showError('register-error', err.message);
  } finally {
    setLoading('register-submit', 'register-spinner', false);
  }
});

// ─── AUTH: Login ──────────────────────────────────────────────────────────────
$('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  clearError('login-error');

  const email    = $('login-email').value.trim();
  const password = $('login-password').value;

  if (!email || !password)
    return showError('login-error', 'Введите email и пароль.');

  setLoading('login-submit', 'login-spinner', true);
  try {
    const data  = await apiPost('/login', { email, password });
    state.user  = data.user;
    state.token = data.token;
    updateHeader();
    startForm();
  } catch (err) {
    showError('login-error', err.message);
  } finally {
    setLoading('login-submit', 'login-spinner', false);
  }
});

// ─── AUTH: Logout ─────────────────────────────────────────────────────────────
$('btn-logout').addEventListener('click', () => {
  state.user  = null;
  state.token = null;
  updateHeader();
  showScreen('landing');
});

// ─── Navigation bindings ──────────────────────────────────────────────────────
$('btn-show-register').addEventListener('click', () => showScreen('register'));
$('btn-show-login').addEventListener('click',    () => showScreen('login'));
$('switch-to-login').addEventListener('click',    e => { e.preventDefault(); showScreen('login'); });
$('switch-to-register').addEventListener('click', e => { e.preventDefault(); showScreen('register'); });
$('hero-start-btn').addEventListener('click', () => {
  state.user ? startForm() : showScreen('register');
});
$('logo').addEventListener('click', () => showScreen('landing'));

// ─── FORM: start ─────────────────────────────────────────────────────────────
// Resets form state and renders block 0 (Basic Info).
function startForm() {
  state.currentBlock = 0;
  renderBlock(0);
  showScreen('form');
}

// ─── FORM: render a block ─────────────────────────────────────────────────────
// Called every time the user moves to a different block.
function renderBlock(index) {
  const block    = BLOCKS[index];
  const isLast   = index === BLOCKS.length - 1;

  // Update progress
  const pct = ((index + 1) / BLOCKS.length) * 100;
  $('form-progress-fill').style.width = `${pct}%`;
  $('form-progress-label').textContent = `${block.title} / ${BLOCKS.length} блоков`;

  // Update block title
  $('block-title').textContent    = block.title;
  $('block-subtitle').textContent = block.subtitle;

  // Render the fields for this block
  const container = $('block-fields');
  container.innerHTML = '';  // clear previous fields

  if (block.type === 'basic_info')    renderBasicInfo(container);
  if (block.type === 'experience')    renderExperience(container);
  if (block.type === 'motivation')    renderMotivation(container);
  if (block.type === 'psychometric')  renderPsychometric(container);
  if (block.type === 'consents')      renderConsents(container);

  // Navigation buttons
  $('btn-form-prev').disabled     = index === 0;
  $('btn-form-next').textContent  = isLast ? 'Отправить заявку ✓' : 'Следующий блок →';

  // Animate in
  const card = $('form-block-card');
  card.style.animation = 'none';
  void card.offsetWidth;
  card.style.animation = '';
}

// ─── Block 1: Basic Info fields ───────────────────────────────────────────────
function renderBasicInfo(container) {
  container.innerHTML = `
    <div class="field-group">
      <label for="f-fullname">Имя и фамилия *</label>
      <input type="text" id="f-fullname" placeholder="Иван Иванов"
             value="${getSaved('basic_info','full_name')}" />
    </div>
    <div class="field-row">
      <div class="field-group">
        <label for="f-age">Возраст *</label>
        <input type="number" id="f-age" placeholder="17" min="10" max="30"
               value="${getSaved('basic_info','age')}" />
      </div>
      <div class="field-group">
        <label for="f-city">Город *</label>
        <input type="text" id="f-city" placeholder="Алматы"
               value="${getSaved('basic_info','city')}" />
      </div>
    </div>
    <div class="field-group">
      <label for="f-school">Школа / Колледж *</label>
      <input type="text" id="f-school" placeholder="NIS Алматы"
             value="${getSaved('basic_info','school')}" />
    </div>
    <div class="field-group">
      <label for="f-grade">Класс / Курс *</label>
      <select id="f-grade">
        <option value="">— выберите —</option>
        ${['9','10','11','1 курс колледжа','Другое'].map(g =>
          `<option value="${g}" ${getSaved('basic_info','grade')===g?'selected':''}>${g}</option>`
        ).join('')}
      </select>
    </div>
    <div class="field-row">
      <div class="field-group">
        <label for="f-email">Email *</label>
        <input type="email" id="f-email" placeholder="ivan@example.com"
               value="${getSaved('basic_info','email')}" />
      </div>
      <div class="field-group">
        <label for="f-phone">Телефон *</label>
        <input type="tel" id="f-phone" placeholder="+7 777 000 00 00"
               value="${getSaved('basic_info','phone')}" />
      </div>
    </div>
  `;
}

// ─── Block 2: Experience fields ───────────────────────────────────────────────
function renderExperience(container) {
  const fields = [
    { id: 'f-projects',      label: 'Расскажи о проектах, в которых ты участвовал(а) — школьных, личных, волонтёрских',      key: 'projects' },
    { id: 'f-self-projects', label: 'Были ли проекты, которые ты начал(а) сам(а)? Если да, опиши кратко',                    key: 'self_projects' },
    { id: 'f-competitions',  label: 'В каких олимпиадах, конкурсах или хакатонах ты участвовал(а)? Укажи результаты',        key: 'competitions' },
    { id: 'f-volunteering',  label: 'Есть ли у тебя опыт волонтёрства или общественной деятельности?',                       key: 'volunteering' },
    { id: 'f-selflearn',     label: 'Чему ты научился(ась) за последний год вне школьной программы?',                         key: 'self_learning' },
    { id: 'f-mentor',        label: 'Есть ли у тебя ментор или человек, который повлиял на твоё развитие? Кто это и как?',   key: 'mentor' },
  ];

  container.innerHTML = fields.map(f => `
    <div class="field-group">
      <label for="${f.id}">${f.label}</label>
      <textarea id="${f.id}" rows="4" placeholder="Опиши подробно...">${getSaved('experience', f.key)}</textarea>
    </div>
  `).join('');
}

// ─── Block 3: Motivation & Essays ─────────────────────────────────────────────
function renderMotivation(container) {
  const fields = [
    {
      id: 'f-why',
      label: 'Почему ты хочешь поступить в inVision U?',
      key: 'why_invision',
      minWords: 150,
      placeholder: 'Минимум 150 слов...',
    },
    {
      id: 'f-difficult',
      label: 'Опиши ситуацию, когда тебе было сложно, но ты не сдался/не сдалась. Что произошло и чему ты научился(ась)?',
      key: 'difficult_situation',
      minWords: 100,
      placeholder: 'Минимум 100 слов...',
    },
    {
      id: 'f-community',
      label: 'Какую проблему в своём городе или сообществе ты хотел(а) бы решить и почему?',
      key: 'community_problem',
      minWords: 100,
      placeholder: 'Минимум 100 слов...',
    },
  ];

  container.innerHTML = fields.map(f => `
    <div class="field-group essay-field">
      <label for="${f.id}">${f.label}</label>
      <div class="essay-hint">Минимум ${f.minWords} слов</div>
      <textarea id="${f.id}" rows="7" placeholder="${f.placeholder}"
                data-min-words="${f.minWords}"
                oninput="updateWordCount('${f.id}')"
      >${getSaved('motivation', f.key)}</textarea>
      <div class="word-count" id="wc-${f.id}">0 / ${f.minWords} слов</div>
    </div>
  `).join('');

  // Run word count on initial render (for restored values)
  fields.forEach(f => updateWordCount(f.id));
}

// Live word counter for essay fields
window.updateWordCount = function(id) {
  const textarea = $(id);
  const wc       = $('wc-' + id);
  if (!textarea || !wc) return;
  const words    = countWords(textarea.value);
  const min      = parseInt(textarea.dataset.minWords);
  wc.textContent = `${words} / ${min} слов`;
  wc.style.color = words >= min ? '#5eead4' : '#94a3b8';
};

function countWords(text) {
  return text.trim().split(/\s+/).filter(w => w.length > 0).length;
}

// ─── Block 4: Psychometric test (40 radio questions) ─────────────────────────
function renderPsychometric(container) {
  const saved = getSavedPsycho();  // previously selected answers

  container.innerHTML = PSYCHO_QUESTIONS.map((q, i) => `
    <div class="psycho-question" id="pq-${q.key}">
      <div class="psycho-q-header">
        <span class="psycho-num">${i + 1}</span>
        <p class="psycho-text">${q.text}</p>
      </div>
      <div class="psycho-options">
        ${q.options.map((opt, oi) => `
          <label class="radio-option ${saved[q.key] === opt ? 'selected' : ''}"
                 for="${q.key}-opt${oi}">
            <input type="radio"
                   id="${q.key}-opt${oi}"
                   name="${q.key}"
                   value="${opt}"
                   ${saved[q.key] === opt ? 'checked' : ''}
                   onchange="onRadioChange('${q.key}', this)"
            />
            <span class="radio-circle"></span>
            <span class="radio-label">${opt}</span>
          </label>
        `).join('')}
      </div>
    </div>
  `).join('');
}

// Called when a radio button changes — highlights the selected option
window.onRadioChange = function(key, input) {
  const group = document.querySelectorAll(`[name="${key}"]`);
  group.forEach(r => {
    r.closest('.radio-option').classList.toggle('selected', r.checked);
  });
};

// ─── Block 5: Consents ────────────────────────────────────────────────────────
function renderConsents(container) {
  const saved = getSaved('consents', null) || {};

  container.innerHTML = `
    <div class="consents-block">
      <p class="consents-intro">
        Пожалуйста, ознакомься с условиями и подтверди своё согласие.
        Оба пункта обязательны для подачи заявки.
      </p>

      <label class="checkbox-option" for="c-data">
        <input type="checkbox" id="c-data" ${saved.data_processing ? 'checked' : ''} />
        <span class="checkbox-box"></span>
        <span class="checkbox-label">
          Я даю согласие на обработку персональных данных в рамках отбора в inVision U
          <span class="required-star">*</span>
        </span>
      </label>

      <label class="checkbox-option" for="c-essay">
        <input type="checkbox" id="c-essay" ${saved.essay_authenticity ? 'checked' : ''} />
        <span class="checkbox-box"></span>
        <span class="checkbox-label">
          Я подтверждаю, что эссе написано мной лично
          <span class="required-star">*</span>
        </span>
      </label>

      <div class="form-error hidden" id="consents-error"></div>
    </div>
  `;
}

// ─── Saved data helpers ───────────────────────────────────────────────────────
// We keep collected data in a global object so navigating between blocks
// doesn't erase previously entered answers.
const formData = {};

function getSaved(block, field) {
  if (!formData[block]) return '';
  if (field === null) return formData[block];
  return formData[block][field] || '';
}

function getSavedPsycho() {
  return formData['psychometric'] || {};
}

// ─── Collect data from the current block ─────────────────────────────────────
// Returns true if valid, false if there's a missing required field.
function collectCurrentBlock() {
  const type = BLOCKS[state.currentBlock].type;

  if (type === 'basic_info') {
    const full_name = $('f-fullname')?.value.trim();
    const age       = $('f-age')?.value.trim();
    const city      = $('f-city')?.value.trim();
    const school    = $('f-school')?.value.trim();
    const grade     = $('f-grade')?.value;
    const email     = $('f-email')?.value.trim();
    const phone     = $('f-phone')?.value.trim();

    if (!full_name || !age || !city || !school || !grade || !email || !phone) {
      alert('Пожалуйста, заполните все поля Блока 1.');
      return false;
    }
    formData['basic_info'] = { full_name, age: parseInt(age), city, school, grade, email, phone };
  }

  if (type === 'experience') {
    formData['experience'] = {
      projects:      $('f-projects')?.value.trim()      || '',
      self_projects: $('f-self-projects')?.value.trim() || '',
      competitions:  $('f-competitions')?.value.trim()  || '',
      volunteering:  $('f-volunteering')?.value.trim()  || '',
      self_learning: $('f-selflearn')?.value.trim()     || '',
      mentor:        $('f-mentor')?.value.trim()         || '',
    };
  }

  if (type === 'motivation') {
    const why    = $('f-why')?.value.trim()       || '';
    const diff   = $('f-difficult')?.value.trim() || '';
    const comm   = $('f-community')?.value.trim() || '';

    // Enforce minimum word counts
    if (countWords(why) < 150) {
      alert('Эссе "Почему inVision U?" должно содержать минимум 150 слов.');
      return false;
    }
    if (countWords(diff) < 100) {
      alert('Эссе о трудной ситуации должно содержать минимум 100 слов.');
      return false;
    }
    if (countWords(comm) < 100) {
      alert('Эссе о проблеме сообщества должно содержать минимум 100 слов.');
      return false;
    }
    formData['motivation'] = {
      why_invision:         why,
      difficult_situation:  diff,
      community_problem:    comm,
    };
  }

  if (type === 'psychometric') {
    // Check that all 40 questions are answered
    const answers = {};
    let unanswered = [];

    PSYCHO_QUESTIONS.forEach(q => {
      const selected = document.querySelector(`[name="${q.key}"]:checked`);
      if (selected) {
        answers[q.key] = selected.value;
      } else {
        unanswered.push(q.key);
      }
    });

    if (unanswered.length > 0) {
      // Scroll to first unanswered question
      const firstMissing = $('pq-' + unanswered[0]);
      if (firstMissing) firstMissing.scrollIntoView({ behavior: 'smooth', block: 'center' });
      alert(`Пожалуйста, ответь на все 40 вопросов. Не отвечено: ${unanswered.length}`);
      return false;
    }

    formData['psychometric'] = answers;
  }

  if (type === 'consents') {
    const dataOk  = $('c-data')?.checked;
    const essayOk = $('c-essay')?.checked;

    if (!dataOk || !essayOk) {
      showError('consents-error', 'Необходимо принять оба согласия для подачи заявки.');
      return false;
    }
    formData['consents'] = {
      data_processing:   true,
      essay_authenticity: true,
    };
  }

  return true;  // all good
}

// ─── Navigation: Next / Prev ──────────────────────────────────────────────────
$('btn-form-next').addEventListener('click', async () => {
  // Collect and validate the current block first
  if (!collectCurrentBlock()) return;

  const isLast = state.currentBlock === BLOCKS.length - 1;

  if (isLast) {
    // Last block (consents) → submit to backend
    await submitApplication();
  } else {
    state.currentBlock++;
    renderBlock(state.currentBlock);
  }
});

$('btn-form-prev').addEventListener('click', () => {
  collectCurrentBlock();  // save silently (no validation on back)
  if (state.currentBlock > 0) {
    state.currentBlock--;
    renderBlock(state.currentBlock);
  }
});

// ─── Submit application to backend ───────────────────────────────────────────
async function submitApplication() {
  const btn  = $('btn-form-next');
  btn.disabled    = true;
  btn.textContent = 'Отправляем... ⏳';

  try {
    // Build the full payload
    const payload = {
      user_id:     state.user.id,
      basic_info:  formData['basic_info'],
      experience:  formData['experience'],
      motivation:  formData['motivation'],
      psychometric: formData['psychometric'],
      consents:    formData['consents'],
    };

    // POST to /api/submit-answers
    const response = await apiPost('/submit-answers', payload);

    // Show results screen with the JSON from the server
    showResults(response);
    showScreen('results');
  } catch (err) {
    alert('Ошибка при отправке: ' + err.message);
    btn.disabled    = false;
    btn.textContent = 'Отправить заявку ✓';
  }
}

// ─── Results: show the JSON response ─────────────────────────────────────────
function showResults(response) {
  // Pretty-print the backend JSON response
  const formatted = JSON.stringify(response, null, 2);
  $('json-output').textContent = formatted;
  $('results-subtitle').textContent =
    `Заявка от ${state.user.username} успешно сохранена в базе данных.`;
}

// ─── Copy JSON button ─────────────────────────────────────────────────────────
$('btn-copy-json').addEventListener('click', () => {
  const text = $('json-output').textContent;
  navigator.clipboard.writeText(text).then(() => {
    $('btn-copy-json').textContent = 'Скопировано ✓';
    setTimeout(() => ($('btn-copy-json').textContent = 'Copy'), 2000);
  });
});

// ─── Results actions ──────────────────────────────────────────────────────────
$('btn-retake').addEventListener('click', () => {
  Object.keys(formData).forEach(k => delete formData[k]);
  startForm();
});

$('btn-home').addEventListener('click', () => showScreen('landing'));

// ─── Init ─────────────────────────────────────────────────────────────────────
updateHeader();
showScreen('landing');
