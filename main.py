from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings
from app.core.database import engine, Base
from app.routes import dashboard, api, leads, blog
from app.routes.enrichment import router as enrichment_router
from app.bots.scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app startup and shutdown"""
    # Startup
    print("🚀 Starting PromoHub...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Start background scheduler
    start_scheduler()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down PromoHub...")
    shutdown_scheduler()


# Initialize FastAPI app
app = FastAPI(
    title="PromoHub",
    description="Self-hosted marketing automation hub",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(dashboard.router, prefix="", tags=["dashboard"])
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(leads.router, prefix="/leads", tags=["leads"])
app.include_router(blog.router, prefix="/blog", tags=["blog"])
app.include_router(enrichment_router, tags=["enrichment"])


@app.get("/")
async def root(request: Request):
    """Home page"""
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "title": "PromoHub Dashboard"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PromoHub"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )