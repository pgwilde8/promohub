"""
API endpoints for Hunter.io lead enrichment
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.enrichment_service import HunterEnrichmentService, run_enrichment_job

router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])


@router.get("/stats")
async def get_enrichment_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get enrichment statistics and status"""
    try:
        async with HunterEnrichmentService(db) as service:
            stats = await service.get_enrichment_stats()
            return {
                "success": True,
                "data": stats
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.post("/run")
async def trigger_enrichment(
    background_tasks: BackgroundTasks,
    batch_size: int = 10,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Manually trigger lead enrichment job"""
    try:
        # Run enrichment in background
        background_tasks.add_task(run_enrichment_job)
        
        return {
            "success": True,
            "message": f"Enrichment job started in background with batch size {batch_size}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting enrichment: {str(e)}")


@router.post("/domain/{domain}")
async def enrich_domain(
    domain: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Test enrichment for a specific domain"""
    try:
        async with HunterEnrichmentService(db) as service:
            result = await service.domain_search(domain)
            
            return {
                "success": True,
                "domain": domain,
                "data": result
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching domain: {str(e)}")


@router.get("/pending")
async def get_pending_leads(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get leads that are pending enrichment"""
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT id, domain, created_at, status
            FROM leads 
            WHERE domain IS NOT NULL 
              AND email IS NULL 
              AND enriched_at IS NULL
            ORDER BY created_at ASC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"limit": limit})
        leads = [
            {
                "id": row.id,
                "domain": row.domain,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "status": row.status
            }
            for row in result.fetchall()
        ]
        
        return {
            "success": True,
            "count": len(leads),
            "leads": leads
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pending leads: {str(e)}")


@router.get("/history")
async def get_enrichment_history(
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recent enrichment history"""
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT domain, emails_found, created_at
            FROM hunter_log 
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"limit": limit})
        history = [
            {
                "domain": row.domain,
                "emails_found": row.emails_found,
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            for row in result.fetchall()
        ]
        
        return {
            "success": True,
            "count": len(history),
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")