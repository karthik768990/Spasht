import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tenders, upload, batch
from .services.file_service import cleanup_old_pdfs

async def cleanup_task():
    """Background task to periodically clean up abandoned PDF files."""
    while True:
        try:
            # Run the synchronous file IO function in a thread to prevent blocking
            await asyncio.to_thread(cleanup_old_pdfs, 1.0)
        except Exception as e:
            print(f"Error in cleanup task: {e}")
        # Run every 1 hour
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background cleanup task
    task = asyncio.create_task(cleanup_task())
    yield
    # Shutdown: Cancel the task
    task.cancel()

app = FastAPI(title="Spasht - Tender Red-Flag Detector", lifespan=lifespan)

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
