"""
serializers.py — Сериалайзеры для валидации входных данных.

Как это работает (простым языком):
  Сериалайзер — это «фильтр» между клиентом и базой данных.
  Когда клиент отправляет JSON, сериалайзер:
    1. Проверяет что все обязательные поля есть
    2. Проверяет типы данных (строка, число, массив)
    3. Запускает кастомные валидации (город→регион)
    4. Только потом данные попадают в БД

  Это защита от SQL-инъекций на уровне данных:
  даже если кто-то отправит вредоносный SQL в поле "name",
  ORM экранирует все автоматически.
"""

from rest_framework import serializers
from .models import (
    Candidate, ScoringResult,
    Application, MBTITestResult, LanguageTestResult,
)
from .kz_regions import (
    CITY_REGION_MAP, LANGUAGES_CHOICES,
    validate_city_region, get_regions_for_city,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Существующие сериалайзеры (ML pipeline)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ScoringResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoringResult
        fields = ['prediction', 'confidence', 'probabilities', 'full_result', 'scored_at']


class CandidateListSerializer(serializers.ModelSerializer):
    """Compact serializer for list/search views."""
    prediction = serializers.SerializerMethodField()
    confidence = serializers.SerializerMethodField()
    gpa = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'age', 'city', 'region', 'school_type',
            'gpa', 'project_count', 'prediction', 'confidence', 'created_at',
        ]

    def get_prediction(self, obj):
        try:
            return obj.scoring.prediction
        except ScoringResult.DoesNotExist:
            return None

    def get_confidence(self, obj):
        try:
            return obj.scoring.confidence
        except ScoringResult.DoesNotExist:
            return None

    def get_gpa(self, obj):
        return obj.profile_data.get('education', {}).get('gpa', None)

    def get_project_count(self, obj):
        return len(obj.profile_data.get('experience', {}).get('projects', []))


class CandidateDetailSerializer(serializers.ModelSerializer):
    """Full serializer with scoring result."""
    scoring = ScoringResultSerializer(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'age', 'city', 'region', 'school_type',
            'has_mentor', 'profile_data', 'scoring', 'created_at',
        ]


