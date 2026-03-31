from django.db import models
import uuid


class Candidate(models.Model):
    """Candidate profile for InVision U."""
    
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
        """Convert to the dict format expected by pipeline/scorer.py"""
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
        # Preserve languages if present
        if 'personal' in self.profile_data and 'languages' in self.profile_data['personal']:
            data['personal']['languages'] = self.profile_data['personal']['languages']
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
