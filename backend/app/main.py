import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import init_db, SessionLocal
from app.api import api_router
from app.scheduler import start_scheduler, stop_scheduler
from app.models import Account, Approval
from app.api.demo import seed_demo_environment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cloudoptima")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing CloudOptima database schema...")
    init_db()

    # If in demo mode and database is empty, automatically seed initial state
    if settings.DEMO_MODE:
        db = SessionLocal()
        try:
            account_count = db.query(Account).count()
            approval_count = db.query(Approval).count()
            if account_count == 0 or approval_count == 0:
                logger.info("Initializing multi-cloud fleet, findings, approvals, and remediation history...")
                seed_demo_environment(db)
        except Exception as e:
            logger.warning(f"Could not auto-seed data: {e}")
        finally:
            db.close()

    # Start background scanner
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    logger.info("CloudOptima shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-Cloud Cost Optimization & Risk Governance Pipeline",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health Check
@app.get("/health")
def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME, "version": settings.VERSION}

# Mount static files and 7 layer web pages
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_root():
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/layer1", include_in_schema=False)
    def serve_layer1():
        f = os.path.join(static_dir, "layer1.html")
        if not os.path.exists(f):
            f = os.path.join(static_dir, "index.html")
        return FileResponse(f)

    @app.get("/layer2", include_in_schema=False)
    def serve_layer2():
        return FileResponse(os.path.join(static_dir, "layer2.html"))

    @app.get("/layer3", include_in_schema=False)
    def serve_layer3():
        return FileResponse(os.path.join(static_dir, "layer3.html"))

    @app.get("/layer4", include_in_schema=False)
    def serve_layer4():
        return FileResponse(os.path.join(static_dir, "layer4.html"))

    @app.get("/layer5", include_in_schema=False)
    def serve_layer5():
        return FileResponse(os.path.join(static_dir, "layer5.html"))

    @app.get("/layer6", include_in_schema=False)
    def serve_layer6():
        return FileResponse(os.path.join(static_dir, "layer6.html"))

    @app.get("/layer7", include_in_schema=False)
    def serve_layer7():
        return FileResponse(os.path.join(static_dir, "layer7.html"))

    @app.get("/doc", include_in_schema=False)
    def serve_doc():
        return FileResponse(os.path.join(static_dir, "CloudOptima_Architecture_Design_Document.html"))

    @app.get("/presentation", include_in_schema=False)
    def serve_presentation():
        return FileResponse(os.path.join(static_dir, "CloudOptima_Presentation.html"))

    @app.get("/download/docx", include_in_schema=False)
    def download_docx():
        f = os.path.join(static_dir, "CloudOptima_Architecture_Design_Document.docx")
        return FileResponse(f, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="CloudOptima_Architecture_Design_Document.docx")

    @app.get("/download/pptx", include_in_schema=False)
    def download_pptx():
        f = os.path.join(static_dir, "CloudOptima_Project_Presentation.pptx")
        return FileResponse(f, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename="CloudOptima_Project_Presentation.pptx")
