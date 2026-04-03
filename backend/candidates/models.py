"""
models.py — Модели базы данных.

Что здесь:
  - Candidate — старая модель для ML pipeline (не трогаем)
  - ScoringResult — результат ML оценки (не трогаем)
  - Application — НОВАЯ модель для заявок пользователей
  - MBTITestResult — результаты MBTI теста
  - LanguageTestResult — результаты языкового теста (с таймером и violation_count)

Все модели используют Django ORM → полная защита от SQL-инъекций.
Пароли хранятся как bcrypt-хеши (не в этих моделях, а в settings).
"""

from django.db import models
import uuid


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Существующие модели (для ML pipeline — НЕ трогаем)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Candidate(models.Model):
    """Candidate profile for InVision U (ML pipeline)."""

    name = models.CharField('ФИО', max_length=200)
    age = models.IntegerField('Возраст')
    city = models.CharField('Город', max_length=100, blank=True, default='')
    region = models.CharField('Регион', max_length=100, blank=True, default='')
    school_type = models.CharField('Тип школы', max_length=50, blank=True, default='')
    has_mentor = models.BooleanField('Есть ментор', default=False)

    # Full candidate data as JSON (education, experience, essay, etc.)
    profile_data = models.JSONField('Полные данные профиля')

    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Кандидат'
        verbose_name_plural = 'Кандидаты'

    def __str__(self):
        return f"{self.name} ({self.city})"

    def to_pipeline_dict(self):
        """Convert to the dict format expected by pipeline/scorer.py

        Origin pipeline expects:
          - candidate["essay"]         → string or {"text": str} for NLP
          - candidate["bot_metadata"]  → dict for SLPI radar (optional)
          - candidate["personal"]      → personal info
          - candidate["education"]     → education data
          - candidate["experience"]    → experience data
        """
        data = self.profile_data.copy()
        data['id'] = str(self.id)
        data['personal'] = {
            'name': self.name,
            'age': self.age,
            'city': self.city,
            'region': self.region,
            'school_type': self.school_type,
            'has_mentor': self.has_mentor,
        }
        if 'personal' in self.profile_data and 'languages' in self.profile_data['personal']:
            data['personal']['languages'] = self.profile_data['personal']['languages']

        # Ensure essay is available for NLP module (origin scorer reads candidate["essay"])
        if 'essay' not in data:
            data['essay'] = ''

        # Ensure bot_metadata exists for SLPI radar (graceful fallback to "pending")
        if 'bot_metadata' not in data:
            data['bot_metadata'] = {}

        return data


