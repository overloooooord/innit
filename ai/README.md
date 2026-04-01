# ai/ — Placeholder for future AI analysis module

This folder is reserved for AI-powered analysis logic.

## What will go here (later)

- `analyzer.py` — reads submitted answers from the DB and produces a profile
- `prompt_builder.py` — builds prompts for LLM APIs
- `scoring.py` — if needed, rule-based scoring before AI is added

## Current status

No AI logic yet. The backend (`back/`) simply saves answers to SQLite  
and returns them as JSON. This folder is intentionally empty.

## Data shape (upcoming input)

```json
{
  "basic_info":   { ... },
  "experience":   { ... },
  "motivation":   { "why_invision": "...", ... },
  "psychometric": { "q1": "option text", ..., "q40": "option text" },
  "consents":     { "data_processing": true, "essay_authenticity": true }
}
```
