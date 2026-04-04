"""
telegram_service.py — Отправка уведомлений в Telegram.
Как это работает:
  1. При новой заявке вызывается notify_new_application(application)
  2. Функция берёт TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_IDS из settings (= из .env)
  3. Отправляет сообщение в каждый chat_id через Telegram Bot API
  4. Если token не настроен — просто логирует предупреждение
Chat IDs настраиваются в .env:
  TELEGRAM_CHAT_IDS=8011349874,1262791177,1255137807
Как получить chat_id:
  1. Напиши своему боту /start
  2. Открой https://api.telegram.org/bot<TOKEN>/getUpdates
  3. Найди "chat": {"id": 123456789}
"""
import urllib.request
import urllib.parse
import json
import logging
from django.conf import settings
logger = logging.getLogger('candidates')
def notify_new_application(application):
    """
    Отправить Telegram-уведомление о новой заявке.
    Вызывается из views.py → application_list_create() после сохранения.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_ids = getattr(settings, 'TELEGRAM_CHAT_IDS', [])
    if not token or token == 'YOUR_BOT_TOKEN_HERE':
        logger.warning(
            "Telegram не настроен: TELEGRAM_BOT_TOKEN не указан в .env. "
            "Уведомление не отправлено."
        )
        return
    if not chat_ids:
        logger.warning("Telegram CHAT_IDS пусты. Уведомление не отправлено.")
        return
    languages_str = ', '.join(application.languages) if application.languages else '—'
    text = (
        f"🆕 *Новая заявка!*\n\n"
        f"👤 *Имя:* {_escape_md(application.name)}\n"
        f"🏙 *Город:* {_escape_md(application.city)}\n"
        f"📍 *Регион:* {_escape_md(application.region)}\n"
        f"🌐 *Языки:* {_escape_md(languages_str)}\n"
        f"📱 *Telegram:* {_escape_md(application.telegram_username)}\n"
        f"⚽ *Спорт:* {_escape_md(application.sport or '—')}\n"
        f"📝 *Хобби:* {_escape_md(application.hobbies[:100] or '—')}\n"
        f"\n📅 *Дата:* {application.created_at.strftime('%d.%m.%Y %H:%M') if application.created_at else '—'}"
    )
    for chat_id in chat_ids:
        try:
            _send_message(token, chat_id, text)
            logger.info(f"Telegram уведомление отправлено в chat {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки Telegram в chat {chat_id}: {e}")
def notify_new_candidate(candidate):
    """
    Отправить уведомление о новом кандидате (для ML pipeline).
    Обратная совместимость со старым кодом.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_ids = getattr(settings, 'TELEGRAM_CHAT_IDS', [])
    if not token or token == 'YOUR_BOT_TOKEN_HERE' or not chat_ids:
        logger.warning("Telegram не настроен, уведомление не отправлено.")
        return
    gpa = candidate.profile_data.get('education', {}).get('gpa', '—')
    projects = len(candidate.profile_data.get('experience', {}).get('projects', []))
    text = (
        f"🆕 *Новый кандидат зарегистрирован!*\n\n"
        f"👤 *Имя:* {_escape_md(candidate.name)}\n"
        f"🎂 *Возраст:* {candidate.age}\n"
        f"🏙 *Город:* {_escape_md(candidate.city or '—')}\n"
        f"📍 *Регион:* {_escape_md(candidate.region or '—')}\n"
        f"🎓 *GPA:* {gpa}\n"
        f"🚀 *Проектов:* {projects}\n"
        f"🏫 *Тип школы:* {_escape_md(candidate.school_type or '—')}\n"
    )
    for chat_id in chat_ids:
        try:
            _send_message(token, chat_id, text)
        except Exception as e:
            logger.error(f"Failed to send Telegram to {chat_id}: {e}")
def _escape_md(text: str) -> str:
    """Экранировать спецсимволы Markdown для Telegram."""
    if not text:
        return '—'
    for char in ('_', '*', '[', ']', '(', ')', '~', '`', '>', '
        text = text.replace(char, f'\\{char}')
    return text
def _send_message(token: str, chat_id: int, text: str):
    """
    Отправить сообщение через Telegram Bot API.
    Используем urllib (без внешних зависимостей).
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            if not result.get('ok'):
                logger.warning(f"Telegram API error: {result}")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        raise
