from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models.base import Lead, OutreachLog
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def leads_list(
    request: Request,
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None
):
    """List all leads with filtering"""
    
    query = db.query(Lead)
    
    # Apply filters
    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    if search:
        query = query.filter(
            or_(
                Lead.name.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%"),
                Lead.company.ilike(f"%{search}%")
            )
        )
    
    leads = query.order_by(Lead.created_at.desc()).all()
    
    # Get unique sources and statuses for filter dropdowns
    sources = db.query(Lead.source).distinct().all()
    statuses = db.query(Lead.status).distinct().all()
    
    return templates.TemplateResponse(
        "leads.html",
        {
            "request": request,
            "leads": leads,
            "sources": [s[0] for s in sources if s[0]],
            "statuses": [s[0] for s in statuses if s[0]],
            "current_status": status,
            "current_source": source,
            "search_term": search
        }
    )


@router.get("/new")
async def new_lead_form(request: Request):
    """Show form to add new lead"""
    return templates.TemplateResponse(
        "lead_form.html",
        {"request": request, "lead": None}
    )


@router.post("/new")
async def create_lead(
    name: str = Form(...),
    email: str = Form(...),
    company: str = Form(None),
    phone: str = Form(None),
    source: str = Form("manual"),
    platform: str = Form(None),
    url: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new lead"""
    
    # Check if email already exists
    existing_lead = db.query(Lead).filter(Lead.email == email).first()
    if existing_lead:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    lead = Lead(
        name=name,
        email=email,
        company=company,
        phone=phone,
        source=source,
        platform=platform,
        url=url,
        notes=notes,
        status="new"
    )
    
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    return RedirectResponse(url="/leads", status_code=303)


@router.get("/{lead_id}")
async def lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Show detailed view of a lead"""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get outreach history
    outreach_history = db.query(OutreachLog).filter(
        OutreachLog.lead_id == lead_id
    ).order_by(OutreachLog.sent_at.desc()).all()
    
    return templates.TemplateResponse(
        "lead_detail.html",
        {
            "request": request,
            "lead": lead,
            "outreach_history": outreach_history
        }
    )


@router.get("/{lead_id}/edit")
async def edit_lead_form(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Show form to edit lead"""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return templates.TemplateResponse(
        "lead_form.html",
        {"request": request, "lead": lead}
    )


@router.post("/{lead_id}/edit")
async def update_lead(
    lead_id: int,
    name: str = Form(...),
    email: str = Form(...),
    company: str = Form(None),
    phone: str = Form(None),
    source: str = Form("manual"),
    platform: str = Form(None),
    url: str = Form(None),
    notes: str = Form(None),
    status: str = Form("new"),
    db: Session = Depends(get_db)
):
    """Update an existing lead"""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if email conflicts with another lead
    existing_lead = db.query(Lead).filter(
        Lead.email == email,
        Lead.id != lead_id
    ).first()
    if existing_lead:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Update lead
    lead.name = name
    lead.email = email
    lead.company = company
    lead.phone = phone
    lead.source = source
    lead.platform = platform
    lead.url = url
    lead.notes = notes
    lead.status = status
    
    db.commit()
    
    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)