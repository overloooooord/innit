# ============================================================
# models.py — Pydantic models for request/response validation
# ============================================================
# All incoming JSON is validated here before hitting our logic.
# ============================================================

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# ── Auth models ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    email: str

class AuthResponse(BaseModel):
    status: str
    user: UserInfo
    token: str


# ── Application models ────────────────────────────────────────

class BasicInfo(BaseModel):
    """Block 1 — Basic personal information"""
    full_name: str
    age: int
    city: str
    school: str
    grade: str          # e.g. "9", "10", "11", "1 курс колледжа", "другое"
    email: str
    phone: str

class Experience(BaseModel):
    """Block 2 — Projects, competitions, volunteering, mentorship"""
    projects: str           # school/personal/volunteer projects
    self_projects: str      # self-initiated projects
    competitions: str       # olympiads, hackathons, competitions + results
    volunteering: str       # community/volunteer work
    self_learning: str      # what learned outside school in past year
    mentor: str             # mentor or influential person

class Motivation(BaseModel):
    """Block 3 — Essays (min word counts enforced on frontend)"""
    why_invision: str       # min 150 words
    difficult_situation: str  # min 100 words
    community_problem: str    # min 100 words

class Consents(BaseModel):
    """Block 5 — Required legal checkboxes"""
    data_processing: bool     # consent to personal data processing
    essay_authenticity: bool  # confirms essays are written by the applicant

class ApplicationSubmission(BaseModel):
    """
    Full application body sent by POST /api/submit-answers

    Structure:
    {
        "user_id": 1,
        "basic_info": { ... },
        "experience": { ... },
        "motivation": { ... },
        "psychometric": { "q1": "answer text", ..., "q40": "answer text" },
        "consents": { "data_processing": true, "essay_authenticity": true }
    }
    """
    user_id: int
    basic_info: BasicInfo
    experience: Experience
    motivation: Motivation
    psychometric: Dict[str, str]   # keys = "q1".."q40", values = selected option text
    consents: Consents

class ApplicationResponse(BaseModel):
    """
    What the backend returns after saving.
    Echoes everything back as JSON — no AI scoring yet.
    """
    status: str
    user_id: int
    application: Dict[str, Any]
