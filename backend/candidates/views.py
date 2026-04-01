"""
views.py — API endpoints.

Как это работает (простым языком):
  View (вью) — это функция, которая:
    1. Получает HTTP запрос от клиента (фронтенда)
    2. Делает что-то с данными (создаёт, читает, обновляет, удаляет)
    3. Возвращает ответ в формате JSON

  Декоратор @api_view(['GET', 'POST']) говорит Django:
    «Эта функция принимает GET или POST запросы».

  Все данные валидируются через сериалайзеры ПЕРЕД попаданием в БД.
  Django ORM автоматически экранирует SQL → защита от инъекций.

Группы endpoints:
  1. /api/applications/ — CRUD заявок
  2. /api/cities/ — справочник городов/регионов
  3. /api/admin/ — авторизация админа
  4. /api/tests/ — MBTI и языковые тесты
  5. /api/candidates/ — старые ML endpoints (сохранены)
"""

import logging
import bcrypt

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.conf import settings

from .models import (
    Candidate, ScoringResult,
    Application, MBTITestResult, LanguageTestResult,
)
from .serializers import (
    CandidateListSerializer,
    CandidateDetailSerializer,
    CandidateRegisterSerializer,
    ApplicationSerializer,
    ApplicationListSerializer,
    MBTITestSerializer,
    LanguageTestSerializer,
    AdminLoginSerializer,
)
from .ml_service import score_candidate, rank_candidates
from .telegram_service import notify_new_application
from .kz_regions import (
    get_all_cities, get_regions_for_city, get_all_regions,
    LANGUAGES_CHOICES,
)


