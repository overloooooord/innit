import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "invision_u")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "Indrivestellaris")
raw_port = os.getenv("DB_PORT")
if not raw_port or raw_port.lower() == "none":
    DB_PORT = "5432"
else:
    DB_PORT = raw_port
DATABASE_URL = f"postgresql+asyncpg://postgres:{DB_PASS}@db.ogbabrukutngsdlbryne.supabase.co:5432/postgres"
MAX_OLYMPIADS = 10
MAX_COURSES = 10
MAX_PROJECTS = 10
ESSAY_MIN_WORDS = 70
ESSAY_MAX_WORDS = 150
SCENARIO_TIMER_SECONDS = 20
MAX_TIMER_VIOLATIONS = 2
