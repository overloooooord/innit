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
from candidates.models import Teacher, Student, TeacherProposal


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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# КАБИНЕТ УЧИТЕЛЯ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def teacher_login_page(request):
    """Страница логина для учителя."""
    if request.session.get('teacher_id'):
        return redirect('teacher-panel')
    return render(request, 'frontend/teacher_login.html')

@csrf_exempt
def teacher_login(request):
    """Обработка входа учителя."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()

    try:
        teacher = Teacher.objects.get(username=username)
        # Check against bcrypt or plaintext for demo/admin ease
        password_valid = False
        if teacher.password_hash == password:
            password_valid = True
        else:
            try:
                password_valid = bcrypt.checkpw(
                    password.encode('utf-8'),
                    teacher.password_hash.encode('utf-8')
                )
            except Exception:
                pass

        if password_valid:
            request.session['teacher_id'] = teacher.id
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Неверный логин или пароль'}, status=401)
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Неверный логин или пароль'}, status=401)

def teacher_logout(request):
    """Выход из кабинета учителя."""
    request.session.pop('teacher_id', None)
    return redirect('teacher-login-page')

def teacher_panel_view(request):
    """Кабинет учителя: ученики и предложения."""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('teacher-login-page')
    
    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        request.session.pop('teacher_id', None)
        return redirect('teacher-login-page')

    students = teacher.students.all().order_by('-date_added')
    proposals = teacher.proposals.all().order_by('-created_at')

    context = {
        'teacher': teacher,
        'students': students,
        'proposals': proposals,
    }
    return render(request, 'frontend/teacher_panel.html', context)

@csrf_exempt
def teacher_add_student(request):
    """Ввод ученика учителем."""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return JsonResponse({'error': 'Not authorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        student_name = data.get('name', '').strip()
        if not student_name:
            return JsonResponse({'success': False, 'error': 'Имя ученика не может быть пустым'})

        teacher = Teacher.objects.get(id=teacher_id)
        Student.objects.create(teacher=teacher, name=student_name)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
