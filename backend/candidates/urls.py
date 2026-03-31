from django.urls import path
from . import views

urlpatterns = [
    path('', views.candidate_list_create, name='candidate-list-create'),
    path('search/', views.candidate_search, name='candidate-search'),
    path('ranking/', views.candidate_ranking, name='candidate-ranking'),
    path('score-all/', views.score_all, name='score-all'),
    path('<int:pk>/', views.candidate_detail, name='candidate-detail'),
    path('<int:pk>/score/', views.candidate_score, name='candidate-score'),
]
