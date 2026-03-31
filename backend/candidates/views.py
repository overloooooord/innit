from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from .models import Candidate, ScoringResult
from .serializers import (
    CandidateListSerializer,
    CandidateDetailSerializer,
    CandidateRegisterSerializer,
)
from .ml_service import score_candidate, rank_candidates


# ============================================================
# 1. POST /api/candidates/ — Register
# ============================================================

@api_view(['GET', 'POST'])
def candidate_list_create(request):
    """
    GET:  List all candidates with sorting, filtering, pagination.
    POST: Register a new candidate.
    """
    if request.method == 'POST':
        serializer = CandidateRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate = serializer.save()
        return Response(
            {
                'id': candidate.id,
                'status': 'registered',
                'message': f'Кандидат {candidate.name} успешно зарегистрирован',
            },
            status=status.HTTP_201_CREATED,
        )
    
    # GET: List with sorting and filtering
    queryset = Candidate.objects.select_related('scoring').all()
    
    # Filter by prediction
    prediction = request.query_params.get('prediction')
    if prediction:
        queryset = queryset.filter(scoring__prediction=prediction)
    
    # Filter by city
    city = request.query_params.get('city')
    if city:
        queryset = queryset.filter(city__icontains=city)
    
    # Sorting
    sort_by = request.query_params.get('sort_by', 'created_at')
    order = request.query_params.get('order', 'desc')
    
    sort_map = {
        'name': 'name',
        'age': 'age',
        'city': 'city',
        'created_at': 'created_at',
        'confidence': 'scoring__confidence',
        'prediction': 'scoring__prediction',
    }
    
    sort_field = sort_map.get(sort_by, 'created_at')
    if order == 'desc':
        sort_field = f'-{sort_field}'
    
    queryset = queryset.order_by(sort_field)
    
    # Pagination
    paginator = PageNumberPagination()
    page_size = request.query_params.get('page_size')
    if page_size:
        paginator.page_size = int(page_size)
    page = paginator.paginate_queryset(queryset, request)
    serializer = CandidateListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ============================================================
# 2. GET /api/candidates/<id>/ — Detail
# ============================================================

@api_view(['GET'])
def candidate_detail(request, pk):
    """Get full details of a candidate including scoring result."""
    try:
        candidate = Candidate.objects.select_related('scoring').get(pk=pk)
    except Candidate.DoesNotExist:
        return Response(
            {'error': 'Кандидат не найден'},
            status=status.HTTP_404_NOT_FOUND,
        )
    
    serializer = CandidateDetailSerializer(candidate)
    return Response(serializer.data)


# ============================================================
# 3. GET /api/candidates/search/?q= — Search
# ============================================================

@api_view(['GET'])
def candidate_search(request):
    """Search candidates by name, city, or region."""
    q = request.query_params.get('q', '').strip()
    if not q:
        return Response({'results': []})
    
    queryset = Candidate.objects.select_related('scoring').filter(
        Q(name__icontains=q) |
        Q(city__icontains=q) |
        Q(region__icontains=q)
    )[:20]
    
    serializer = CandidateListSerializer(queryset, many=True)
    return Response({'results': serializer.data})


# ============================================================
# 4. POST /api/candidates/<id>/score/ — Run ML scoring
# ============================================================

@api_view(['POST'])
def candidate_score(request, pk):
    """Run ML scoring for a candidate."""
    try:
        candidate = Candidate.objects.get(pk=pk)
    except Candidate.DoesNotExist:
        return Response(
            {'error': 'Кандидат не найден'},
            status=status.HTTP_404_NOT_FOUND,
        )
    
    try:
        candidate_dict = candidate.to_pipeline_dict()
        result = score_candidate(candidate_dict)
        
        # Save scoring result
        ScoringResult.objects.update_or_create(
            candidate=candidate,
            defaults={
                'prediction': result['prediction'],
                'confidence': result['confidence'],
                'probabilities': result.get('probabilities', {}),
                'full_result': result,
            },
        )
        
        return Response(result)
    
    except FileNotFoundError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except Exception as e:
        return Response(
            {'error': f'Ошибка скоринга: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================
# 5. GET /api/candidates/ranking/ — Ranking
# ============================================================

@api_view(['GET'])
def candidate_ranking(request):
    """
    Get all scored candidates ranked by shortlist probability.
    """
    scored = ScoringResult.objects.select_related('candidate').all()
    
    results = []
    for sr in scored:
        shortlist_prob = sr.probabilities.get('shortlist', 0)
        results.append({
            'id': sr.candidate.id,
            'name': sr.candidate.name,
            'city': sr.candidate.city,
            'prediction': sr.prediction,
            'confidence': sr.confidence,
            'shortlist_probability': shortlist_prob,
        })
    
    results.sort(key=lambda x: x['shortlist_probability'], reverse=True)
    
    for i, r in enumerate(results):
        r['rank'] = i + 1
        r['total_candidates'] = len(results)
    
    return Response({'results': results})


# ============================================================
# 6. POST /api/candidates/score-all/ — Score all unscored
# ============================================================

@api_view(['POST'])
def score_all(request):
    """Score all candidates that haven't been scored yet."""
    unscored = Candidate.objects.filter(scoring__isnull=True)
    count = unscored.count()
    
    if count == 0:
        return Response({'message': 'Все кандидаты уже оценены', 'scored': 0})
    
    try:
        scored_count = 0
        for candidate in unscored:
            candidate_dict = candidate.to_pipeline_dict()
            result = score_candidate(candidate_dict)
            
            ScoringResult.objects.update_or_create(
                candidate=candidate,
                defaults={
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'probabilities': result.get('probabilities', {}),
                    'full_result': result,
                },
            )
            scored_count += 1
        
        return Response({
            'message': f'Оценено {scored_count} кандидатов',
            'scored': scored_count,
        })
    
    except Exception as e:
        return Response(
            {'error': f'Ошибка: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
