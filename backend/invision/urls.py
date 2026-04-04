"""
invision/urls.py — Главный роутер проекта.
Все маршруты:
  /admin/              → встроенная Django admin панель
  /api/...             → REST API (candidates/urls.py)
  /panel/...           → кастомная админ-панель с фильтрами
  /                    → фронтенд
"""
from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('candidates.urls')),
    path('', include('frontend.urls')),
]
