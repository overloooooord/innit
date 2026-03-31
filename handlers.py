import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command

from states import Form
from keyboards import (
    kb_city_type, kb_school_type, kb_english_level,
    kb_skip, kb_skip_document, kb_projects_menu,
    kb_olympiads_menu, kb_confirm, remove_kb
)
from database import upsert_applicant

router = Router()
logger = logging.getLogger(__name__)

CITY_TYPE_MAP = {
    "Мегаполис": "megacity",
    "Город": "city",
    "Посёлок": "town",
    "Село": "village",
}

SCHOOL_TYPE_MAP = {
    "Обычная": "regular",
    "Лицей": "lyceum",
    "Гимназия": "gymnasium",
    "Специализированная": "specialized",
    "Колледж": "college",
    "Другое": "other",
}

SECTION_HEADERS = {
    "personal": "👤 *Личная информация*",
    "education": "🎓 *Образование*",
    "scores": "📊 *Баллы и языки*",
    "projects": "🚀 *Проекты*",
    "olympiads": "🏆 *Олимпиады*",
    "experience": "💼 *Опыт*",
    "essays": "✍️ *Эссе*",
}


def progress(step: int, total: int = 30) -> str:
    filled = int(step / total * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {step}/{total}"


# ─── START ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.last_name)
    await message.answer(
        "👋 *Добро пожаловать!*\n\n"
        "Этот бот поможет вам заполнить анкету абитуриента.\n"
        "Вы можете написать /cancel в любой момент.\n\n"
        f"{SECTION_HEADERS['personal']}\n\n"
        f"{progress(1)}\n"
        "Введите вашу *фамилию*:",
        parse_mode="Markdown",
        reply_markup=remove_kb()
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Заполнение анкеты отменено.\nНапишите /start чтобы начать заново.",
        reply_markup=remove_kb()
    )


# ─── PERSONAL INFO ────────────────────────────────────────────────────────────

@router.message(Form.last_name)
async def process_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await state.set_state(Form.first_name)
    await message.answer(f"{progress(2)}\nВведите ваше *имя*:", parse_mode="Markdown")


@router.message(Form.first_name)
async def process_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())
    await state.set_state(Form.patronymic)
    await message.answer(f"{progress(3)}\nВведите ваше *отчество* (или «-» если нет):", parse_mode="Markdown")


@router.message(Form.patronymic)
async def process_patronymic(message: Message, state: FSMContext):
    val = message.text.strip()
    await state.update_data(patronymic=None if val == "-" else val)
    await state.set_state(Form.age)
    await message.answer(f"{progress(4)}\nВведите ваш *возраст* (число):", parse_mode="Markdown")


@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if not (5 <= age <= 100):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректный возраст (число от 5 до 100):")
        return
    await state.update_data(age=age)
    await state.set_state(Form.city)
    await message.answer(f"{progress(5)}\nВведите ваш *город/населённый пункт*:", parse_mode="Markdown")


@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await state.set_state(Form.city_type)
    await message.answer(
        f"{progress(6)}\nВыберите *тип населённого пункта*:",
        parse_mode="Markdown",
        reply_markup=kb_city_type()
    )


@router.message(Form.city_type)
async def process_city_type(message: Message, state: FSMContext):
    city_type = CITY_TYPE_MAP.get(message.text.strip())
    if not city_type:
        await message.answer("⚠️ Пожалуйста, выберите вариант из кнопок:", reply_markup=kb_city_type())
        return
    await state.update_data(city_type=city_type)
    await state.set_state(Form.region)
    await message.answer(
        f"{progress(7)}\nВведите ваш *регион/область*:",
        parse_mode="Markdown",
        reply_markup=remove_kb()
    )


@router.message(Form.region)
async def process_region(message: Message, state: FSMContext):
    await state.update_data(region=message.text.strip())
    await state.set_state(Form.school_type)
    await message.answer(
        f"\n{SECTION_HEADERS['education']}\n\n{progress(8)}\nВыберите *тип учебного заведения*:",
        parse_mode="Markdown",
        reply_markup=kb_school_type()
    )


# ─── EDUCATION ────────────────────────────────────────────────────────────────

@router.message(Form.school_type)
async def process_school_type(message: Message, state: FSMContext):
    school_type = SCHOOL_TYPE_MAP.get(message.text.strip())
    if not school_type:
        await message.answer("⚠️ Пожалуйста, выберите вариант из кнопок:", reply_markup=kb_school_type())
        return
    await state.update_data(school_type=school_type)
    await state.set_state(Form.school_name)
    await message.answer(
        f"{progress(9)}\nВведите *название вашей школы*:",
        parse_mode="Markdown",
        reply_markup=remove_kb()
    )


