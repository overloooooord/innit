# Архитектура Indrive-AI — Полный Гайд

> Этот документ объясняет **простым языком**: где лежат вопросы, как их менять, куда уходят данные, и где объявляется база данных.

---

## Общая схема системы

```
┌─────────────────────────────────────────────────────────────────┐
│                        ПОЛЬЗОВАТЕЛЬ (браузер)                   │
│                                                                 │
│  front/index.html + front/app.js + front/styles.css             │
│  ┌──────────┐   ┌───────────┐   ┌────────────┐   ┌──────────┐  │
│  │ Регист-  │──▶│ MBTI тест │──▶│ Языковой   │──▶│ Успех!   │  │
│  │ рация    │   │ 40 вопр.  │   │ тест 20 в. │   │          │  │
│  └──────────┘   └───────────┘   └────────────┘   └──────────┘  │
└────────┬────────────┬──────────────┬────────────────────────────┘
         │            │              │
         ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Django Backend (backend/)                    │
│                                                                 │
│  POST /api/applications/    ← анкета                            │
│  POST /api/tests/mbti/      ← ответы MBTI                      │
│  POST /api/tests/language/  ← ответы языкового теста            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ SQLite / PostgreSQL (backend/db.sqlite3)                 │   │
│  │                                                          │   │
│  │  Application ──┬── MBTITestResult                        │   │
│  │                └── LanguageTestResult                     │   │
│  │  Candidate ────── ScoringResult                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ (опционально)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ML Pipeline (pipeline/)                     │
│                                                                 │
│  scorer.py → feature_extractor.py → XGBoost модель              │
│  Выдаёт: reject / maybe / shortlist + объяснение                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. ГДЕ ЛЕЖАТ ВОПРОСЫ И КАК ИХ МЕНЯТЬ

### 1.1 MBTI Вопросы (40 штук)

**Файл:** [app.js](file:///home/caterinw/Indrive-AI/front/app.js#L47-L137)

Массив `MBTI_QUESTIONS` — строка 47. Каждый вопрос это объект:

```javascript
{ key: 'q1',  text: 'Когда у меня есть важная цель, я...',
  a: 'Сразу составляю план и следую ему',
  b: 'Действую по ситуации и настроению' },
```

| Поле   | Что это                              |
|--------|--------------------------------------|
| `key`  | Уникальный ID вопроса (`q1`..`q40`) |
| `text` | Текст вопроса                        |
| `a`    | Первый вариант ответа                |
| `b`    | Второй вариант ответа               |

**Группы вопросов:**
| Вопросы  | Категория              |
|----------|------------------------|
| q1–q8    | Целеустремлённость     |
| q9–q16   | Мотивация              |
| q17–q24  | Стрессоустойчивость    |
| q25–q32  | Командная работа       |
| q33–q40  | Критическое мышление   |

#### Как изменить MBTI вопрос

Открой `front/app.js`, найди нужный вопрос по ключу (например `q5`) и измени текст:

```diff
-  { key: 'q5',  text: 'Когда у меня несколько задач, я...',
-    a: 'Приоритизирую и делаю по очереди', b: 'Переключаюсь по настроению' },
+  { key: 'q5',  text: 'Твой новый вопрос здесь...',
+    a: 'Новый вариант A', b: 'Новый вариант B' },
```

#### Как добавить/удалить MBTI вопрос

- **Добавить:** Добавь новый объект в массив `MBTI_QUESTIONS` с новым ключом (`q41`, `q42`...)
- **Удалить:** Просто убери объект из массива
- **⚠ После этого** обнови MBTI-калькулятор на бэкенде (файл `backend/candidates/serializers.py` — метод `calculate_mbti_type`), потому что он считает тип по номерам вопросов

---

### 1.2 Языковой тест (20 вопросов)

**Файл:** [app.js](file:///home/caterinw/Indrive-AI/front/app.js#L142-L183)

Массив `LANG_QUESTIONS` — строка 142. Каждый вопрос:

```javascript
{ key: 'q1',  text: 'Choose the correct sentence:',
  options: ['She go to school every day.',
            'She goes to school every day.',
            'She going to school every day.',
            'She are go to school every day.'],
  correct: 'B' },
