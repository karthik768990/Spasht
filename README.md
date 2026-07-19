# Spasht

## 1. The Problem We're Solving

**Problem**: Government procurement data is published as a transparency gesture (GeM, state e-procurement portals, CPPP) but is never analyzed at scale. Statistical red flags obvious in aggregate — one vendor winning 90% of tenders in a district, eligibility criteria narrow enough to fit one company — stay invisible unless a journalist or RTI activist manually digs through records case by case.

**Amplify**: Government procurement is one of the largest channels of public spending in India, and one of the least algorithmically audited. Publishing data is not the same as making it legible. The OECD's 2025 Guidelines for Fighting Bid Rigging explicitly lists "same supplier repeatedly winning" and "geographic win allocation" as established red flags — this isn't a hypothetical problem, it's a documented one with no automated detection layer at the scale India operates at.

**Impact**: Without this layer, honest vendors/MSMEs get locked out of competitive bidding when tenders are structured to favor incumbents; procurement officers and auditors rely on manual sampling instead of systemic monitoring; citizens have no visibility into how public money is actually being spent.

**Need**: What's missing isn't more disclosure — it's an interpretation layer that converts raw, scattered, unstructured tender data into actionable, explainable signal, sitting beside existing systems rather than replacing them.

**Payoff**: Spasht turns published tender data into two independently explainable red-flag signals per tender — a concentration score and an eligibility-criteria deviation score — so a procurement officer, auditor, or citizen can see not just *that* something looks unusual, but exactly *why*, with the evidence shown, not asserted.

## 2. What Spasht Computes

Spasht exposes TWO SEPARATE, never-blended scores per tender.

1. **Concentration score (HHI)** — computed at both the department level and category level. 
   - *Why two levels?* High department HHI alone suggests department-level favoritism. High category HHI alone could just mean a legitimate niche specialist. High on BOTH is the strongest, hardest-to-explain-away signal.
2. **Eligibility-text deviation score** — measures how far a tender's eligibility criteria deviates from the norm for its category, using semantic similarity.

**Important Context**: This is a flagging tool, not a verdict. As the OECD frames it, these indicators do not necessarily demonstrate the presence of corruption — they signal risk worth human review.

## 3. Architecture

Spasht uses a decoupled architecture consisting of a FastAPI backend, a React frontend, and a PostgreSQL database (NeonDB), interacting through a pluggable `TenderDataSource` abstraction.

### Flow 1: Single Document (Insert into shared dataset)

```mermaid
flowchart TD
    A[User uploads one tender document] --> B[Job A: pdf_extractor.py<br/>regex-based field extraction]
    B --> C[Job B: category_matcher.py<br/>embedding similarity vs canonical categories]
    C --> D{New department<br/>or category?}
    D -->|Yes| E[Create new department/category/vendor rows]
    D -->|No| F[Match existing rows]
    E --> G[(NeonDB / Postgres<br/>departments, vendors, tenders, bids)]
    F --> G
    G --> H[PostgresTenderDataSource<br/>SQL aggregation: win-counts, single-bidder detection]
    H --> I[data/scoring.py<br/>compute_hhi_from_win_counts,<br/>compute_eligibility_scores,<br/>classify_pattern]
    I --> J[API response: two independent scores<br/>+ pattern classification + reasoning]
    J --> K[React frontend:<br/>dashboard + tender detail view]
```

### Flow 2: Isolated Batch Analysis (In-memory, never persisted)

```mermaid
flowchart TD
    A2[User uploads up to 25 documents as one batch] --> B2[Job A: pdf_extractor.py<br/>same extraction logic, reused]
    B2 --> C2[Job B: category_matcher.py<br/>canonical categories drawn ONLY from this batch]
    C2 --> D2[InMemoryTenderDataSource<br/>built fresh per-request, no DB writes]
    D2 --> E2[data/scoring.py<br/>SAME pure scoring functions as Diagram 1]
    E2 --> F2[API response scoped to this batch only]
    F2 --> G2[React frontend:<br/>isolated batch-results view<br/>never mixed with main dashboard]

    style D2 fill:#00000000,stroke-dasharray: 5 5
```

*Note: This path never touches Postgres. Both diagrams reuse the exact same `data/scoring.py` functions — the only thing that differs is which `TenderDataSource` implementation feeds them, which is the payoff of the pluggable-data-source design used throughout this project.*

- **Scalability**: The pluggable data-source interface means connecting a new procurement portal requires writing one new adapter implementing 6 methods, rather than redesigning the entire system. Aggregation happens directly in SQL, meaning query costs scale efficiently with the database engine, not with application server memory. The embedding function (`get_embeddings()`) is a single swappable seam — upgrading the semantic model never requires touching the core scoring logic that consumes it.
- **Fault Tolerance**: Document extraction fails LOUDLY and explicitly. A missing critical field raises a clear error rather than silently inserting wrong data. This is deliberate because silent mis-extraction is worse than a visible failure in a governance tool. Database writes for a parsed document are strictly validated before insertion via parameterized queries (new department/vendor/category detection is explicit, not accidental).

## 4. How Correctness is Verified

Correctness is not asserted; it is rigorously tested. 

The system is validated against a **synthetic dataset with documented, known ground truth**. We use synthetic data not because real data was unavailable, but because it lets every claim the system makes be checked against a known-correct answer (e.g., a group deliberately seeded so one vendor wins 85% of tenders should score HIGH concentration; a group with 6 vendors rotating evenly should score LOW).

Our test pyramid is structured to prove this:
- **Unit Tests**: Verify the pure mathematical scoring functions (HHI calculations handling exact numeric bounds and minimum-count gating, deviation scoring).
- **Extraction Tests**: Verify our PDF parser against sample documents with a field-by-field ground truth file (`sample_documents/ground_truth.md`).
- **Integration Tests**: Upload test documents and verify the resulting database side-effects and score changes are directionally correct.
- **Security Tests**: Validate file-type/size limits on uploads and assert that SQL injection payloads are neutralized by parameterized queries.

*What is and isn't proven*: The mathematical properties of HHI (bounded 0–10,000, monotonic in concentration) and of cosine similarity (bounded 0–1) are provable properties of the formulas themselves. Whether the system correctly flags real-world rigging is an empirical claim, validated here against seeded ground truth, not a mathematical proof.

## 5. Development Setup

Here is the exact command sequence to run the project locally.

```bash
# 1. Database
# (run db/schema.sql in your PostgreSQL / NeonDB SQL editor first)
export DATABASE_URL="postgresql+psycopg2://user:pass@host/dbname"
python db/seed_data.py

# 2. Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. Frontend
cd ../frontend
npm install
npm run dev

# 4. Tests
cd ../backend
pytest tests/ -v

# 5. Docker Compose (Alternative to manual setup)
# (Ensure your backend/.env file contains the DATABASE_URL)
docker compose up --build
```

## 6. Status

This project is a hackathon submission under active development. 

*Proven*: The core mathematical extraction, SQL aggregation scaling, and UI score separation work reliably and are thoroughly tested. 
*Open Questions*: Real-world small-sample HHI threshold tuning and embedding model finalization remain documented open areas for future iteration.