@router.message(Form.school_name)
async def process_school_name(message: Message, state: FSMContext):
    await state.update_data(school_name=message.text.strip())
    await state.set_state(Form.gpa)
    await message.answer(
        f"{progress(10)}\nВведите ваш *средний балл* (GPA, например: 4.8):",
        parse_mode="Markdown"
    )


@router.message(Form.gpa)
async def process_gpa(message: Message, state: FSMContext):
    try:
        gpa = float(message.text.strip().replace(",", "."))
        if not (0 <= gpa <= 5):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите GPA от 0 до 5 (например: 4.8):")
        return
    await state.update_data(gpa=gpa)
    await state.set_state(Form.ent_score)
    await message.answer(
        f"\n{SECTION_HEADERS['scores']}\n\n{progress(11)}\n"
        "Введите ваш *балл ЕНТ* (или «-» если не сдавали):",
        parse_mode="Markdown"
    )


# ─── SCORES ───────────────────────────────────────────────────────────────────

@router.message(Form.ent_score)
async def process_ent_score(message: Message, state: FSMContext):
    val = message.text.strip()
    if val == "-":
        await state.update_data(ent_score=None)
        await state.set_state(Form.ielts_score)
        await message.answer(
            f"{progress(12)}\nВведите ваш *балл IELTS* (например: 7.5) или «-»:",
            parse_mode="Markdown", reply_markup=remove_kb()
        )
        return
    try:
        score = int(val)
        if not (0 <= score <= 140):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите балл ЕНТ от 0 до 140 или «-»:")
        return
    await state.update_data(ent_score=score)
    await state.set_state(Form.ent_document)
    await message.answer(
        f"{progress(11)}.5\n📎 Прикрепите *документ ЕНТ* (фото/PDF) или нажмите «Пропустить»:",
        parse_mode="Markdown",
        reply_markup=kb_skip_document()
    )


