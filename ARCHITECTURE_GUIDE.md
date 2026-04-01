# Indrive-AI: Полное руководство по архитектуре

## Оглавление
1. [Что такое Indrive-AI](#1-что-такое-indrive-ai)
2. [Структура проекта](#2-структура-проекта)
3. [Что делает каждый файл](#3-что-делает-каждый-файл)
4. [Как работает ML-пайплайн (пошагово)](#4-как-работает-ml-пайплайн-пошагово)
5. [Схема кандидата (JSON)](#5-схема-кандидата-json)
6. [23 фичи и что они значат](#6-23-фичи-и-что-они-значат)
7. [Рекомендация: Django для бэкенда](#7-рекомендация-django-для-бэкенда)
8. [Архитектура Backend + Frontend](#8-архитектура-backend--frontend)
9. [Описание эндпоинтов API](#9-описание-эндпоинтов-api)
10. [Как связать ML-пайплайн с Django](#10-как-связать-ml-пайплайн-с-django)
11. [Пошаговый план создания проекта](#11-пошаговый-план-создания-проекта)

---

## 1. Что такое Indrive-AI

Это **система отбора кандидатов** для программы InVision U. 

Система:
- Принимает анкету кандидата (JSON)
- Извлекает 23 числовых признака (GPA, олимпиады, проекты и т.д.)
- Обучает модель XGBoost для классификации: **reject / maybe / shortlist**
- Даёт объяснение решения с помощью SHAP (какие факторы повлияли)
- Проверяет bias по демографии (город, тип школы, ментор)

---

## 2. Структура проекта

```
Indrive-AI/
├── data/
│   ├── candidate_scheme.json     # JSON-схема кандидата (формат данных)
│   ├── sample_candidate.json     # Пример одного кандидата
│   └── synthetic_dataset.json    # 80 синтетических кандидатов для обучения
│
├── pipeline/
│   ├── __init__.py
│   ├── config.py                 # Конфигурация: маппинги, параметры, пути
│   ├── feature_extractor.py      # Извлечение 23 фичей из JSON кандидата
│   ├── trainer.py                # Обучение XGBoost + базовые модели
│   ├── evaluator.py              # Оценка модели: метрики, confusion matrix
│   ├── explainer.py              # SHAP-объяснения + ablation study
│   ├── scorer.py                 # Скоринг одного кандидата (основной вход для API)
│   ├── fairness_audit.py         # Аудит bias по демографии
│   └── run_pipeline.py           # CLI — запуск всего пайплайна целиком
│
└── requirements.txt              # Зависимости: scikit-learn, xgboost, shap, numpy
```

---

## 3. Что делает каждый файл

### `config.py` — Конфигурация
Содержит все настройки проекта:
- **OLYMPIAD_LEVEL_MAP**: маппинг уровней олимпиад (school=1, city=2, regional=3, national=4, international=5)
- **OLYMPIAD_RESULT_MAP**: результаты (participant=0, honorable_mention=1, prize=2)
- **PROJECT_ROLE_MAP**: роли в проектах (volunteer=0, participant=1, co_founder=2, founder=3)
- **LABEL_MAP**: метки классификации (reject=0, maybe=1, shortlist=2)
- **STRUCTURED_FEATURES**: список всех 23 фичей по именам
- **XGBOOST_PARAMS**: гиперпараметры модели (200 деревьев, глубина 5, learning_rate 0.1)
- **Пути**: MODEL_PATH, SHAP_PLOTS_DIR, METRICS_DIR, FAIRNESS_DIR

### `feature_extractor.py` — Извлечение фичей
Главная функция: `extract_features(candidate) → numpy array (23 элемента)`

Берёт JSON кандидата и превращает его в числовой вектор из 23 фичей:
- **Образование** (6 фичей): GPA, количество олимпиад, макс. уровень, наличие призов, курсы
- **Опыт** (7 фичей): количество проектов, доля founder, типы проектов, размер команд
- **Траектория** (6 фичей): рост ролей, масштаба, навыков, период активности, упорство
- **Метаданные бота** (3 фичи): длительность сессии, время написания эссе, паузы

Также есть `extract_batch()` для пакетной обработки нескольких кандидатов.

### `trainer.py` — Обучение модели
Главная функция: `train(dataset_path) → dict`

Шаги:
1. Загружает JSON-датасет → извлекает фичи для каждого кандидата
2. Делит на train/test (80/20, стратифицированно)
3. Кросс-валидация (5 fold)
4. Обучает финальную модель XGBoost
5. Сохраняет модель в `models/model.pkl`
6. Возвращает модель + сплиты для дальнейшего использования

Также содержит 3 базовых модели для сравнения:
- GPA Ranking (только по GPA)
- Rule-Based (ручная формула)
- Logistic Regression

### `evaluator.py` — Оценка качества
Главная функция: `evaluate(training_results) → dict`

Шаги:
1. Считает метрики модели: Accuracy, Precision, Recall, F1, AUC-ROC
2. Строит confusion matrix
3. Оценивает все 3 базовые модели на том же тесте
4. Выводит таблицу сравнения (XGBoost vs baselines)
5. Анализ ошибок: где модель ошибается
6. Сохраняет отчёт в `outputs/metrics/evaluation_report.json`

### `explainer.py` — SHAP-объяснения
Класс `CandidateExplainer`:
- `explain(feature_vector)` — объяснение для одного кандидата:
  - Какие фичи **помогли** (top_positive_factors)
  - Какие фичи **помешали** (top_negative_factors)
- `global_importance(X)` — глобальная важность фичей по SHAP

Также содержит:
- **Ablation study**: убирает группы фичей по одной и смотрит, как падает F1
- **FEATURE_DESCRIPTIONS**: русские описания всех 23 фичей

### `scorer.py` — Скоринг кандидата ⭐ (САМЫЙ ВАЖНЫЙ ДЛЯ API)
Класс `CandidateScorer` — **это то, что будет вызывать твой бэкенд**.

Методы:
- `score(candidate_json) → dict` — оценка одного кандидата. Возвращает:
  - `prediction`: "reject" / "maybe" / "shortlist"
  - `confidence`: уверенность (0.0 — 1.0)
  - `probabilities`: вероятности каждого класса
  - `explanation`: сильные и слабые стороны (SHAP)
  - `radar`: данные для радар-диаграммы (Инициативность, Устойчивость, Академические, Лидерство, Разнообразие)
  - `flags`: предупреждения (нет проектов, давняя активность и т.д.)
  - `trajectory`: хронология достижений для timeline

- `score_batch(candidates) → list` — оценка списка кандидатов
- `rank(candidates) → list` — ранжирование кандидатов по shortlist probability (с полями rank и total_candidates)

### `fairness_audit.py` — Аудит предвзятости
- Проверяет, не дискриминирует ли модель по: городу, типу школы, наличию ментора, возрасту, региону
- ANOVA тест для каждой группы
- Проверка proxy-корреляций (косвенный bias)
- Выносит вердикт: ✅ PASSED или ⚠️ NEEDS REVIEW

### `run_pipeline.py` — CLI запуск
Запускает весь пайплайн последовательно:
```bash
python pipeline/run_pipeline.py --dataset data/synthetic_dataset.json --candidate data/sample_candidate.json
```

---

## 4. Как работает ML-пайплайн (пошагово)

```
Кандидат (JSON)
      │
      ▼
┌─────────────────────┐
│  feature_extractor   │  → 23 числовых фичи
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│     trainer          │  → Обученная модель XGBoost (model.pkl)
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│     evaluator        │  → Метрики: F1, Accuracy, AUC-ROC
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│     explainer        │  → SHAP-объяснения + Ablation + Feature Importance
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  fairness_audit      │  → Проверка bias по демографии
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│     scorer           │  → Финальный скоринг: prediction + explanation + radar
└─────────────────────┘
```

**Для API тебе нужен только `scorer.py`!** Он загружает обученную модель и вызывает всё остальное автоматически.

---

## 5. Схема кандидата (JSON)

Кандидат — это JSON-объект со следующими разделами:

| Раздел           | Описание                                                      | Используется в скоринге? |
|------------------|---------------------------------------------------------------|:------------------------:|
| `id`             | Уникальный идентификатор                                      | Нет (ID)                 |
| `personal`       | ФИО, возраст, город, тип школы, ментор                        | ❌ Только для отображения  |
| `education`      | GPA, олимпиады, курсы                                         | ✅ Да (6 фичей)           |
| `experience`     | Проекты, волонтёрство, лидерские роли                         | ✅ Да (7 фичей)           |
| `essay`          | Тема, текст, количество слов                                  | ❌ (будущий NLP модуль)    |
| `motivation`     | Мотивационное письмо                                          | ❌ (будущий NLP модуль)    |
| `self_assessment`| Самооценка 1-5 (лидерство, работа в команде, и т.д.)          | ❌ (пока)                 |
| `bot_metadata`   | Длительность сессии, паузы, время написания эссе               | ✅ Да (3 фичи)            |
| `label`          | Ручная метка: reject/maybe/shortlist (только в training data)  | Целевая переменная        |

---

## 6. 23 фичи и что они значат

### Образование (features 0-5)
| Фича                       | Описание                                              |
|----------------------------|-------------------------------------------------------|
| `f_gpa`                    | Средний балл (0.0 — 5.0)                             |
| `f_olympiad_count`         | Количество олимпиад                                   |
| `f_olympiad_max_level`     | Макс. уровень (1=школа, 5=международная)              |
| `f_olympiad_has_prize`     | Есть ли призовое место (0/1)                          |
| `f_courses_count`          | Количество онлайн-курсов                               |
| `f_courses_completed_ratio`| Доля завершённых курсов (0.0 — 1.0)                   |

### Опыт (features 6-12)
| Фича                    | Описание                                                 |
|--------------------------|----------------------------------------------------------|
| `f_project_count`        | Количество проектов                                       |
| `f_founder_ratio`        | Доля проектов, где роль = founder/co_founder              |
| `f_has_technical_project`| Есть ли технический проект (0/1)                          |
| `f_has_social_project`   | Есть ли социальный проект (0/1)                           |
| `f_project_diversity`    | Количество различных типов проектов                       |
| `f_max_team_size`        | Макс. размер команды                                      |
| `f_solo_project_count`   | Количество сольных проектов                               |

### Траектория (features 13-18)
| Фича                       | Описание                                               |
|-----------------------------|--------------------------------------------------------|
| `f_role_progression`        | Рост ролей (участник → лидер) со временем              |
| `f_scope_progression`       | Рост масштаба: команды больше, олимпиады выше          |
| `f_skill_diversity_growth`  | Сколько новых типов навыков появилось со временем       |
| `f_activity_years_span`     | Период активности (max_year - min_year)                |
| `f_persistence_signal`      | Повторял ли олимпиаду после неудачи? (0/1)             |
| `f_activity_recency`        | Лет с последней активности (меньше = лучше)            |

### Метаданные бота (features 19-21)
| Фича                    | Описание                                                 |
|--------------------------|----------------------------------------------------------|
| `f_session_duration`     | Длительность заполнения заявки (сек)                      |
| `f_essay_typing_duration`| Время написания эссе (сек)                                |
| `f_total_pauses`         | Количество пауз при заполнении                            |

---

## 7. Рекомендация: Django для бэкенда

### Почему Django + Django REST Framework (DRF)?

| Критерий               | Django + DRF        | Flask               | FastAPI             |
|------------------------|---------------------|----------------------|---------------------|
| Встроенная админка     | ✅ Есть              | ❌ Нет               | ❌ Нет              |
| ORM для базы данных    | ✅ Мощный            | ❌ Нужен SQLAlchemy   | ❌ Нужен SQLAlchemy  |
| Аутентификация/регистрация | ✅ Из коробки    | ❌ Руками            | ❌ Руками           |
| REST API              | ✅ DRF               | ⚠️ Руками           | ✅ Авто-docs         |
| Интеграция с Python ML | ✅ Да               | ✅ Да                | ✅ Да               |
| Сложность для новичка  | ⚠️ Средняя          | ✅ Простой            | ⚠️ Средняя          |

**Рекомендация: Django + DRF**, потому что:
1. У тебя уже нужна **регистрация** → Django Auth из коробки
2. Нужна **база данных** для кандидатов → Django ORM
3. Нужны **REST API** для фронтенда → DRF
4. Django Admin — бесплатная админка для просмотра/редактирования данных

---

## 8. Архитектура Backend + Frontend

```
┌────────────────────────────────────────────────────────┐
│                     FRONTEND                           │
│  (React / Vue / Plain HTML+JS)                         │
│                                                        │
│  Страницы:                                             │
│  - Регистрация кандидата (форма)                       │
│  - Список кандидатов (таблица + сортировка)            │
│  - Профиль кандидата (детальная карточка)              │
│  - Поиск кандидата (по имени/ID)                       │
└────────────────────┬───────────────────────────────────┘
                     │  HTTP запросы (JSON)
                     ▼
┌────────────────────────────────────────────────────────┐
│                 DJANGO BACKEND (API)                    │
│                                                        │
│  Эндпоинты (REST):                                     │
│  POST /api/candidates/register/    — регистрация       │
│  GET  /api/candidates/             — список + сортровка│
│  GET  /api/candidates/<id>/        — один кандидат     │
│  GET  /api/candidates/search/?q=   — поиск             │
│  POST /api/candidates/<id>/score/  — запуск скоринга   │
│  GET  /api/candidates/ranking/     — ранжирование      │
│                                                        │
│  Модели Django (база данных):                          │
│  - Candidate (все поля из схемы)                       │
│  - ScoringResult (результат оценки)                    │
└────────────────────┬───────────────────────────────────┘
                     │  Python-вызовы
                     ▼
┌────────────────────────────────────────────────────────┐
│              ML PIPELINE (существующий код)             │
│                                                        │
│  scorer.py → CandidateScorer.score(candidate_dict)     │
│  scorer.py → CandidateScorer.rank(candidates_list)     │
│                                                        │
│  Загружает models/model.pkl                            │
│  Вызывает feature_extractor → explainer → результат    │
└────────────────────────────────────────────────────────┘
```

---

## 9. Описание эндпоинтов API

### 1. `POST /api/candidates/register/` — Регистрация кандидата

**Что делает:** Принимает анкету кандидата и сохраняет в базу.

**Тело запроса (JSON):**
```json
{
  "personal": {
    "name": "Алия Ибрагимова",
    "age": 17,
    "city": "Алматы",
    "school_type": "lyceum"
  },
  "education": {
    "gpa": 4.7,
    "olympiads": [...],
    "courses": [...]
  },
  "experience": {
    "projects": [...]
  },
  "essay": {
    "topic": "...",
    "text": "...",
    "word_count": 350
  },
  "motivation": { "text": "..." },
  "self_assessment": { "leadership": 4, "teamwork": 5 }
}
```

**Ответ:**
```json
{
  "id": "cand_abc123",
  "status": "registered",
  "message": "Кандидат успешно зарегистрирован"
}
```

---

### 2. `GET /api/candidates/` — Список кандидатов + Сортировка

**Параметры запроса:**
```
?sort_by=gpa           # или: name, score, confidence, created_at
&order=desc            # asc / desc
&page=1                # пагинация
&page_size=20          # кандидатов на страницу
&prediction=shortlist  # фильтр по предсказанию
```

**Ответ:**
```json
{
  "count": 80,
  "page": 1,
  "results": [
    {
      "id": "cand_abc123",
      "name": "Алия Ибрагимова",
      "city": "Алматы",
      "gpa": 4.7,
      "prediction": "shortlist",
      "confidence": 0.87,
      "rank": 1
    },
    ...
  ]
}
```

---

### 3. `GET /api/candidates/<id>/` — Детальная информация

**Ответ:** Полный JSON кандидата + результат скоринга (prediction, explanation, radar, flags, trajectory).

---

### 4. `GET /api/candidates/search/?q=Алия` — Поиск

**Параметры:**
```
?q=Алия          # поиск по имени (частичное совпадение)
&city=Алматы     # дополнительный фильтр
```

**Ответ:** Список совпавших кандидатов (формат как в списке).

---

### 5. `POST /api/candidates/<id>/score/` — Запуск ML-скоринга

**Что делает:** Берёт кандидата из базы, прогоняет через `CandidateScorer.score()`, сохраняет результат.

**Ответ:**
```json
{
  "candidate_id": "cand_abc123",
  "prediction": "shortlist",
  "confidence": 0.87,
  "probabilities": { "reject": 0.05, "maybe": 0.08, "shortlist": 0.87 },
  "explanation": {
    "top_positive_factors": [
      { "description": "Наличие призового места", "impact": 0.15 }
    ],
    "top_negative_factors": [
      { "description": "Давность последней активности", "impact": -0.03 }
    ]
  },
  "radar": {
    "Инициативность": 4,
    "Устойчивость": 3,
    "Академические": 5,
    "Лидерство": 3,
    "Разнообразие": 4
  },
  "flags": { ... },
  "trajectory": [ ... ]
}
```

---

### 6. `GET /api/candidates/ranking/` — Ранжирование

**Что делает:** Возвращает всех оценённых кандидатов, отсортированных по shortlist probability.

---

## 10. Как связать ML-пайплайн с Django (Практика из кода)

Вместо теории давайте проследим связь **Фронтенд → Django → ML pipeline** прямо по реальному коду на примере нажатия кнопки "Оценить кандидата".

### Шаг 1: Фронтенд (JavaScript) просит оценить кандидата
На фронтенде в файле `backend/frontend/templates/frontend/candidate_detail.html` есть кнопка и функция `runScore()`. По клику интерфейс вызывает API:

```javascript
// JS код в браузере (frontend/templates/frontend/candidate_detail.html)
async function runScore() {
    // 1. Делаем HTTP POST-запрос к API Django, передаём только ID кандидата
    // Примерно так: POST /api/candidates/5/score/
    await api(`/api/candidates/${CANDIDATE_ID}/score/`, { method: 'POST' });
    
    // 2. После успешного ответа просто перезапрашиваем страницу, чтобы нарисовать радар
    loadCandidate(); 
}
```
**Суть:** Фронтенд ничего не знает про ML. Он просто дергает URL `.../score/`.

### Шаг 2: Django ловит URL и вызывает функцию `candidate_score`
В файле `backend/candidates/urls.py` прописан маршрут: `path('<int:pk>/score/', views.candidate_score)`. 
Запрос попадает в контроллер (`backend/candidates/views.py`):

```python
# Django (backend/candidates/views.py)
from .models import Candidate, ScoringResult
from .ml_service import score_candidate # Наш мост к ML

@api_view(['POST'])
def candidate_score(request, pk):
    # 1. Django находит кандидата в базе SQLite
    candidate = Candidate.objects.get(pk=pk)
    
    # 2. ПОДГОТОВКА ДАННЫХ ДЛЯ ML
    # Метод to_pipeline_dict() берёт данные из таблицы БД и переводит их 
    # в простой Python-словарь (JSON), который понимает ML-модель.
    candidate_dict = candidate.to_pipeline_dict()
    
    # 3. ВЫЗОВ ML-ПАЙПЛАЙНА
    # Передаём словарь в функцию score_candidate и ждём ответ
    result = score_candidate(candidate_dict)
```

### Шаг 3: Мост между Django и ML (ml_service.py)
Функция `score_candidate` находится в специальном слое-обёртке (`backend/candidates/ml_service.py`). Эта обёртка нужна для того, чтобы модель XGBoost загружалась в память только ОДИН раз при запуске сервера, а не скачивалась каждый раз при клике.

```python
# Физический мост (backend/candidates/ml_service.py)
import sys
# Добавляем папку pipeline в пути питона, чтобы можно было импортировать scorer
sys.path.insert(0, settings.ML_PIPELINE_DIR) 
from scorer import CandidateScorer

def score_candidate(candidate_dict):
    """Обертка над тяжёлой ML-моделью."""
    
    # Получаем уже загруженную в оперативную память модель (singleton)
    scorer = get_scorer() 
    
    # Запускаем чистый Data Science код (scorer.py)
    # ML извлекает 23 фичи, считает SHAP, делает prediction
    return scorer.score(candidate_dict)
```
**Что возвращает ML (`result`):**
Словарь вида `{"prediction": "shortlist", "confidence": 0.85, "radar": {"Лидерство": 5...}, ...}`

### Шаг 4: Сохранение результатов и ответ Фронтенду
Мы возвращаемся обратно во `views.py`. ML-модель отдала цифры, теперь Django должен их запомнить (сохранить в БД) и отдать ответ браузеру:

```python
# Возвращаемся в Django (backend/candidates/views.py)

    # 4. СОХРАНЕНИЕ В БАЗУ ДАННЫХ
    # Мы сохраняем результаты ML в специальную таблицу ScoringResult
    ScoringResult.objects.update_or_create(
        candidate=candidate,
        defaults={
            'prediction': result['prediction'],          # "shortlist"
            'confidence': result['confidence'],          # 0.87
            'probabilities': result.get('probabilities', {}), 
            'full_result': result,                       # Весь JSON с радаром и объяснениями
        },
    )
    
    # 5. ОТВЕТ БРАУЗЕРУ
    # Возвращаем эти же данные на фронтенд
    return Response(result)
```

### Шаг 5: Фронтенд отрисовывает радар
JavaScript во фронтенде (из Шага 1) видит, что ответ пришёл без ошибок. Вызывается функция `loadCandidate()`, она забирает новые данные и передает графики на отрисовку:
```javascript
// JS код отрисовки (frontend/templates/frontend/candidate_detail.html)
if (scoring && scoring.full_result && scoring.full_result.radar) {
    drawRadar(scoring.full_result.radar); // Рисует канвас по данным радара от ML
}
```

**Вот и всё!** Django выступает "дирижёром": он забирает данные из базы → переводит их в словарь для ML → вызывает ML → берёт ответ ML → пишет его в базу → отправляет на фронт.

---

## 11. Пошаговый план создания проекта

### Фаза 1: Подготовка (1-2 дня)
```bash
# 1. Обучить модель (если ещё не обучена)
cd Indrive-AI
pip install -r requirements.txt
cd pipeline
python run_pipeline.py --dataset ../data/synthetic_dataset.json
# → создаст models/model.pkl

# 2. Создать Django проект
cd ../..
pip install django djangorestframework django-cors-headers
django-admin startproject invision_backend
cd invision_backend
python manage.py startapp candidates
```

### Фаза 2: Бэкенд (3-5 дней)
1. Настроить `settings.py`: добавить `rest_framework`, `corsheaders`, `candidates`
2. Создать модели в `candidates/models.py`
3. Создать сериализаторы в `candidates/serializers.py`
4. Создать вьюшки в `candidates/views.py`
5. Настроить URL-маршруты
6. Создать `ml_service.py` — обёртку над `scorer.py`
7. `python manage.py makemigrations && python manage.py migrate`

### Фаза 3: Фронтенд (3-5 дней)
1. Создать проект (React/Vue/простой HTML)
2. Страница регистрации кандидата (форма → `POST /api/candidates/register/`)
3. Страница списка кандидатов (таблица → `GET /api/candidates/`)
4. Поиск (строка поиска → `GET /api/candidates/search/`)
5. Карточка кандидата (детали + radar chart + timeline)

### Фаза 4: Интеграция (1-2 дня)
1. Настроить CORS для фронтенда
2. Тестирование всех эндпоинтов
3. Деплой (Railway / Heroku / VPS)

---

## Важные заметки

1. **Модель нужно обучить заранее** — файл `models/model.pkl` должен существовать до запуска API
2. **scorer.py — единственная точка входа** для фронтенда. Не нужно вызывать trainer/evaluator из API
3. **Демографические данные НЕ используются в скоринге** — это принципиальное дизайн-решение
4. **SHAP-объяснения** делают систему прозрачной: комиссия видит, ПОЧЕМУ модель приняла решение
5. **Radar chart** (5 осей) предназначен для визуализации на фронтенде
6. **Flags** — предупреждения для комиссии, которые нужно отображать на карточке кандидата
