import os
import json
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DB_URL)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS applicants (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                telegram_username TEXT,

                -- Personal info
                last_name TEXT,
                first_name TEXT,
                patronymic TEXT,
                age INTEGER,
                city TEXT,
                city_type TEXT,
                region TEXT,

                -- Education
                school_type TEXT,
                school_name TEXT,
                gpa NUMERIC(4,2),
                ent_score INTEGER,
                ielts_score NUMERIC(3,1),
                toefl_score INTEGER,
                languages TEXT[],
                english_level TEXT,
                circle TEXT,

                -- Documents (file_ids)
                ent_document TEXT,
                ielts_document TEXT,
                toefl_document TEXT,

                -- Complex data as JSONB
                projects JSONB DEFAULT '[]'::jsonb,
                olympiads JSONB DEFAULT '[]'::jsonb,
                volunteer_experience TEXT,
                work_experience TEXT,

                -- Essays
                essay_university TEXT,
                essay_leadership TEXT,
                essay_challenges TEXT,

                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)


async def upsert_applicant(telegram_id: int, username: str, data: dict):
    pool = await get_pool()

    # Serialize list fields
    if "languages" in data and isinstance(data["languages"], list):
        languages = data["languages"]
    else:
        languages = data.get("languages", [])

    if "projects" in data and isinstance(data["projects"], list):
        projects = json.dumps(data["projects"])
    else:
        projects = data.get("projects", "[]")

    if "olympiads" in data and isinstance(data["olympiads"], list):
        olympiads = json.dumps(data["olympiads"])
    else:
        olympiads = data.get("olympiads", "[]")

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO applicants (
                telegram_id, telegram_username,
                last_name, first_name, patronymic, age,
                city, city_type, region,
                school_type, school_name, gpa,
                ent_score, ielts_score, toefl_score,
                languages, english_level, circle,
                ent_document, ielts_document, toefl_document,
                projects, olympiads,
                volunteer_experience, work_experience,
                essay_university, essay_leadership, essay_challenges,
                updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9,
                $10, $11, $12, $13, $14, $15,
                $16, $17, $18, $19, $20, $21,
                $22::jsonb, $23::jsonb,
                $24, $25, $26, $27, $28, NOW()
            )
            ON CONFLICT (telegram_id) DO UPDATE SET
                telegram_username = EXCLUDED.telegram_username,
                last_name = EXCLUDED.last_name,
                first_name = EXCLUDED.first_name,
                patronymic = EXCLUDED.patronymic,
                age = EXCLUDED.age,
                city = EXCLUDED.city,
                city_type = EXCLUDED.city_type,
                region = EXCLUDED.region,
                school_type = EXCLUDED.school_type,
                school_name = EXCLUDED.school_name,
                gpa = EXCLUDED.gpa,
                ent_score = EXCLUDED.ent_score,
                ielts_score = EXCLUDED.ielts_score,
                toefl_score = EXCLUDED.toefl_score,
                languages = EXCLUDED.languages,
                english_level = EXCLUDED.english_level,
                circle = EXCLUDED.circle,
                ent_document = EXCLUDED.ent_document,
                ielts_document = EXCLUDED.ielts_document,
                toefl_document = EXCLUDED.toefl_document,
                projects = EXCLUDED.projects,
                olympiads = EXCLUDED.olympiads,
                volunteer_experience = EXCLUDED.volunteer_experience,
                work_experience = EXCLUDED.work_experience,
                essay_university = EXCLUDED.essay_university,
                essay_leadership = EXCLUDED.essay_leadership,
                essay_challenges = EXCLUDED.essay_challenges,
                updated_at = NOW()
        """,
            telegram_id, username,
            data.get("last_name"), data.get("first_name"), data.get("patronymic"),
            data.get("age"), data.get("city"), data.get("city_type"), data.get("region"),
            data.get("school_type"), data.get("school_name"), data.get("gpa"),
            data.get("ent_score"), data.get("ielts_score"), data.get("toefl_score"),
            languages, data.get("english_level"), data.get("circle"),
            data.get("ent_document"), data.get("ielts_document"), data.get("toefl_document"),
            projects, olympiads,
            data.get("volunteer_experience"), data.get("work_experience"),
            data.get("essay_university"), data.get("essay_leadership"), data.get("essay_challenges")
        )
