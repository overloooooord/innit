# Olympiad levels — 4 values as bot_pipeline collects:
# [Международный] [Республиканский] [Областной] [Школьный]
# Legacy aliases (city, national) for backward compatibility with synthetic data.
OLYMPIAD_LEVEL_MAP = {
    "school": 1,
    "regional": 2,
    "city": 2,        # legacy alias
    "republican": 3,
    "national": 4,    # legacy alias
    "international": 4,
}

# Project roles — as bot_pipeline block 5 collects:
# [Основал(а)] [Сооснователь] [Ключевой участник] [Рядовой участник]
PROJECT_ROLE_MAP = {
    "participant": 0,
    "key_member": 1,
    "co_founder": 2,
    "founder": 3,
}

# Project types — as bot_pipeline block 5 collects:
PROJECT_TYPES = ["technical", "social", "creative", "business", "educational", "other"]

LABEL_MAP = {
    "reject": 0,
    "maybe": 1,
    "shortlist": 2,
}

LABEL_NAMES = ["reject", "maybe", "shortlist"]

# 18 structural features per PROJECT_DOCUMENTATION.md
# Explicitly excluded from scoring:
#   bot_metadata fields (session_duration, pauses, typing_time) — unreliable, biased
#   city, school_type, has_mentor — demographic proxies (fairness audit only)
#   nomination_pre_score — inequality between nominated and self-applied candidates
#   ai_detection_flag — shown to commission card, never enters model
STRUCTURED_FEATURES = [
    # Education (7)
    "f_gpa",
    "f_olympiad_count",
    "f_olympiad_max_level",
    "f_olympiad_has_prize",
    "f_courses_count",
    "f_has_any_courses",
    "f_courses_completed_ratio",
    # Experience (5)
    "f_project_count",
    "f_founder_ratio",
    "f_max_role",
    "f_project_diversity",
    "f_max_team_size",
    # Trajectory (6)
    "f_role_progression",
    "f_scope_progression",
    "f_skill_diversity_growth",
    "f_activity_years_span",
    "f_persistence_signal",
    "f_failure_acknowledgment_ratio",
]

# Feature groups for ablation study (indices into STRUCTURED_FEATURES)
FEATURE_GROUPS = {
    "Education":  [0, 1, 2, 3, 4, 5, 6],
    "Experience": [7, 8, 9, 10, 11],
    "Trajectory": [12, 13, 14, 15, 16, 17],
}

# Human-readable Russian descriptions for commission dashboard
FEATURE_DESCRIPTIONS = {
    "f_gpa":                          "Средний балл (GPA)",
    "f_olympiad_count":               "Количество олимпиад",
    "f_olympiad_max_level":           "Максимальный уровень олимпиады",
    "f_olympiad_has_prize":           "Наличие призового места",
    "f_courses_count":                "Количество онлайн-курсов",
    "f_has_any_courses":              "Проходил(а) хоть один курс",
    "f_courses_completed_ratio":      "Доля завершённых курсов",
    "f_project_count":                "Количество проектов",
    "f_founder_ratio":                "Доля проектов как основатель",
    "f_max_role":                     "Максимальная роль в проектах",
    "f_project_diversity":            "Разнообразие типов проектов",
    "f_max_team_size":                "Макс. размер команды (до 500)",
    "f_role_progression":             "Рост ролей (участник → лидер)",
    "f_scope_progression":            "Рост масштаба деятельности",
    "f_skill_diversity_growth":       "Рост разнообразия навыков",
    "f_activity_years_span":          "Период активности (лет)",
    "f_persistence_signal":           "Упорство (продолжил после неудачи)",
    "f_failure_acknowledgment_ratio": "Доля проектов с признанием трудностей",
}

XGBOOST_PARAMS = {
    "n_estimators": 200,
    "max_depth": 5,
    "learning_rate": 0.1,
    "min_child_weight": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "multi:softprob",
    "num_class": 3,
    "eval_metric": "mlogloss",
    "random_state": 42,
}

MODEL_PATH = "models/model.pkl"
SHAP_PLOTS_DIR = "outputs/shap_plots"
METRICS_DIR = "outputs/metrics"
FAIRNESS_DIR = "outputs/fairness"
CURRENT_YEAR = 2025
