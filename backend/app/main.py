import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tenders, upload, batch

app = FastAPI(title="Spasht - Tender Red-Flag Detector")

# Get allowed origin from environment variable, fallback to local dev URLs
allowed_origin = os.environ.get("CORS_ALLOWED_ORIGIN")
origins = [allowed_origin] if allowed_origin else [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "https://spasht-kappa.vercel.app",
    "http://spasht-kappa.vercel.app"
]

# Restrict CORS to actual frontend origin and explicit Vercel preview URL regex
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://spasht-kappa-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenders.router, prefix="/api/tenders", tags=["Tenders"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(batch.router, prefix="/api/scan-batch", tags=["Batch"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
