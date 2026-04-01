"""
urls.py — Маршруты API.

Как это работает (простым языком):
  URL (маршрут) — это адрес, по которому фронт обращается к серверу.
  path('applications/', views.application_list_create) означает:
    «Когда кто-то заходит на /api/applications/ — вызови функцию application_list_create»

  prefix /api/ добавляется в invision/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── Заявки (CRUD) ────────────────────────────────────────
    path('applications/', views.application_list_create, name='application-list-create'),
    path('applications/<int:pk>/', views.application_detail, name='application-detail'),

    # ── Справочник городов ───────────────────────────────────
    path('cities/', views.city_list, name='city-list'),
    path('cities/<str:city>/regions/', views.city_regions, name='city-regions'),

    # ── Тесты ────────────────────────────────────────────────
    path('tests/mbti/', views.mbti_test_submit, name='mbti-test-submit'),
    path('tests/language/', views.language_test_submit, name='language-test-submit'),

    # ── Админ ────────────────────────────────────────────────
    path('admin/login/', views.admin_login, name='admin-api-login'),
    path('admin/applications/', views.admin_applications, name='admin-applications'),

    # ── Кандидаты (ML pipeline — старые endpoints) ───────────
    path('candidates/', views.candidate_list_create, name='candidate-list-create'),
    path('candidates/search/', views.candidate_search, name='candidate-search'),
    path('candidates/ranking/', views.candidate_ranking, name='candidate-ranking'),
    path('candidates/score-all/', views.score_all, name='score-all'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate-detail'),
    path('candidates/<int:pk>/score/', views.candidate_score, name='candidate-score'),
]