```

| Поле      | Что это                                          |
|-----------|--------------------------------------------------|
| `key`     | Уникальный ID (`q1`..`q20`)                     |
| `text`    | Текст вопроса                                    |
| `options` | Массив из 4 вариантов (A, B, C, D по порядку)   |
| `correct` | Правильный ответ (`'A'`, `'B'`, `'C'` или `'D'`) |

#### Как изменить языковой вопрос

```diff
-  { key: 'q3',  text: '"I ___ to the cinema yesterday."',
-    options: ['go', 'goes', 'went', 'gone'], correct: 'C' },
+  { key: 'q3',  text: 'Твой новый вопрос...',
+    options: ['вариант1', 'вариант2', 'вариант3', 'вариант4'], correct: 'A' },
```

#### Как добавить/удалить языковой вопрос

- **Добавить:** Добавь объект в массив `LANG_QUESTIONS` с новым ключом (`q21`, `q22`...)
- **Удалить:** Убери объект из массива
- **Баллы пересчитаются автоматически** — функция `calculateLangScore()` на строке 747 считает правильные ответы динамически

---

### 1.3 Поля регистрационной формы

**Файл:** [app.js](file:///home/caterinw/Indrive-AI/front/app.js#L370-L444) + [index.html](file:///home/caterinw/Indrive-AI/front/index.html)

Форма собирает эти поля:

| Поле                | HTML id         | Описание                  |
|---------------------|-----------------|---------------------------|
| ФИО                 | `f-name`        | Обязательное              |
| Город               | `f-city`        | Dropdown из API           |
| Регион              | `f-region`      | Автоматически по городу   |
| Telegram            | `f-telegram`    | Обязательное              |
| Хобби               | `f-hobbies`     | Свободный текст           |
| Спорт               | `f-sport`       | Свободный текст           |
| Эссе                | `f-essay`       | Свободный текст           |
| Мотивационное письмо| `f-motivation`  | Свободный текст           |
| Языки               | `lang-chips`    | Мульти-выбор (чипсы)      |

Чтобы **добавить новое поле** в регистрацию:
1. Добавь `<input>` в `front/index.html` внутри `<form id="register-form">`
2. Прочитай его в `front/app.js` → функция `initRegistrationForm()` (строка 370)
3. Добавь в `payload` (строка 406)
4. Добавь поле в Django модель `Application` (`backend/candidates/models.py`, строка 91)
5. Добавь в сериалайзер (`backend/candidates/serializers.py`)
6. Сделай миграцию: `cd backend && python manage.py makemigrations && python manage.py migrate`

---

## 2. ПУТЬ ДАННЫХ (как данные идут по пайплайну)

### 2.1 Пользовательский пайплайн (заполнение заявки)

```
Шаг 1: РЕГИСТРАЦИЯ
─────────────────────────────────────────────────
Пользователь заполняет форму → нажимает "Далее"
    ↓
front/app.js:initRegistrationForm() (строка 370)
    собирает данные из полей формы в объект payload
    ↓
front/api.js:API.submitApplication(payload) (строка 104)
    отправляет POST /api/applications/
    ↓
backend/candidates/views.py:application_list_create() (строка 66)
    валидирует через ApplicationSerializer
    ↓
backend/candidates/models.py:Application (строка 91)
    сохраняет в таблицу candidates_application
    ↓
Возвращает JSON с id заявки → state.applicationId = result.id


Шаг 2: MBTI ТЕСТ
─────────────────────────────────────────────────
Пользователь отвечает на 40 вопросов по одному
    ↓
front/app.js:submitMBTI() (строка 543)
    отправляет { application_id, answers: {q1:"A", q2:"B"...} }
    ↓
front/api.js:API.submitMBTI() (строка 112)
    POST /api/tests/mbti/
    ↓
backend/candidates/views.py:mbti_test_submit() (строка 207)
    валидирует, рассчитывает MBTI тип (INTJ, ENFP и т.д.)
    ↓
