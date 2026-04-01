/**
 * api.js — API клиент для связи с backend
 * =========================================
 *
 * КАК ЭТО РАБОТАЕТ (для начинающих):
 *
 *   API (Application Programming Interface) — это «мост» между фронтом и сервером.
 *   Фронт отправляет HTTP запросы (GET, POST) на определённые адреса (endpoints),
 *   а сервер отвечает JSON данными.
 *
 *   Пример:
 *     Фронт: POST /api/applications/ + JSON тело → Сервер создаёт заявку
 *     Сервер: { id: 42, name: "Иванов", ... } → Фронт получает ID заявки
 *
 *   fetch() — встроенная функция браузера для HTTP запросов.
 *   async/await — удобный способ работы с асинхронными операциями
 *   (не «замораживает» страницу, пока ждём ответ от сервера).
 */

'use strict';

// ─── Базовый URL ──────────────────────────────────────────────────────────────
// Если фронт и backend на одном сервере → '/api'
// Если backend отдельно → 'http://localhost:8000/api'
const API_BASE = '/api';


// ─── Универсальная функция для HTTP запросов ──────────────────────────────────
async function apiRequest(method, endpoint, body = null) {
  /*
   * Алгоритм:
   * 1. Формируем URL: API_BASE + endpoint (например, '/api/applications/')
   * 2. Настраиваем заголовки (Content-Type: application/json)
   * 3. Если есть тело — превращаем объект в JSON строку
   * 4. Отправляем запрос через fetch()
   * 5. Парсим ответ как JSON
   * 6. Если ошибка (статус 400+) — бросаем исключение
   */

  const options = {
    method: method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Добавляем тело только для POST/PUT (GET запросы не имеют тела)
  if (body && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(body);
  }

  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok) {
      // Сервер вернул ошибку (400, 404, 500 и т.д.)
      // Пробуем достать сообщение об ошибке из ответа
      const errorMsg = data.detail
        || data.error
        || JSON.stringify(data)
        || `Ошибка ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    // Если fetch() не смог подключиться (нет интернета, сервер не отвечает)
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('Нет связи с сервером. Проверьте подключение.');
    }
    throw error;
  }
}


// ─── API функции ──────────────────────────────────────────────────────────────
// Каждая функция = один endpoint backend'а

const API = {

  /**
   * Получить список городов и доступных языков
   * GET /api/cities/
   * Ответ: { cities: ["Алматы", "Астана", ...], languages: ["Казахский", ...] }
   */
  getCities: () => apiRequest('GET', '/cities/'),

  /**
   * Получить регион для выбранного города
   * GET /api/cities/<город>/regions/
   * Ответ: { city: "Алматы", region: "город Алматы" }
   */
  getRegion: (city) => apiRequest('GET', `/cities/${encodeURIComponent(city)}/regions/`),

  /**
   * Создать новую заявку
   * POST /api/applications/
   * Тело:  { name, city, region, languages: [...], telegram_username, hobbies, sport }
   * Ответ: { id: 42, name: "...", city: "...", ... }
   */
  submitApplication: (data) => apiRequest('POST', '/applications/', data),

  /**
   * Отправить результаты MBTI теста
   * POST /api/tests/mbti/
   * Тело:  { application_id: 42, answers: { q1: "A", q2: "B", ..., q40: "A" } }
   * Ответ: { id: 1, result_type: "INTJ", answers: {...} }
   */
  submitMBTI: (applicationId, answers) =>
    apiRequest('POST', '/tests/mbti/', {
      application_id: applicationId,
      answers: answers,
    }),

  /**
   * Отправить результаты языкового теста
   * POST /api/tests/language/
   * Тело: { application_id, language, answers, score, max_score, time_spent_seconds, violation_count }
   * Ответ: { id: 1, language: "Английский", score: 15, ... }
   */
  submitLanguageTest: (data) =>
    apiRequest('POST', '/tests/language/', data),
};
