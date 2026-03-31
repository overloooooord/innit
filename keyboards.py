from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def kb_city_type():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мегаполис"), KeyboardButton(text="Город")],
            [KeyboardButton(text="Посёлок"), KeyboardButton(text="Село")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def kb_school_type():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Обычная"), KeyboardButton(text="Лицей")],
            [KeyboardButton(text="Гимназия"), KeyboardButton(text="Специализированная")],
            [KeyboardButton(text="Колледж"), KeyboardButton(text="Другое")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def kb_english_level():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="A1"), KeyboardButton(text="A2")],
            [KeyboardButton(text="B1"), KeyboardButton(text="B2")],
            [KeyboardButton(text="C1"), KeyboardButton(text="C2")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def kb_skip_document():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def kb_skip():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def kb_projects_menu(count: int):
    buttons = []
    if count > 0:
        buttons.append([KeyboardButton(text="➕ Добавить ещё проект")])
    else:
        buttons.append([KeyboardButton(text="➕ Добавить проект")])
    buttons.append([KeyboardButton(text="✅ Готово (проекты)")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


def kb_olympiads_menu(count: int):
    buttons = []
    if count > 0:
        buttons.append([KeyboardButton(text="➕ Добавить ещё олимпиаду")])
    else:
        buttons.append([KeyboardButton(text="➕ Добавить олимпиаду")])
    buttons.append([KeyboardButton(text="✅ Готово (олимпиады)")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


def kb_confirm():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить и отправить")],
            [KeyboardButton(text="🔄 Начать заново")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def remove_kb():
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()