backend/candidates/models.py:MBTITestResult (строка 182)
    сохраняет в таблицу candidates_mbtitestresult
    связано с Application через OneToOneField


Шаг 3: ЯЗЫКОВОЙ ТЕСТ
─────────────────────────────────────────────────
Пользователь отвечает на 20 вопросов + таймер 10 мин
    ↓
front/app.js:submitLangTest() (строка 757)
    считает score, время, нарушения
    отправляет { application_id, language, answers, score,
                 max_score, time_spent_seconds, violation_count }
    ↓
front/api.js:API.submitLanguageTest() (строка 124)
    POST /api/tests/language/
    ↓
backend/candidates/views.py:language_test_submit() (строка 234)
    валидирует и сохраняет
    ↓
backend/candidates/models.py:LanguageTestResult (строка 223)
    сохраняет в таблицу candidates_languagetestresult
    связано с Application через ForeignKey


Шаг 4: ЭКРАН УСПЕХА
─────────────────────────────────────────────────
front/app.js:showScreen('success') — показывает "Заявка отправлена!"
```

### 2.2 ML Пайплайн (оценка кандидата — для админа)

ML пайплайн — это **отдельная** система для старых `Candidate` записей. Она **не связана** напрямую с `Application` заявками.

```
Админ нажимает "Оценить" на кандидате
    ↓
POST /api/candidates/<id>/score/
    ↓
backend/candidates/views.py:candidate_score() (строка 483)
    ↓
backend/candidates/ml_service.py:score_candidate() (строка 49)
    загружает модель из pipeline/models/model.pkl (один раз, синглтон)
    ↓
pipeline/scorer.py:CandidateScorer.score() (строка 17)
    1. extract_features(candidate) → вектор из 22 чисел
    2. model.predict_proba(X) → вероятности [reject, maybe, shortlist]
    3. explainer.explain() → SHAP объяснение
    4. _build_radar() → 5 метрик для радар-чарта
    5. _build_flags() → предупреждения
    ↓
Результат сохраняется в ScoringResult (модель Django)
Возвращается JSON
```

---

## 3. ГДЕ ОБЪЯВЛЯЕТСЯ БАЗА ДАННЫХ

У тебя **две базы данных** от двух бэкендов. **Активный** — Django (`backend/`).

### 3.1 Django БД (АКТИВНАЯ) ✅

**Конфигурация:** [settings.py](file:///home/caterinw/Indrive-AI/backend/invision/settings.py#L66-L93)

```python
# Строки 66-93 в backend/invision/settings.py

# По умолчанию — SQLite
_db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')

if _db_engine == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',  # → backend/db.sqlite3
        }
    }
else:
    # PostgreSQL (для продакшена)
    DATABASES = {
        'default': {
            'ENGINE': _db_engine,
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT'),
        }
    }

# Railway автоматически даёт DATABASE_URL
_database_url = config('DATABASE_URL', default='')
if _database_url:
    DATABASES['default'] = dj_database_url.parse(_database_url)