@router.message(Form.ent_document)
async def process_ent_document(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "⏭ Пропустить":
        await state.update_data(ent_document=None)
    elif message.document:
        await state.update_data(ent_document=message.document.file_id)
    elif message.photo:
        await state.update_data(ent_document=message.photo[-1].file_id)
    else:
        await message.answer("⚠️ Пожалуйста, прикрепите файл или нажмите «Пропустить»:", reply_markup=kb_skip_document())
        return
    await state.set_state(Form.ielts_score)
    await message.answer(
        f"{progress(12)}\nВведите ваш *балл IELTS* (например: 7.5) или «-»:",
        parse_mode="Markdown",
        reply_markup=remove_kb()
    )


@router.message(Form.ielts_score)
async def process_ielts_score(message: Message, state: FSMContext):
    val = message.text.strip()
    if val == "-":
        await state.update_data(ielts_score=None)
        await state.set_state(Form.toefl_score)
        await message.answer(
            f"{progress(13)}\nВведите ваш *балл TOEFL* (например: 100) или «-»:",
            parse_mode="Markdown"
        )
        return
    try:
        score = float(val.replace(",", "."))
        if not (0 <= score <= 9):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите балл IELTS от 0 до 9 или «-»:")
        return
    await state.update_data(ielts_score=score)
    await state.set_state(Form.ielts_document)
    await message.answer(
        f"{progress(12)}.5\n📎 Прикрепите *сертификат IELTS* (фото/PDF) или нажмите «Пропустить»:",
        parse_mode="Markdown",
        reply_markup=kb_skip_document()
    )


@router.message(Form.ielts_document)
async def process_ielts_document(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "⏭ Пропустить":
        await state.update_data(ielts_document=None)
    elif message.document:
        await state.update_data(ielts_document=message.document.file_id)
    elif message.photo:
        await state.update_data(ielts_document=message.photo[-1].file_id)
    else:
        await message.answer("⚠️ Прикрепите файл или нажмите «Пропустить»:", reply_markup=kb_skip_document())
        return
    await state.set_state(Form.toefl_score)
    await message.answer(
        f"{progress(13)}\nВведите ваш *балл TOEFL* (например: 100) или «-»:",
        parse_mode="Markdown",
        reply_markup=remove_kb()
    )


@router.message(Form.toefl_score)
async def process_toefl_score(message: Message, state: FSMContext):
    val = message.text.strip()
    if val == "-":
        await state.update_data(toefl_score=None)
        await state.set_state(Form.languages)
        await message.answer(
            f"{progress(14)}\nПеречислите *языки*, которыми вы владеете\n(через запятую, например: Казахский, Русский, Английский):",
            parse_mode="Markdown"
        )
        return
    try:
        score = int(val)
        if not (0 <= score <= 120):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите балл TOEFL от 0 до 120 или «-»:")
        return
    await state.update_data(toefl_score=score)
    await state.set_state(Form.toefl_document)
    await message.answer(
        f"{progress(13)}.5\n📎 Прикрепите *сертификат TOEFL* (фото/PDF) или нажмите «Пропустить»:",
        parse_mode="Markdown",
        reply_markup=kb_skip_document()
    )


@router.message(Form.toefl_document)
async def process_toefl_document(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "⏭ Пропустить":
        await state.update_data(toefl_document=None)
    elif message.document:
        await state.update_data(toefl_document=message.document.file_id)
    elif message.photo:
        await state.update_data(toefl_document=message.photo[-1].file_id)
    else:
        await message.answer("⚠️ Прикрепите файл или нажмите «Пропустить»:", reply_markup=kb_skip_document())
        return
    await state.set_state(Form.languages)
    await message.answer(
        f"{progress(14)}\nПеречислите *языки*, которыми вы владеете\n(через запятую, например: Казахский, Русский, Английский):",
        parse_mode="Markdown",
        reply_markup=remove_kb()
    )


@router.message(Form.languages)
async def process_languages(message: Message, state: FSMContext):
    langs = [l.strip() for l in message.text.split(",") if l.strip()]
    await state.update_data(languages=langs)
    await state.set_state(Form.english_level)
    await message.answer(
        f"{progress(15)}\nВыберите ваш *уровень английского*:",
        parse_mode="Markdown",
        reply_markup=kb_english_level()
    )


@router.message(Form.english_level)
async def process_english_level(message: Message, state: FSMContext):
    level = message.text.strip().upper()
    if level not in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        await message.answer("⚠️ Выберите уровень из кнопок:", reply_markup=kb_english_level())
        return
    await state.update_data(english_level=level)
    await state.set_state(Form.projects_menu)
    await message.answer(
        f"\n{SECTION_HEADERS['projects']}\n\n{progress(16)}\n"
        "Добавьте ваши проекты. Нажмите кнопку ниже:",
        parse_mode="Markdown",
        reply_markup=kb_projects_menu(0)
    )


# ─── PROJECTS ─────────────────────────────────────────────────────────────────

@router.message(Form.projects_menu)
async def process_projects_menu(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    projects = data.get("projects", [])

    if text in ["➕ Добавить проект", "➕ Добавить ещё проект"]:
        await state.set_state(Form.project_name)
        await message.answer("📝 Введите *название проекта*:", parse_mode="Markdown", reply_markup=remove_kb())
    elif text == "✅ Готово (проекты)":
        await state.set_state(Form.olympiads_menu)
        await message.answer(
            f"\n{SECTION_HEADERS['olympiads']}\n\n{progress(20)}\n"
            "Добавьте ваши олимпиады:",
            parse_mode="Markdown",
            reply_markup=kb_olympiads_menu(0)
        )
    else:
        await message.answer("⚠️ Используйте кнопки:", reply_markup=kb_projects_menu(len(projects)))


@router.message(Form.project_name)
async def process_project_name(message: Message, state: FSMContext):
    await state.update_data(_current_project={"name": message.text.strip()})
    await state.set_state(Form.project_description)
    await message.answer("📄 Введите *краткое описание проекта*:", parse_mode="Markdown")


@router.message(Form.project_description)
async def process_project_description(message: Message, state: FSMContext):
    data = await state.get_data()
    proj = data.get("_current_project", {})
    proj["description"] = message.text.strip()
    await state.update_data(_current_project=proj)
    await state.set_state(Form.project_role)
    await message.answer("👤 Введите *вашу роль* в проекте:", parse_mode="Markdown")


@router.message(Form.project_role)
async def process_project_role(message: Message, state: FSMContext):
    data = await state.get_data()
    proj = data.get("_current_project", {})
    proj["role"] = message.text.strip()
    await state.update_data(_current_project=proj)
    await state.set_state(Form.project_scale)
    await message.answer("📏 Введите *масштаб проекта* (например: школьный, городской, международный):", parse_mode="Markdown")


@router.message(Form.project_scale)
async def process_project_scale(message: Message, state: FSMContext):
    data = await state.get_data()
    proj = data.get("_current_project", {})
    proj["scale"] = message.text.strip()
    projects = data.get("projects", [])
    projects.append(proj)
    await state.update_data(projects=projects, _current_project={})
    await state.set_state(Form.projects_menu)
    await message.answer(
        f"✅ Проект *«{proj['name']}»* добавлен! (Всего: {len(projects)})\n\nДобавить ещё?",
        parse_mode="Markdown",
        reply_markup=kb_projects_menu(len(projects))
    )


# ─── OLYMPIADS ────────────────────────────────────────────────────────────────

@router.message(Form.olympiads_menu)
async def process_olympiads_menu(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    olympiads = data.get("olympiads", [])

    if text in ["➕ Добавить олимпиаду", "➕ Добавить ещё олимпиаду"]:
        await state.set_state(Form.olympiad_name)
        await message.answer("🏅 Введите *название олимпиады*:", parse_mode="Markdown", reply_markup=remove_kb())
    elif text == "✅ Готово (олимпиады)":
        await state.set_state(Form.volunteer_experience)
        await message.answer(
            f"\n{SECTION_HEADERS['experience']}\n\n{progress(22)}\n"
            "📝 Опишите ваш *волонтёрский опыт*\n(или введите «-» если нет):",
            parse_mode="Markdown",
            reply_markup=remove_kb()
        )
    else:
        await message.answer("⚠️ Используйте кнопки:", reply_markup=kb_olympiads_menu(len(olympiads)))


@router.message(Form.olympiad_name)
async def process_olympiad_name(message: Message, state: FSMContext):
    await state.update_data(_current_olympiad={"name": message.text.strip()})
    await state.set_state(Form.olympiad_level)
    await message.answer("🌍 Введите *уровень олимпиады* (школьный / районный / городской / областной / республиканский / международный):", parse_mode="Markdown")


@router.message(Form.olympiad_level)
async def process_olympiad_level(message: Message, state: FSMContext):
    data = await state.get_data()
    olym = data.get("_current_olympiad", {})
    olym["level"] = message.text.strip()
    await state.update_data(_current_olympiad=olym)
    await state.set_state(Form.olympiad_result)
    await message.answer("🥇 Введите *результат* (например: 1 место, диплом III степени):", parse_mode="Markdown")


@router.message(Form.olympiad_result)
async def process_olympiad_result(message: Message, state: FSMContext):
    data = await state.get_data()
    olym = data.get("_current_olympiad", {})
    olym["result"] = message.text.strip()
    olympiads = data.get("olympiads", [])
    olympiads.append(olym)
    await state.update_data(olympiads=olympiads, _current_olympiad={})
    await state.set_state(Form.olympiads_menu)
    await message.answer(
        f"✅ Олимпиада *«{olym['name']}»* добавлена! (Всего: {len(olympiads)})\n\nДобавить ещё?",
        parse_mode="Markdown",
        reply_markup=kb_olympiads_menu(len(olympiads))
    )


# ─── EXPERIENCE ───────────────────────────────────────────────────────────────

@router.message(Form.volunteer_experience)
async def process_volunteer(message: Message, state: FSMContext):
    val = message.text.strip()
    await state.update_data(volunteer_experience=None if val == "-" else val)
    await state.set_state(Form.work_experience)
    await message.answer(
        f"{progress(23)}\nОпишите ваш *рабочий опыт* (или «-» если нет):",
        parse_mode="Markdown"
    )


@router.message(Form.work_experience)
async def process_work(message: Message, state: FSMContext):
    val = message.text.strip()
    await state.update_data(work_experience=None if val == "-" else val)
    await state.set_state(Form.essay_university)
    await message.answer(
        f"\n{SECTION_HEADERS['essays']}\n\n{progress(24)}\n"
        "✍️ *Эссе: Почему этот университет?*\n\nРасскажите, почему вы хотите поступить именно в этот университет:",
        parse_mode="Markdown"
    )


# ─── ESSAYS ───────────────────────────────────────────────────────────────────

@router.message(Form.essay_university)
async def process_essay_university(message: Message, state: FSMContext):
    await state.update_data(essay_university=message.text.strip())
    await state.set_state(Form.essay_leadership)
    await message.answer(
        f"{progress(25)}\n✍️ *Эссе о лидерском опыте*\n\nОпишите ситуацию, когда вы проявили лидерство:",
        parse_mode="Markdown"
    )


@router.message(Form.essay_leadership)
async def process_essay_leadership(message: Message, state: FSMContext):
    await state.update_data(essay_leadership=message.text.strip())
    await state.set_state(Form.essay_challenges)
    await message.answer(
        f"{progress(26)}\n✍️ *Эссе о преодолении трудностей*\n\nОпишите трудность, с которой вы столкнулись и как её преодолели:",
        parse_mode="Markdown"
    )


@router.message(Form.essay_challenges)
async def process_essay_challenges(message: Message, state: FSMContext):
    await state.update_data(essay_challenges=message.text.strip())
    await state.set_state(Form.circle)
    await message.answer(
        f"{progress(27)}\nВ каких *кружках/секциях* вы занимаетесь? (или «-» если нет):",
        parse_mode="Markdown"
    )


@router.message(Form.circle)
async def process_circle(message: Message, state: FSMContext):
    val = message.text.strip()
    await state.update_data(circle=None if val == "-" else val)
    await state.set_state(Form.review)

    # Build summary
    data = await state.get_data()
    summary = build_summary(data)
    await message.answer(
        f"{progress(30)}\n\n📋 *Проверьте вашу анкету:*\n\n{summary}\n\n"
        "Всё верно?",
        parse_mode="Markdown",
        reply_markup=kb_confirm()
    )


def build_summary(data: dict) -> str:
    lines = [
        f"👤 *Личные данные*",
        f"ФИО: {data.get('last_name')} {data.get('first_name')} {data.get('patronymic') or ''}",
        f"Возраст: {data.get('age')}",
        f"Город: {data.get('city')} ({data.get('city_type')}), {data.get('region')}",
        "",
        f"🎓 *Образование*",
        f"Тип школы: {data.get('school_type')}",
        f"Школа: {data.get('school_name')}",
        f"GPA: {data.get('gpa')}",
        "",
        f"📊 *Баллы*",
        f"ЕНТ: {data.get('ent_score') or '—'}",
        f"IELTS: {data.get('ielts_score') or '—'}",
        f"TOEFL: {data.get('toefl_score') or '—'}",
        f"Языки: {', '.join(data.get('languages', []))}",
        f"Уровень EN: {data.get('english_level')}",
        "",
        f"🚀 *Проекты*: {len(data.get('projects', []))} шт.",
        f"🏆 *Олимпиады*: {len(data.get('olympiads', []))} шт.",
        f"🎯 *Кружок*: {data.get('circle') or '—'}",
        "",
        f"💼 *Волонтёрство*: {'есть' if data.get('volunteer_experience') else '—'}",
        f"💼 *Опыт работы*: {'есть' if data.get('work_experience') else '—'}",
        "",
        f"✍️ *Эссе*: {'✅' if data.get('essay_university') else '—'} / {'✅' if data.get('essay_leadership') else '—'} / {'✅' if data.get('essay_challenges') else '—'}",
    ]
    return "\n".join(lines)


# ─── REVIEW & SAVE ────────────────────────────────────────────────────────────

@router.message(Form.review)
async def process_review(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "🔄 Начать заново":
        await state.clear()
        await state.set_state(Form.last_name)
        await message.answer(
            "🔄 Начинаем заново!\n\nВведите вашу *фамилию*:",
            parse_mode="Markdown",
            reply_markup=remove_kb()
        )
        return

    if text == "✅ Подтвердить и отправить":
        data = await state.get_data()
        try:
            await upsert_applicant(
                telegram_id=message.from_user.id,
                username=message.from_user.username or "",
                data=data
            )
            await message.answer(
                "🎉 *Анкета успешно сохранена!*\n\n"
                "Ваши данные записаны в базу данных.\n"
                "Удачи с поступлением! 🍀\n\n"
                "Написать /start чтобы заполнить заново.",
                parse_mode="Markdown",
                reply_markup=remove_kb()
            )
        except Exception as e:
            logger.error(f"DB error: {e}")
            await message.answer(
                "❌ Произошла ошибка при сохранении. Попробуйте позже или свяжитесь с администратором.",
                reply_markup=remove_kb()
            )
        await state.clear()
        return

    await message.answer("⚠️ Используйте кнопки для подтверждения:", reply_markup=kb_confirm())
