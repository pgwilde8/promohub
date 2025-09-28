from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.base import Content, SocialLog
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def blog_index(request: Request, db: Session = Depends(get_db)):
    """Public blog index page"""
    
    # Get published blog posts
    posts = db.query(Content).filter(
        Content.status == "published"
    ).order_by(Content.published_at.desc()).all()
    
    return templates.TemplateResponse(
        "blog_index.html",
        {"request": request, "posts": posts}
    )


@router.get("/{slug}")
async def blog_post(request: Request, slug: str, db: Session = Depends(get_db)):
    """Individual blog post page"""
    
    post = db.query(Content).filter(
        Content.slug == slug,
        Content.status == "published"
    ).first()
    
    if not post:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )
    
    return templates.TemplateResponse(
        "blog_post.html",
        {"request": request, "post": post}
    )


@router.get("/admin/content")
async def admin_content_list(request: Request, db: Session = Depends(get_db)):
    """Admin content management page"""
    
    content = db.query(Content).order_by(Content.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "admin_content.html",
        {"request": request, "content": content}
    )


@router.get("/admin/content/{content_id}")
async def admin_content_detail(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db)
):
    """Admin content detail and social sharing stats"""
    
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )
    
    # Get social media posts for this content
    social_posts = db.query(SocialLog).filter(
        SocialLog.content_id == content_id
    ).order_by(SocialLog.posted_at.desc()).all()
    
    return templates.TemplateResponse(
        "admin_content_detail.html",
        {
            "request": request,
            "content": content,
            "social_posts": social_posts
        }
    )