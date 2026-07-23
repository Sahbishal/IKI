import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "False"

"""
Industrial Knowledge Intelligence — FastAPI Backend
Main application entrypoint
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from core.database import init_db
from core.vectorstore import init_vectorstore
from core.knowledge_graph import knowledge_graph
from routers import upload, chat, documents, graph, reports, dashboard

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("./chroma_db", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifecycle"""
    logger.info("🚀 Starting Industrial Knowledge Intelligence...")
    await init_db()
    init_vectorstore()
    knowledge_graph.load()
    logger.info("✅ All systems initialized")
    yield
    knowledge_graph.save()
    logger.info("💾 Knowledge graph saved. Shutting down.")


app = FastAPI(
    title="Industrial Knowledge Intelligence API",
    description="AI-powered industrial asset & operations brain",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Register routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(graph.router, prefix="/api/graph", tags=["Knowledge Graph"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


@app.get("/")
async def root():
    return {
        "name": "Industrial Knowledge Intelligence",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "IKI Backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
