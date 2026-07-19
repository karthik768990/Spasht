from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tenders, upload, batch

app = FastAPI(title="Spasht - Tender Red-Flag Detector")

# Restrict CORS to actual frontend origin (e.g. localhost:5173 for Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173","https://spasht-kappa.vercel.app/","http://spasht-kappa.vercel.app/"],
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