class ScoringResult(models.Model):
    """ML scoring result for a candidate."""

    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name='scoring',
        verbose_name='Кандидат',
    )
    prediction = models.CharField('Рекомендация', max_length=20)
    confidence = models.FloatField('Уверенность')
    probabilities = models.JSONField('Вероятности')
    full_result = models.JSONField('Полный результат')
    scored_at = models.DateTimeField('Дата оценки', auto_now=True)

    class Meta:
        verbose_name = 'Результат оценки'
        verbose_name_plural = 'Результаты оценки'

    def __str__(self):
        return f"{self.candidate.name}: {self.prediction} ({self.confidence:.0%})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# НОВЫЕ модели — заявки и тесты
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Application(models.Model):
    """
    Заявка пользователя.

    Поля:
      - name: ФИО
      - city: город из dropdown (валидируется по kz_regions.CITY_REGION_MAP)
      - region: регион (должен соответствовать городу)
      - languages: JSON массив выбранных языков ["Казахский", "Русский"]
      - telegram_username: @username в Telegram
      - hobbies: хобби (свободный текст)
      - sport: вид спорта (пока без логики оценки)
      - status: статус заявки
    """

    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_review', 'На рассмотрении'),
        ('accepted', 'Принята'),
        ('rejected', 'Отклонена'),
    ]

    name = models.CharField(
        'ФИО',
        max_length=200,
        help_text='Полное имя заявителя',
    )
    city = models.CharField(
        'Город',
        max_length=100,
        help_text='Город из списка городов Казахстана',
    )
    region = models.CharField(
        'Регион',
        max_length=100,
        help_text='Регион — определяется автоматически по городу',
    )
    languages = models.JSONField(
        'Языки',
        default=list,
        help_text='Массив языков: ["Казахский", "Русский", "Английский"]',
    )
    telegram_username = models.CharField(
        'Telegram',
        max_length=100,
        help_text='Username в Telegram, например @ivanov',
    )
    hobbies = models.TextField(
        'Хобби',
        blank=True,
        default='',
        help_text='Хобби и увлечения (свободный текст)',
    )
    essay = models.TextField(
        'Эссе',
        blank=True,
        default='',
        help_text='Эссе кандидата',
    )
    motivation_letter = models.TextField(
        'Мотивационное письмо',
        blank=True,
        default='',
        help_text='Почему кандидат хочет учиться у нас',
    )
    sport = models.CharField(
        'Спорт',
        max_length=200,
        blank=True,
        default='',
        help_text='Вид спорта (пока без логики оценки)',
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
    )

    created_at = models.DateTimeField('Дата подачи', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f"#{self.pk} {self.name} — {self.city}"


class MBTITestResult(models.Model):
    """
    Результат MBTI теста.

    Как работает MBTI:
      40 вопросов → 4 шкалы → итоговый тип (INTJ, ENFP и т.д.)
      Шкалы: E/I, S/N, T/F, J/P

    Хранение:
      - answers: JSON словарь {"q1": "A", "q2": "B", ..., "q40": "A"}
      - result_type: итоговый 4-буквенный тип (рассчитывается при сохранении)
    """

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='mbti_result',
        verbose_name='Заявка',
    )
    answers = models.JSONField(
        'Ответы',
        help_text='{"q1": "A", "q2": "B", ...} — A или B для каждого вопроса',
    )
    result_type = models.CharField(
        'Тип MBTI',
        max_length=4,
        blank=True,
        default='',
        help_text='Например: INTJ, ENFP, ISTP',
    )

    created_at = models.DateTimeField('Дата прохождения', auto_now_add=True)

    class Meta:
        verbose_name = 'Результат MBTI'
        verbose_name_plural = 'Результаты MBTI'

    def __str__(self):
        return f"MBTI: {self.application.name} → {self.result_type or '?'}"


class LanguageTestResult(models.Model):
    """
    Результат языкового теста.

    Особенности:
      - Таймер на фронте → time_spent_seconds сохраняется on submit
      - violation_count: сколько раз пользователь пытался выйти из вкладки
        (document.visibilitychange event на фронте)
      - score: количество правильных ответов
    """

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='language_tests',
        verbose_name='Заявка',
    )
    language = models.CharField(
        'Тестируемый язык',
        max_length=50,
        help_text='Например: Английский, Казахский',
    )
    answers = models.JSONField(
        'Ответы',
        help_text='{"q1": "A", "q2": "C", ...}',
    )
    score = models.IntegerField(
        'Баллы',
        default=0,
        help_text='Количество правильных ответов',
    )
    max_score = models.IntegerField(
        'Максимум баллов',
        default=0,
        help_text='Общее количество вопросов',
    )
    time_spent_seconds = models.IntegerField(
        'Время (сек)',
        default=0,
        help_text='Сколько секунд потратил на тест',
    )
    violation_count = models.IntegerField(
        'Нарушения',
        default=0,
        help_text='Сколько раз пытался уйти из вкладки',
    )

    created_at = models.DateTimeField('Дата прохождения', auto_now_add=True)

    class Meta:
        verbose_name = 'Результат языкового теста'
        verbose_name_plural = 'Результаты языковых тестов'

    def __str__(self):
        violations = f" ⚠{self.violation_count}" if self.violation_count else ""
        return f"{self.application.name} — {self.language}: {self.score}/{self.max_score}{violations}"
