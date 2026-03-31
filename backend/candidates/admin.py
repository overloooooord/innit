from django.contrib import admin
from .models import Candidate, ScoringResult


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