```

**Файл БД:** `backend/db.sqlite3`

**Переключение на PostgreSQL:** В файле `backend/.env`:
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=indrive_ai
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

**Или через Railway:** достаточно задать переменную `DATABASE_URL`.

**Таблицы Django (модели):**

| Таблица                          | Модель               | Файл                          |
|----------------------------------|----------------------|-------------------------------|
| `candidates_application`         | `Application`        | `backend/candidates/models.py:91` |
| `candidates_mbtitestresult`      | `MBTITestResult`     | `backend/candidates/models.py:182`|
| `candidates_languagetestresult`  | `LanguageTestResult` | `backend/candidates/models.py:223`|
| `candidates_candidate`           | `Candidate`          | `backend/candidates/models.py:23` |
| `candidates_scoringresult`       | `ScoringResult`      | `backend/candidates/models.py:64` |

**Миграции:**
```bash
cd backend
python manage.py makemigrations   # генерирует файл миграции
python manage.py migrate          # применяет к БД
```

---

### 3.2 FastAPI БД (СТАРАЯ, не используется фронтом) ⚠️

**Файл:** [database.py](file:///home/caterinw/Indrive-AI/back/database.py)

```python
# back/database.py — строка 8
DB_PATH = os.path.join(os.path.dirname(__file__), "uniadmit.db")
```

Это **альтернативный** бэкенд в папке `back/`. Он использует чистый SQLite через `sqlite3` модуль Python (без ORM). Фронт сейчас **НЕ** использует этот бэкенд, потому что `api.js` ходит на Django-маршруты (`/api/applications/`, `/api/tests/mbti/`).

Таблицы FastAPI:
- `users` (id, username, email, password_hash)
- `applications` (id, user_id, basic_info, experience, motivation, psychometric, consents)

---

## 4. СТРУКТУРА ФАЙЛОВ — КАРТА ПРОЕКТА

```
Indrive-AI/
├── front/                          ← ФРОНТЕНД
│   ├── index.html                  ← HTML разметка (все экраны)
│   ├── app.js                      ← Логика + ВОПРОСЫ ТЕСТОВ
│   ├── api.js                      ← HTTP клиент (fetch запросы)
│   ├── i18n.js                     ← Переводы (RU/KZ/EN)
│   └── styles.css                  ← Стили
│
├── backend/                        ← DJANGO БЭКЕНД (АКТИВНЫЙ)
│   ├── manage.py                   ← Точка входа Django
│   ├── db.sqlite3                  ← ФАЙЛ БАЗЫ ДАННЫХ
│   ├── .env                        ← Секреты (пароли, токены)
│   ├── invision/
│   │   ├── settings.py             ← КОНФИГ БД (строки 66-93)
│   │   └── urls.py                 ← Главный роутер
│   └── candidates/
│       ├── models.py               ← МОДЕЛИ БД (таблицы)
│       ├── views.py                ← API endpoints (логика)
│       ├── serializers.py          ← Валидация данных
│       ├── urls.py                 ← Маршруты API
│       ├── admin.py                ← Django admin панель
│       ├── ml_service.py           ← Мост к ML pipeline
│       ├── kz_regions.py           ← Справочник городов КЗ
│       └── telegram_service.py     ← Telegram уведомления
│
├── back/                           ← FASTAPI БЭКЕНД (старый)
│   ├── main.py                     ← Старый сервер
│   ├── database.py                 ← Старая БД (uniadmit.db)
│   ├── models.py                   ← Pydantic модели
│   └── routers/
│       ├── auth.py                 ← Регистрация/логин
│       └── assessment.py           ← Отправка заявки
│
├── pipeline/                       ← ML ПАЙПЛАЙН
│   ├── scorer.py                   ← Оценка кандидата
│   ├── feature_extractor.py        ← Извлечение 22 фичей
│   ├── trainer.py                  ← Обучение модели
│   ├── explainer.py                ← SHAP объяснения
│   ├── config.py                   ← Параметры модели
│   ├── run_pipeline.py             ← Запуск всего пайплайна
│   └── models/model.pkl            ← Обученная модель
│
└── data/
    ├── candidate_scheme.json       ← JSON схема кандидата
    ├── sample_candidate.json       ← Пример кандидата
    └── synthetic_dataset.json      ← Тренировочный датасет
```

---

## 5. БЫСТРАЯ ШПАРГАЛКА

### Хочу изменить вопрос MBTI:
→ Открой `front/app.js`, найди `MBTI_QUESTIONS` (строка 47), меняй объект

### Хочу изменить вопрос языкового теста:
→ Открой `front/app.js`, найди `LANG_QUESTIONS` (строка 142), меняй объект

### Хочу добавить поле в анкету:
→ `front/index.html` (HTML) + `front/app.js` (JS payload) + `backend/candidates/models.py` (модель) + `backend/candidates/serializers.py` (сериалайзер) + `makemigrations`

### Хочу поменять настройки БД:
→ `backend/.env` (переменные) или `backend/invision/settings.py` (строка 66)

### Хочу посмотреть все API маршруты:
→ `backend/candidates/urls.py`

### Хочу понять как работает ML оценка:
→ `pipeline/scorer.py` (вход) → `pipeline/feature_extractor.py` (фичи) → `pipeline/config.py` (параметры)
