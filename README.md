
# Spasht

A procurement transparency tool that surfaces vendor-concentration and
eligibility-criteria red flags in public tender data — built for the
"Inclusive Innovation for Bharat" GovTech track.

## Structure

- `backend/` — FastAPI application
  - `app/data/` — pluggable data sources (Postgres) + pure scoring functions
  - `app/data/parser/` — document extraction (regex) + category matching (embeddings)
  - `app/services/` — orchestration layer (build_report, parsing pipeline) — TO BUILD
  - `app/routers/` — HTTP endpoints — TO BUILD
  - `app/schemas/` — Pydantic response models — TO BUILD
- `frontend/` — React application — TO BUILD
- `db/` — schema.sql (run in NeonDB SQL editor) + seed_data.py
- `sample_documents/` — simulated tender PDFs for Parser dev/testing, with ground_truth.md
- `scripts/` — one-off dev utilities (e.g. sample document generator)

## Setup

1. Run `db/schema.sql` in your NeonDB SQL editor.
2. `export DATABASE_URL="postgresql+psycopg2://..."`, then `python db/seed_data.py`
3. `pip install -r backend/requirements.txt --break-system-packages`
4. (once built) `uvicorn app.main:app --reload` from `backend/`