class CandidateRegisterSerializer(serializers.Serializer):
    """Accepts the full candidate JSON (matching candidate_scheme.json)."""
    personal = serializers.DictField(required=True)
    education = serializers.DictField(required=True)
    experience = serializers.DictField(required=False, default=dict)
    essay = serializers.DictField(required=False, default=dict)
    motivation = serializers.DictField(required=False, default=dict)
    self_assessment = serializers.DictField(required=False, default=dict)
    bot_metadata = serializers.DictField(required=False, default=dict)

    def validate_personal(self, value):
        if 'name' not in value:
            raise serializers.ValidationError("Поле 'name' обязательно")
        if 'age' not in value:
            raise serializers.ValidationError("Поле 'age' обязательно")
        return value

    def create(self, validated_data):
        personal = validated_data['personal']
        candidate = Candidate.objects.create(
            name=personal.get('name', ''),
            age=personal.get('age', 0),
            city=personal.get('city', ''),
            region=personal.get('region', ''),
            school_type=personal.get('school_type', ''),
            has_mentor=personal.get('has_mentor', False),
            profile_data=validated_data,
        )
        return candidate


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. НОВЫЕ сериалайзеры — Заявки + Тесты
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ApplicationSerializer(serializers.ModelSerializer):
    """
    CRUD сериалайзер для заявок.

    Валидации:
      - city должен быть в списке городов Казахстана
      - region должен соответствовать выбранному городу
      - languages — массив из допустимых значений
      - telegram_username — не пустой
    """

    # Показываем результаты тестов при чтении (read_only)
    mbti_result = serializers.SerializerMethodField()
    language_tests = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'name', 'city', 'region', 'languages',
            'telegram_username', 'hobbies', 'sport', 'status',
            'created_at', 'updated_at',
            'mbti_result', 'language_tests',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def get_mbti_result(self, obj):
        """Получить MBTI результат если он есть."""
        try:
            mbti = obj.mbti_result
            return {
                'result_type': mbti.result_type,
                'answers': mbti.answers,
                'created_at': mbti.created_at,
            }
        except MBTITestResult.DoesNotExist:
            return None

    def get_language_tests(self, obj):
        """Получить все результаты языковых тестов."""
        tests = obj.language_tests.all()
        return [
            {
                'id': t.id,
                'language': t.language,
                'score': t.score,
                'max_score': t.max_score,
                'time_spent_seconds': t.time_spent_seconds,
                'violation_count': t.violation_count,
                'created_at': t.created_at,
            }
            for t in tests
        ]

    def validate_city(self, value):
        """Проверить что город есть в списке городов Казахстана."""
        value = value.strip()
        if value not in CITY_REGION_MAP:
            available = ', '.join(sorted(set(CITY_REGION_MAP.keys()))[:10])
            raise serializers.ValidationError(
                f"Город '{value}' не найден. Доступные: {available}..."
            )
        return value

    def validate_telegram_username(self, value):
        """Проверить формат Telegram username."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Telegram username обязателен")
        # Убрать @ если пользователь его добавил
        if value.startswith('@'):
            value = value[1:]
        # Проверить что содержит только допустимые символы
        if len(value) < 3:
            raise serializers.ValidationError("Username слишком короткий (мин. 3 символа)")
        return f"@{value}"

    def validate_languages(self, value):
        """Проверить что языки из допустимого списка."""
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError("Выберите хотя бы один язык")
        invalid = [lang for lang in value if lang not in LANGUAGES_CHOICES]
        if invalid:
            raise serializers.ValidationError(
                f"Недопустимые языки: {invalid}. Допустимые: {LANGUAGES_CHOICES}"
            )
        return value

    def validate(self, data):
        """
        Кросс-валидация: проверить что регион соответствует городу.
        Эта валидация запускается ПОСЛЕ индивидуальных validate_*
        """
        city = data.get('city', '')
        region = data.get('region', '')

        if city and region:
            if not validate_city_region(city, region):
                expected = get_regions_for_city(city)
                raise serializers.ValidationError({
                    'region': f"Регион '{region}' не соответствует городу '{city}'. "
                              f"Ожидается: '{expected}'"
                })

        return data


class ApplicationListSerializer(serializers.ModelSerializer):
    """Компактный сериалайзер для списка заявок (без тестов)."""

    class Meta:
        model = Application
        fields = [
            'id', 'name', 'city', 'region', 'languages',
            'telegram_username', 'sport', 'status', 'created_at',
        ]


class MBTITestSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для результатов MBTI теста.

    Ожидаемый JSON:
    {
        "application_id": 1,
        "answers": {"q1": "A", "q2": "B", ..., "q40": "A"}
    }
    """

    application_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MBTITestResult
        fields = ['id', 'application_id', 'answers', 'result_type', 'created_at']
        read_only_fields = ['id', 'result_type', 'created_at']

    def validate_answers(self, value):
        """Проверить что ответы содержат q1..q40 с значениями A или B."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Ответы должны быть словарём")

        expected_keys = {f"q{i}" for i in range(1, 41)}
        actual_keys = set(value.keys())

        missing = expected_keys - actual_keys
        if missing:
            raise serializers.ValidationError(
                f"Отсутствуют ответы на вопросы: {sorted(missing)}"
            )

        invalid_values = {k: v for k, v in value.items() if v not in ('A', 'B')}
        if invalid_values:
            raise serializers.ValidationError(
                f"Допустимые значения: A или B. Ошибки: {invalid_values}"
            )

        return value

    def validate_application_id(self, value):
        """Проверить что заявка существует."""
        if not Application.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"Заявка #{value} не найдена")
        return value

    def create(self, validated_data):
        application_id = validated_data.pop('application_id')
        application = Application.objects.get(pk=application_id)

        # Рассчитать тип MBTI из ответов
        result_type = self._calculate_mbti_type(validated_data['answers'])

        return MBTITestResult.objects.create(
            application=application,
            answers=validated_data['answers'],
            result_type=result_type,
        )

    @staticmethod
    def _calculate_mbti_type(answers: dict) -> str:
        """
        Рассчитать 4-буквенный тип MBTI.

        Распределение вопросов по шкалам:
          q1-q10  → E/I (Экстравертный / Интровертный)
          q11-q20 → S/N (Сенсорный / Интуитивный)
          q21-q30 → T/F (Думающий / Чувствующий)
          q31-q40 → J/P (Решающий / Воспринимающий)

        A = первая буква в паре (E, S, T, J)
        B = вторая буква в паре (I, N, F, P)
        """
        scales = [
            (range(1, 11), 'E', 'I'),
            (range(11, 21), 'S', 'N'),
            (range(21, 31), 'T', 'F'),
            (range(31, 41), 'J', 'P'),
        ]

        result = ''
        for q_range, letter_a, letter_b in scales:
            a_count = sum(1 for i in q_range if answers.get(f'q{i}') == 'A')
            b_count = len(q_range) - a_count
            result += letter_a if a_count >= b_count else letter_b

        return result


class LanguageTestSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для языкового теста.

    Ожидаемый JSON:
    {
        "application_id": 1,
        "language": "Английский",
        "answers": {"q1": "B", "q2": "A", ...},
        "score": 15,
        "max_score": 20,
        "time_spent_seconds": 540,
        "violation_count": 2
    }

    violation_count — фронт отслеживает document.visibilitychange
    и инкрементирует счётчик каждый раз когда пользователь уходит из вкладки.
    """

    application_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = LanguageTestResult
        fields = [
            'id', 'application_id', 'language', 'answers',
            'score', 'max_score', 'time_spent_seconds',
            'violation_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_application_id(self, value):
        if not Application.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"Заявка #{value} не найдена")
        return value

    def validate_violation_count(self, value):
        if value < 0:
            raise serializers.ValidationError("violation_count не может быть отрицательным")
        return value

    def validate_time_spent_seconds(self, value):
        if value < 0:
            raise serializers.ValidationError("Время не может быть отрицательным")
        return value

    def create(self, validated_data):
        application_id = validated_data.pop('application_id')
        application = Application.objects.get(pk=application_id)
        return LanguageTestResult.objects.create(
            application=application,
            **validated_data,
        )


class AdminLoginSerializer(serializers.Serializer):
    """
    Сериалайзер для авторизации админа.
    Просто валидирует что username и password не пустые.
    Проверка пароля через bcrypt — во view.
    """
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100)
