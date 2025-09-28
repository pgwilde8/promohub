from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.base import Lead, PageView
from app.bots.outreach_bot import OutreachBot
from pydantic import BaseModel, EmailStr
import uuid

router = APIRouter()


class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    source: str = "api"
    platform: str = None
    company: str = None
    url: str = None


class ChatMessage(BaseModel):
    message: str
    email: EmailStr = None
    name: str = None


@router.post("/leads")
async def create_lead_api(lead: LeadCreate, db: Session = Depends(get_db)):
    """API endpoint to create a new lead"""
    
    # Check if email already exists
    existing_lead = db.query(Lead).filter(Lead.email == lead.email).first()
    if existing_lead:
        return JSONResponse(
            content={"message": "Lead already exists", "lead_id": existing_lead.id},
            status_code=200
        )
    
    new_lead = Lead(
        name=lead.name,
        email=lead.email,
        source=lead.source,
        platform=lead.platform,
        company=lead.company,
        url=lead.url,
        status="new"
    )
    
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    return JSONResponse(
        content={"message": "Lead created successfully", "lead_id": new_lead.id},
        status_code=201
    )


@router.post("/demo-bot")
async def demo_chat_bot(
    message: ChatMessage,
    request: Request,
    db: Session = Depends(get_db)
):
    """Demo chat bot endpoint - captures emails and answers basic questions"""
    
    # Simple FAQ responses (in production, use OpenAI API)
    responses = {
        "pricing": "Our pricing starts at $29/month for basic features. Visit /pricing for detailed plans.",
        "features": "We offer lead generation, email automation, content creation, and social media management.",
        "demo": "You can book a demo at /demo or contact us at demo@promohub.com",
        "support": "For support, reach out to support@promohub.com or use our live chat.",
        "contact": "Contact us at hello@promohub.com or call (555) 123-4567"
    }
    
    # Simple keyword matching
    response_text = "Thank you for your message! "
    message_lower = message.message.lower()
    
    for keyword, response in responses.items():
        if keyword in message_lower:
            response_text += response
            break
    else:
        response_text += "I'd love to help you learn more about PromoHub. Can I get your email so our team can follow up with detailed information?"
    
    # If email is provided, save as lead
    lead_id = None
    if message.email:
        existing_lead = db.query(Lead).filter(Lead.email == message.email).first()
        if not existing_lead:
            new_lead = Lead(
                name=message.name or "Demo User",
                email=message.email,
                source="demo_chat",
                platform="promohub",
                status="new"
            )
            db.add(new_lead)
            db.commit()
            db.refresh(new_lead)
            lead_id = new_lead.id
            response_text += " Thanks for providing your email - our team will be in touch soon!"
    
    return JSONResponse(content={
        "response": response_text,
        "lead_captured": lead_id is not None,
        "lead_id": lead_id
    })


@router.post("/track-page-view")
async def track_page_view(
    request: Request,
    db: Session = Depends(get_db)
):
    """Track page views for retargeting"""
    
    # Get request data
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    referrer = request.headers.get("referer", "")
    
    # Generate session ID if not provided
    session_id = str(uuid.uuid4())
    
    # Get page from request body or query params
    body = await request.json()
    page = body.get("page", "/")
    
    # Determine if it's a pricing or signup page
    is_pricing = "pricing" in page.lower()
    is_signup = "signup" in page.lower() or "register" in page.lower()
    
    # Create page view record
    page_view = PageView(
        page=page,
        session_id=session_id,
        ip_address=client_ip,
        user_agent=user_agent,
        referrer=referrer,
        is_pricing_page=is_pricing,
        is_signup_page=is_signup
    )
    
    db.add(page_view)
    db.commit()
    
    return JSONResponse(content={
        "status": "tracked",
        "session_id": session_id,
        "retarget_eligible": is_pricing and not is_signup
    })


@router.post("/trigger-outreach/{lead_id}")
async def trigger_manual_outreach(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Manually trigger outreach for a specific lead"""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Initialize outreach bot and send email
    outreach_bot = OutreachBot(db)
    try:
        success = await outreach_bot.send_personalized_email(lead)
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": f"Outreach email sent to {lead.email}"
            })
        else:
            return JSONResponse(content={
                "status": "error",
                "message": "Failed to send outreach email"
            }, status_code=500)
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        }, status_code=500)


@router.get("/health")
async def health_check():
    """API health check"""
    return {"status": "healthy", "service": "PromoHub API"}