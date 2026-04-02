"""
language_questions.py — Вопросы языкового теста.

Правильные ответы хранятся ТОЛЬКО здесь, на бэкенде.
Фронт получает вопросы через GET /api/tests/language/questions/
БЕЗ поля correct — чтобы пользователь не мог подсмотреть ответы.

Как добавить/изменить вопрос:
  1. Измени/добавь объект в LANGUAGE_QUESTIONS ниже
  2. Перезапусти бэкенд
  3. Фронт подгрузит новые вопросы автоматически

Формат:
  key     — уникальный ID (q1, q2, ...)
  text    — текст вопроса
  options — 4 варианта ответа (A, B, C, D по порядку)
  correct — правильный ответ ('A', 'B', 'C' или 'D')
"""

LANGUAGE_QUESTIONS = [
    {
        'key': 'q1',
        'text': 'Choose the correct sentence:',
        'options': [
            'She go to school every day.',
            'She goes to school every day.',
            'She going to school every day.',
            'She are go to school every day.',
        ],
        'correct': 'B',
    },
    {
        'key': 'q2',
        'text': 'What is the past tense of "buy"?',
        'options': ['buyed', 'bought', 'buied', 'boughted'],
        'correct': 'B',
    },
    {
        'key': 'q3',
        'text': '"I ___ to the cinema yesterday."',
        'options': ['go', 'goes', 'went', 'gone'],
        'correct': 'C',
    },
    {
        'key': 'q4',
        'text': 'Choose the synonym for "happy":',
        'options': ['sad', 'joyful', 'angry', 'tired'],
        'correct': 'B',
    },
    {
        'key': 'q5',
        'text': '"She has been studying ___ 3 hours."',
        'options': ['since', 'for', 'during', 'while'],
        'correct': 'B',
    },
    {
        'key': 'q6',
        'text': 'Which sentence is correct?',
        'options': [
            'I have went there.',
            'I have gone there.',
            'I has gone there.',
            'I have go there.',
        ],
        'correct': 'B',
    },
    {
        'key': 'q7',
        'text': '"If I ___ rich, I would travel the world."',
        'options': ['am', 'was', 'were', 'be'],
        'correct': 'C',
    },
    {
        'key': 'q8',
        'text': 'Choose the antonym of "ancient":',
        'options': ['old', 'modern', 'historic', 'traditional'],
        'correct': 'B',
    },
    {
        'key': 'q9',
        'text': '"By the time she arrived, the movie ___."',
        'options': ['started', 'has started', 'had started', 'was starting'],
        'correct': 'C',
    },
    {
        'key': 'q10',
        'text': '"I wish I ___ more time to study."',
        'options': ['have', 'has', 'had', 'having'],
        'correct': 'C',
    },
    {
        'key': 'q11',
        'text': 'Choose the correct word: "He speaks English ___."',
        'options': ['fluent', 'fluently', 'fluence', 'fluid'],
        'correct': 'B',
    },
    {
        'key': 'q12',
        'text': '"The book ___ by many students."',
        'options': ['is reading', 'is read', 'are read', 'reads'],
        'correct': 'B',
    },
    {
        'key': 'q13',
        'text': '"She asked me where I ___."',
        'options': ['live', 'lived', 'living', 'lives'],
        'correct': 'B',
    },
    {
        'key': 'q14',
        'text': 'Choose the correct form: "___ you ever been to London?"',
        'options': ['Do', 'Did', 'Have', 'Are'],
        'correct': 'C',
    },
    {
        'key': 'q15',
        'text': '"I\'m looking forward ___ you again."',
        'options': ['to see', 'to seeing', 'seeing', 'see'],
        'correct': 'B',
    },
    {
        'key': 'q16',
        'text': '"He ___ have left already; the office is empty."',
        'options': ['must', 'can', 'should', 'would'],
        'correct': 'A',
    },
    {
        'key': 'q17',
        'text': '"Despite ___ tired, she continued working."',
        'options': ['be', 'being', 'been', 'was'],
        'correct': 'B',
    },
    {
        'key': 'q18',
        'text': '"The more you practice, the ___ you get."',
        'options': ['good', 'better', 'best', 'well'],
        'correct': 'B',
    },
    {
        'key': 'q19',
        'text': '"I\'d rather you ___ to the meeting tomorrow."',
        'options': ['come', 'came', 'coming', 'will come'],
        'correct': 'B',
    },
    {
        'key': 'q20',
        'text': '"Not until the rain stopped ___ go outside."',
        'options': ['we could', 'could we', 'we can', 'can we'],
        'correct': 'B',
    },
]


def get_questions_for_client():
    """
    Возвращает вопросы БЕЗ правильных ответов — для отправки на фронт.
    """
    return [
        {
            'key': q['key'],
            'text': q['text'],
            'options': q['options'],
        }
        for q in LANGUAGE_QUESTIONS
    ]


def calculate_score(answers: dict) -> dict:
    """
    Проверяет ответы пользователя и считает балл.

    Args:
        answers: dict вида {"q1": "B", "q2": "A", ...}

    Returns:
        dict с score и max_score
    """
    score = 0
    for q in LANGUAGE_QUESTIONS:
        if answers.get(q['key']) == q['correct']:
            score += 1

    return {
        'score': score,
        'max_score': len(LANGUAGE_QUESTIONS),
    }
