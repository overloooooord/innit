from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('candidate/<int:pk>/', views.candidate_detail, name='frontend-candidate-detail'),
]
