# ============================================================
# routers/assessment.py — /api/submit-answers
# ============================================================
# Receives the full 5-block application form, saves it to the
# database, and returns everything back as JSON.
# No AI. No scoring. Just store and echo.
# ============================================================

import json

from fastapi import APIRouter, HTTPException
from database import get_connection
from models import ApplicationSubmission, ApplicationResponse

router = APIRouter()


# ── POST /api/submit-answers ─────────────────────────────────
@router.post("/submit-answers", response_model=ApplicationResponse)
async def submit_answers(data: ApplicationSubmission):
    """
    Receives the complete application (5 blocks).

    Incoming JSON shape:
    {
        "user_id": 1,
        "basic_info":   { "full_name": "...", "age": 17, ... },
        "experience":   { "projects": "...", ... },
        "motivation":   { "why_invision": "...", ... },
        "psychometric": { "q1": "answer text", ..., "q40": "..." },
        "consents":     { "data_processing": true, "essay_authenticity": true }
    }

    Returns the same data back as JSON confirmation:
    {
        "status": "ok",
        "user_id": 1,
        "application": { ... all 5 blocks ... }
    }
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # ── Step 1: make sure the user exists ───────────────────
    user = cursor.execute(
        "SELECT id FROM users WHERE id = ?", (data.user_id,)
    ).fetchone()

    if not user:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"User id={data.user_id} not found."
        )

    # ── Step 2: validate consents — both must be True ────────
    if not data.consents.data_processing or not data.consents.essay_authenticity:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Both consent checkboxes must be accepted."
        )

    # ── Step 3: convert each block to a JSON string for DB ───
    basic_json    = json.dumps(data.basic_info.model_dump(),   ensure_ascii=False)
    exp_json      = json.dumps(data.experience.model_dump(),   ensure_ascii=False)
    motiv_json    = json.dumps(data.motivation.model_dump(),   ensure_ascii=False)
    psycho_json   = json.dumps(data.psychometric,              ensure_ascii=False)
    consent_json  = json.dumps(data.consents.model_dump(),     ensure_ascii=False)

    # ── Step 4: insert into the applications table ───────────
    cursor.execute(
        """
        INSERT INTO applications
            (user_id, basic_info, experience, motivation, psychometric, consents)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (data.user_id, basic_json, exp_json, motiv_json, psycho_json, consent_json)
    )
    conn.commit()
    conn.close()

    # ── Step 5: build the full application dict to return ────
    application = {
        "basic_info":   data.basic_info.model_dump(),
        "experience":   data.experience.model_dump(),
        "motivation":   data.motivation.model_dump(),
        "psychometric": data.psychometric,
        "consents":     data.consents.model_dump(),
    }

    # Return it all as JSON — this is what the frontend will display
    return ApplicationResponse(
        status="ok",
        user_id=data.user_id,
        application=application,
    )


# ── GET /api/applications/{user_id} ──────────────────────────
@router.get("/applications/{user_id}")
async def get_applications(user_id: int):
    """
    Returns all submitted applications for a given user.
    Useful for history and debugging.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        """
        SELECT id, basic_info, experience, motivation, psychometric, consents, submitted_at
        FROM applications
        WHERE user_id = ?
        ORDER BY submitted_at DESC
        """,
        (user_id,)
    ).fetchall()
    conn.close()

    return {
        "status": "ok",
        "user_id": user_id,
        "applications": [
            {
                "id":           row["id"],
                "basic_info":   json.loads(row["basic_info"]),
                "experience":   json.loads(row["experience"]),
                "motivation":   json.loads(row["motivation"]),
                "psychometric": json.loads(row["psychometric"]),
                "consents":     json.loads(row["consents"]),
                "submitted_at": row["submitted_at"],
            }
            for row in rows
        ],
    }
