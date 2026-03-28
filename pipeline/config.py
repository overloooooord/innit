OLYMPIAD_LEVEL_MAP = {
    "school": 1,
    "city": 2,
    "regional": 3,
    "national": 4,
    "international": 5,
}

OLYMPIAD_RESULT_MAP = {
    "participant": 0,
    "honorable_mention": 1,
    "prize": 2,
}

PROJECT_ROLE_MAP = {
    "volunteer": 0,
    "participant": 1,
    "co_founder": 2,
    "founder": 3,
}

PROJECT_TYPES = ["technical", "social", "media", "business", "education", "other"]

LABEL_MAP = {
    "reject": 0,
    "maybe": 1,
    "shortlist": 2,
}

LABEL_NAMES = ["reject", "maybe", "shortlist"]

STRUCTURED_FEATURES = [
    "f_gpa",
    "f_olympiad_count",
    "f_olympiad_max_level",
    "f_olympiad_has_prize",
    "f_courses_count",
    "f_courses_completed_ratio",
    "f_project_count",
    "f_founder_ratio",
    "f_has_technical_project",
    "f_has_social_project",
    "f_project_diversity",
    "f_max_team_size",
    "f_solo_project_count",
    "f_role_progression",
    "f_scope_progression",
    "f_skill_diversity_growth",
    "f_activity_years_span",
    "f_persistence_signal",
    "f_activity_recency",
    "f_session_duration",
    "f_essay_typing_duration",
    "f_total_pauses",
]

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
    "use_label_encoder": False,
}

MODEL_PATH = "models/model.pkl"
SHAP_PLOTS_DIR = "outputs/shap_plots"
METRICS_DIR = "outputs/metrics"
FAIRNESS_DIR = "outputs/fairness"
CURRENT_YEAR = 2025
