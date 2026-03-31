from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    # Personal info
    last_name = State()
    first_name = State()
    patronymic = State()
    age = State()
    city = State()
    city_type = State()
    region = State()

    # Education
    school_type = State()
    school_name = State()
    gpa = State()

    # Scores
    ent_score = State()
    ent_document = State()
    ielts_score = State()
    ielts_document = State()
    toefl_score = State()
    toefl_document = State()

    # Languages
    languages = State()
    english_level = State()

    # Projects
    projects_menu = State()
    project_name = State()
    project_description = State()
    project_role = State()
    project_scale = State()

    # Olympiads
    olympiads_menu = State()
    olympiad_name = State()
    olympiad_level = State()
    olympiad_result = State()

    # Experience
    volunteer_experience = State()
    work_experience = State()

    # Essays
    essay_university = State()
    essay_leadership = State()
    essay_challenges = State()

    # Circle
    circle = State()

    # Review
    review = State()
