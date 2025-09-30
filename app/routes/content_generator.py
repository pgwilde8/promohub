"""
Content Generator API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.enhanced_content_generator import EnhancedContentGenerator
from app.services.social_media_distributor import SocialMediaDistributor

router = APIRouter()


class BlogGenerationRequest(BaseModel):
    keywords: List[str]
    product_focus: str = "general"  # ezclub, ezdirectory, general
    content_type: str = "blog_post"
    target_audience: Optional[str] = None
    word_count: int = 1000


class SocialDistributionRequest(BaseModel):
    content_id: int
    platforms: List[str] = ["twitter", "linkedin", "facebook"]
    schedule_delay_hours: int = 2


@router.post("/generate-blog")
async def generate_blog_from_keywords(
    request: BlogGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate a blog post from keywords"""
    
    try:
        generator = EnhancedContentGenerator(db)
        
        result = await generator.generate_blog_from_keywords(
            keywords=request.keywords,
            product_focus=request.product_focus,
            content_type=request.content_type,
            target_audience=request.target_audience,
            word_count=request.word_count
        )
        
        if result["success"]:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "Blog post generated successfully",
                    "data": result
                },
                status_code=201
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "Failed to generate blog post",
                    "error": result.get("error", "Unknown error")
                },
                status_code=400
            )
            
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            },
            status_code=500
        )


@router.post("/generate-blog-simple")
async def generate_blog_simple(
    keywords: str = Form(...),
    product_focus: str = Form("general"),
    db: Session = Depends(get_db)
):
    """Simple form-based blog generation"""
    
    try:
        # Parse keywords from comma-separated string
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        
        generator = EnhancedContentGenerator(db)
        
        result = await generator.generate_blog_from_keywords(
            keywords=keyword_list,
            product_focus=product_focus
        )
        
        if result["success"]:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "Blog post generated successfully",
                    "data": result
                },
                status_code=201
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "Failed to generate blog post",
                    "error": result.get("error", "Unknown error")
                },
                status_code=400
            )
            
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            },
            status_code=500
        )


@router.post("/process-social")
async def process_content_for_social(
    request: SocialDistributionRequest,
    db: Session = Depends(get_db)
):
    """Process blog content for social media distribution"""
    
    try:
        distributor = SocialMediaDistributor(db)
        
        result = await distributor.process_content_for_social(
            content_id=request.content_id,
            platforms=request.platforms
        )
        
        if result["success"]:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "Social media content processed successfully",
                    "data": result
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "Failed to process social content",
                    "error": result.get("error", "Unknown error")
                },
                status_code=400
            )
            
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            },
            status_code=500
        )


@router.post("/schedule-social")
async def schedule_social_posts(
    request: SocialDistributionRequest,
    db: Session = Depends(get_db)
):
    """Schedule social media posts"""
    
    try:
        distributor = SocialMediaDistributor(db)
        
        result = await distributor.schedule_social_posts(
            content_id=request.content_id,
            platforms=request.platforms,
            schedule_delay_hours=request.schedule_delay_hours
        )
        
        if result["success"]:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "Social media posts scheduled successfully",
                    "data": result
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "Failed to schedule social posts",
                    "error": result.get("error", "Unknown error")
                },
                status_code=400
            )
            
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            },
            status_code=500
        )


@router.get("/content-calendar")
async def get_content_calendar(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get content calendar with keyword suggestions"""
    
    try:
        generator = EnhancedContentGenerator(db)
        calendar = await generator.generate_content_calendar(days=days)
        
        return JSONResponse(
            content={
                "success": True,
                "data": calendar
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Failed to generate content calendar",
                "error": str(e)
            },
            status_code=500
        )


@router.get("/social-analytics/{content_id}")
async def get_social_analytics(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Get social media analytics for a specific content"""
    
    try:
        distributor = SocialMediaDistributor(db)
        analytics = await distributor.get_social_analytics(content_id)
        
        return JSONResponse(
            content={
                "success": True,
                "data": analytics
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Failed to get social analytics",
                "error": str(e)
            },
            status_code=500
        )


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported social media platforms"""
    
    platforms = {
        "twitter": {
            "name": "Twitter/X",
            "max_length": 280,
            "hashtag_limit": 2,
            "best_for": "Quick updates, news, engagement"
        },
        "linkedin": {
            "name": "LinkedIn",
            "max_length": 3000,
            "hashtag_limit": 5,
            "best_for": "Professional content, B2B, thought leadership"
        },
        "facebook": {
            "name": "Facebook",
            "max_length": 63206,
            "hashtag_limit": 3,
            "best_for": "Community engagement, longer content, visual posts"
        },
        "instagram": {
            "name": "Instagram",
            "max_length": 2200,
            "hashtag_limit": 30,
            "best_for": "Visual content, lifestyle, creative posts"
        }
    }
    
    return JSONResponse(
        content={
            "success": True,
            "data": platforms
        },
        status_code=200
    )


@router.post("/generate-and-distribute")
async def generate_and_distribute(
    keywords: str = Form(...),
    product_focus: str = Form("general"),
    platforms: str = Form("twitter,linkedin,facebook"),
    db: Session = Depends(get_db)
):
    """Generate blog post and immediately process for social media"""
    
    try:
        # Parse inputs
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        platform_list = [p.strip() for p in platforms.split(',') if p.strip()]
        
        # Generate blog post
        generator = EnhancedContentGenerator(db)
        blog_result = await generator.generate_blog_from_keywords(
            keywords=keyword_list,
            product_focus=product_focus
        )
        
        if not blog_result["success"]:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "Failed to generate blog post",
                    "error": blog_result.get("error", "Unknown error")
                },
                status_code=400
            )
        
        # Process for social media
        distributor = SocialMediaDistributor(db)
        social_result = await distributor.process_content_for_social(
            content_id=blog_result["content_id"],
            platforms=platform_list
        )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "Blog post generated and social content created",
                "data": {
                    "blog": blog_result,
                    "social": social_result
                }
            },
            status_code=201
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            },
            status_code=500
        )
