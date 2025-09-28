from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.base import Lead, OutreachLog, Content, SocialLog, PageView

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main admin dashboard"""
    
    # Get dashboard statistics
    total_leads = db.query(Lead).count()
    new_leads = db.query(Lead).filter(Lead.status == "new").count()
    total_outreach = db.query(OutreachLog).count()
    published_content = db.query(Content).filter(Content.status == "published").count()
    
    # Recent activity
    recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()
    recent_outreach = db.query(OutreachLog).order_by(OutreachLog.sent_at.desc()).limit(5).all()
    
    # Email stats
    email_stats = db.query(
        OutreachLog.status,
        func.count(OutreachLog.id)
    ).group_by(OutreachLog.status).all()
    
    stats = {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "total_outreach": total_outreach,
        "published_content": published_content,
        "recent_leads": recent_leads,
        "recent_outreach": recent_outreach,
        "email_stats": dict(email_stats)
    }
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "stats": stats}
    )


@router.get("/analytics")
async def analytics(request: Request, db: Session = Depends(get_db)):
    """Analytics and reporting page"""
    
    # Lead source breakdown
    lead_sources = db.query(
        Lead.source,
        func.count(Lead.id)
    ).group_by(Lead.source).all()
    
    # Content performance
    content_performance = db.query(Content).filter(
        Content.status == "published"
    ).order_by(Content.published_at.desc()).all()
    
    # Social media performance
    social_stats = db.query(
        SocialLog.platform,
        func.count(SocialLog.id),
        func.sum(SocialLog.engagement_likes)
    ).group_by(SocialLog.platform).all()
    
    analytics_data = {
        "lead_sources": dict(lead_sources),
        "content_performance": content_performance,
        "social_stats": social_stats
    }
    
    return templates.TemplateResponse(
        "analytics.html",
        {"request": request, "analytics": analytics_data}
    )