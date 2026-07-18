from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tenders, upload

app = FastAPI(title="Spasht - Tender Red-Flag Detector")

# Restrict CORS to actual frontend origin (e.g. localhost:5173 for Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenders.router, prefix="/api/tenders", tags=["Tenders"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
