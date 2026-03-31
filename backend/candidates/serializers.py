from rest_framework import serializers
from .models import Candidate, ScoringResult


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