# Логгеры
logger = logging.getLogger('candidates')
app_logger = logging.getLogger('candidates.applications')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ЗАЯВКИ — CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['GET', 'POST'])
def application_list_create(request):
    """
    GET  /api/applications/ — список всех заявок (с фильтрами и пагинацией)
    POST /api/applications/ — создать новую заявку

    Фильтры (query params):
      ?city=Алматы — по городу
      ?language=Казахский — по языку
      ?status=new — по статусу
      ?search=Иванов — поиск по имени
    """
    if request.method == 'POST':
        serializer = ApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        app_logger.info(
            f"Новая заявка #{application.pk}: {application.name} "
            f"из {application.city}, языки: {application.languages}"
        )

        # Telegram уведомление
        try:
            notify_new_application(application)
        except Exception as e:
            logger.error(f"Ошибка Telegram: {e}")

        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )

    # GET: список с фильтрацией
    queryset = Application.objects.all()

    # Фильтр по городу
    city = request.query_params.get('city')
    if city:
        queryset = queryset.filter(city__icontains=city)

    # Фильтр по языку (ищем в JSON массиве)
    language = request.query_params.get('language')
    if language:
        queryset = queryset.filter(languages__contains=[language])

    # Фильтр по статусу
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Фильтр по наличию MBTI результата
    mbti = request.query_params.get('mbti')
    if mbti:
        queryset = queryset.filter(mbti_result__result_type=mbti)

    # Текстовый поиск
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(telegram_username__icontains=search)
        )

    # Пагинация
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = ApplicationListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PUT', 'DELETE'])
def application_detail(request, pk):
    """
    GET    /api/applications/<id>/ — детали заявки
    PUT    /api/applications/<id>/ — обновить заявку
    DELETE /api/applications/<id>/ — удалить заявку
    """
    try:
        application = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        return Response(
            {'error': f'Заявка #{pk} не найдена'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = ApplicationSerializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        app_logger.info(f"Заявка #{pk} обновлена")
        return Response(serializer.data)

    if request.method == 'DELETE':
        app_logger.info(f"Заявка #{pk} удалена ({application.name})")
        application.delete()
        return Response(
            {'status': 'deleted', 'id': pk},
            status=status.HTTP_204_NO_CONTENT,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ГОРОДА И РЕГИОНЫ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['GET'])
def city_list(request):
    """
    GET /api/cities/ — список всех городов Казахстана.
    Фронт использует это для dropdown.
    """
    return Response({
        'cities': get_all_cities(),
        'languages': LANGUAGES_CHOICES,
    })


@api_view(['GET'])
def city_regions(request, city):
    """
    GET /api/cities/<city>/regions/ — регион для указанного города.
    Пример: GET /api/cities/Алматы/regions/ → {"region": "город Алматы"}
    """
    region = get_regions_for_city(city)
    if region is None:
        return Response(
            {'error': f"Город '{city}' не найден"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response({'city': city, 'region': region})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ТЕСТЫ — MBTI и Язык
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['POST'])
def mbti_test_submit(request):
    """
    POST /api/tests/mbti/ — отправить результаты MBTI теста.

    JSON:
    {
        "application_id": 1,
        "answers": {"q1": "A", "q2": "B", ..., "q40": "A"}
    }

    Возвращает рассчитанный тип (INTJ, ENFP и т.д.)
    """
    serializer = MBTITestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    result = serializer.save()

    app_logger.info(
        f"MBTI тест для заявки #{result.application.pk}: {result.result_type}"
    )

    return Response(
        MBTITestSerializer(result).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
def language_test_submit(request):
    """
    POST /api/tests/language/ — отправить результаты языкового теста.

    JSON:
    {
        "application_id": 1,
        "language": "Английский",
        "answers": {"q1": "B", "q2": "A"},
        "score": 15,
        "max_score": 20,
        "time_spent_seconds": 540,
        "violation_count": 2
    }

    violation_count — количество раз когда пользователь
    ушёл из вкладки (document.visibilitychange event).
    """
    serializer = LanguageTestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    result = serializer.save()

    warning = ""
    if result.violation_count > 0:
        warning = f" ⚠ нарушений: {result.violation_count}"

    app_logger.info(
        f"Языковой тест ({result.language}) для заявки #{result.application.pk}: "
        f"{result.score}/{result.max_score}, "
        f"время: {result.time_spent_seconds}с{warning}"
    )

    return Response(
        LanguageTestSerializer(result).data,
        status=status.HTTP_201_CREATED,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# АДМИН АВТОРИЗАЦИЯ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['POST'])
def admin_login(request):
    """
    POST /api/admin/login/ — авторизация админа.

    JSON: {"username": "era", "password": "admin1"}

    Как работает:
      1. Проверяем username == settings.PANEL_USERNAME
      2. Проверяем password через bcrypt.checkpw() vs settings.PANEL_PASSWORD_HASH
      3. Если правильно → сохраняем сессию

    Пароль НИКОГДА не хранится в открытом виде.
    Хеш генерируется командой:
      python -c "import bcrypt; print(bcrypt.hashpw(b'admin1', bcrypt.gensalt()).decode())"
    """
    serializer = AdminLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    expected_user = settings.PANEL_USERNAME
    password_hash = settings.PANEL_PASSWORD_HASH

    # Проверка username
    if username != expected_user:
        logger.warning(f"Неудачная попытка входа: username={username}")
        return Response(
            {'success': False, 'error': 'Неверный логин или пароль'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Проверка пароля через bcrypt
    if not password_hash:
        logger.error("PANEL_PASSWORD_HASH не настроен в .env!")
        return Response(
            {'success': False, 'error': 'Сервер не настроен'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        password_valid = bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8'),
        )
    except Exception as e:
        logger.error(f"Ошибка проверки пароля: {e}")
        return Response(
            {'success': False, 'error': 'Ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not password_valid:
        logger.warning(f"Неверный пароль для пользователя {username}")
        return Response(
            {'success': False, 'error': 'Неверный логин или пароль'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Успех — сохраняем в сессию
    request.session['panel_auth'] = True
    logger.info(f"Успешный вход в админку: {username}")
    return Response({'success': True})


@api_view(['GET'])
def admin_applications(request):
    """
    GET /api/admin/applications/ — список заявок для админа.

    Доступ только с активной сессией (panel_auth=True).

    Фильтры:
      ?city=Алматы
      ?language=Казахский
      ?mbti=INTJ
      ?status=new
    """
    if not request.session.get('panel_auth'):
        return Response(
            {'error': 'Не авторизован'},
            status=status.HTTP_403_FORBIDDEN,
        )

    queryset = Application.objects.prefetch_related(
        'mbti_result', 'language_tests'
    ).all()

    # Фильтры
    city = request.query_params.get('city')
    if city:
        queryset = queryset.filter(city__icontains=city)

    language = request.query_params.get('language')
    if language:
        queryset = queryset.filter(languages__contains=[language])

    mbti = request.query_params.get('mbti')
    if mbti:
        queryset = queryset.filter(mbti_result__result_type=mbti)

    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Пагинация
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = ApplicationSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# СТАРЫЕ ENDPOINTS — ML pipeline (сохранены)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

    prediction = request.query_params.get('prediction')
    if prediction:
        queryset = queryset.filter(scoring__prediction=prediction)

    city = request.query_params.get('city')
    if city:
        queryset = queryset.filter(city__icontains=city)

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

    paginator = PageNumberPagination()
    page_size = request.query_params.get('page_size')
    if page_size:
        paginator.page_size = int(page_size)
    page = paginator.paginate_queryset(queryset, request)
    serializer = CandidateListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


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


@api_view(['GET'])
def candidate_ranking(request):
    """Get all scored candidates ranked by shortlist probability."""
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
