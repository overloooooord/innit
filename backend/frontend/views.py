"""
views.py — Frontend views (страницы, не API).

Как это работает:
  Эти views отдают HTML-страницы (шаблоны Django).
  API endpoints (JSON) — в candidates/views.py.

  panel_login():
    Проверяет пароль через bcrypt.checkpw() — пароль
    НИКОГДА не хранится в открытом виде. Хеш берётся из .env.
"""

import bcrypt
import logging

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json


logger = logging.getLogger('candidates')


def index(request):
    """Главная страница: список кандидатов."""
    return render(request, 'frontend/index.html')


def register(request):
    """Страница регистрации кандидата."""
    return render(request, 'frontend/register.html')


def candidate_detail(request, pk):
    """Страница деталей кандидата."""
    return render(request, 'frontend/candidate_detail.html', {'candidate_id': pk})


def panel_view(request):
    """
    Админ-панель — доступ ТОЛЬКО с сессией.
    Если нет panel_auth в сессии → редирект на страницу логина.
    """
    if not request.session.get('panel_auth'):
        return redirect('panel-login-page')
    return render(request, 'frontend/admin_panel.html')


def panel_login_page(request):
    """Показать страницу логина (если ещё не залогинен → показать форму)."""
    if request.session.get('panel_auth'):
        return redirect('panel')
    return render(request, 'frontend/login.html')


@csrf_exempt
def panel_login(request):
    """
    POST — обработка логина админа.

    Безопасность:
      1. Логин/пароль НЕ сравниваются с БД → никакого SQL вообще
      2. Пароль проверяется через bcrypt.checkpw() vs хеш из .env
      3. Никаких plaintext паролей ни в коде, ни в settings

    Логин: era
    Пароль: admin1 (хранится как bcrypt хеш)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()

    expected_user = getattr(settings, 'PANEL_USERNAME', 'era')
    password_hash = getattr(settings, 'PANEL_PASSWORD_HASH', '')

    # Проверка username
    if username != expected_user:
        logger.warning(f"Неудачная попытка входа в панель: username={username}")
        return JsonResponse(
            {'success': False, 'error': 'Неверный логин или пароль'},
            status=401,
        )

    # Проверка пароля через bcrypt
    if not password_hash:
        logger.error("PANEL_PASSWORD_HASH не настроен в .env!")
        return JsonResponse(
            {'success': False, 'error': 'Сервер не настроен'},
            status=500,
        )

    try:
        password_valid = bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8'),
        )
    except Exception as e:
        logger.error(f"Ошибка проверки bcrypt: {e}")
        return JsonResponse(
            {'success': False, 'error': 'Ошибка сервера'},
            status=500,
        )

    if password_valid:
        request.session['panel_auth'] = True
        logger.info(f"Успешный вход в админ-панель: {username}")
        return JsonResponse({'success': True})
    else:
        logger.warning(f"Неверный пароль для {username}")
        return JsonResponse(
            {'success': False, 'error': 'Неверный логин или пароль'},
            status=401,
        )


def panel_logout(request):
    """Выход из админ-панели: удаляем сессию."""
    request.session.pop('panel_auth', None)
    logger.info("Выход из админ-панели")
    return redirect('panel-login-page')
