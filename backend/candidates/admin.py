"""
admin.py — Настройка Django Admin.

Как это работает:
  Django Admin — это встроенная панель управления.
  Она доступна по /admin/ и позволяет просматривать/редактировать данные в БД.

  Мы регистрируем здесь все модели чтобы админ мог:
    - Просматривать заявки, кандидатов, результаты тестов
    - Фильтровать по городу, языку, статусу
    - Искать по имени
"""

from django.contrib import admin
from .models import (
    Candidate, ScoringResult,
    Application, MBTITestResult, LanguageTestResult,
)


# ── Старые модели (ML pipeline) ─────────────────────────────

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'city', 'school_type', 'get_prediction', 'created_at')
    list_filter = ('city', 'school_type', 'has_mentor')
    search_fields = ('name', 'city', 'region')
    readonly_fields = ('created_at', 'updated_at')

    def get_prediction(self, obj):
        try:
            return obj.scoring.prediction
        except ScoringResult.DoesNotExist:
            return '—'
    get_prediction.short_description = 'Рекомендация'


@admin.register(ScoringResult)
class ScoringResultAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'prediction', 'confidence', 'scored_at')
    list_filter = ('prediction',)


# ── Новые модели (заявки) ────────────────────────────────────

class MBTIInline(admin.StackedInline):
    """Показать MBTI результат прямо на странице заявки."""
    model = MBTITestResult
    extra = 0
    readonly_fields = ('result_type', 'answers', 'created_at')


class LanguageTestInline(admin.TabularInline):
    """Показать языковые тесты прямо на странице заявки."""
    model = LanguageTestResult
    extra = 0
    readonly_fields = ('language', 'score', 'max_score', 'time_spent_seconds', 'violation_count', 'created_at')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'city', 'region', 'get_languages',
        'telegram_username', 'sport', 'status', 'get_mbti', 'created_at',
    )
    list_filter = ('city', 'status', 'region')
    search_fields = ('name', 'telegram_username', 'city')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MBTIInline, LanguageTestInline]

    def get_languages(self, obj):
        """Показать языки через запятую."""
        if isinstance(obj.languages, list):
            return ', '.join(obj.languages)
        return str(obj.languages)
    get_languages.short_description = 'Языки'

    def get_mbti(self, obj):
        """Показать тип MBTI если есть."""
        try:
            return obj.mbti_result.result_type
        except MBTITestResult.DoesNotExist:
            return '—'
    get_mbti.short_description = 'MBTI'


@admin.register(MBTITestResult)
class MBTITestResultAdmin(admin.ModelAdmin):
    list_display = ('application', 'result_type', 'created_at')
    list_filter = ('result_type',)
    search_fields = ('application__name',)


@admin.register(LanguageTestResult)
class LanguageTestResultAdmin(admin.ModelAdmin):
    list_display = (
        'application', 'language', 'score', 'max_score',
        'time_spent_seconds', 'violation_count', 'created_at',
    )
    list_filter = ('language',)
    search_fields = ('application__name',)
