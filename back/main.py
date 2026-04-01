# ============================================================
# main.py — Entry point of the FastAPI backend
# ============================================================
# This file starts the server, connects all the route handlers
# (auth + assessment), sets up CORS so the frontend can talk
# to the backend, and serves the frontend HTML files.
# ============================================================

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import our route handlers
from routers import auth, assessment

# Import the database initializer (creates tables if they don't exist)
from database import init_db

# ── Create the FastAPI app ───────────────────────────────────
app = FastAPI(
    title="UniAdmit",
    description="University Admission — collects user answers and returns them as JSON",
    version="1.0.0"
)

# ── CORS Middleware ──────────────────────────────────────────
# Without this the browser would block requests from the frontend
# to the backend (they run on the same port here, but good practice)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────────
# All auth endpoints will be prefixed with /api  → /api/register, /api/login
# All assessment endpoints will also be under /api → /api/submit-answers
app.include_router(auth.router,       prefix="/api", tags=["Auth"])
app.include_router(assessment.router, prefix="/api", tags=["Assessment"])

# ── Serve the frontend (HTML/CSS/JS) ─────────────────────────
# The front/ folder sits one level up from back/
frontend_path = os.path.join(os.path.dirname(__file__), "..", "front")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Root URL → send back index.html
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# ── Startup event ────────────────────────────────────────────
# Runs once when the server boots — creates the DB tables
@app.on_event("startup")
async def on_startup():
    init_db()
    print("Server started — database ready.")

# ── Run directly with: python main.py ────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
