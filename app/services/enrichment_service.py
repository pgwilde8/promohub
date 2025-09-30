"""
Hunter.io Lead Enrichment Service

This service integrates with Hunter.io API to enrich lead data with email addresses,
organization information, and verification scores.
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class HunterEnrichmentService:
    """Service for enriching leads using Hunter.io API"""
    
    def __init__(self, db_session: Session = None):
        self.api_key = settings.hunter_api_key
        self.api_base_url = "https://api.hunter.io/v2"
        self.db = db_session or SessionLocal()
        self.rate_limit_per_day = settings.hunter_rate_limit_per_day
        self.min_confidence_score = settings.hunter_min_confidence
        
        # HTTP client with timeout and retry settings
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        if not self.db.bind.pool.checkedout():
            self.db.close()
    
    async def check_rate_limit(self) -> bool:
        """Check if we've hit our daily rate limit"""
        try:
            today = datetime.now().date()
            
            # Count enrichments made today
            result = self.db.execute(text("""
                SELECT COUNT(*) as count 
                FROM hunter_log 
                WHERE DATE(created_at) = :today
            """), {"today": today})
            
            count = result.scalar() or 0
            
            if count >= self.rate_limit_per_day:
                logger.warning(f"Hunter.io rate limit reached: {count}/{self.rate_limit_per_day} for {today}")
                return False
                
            logger.info(f"Hunter.io usage: {count}/{self.rate_limit_per_day} for {today}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True  # Allow on error to prevent blocking
    
    async def domain_search(self, domain: str) -> Dict[str, Any]:
        """Search for email addresses associated with a domain"""
        if not self.api_key:
            raise ValueError("Hunter.io API key not configured")
        
        url = f"{self.api_base_url}/domain-search"
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "limit": 10,  # Limit results to control API usage
            "type": "personal"  # Focus on personal emails, not generic ones
        }
        
        try:
            logger.info(f"Searching domain: {domain}")
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("errors"):
                logger.error(f"Hunter.io API errors for {domain}: {data['errors']}")
                return {"emails": [], "error": data["errors"]}
            
            # Log the API call
            await self.log_hunter_request(domain, len(data.get("data", {}).get("emails", [])))
            
            return data.get("data", {})
            
        except httpx.TimeoutException:
            logger.error(f"Hunter.io API timeout for domain: {domain}")
            return {"emails": [], "error": "API timeout"}
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Hunter.io API HTTP error for {domain}: {e.response.status_code}")
            return {"emails": [], "error": f"HTTP {e.response.status_code}"}
            
        except Exception as e:
            logger.error(f"Hunter.io API error for {domain}: {str(e)}")
            return {"emails": [], "error": str(e)}
    
    async def email_verifier(self, email: str) -> Dict[str, Any]:
        """Verify a single email address"""
        if not self.api_key:
            raise ValueError("Hunter.io API key not configured")
        
        url = f"{self.api_base_url}/email-verifier"
        params = {
            "email": email,
            "api_key": self.api_key
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", {})
            
        except Exception as e:
            logger.error(f"Email verification error for {email}: {str(e)}")
            return {"result": "unknown", "score": 0}
    
    async def enrich_domain(self, lead_id: int, domain: str) -> bool:
        """Enrich a single lead with domain information"""
        try:
            # Get domain search results
            domain_data = await self.domain_search(domain)
            
            if domain_data.get("error"):
                logger.warning(f"Skipping domain {domain}: {domain_data['error']}")
                return False
            
            emails = domain_data.get("emails", [])
            if not emails:
                logger.info(f"No emails found for domain: {domain}")
                return False
            
            # Find the best email (highest confidence, verified if possible)
            best_email = self.select_best_email(emails)
            
            if not best_email:
                logger.info(f"No suitable emails found for domain: {domain}")
                return False
            
            # Update the lead record
            await self.update_lead_with_enrichment(lead_id, domain, best_email, domain_data)
            
            logger.info(f"Successfully enriched lead {lead_id} with email: {best_email['value']}")
            return True
            
        except Exception as e:
            logger.error(f"Error enriching domain {domain}: {str(e)}")
            return False
    
    def select_best_email(self, emails: List[Dict]) -> Optional[Dict]:
        """Select the best email from Hunter.io results"""
        if not emails:
            return None
        
        # Filter by minimum confidence score
        qualified_emails = [
            email for email in emails 
            if email.get("confidence", 0) >= self.min_confidence_score
        ]
        
        if not qualified_emails:
            logger.info("No emails meet minimum confidence threshold")
            return None
        
        # Sort by confidence (desc), then by verification status
        def email_score(email):
            confidence = email.get("confidence", 0)
            verification = email.get("verification", {}).get("result", "unknown")
            
            # Bonus points for verified emails
            verification_bonus = 10 if verification == "deliverable" else 0
            
            return confidence + verification_bonus
        
        return max(qualified_emails, key=email_score)
    
    async def update_lead_with_enrichment(self, lead_id: int, domain: str, email_data: Dict, domain_info: Dict):
        """Update lead record with enriched data"""
        try:
            sources = email_data.get("sources", [])
            source_url = sources[0].get("uri") if sources else None
            
            # Check if this lead already has a manually added email
            lead_check = self.db.execute(
                text("SELECT email, lead_source FROM leads WHERE id = :lead_id"),
                {"lead_id": lead_id}
            ).fetchone()
            
            # Only overwrite email if it's from domain scraping or if current email is placeholder
            should_update_email = False
            if lead_check:
                current_email = lead_check[0]
                lead_source = lead_check[1]
                
                # Update email if:
                # 1. Current email is a placeholder (unknown@domain.com)
                # 2. Lead source is from domain scraping
                # 3. Current email is null/empty
                if (current_email and "unknown@" in current_email) or \
                   (lead_source and "domain_scraping" in lead_source) or \
                   not current_email:
                    should_update_email = True
                    logger.info(f"✅ Updating email for lead {lead_id} (source: {lead_source}, current: {current_email})")
                else:
                    logger.info(f"🛡️ Preserving manual email for lead {lead_id} (source: {lead_source}, current: {current_email})")
            
            # Build dynamic update query based on whether we should update email
            if should_update_email:
                update_query = text("""
                    UPDATE leads 
                    SET 
                        email = :email,
                        organization = :organization,
                        type = :type,
                        confidence = :confidence,
                        source_url = :source_url,
                        verified = :verified,
                        enriched_at = NOW(),
                        hunter_data = :hunter_data
                    WHERE id = :lead_id
                """)
            else:
                # Update everything except email
                update_query = text("""
                    UPDATE leads 
                    SET 
                        organization = :organization,
                        type = :type,
                        confidence = :confidence,
                        source_url = :source_url,
                        verified = :verified,
                        enriched_at = NOW(),
                        hunter_data = :hunter_data
                    WHERE id = :lead_id
                """)
            
            # Prepare parameters based on whether we're updating email
            params = {
                "organization": domain_info.get("organization"),
                "type": email_data.get("type"),
                "confidence": email_data.get("confidence"),
                "source_url": source_url,
                "verified": email_data.get("confidence", 0) >= 70,
                "hunter_data": str(email_data),  # Store full data as JSON string
                "lead_id": lead_id
            }
            
            # Only add email parameter if we're updating it
            if should_update_email:
                params["email"] = email_data.get("value")
            
            self.db.execute(update_query, params)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating lead {lead_id}: {str(e)}")
            self.db.rollback()
            raise
    
    async def log_hunter_request(self, domain: str, emails_found: int):
        """Log Hunter.io API request for rate limiting and analytics"""
        try:
            insert_query = text("""
                INSERT INTO hunter_log (domain, emails_found, created_at)
                VALUES (:domain, :emails_found, NOW())
            """)
            
            self.db.execute(insert_query, {
                "domain": domain,
                "emails_found": emails_found
            })
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging Hunter request for {domain}: {str(e)}")
            # Don't raise - logging failure shouldn't stop enrichment
    
    async def enrich_pending_leads(self, batch_size: int = 10) -> Dict[str, int]:
        """Process a batch of leads that need enrichment"""
        if not await self.check_rate_limit():
            return {"processed": 0, "enriched": 0, "skipped": 1}
        
        try:
            # Get leads that need enrichment (placeholder emails starting with "unknown@")
            query = text("""
                SELECT id, domain 
                FROM leads 
                WHERE domain IS NOT NULL 
                  AND (email LIKE 'unknown@%' OR email IS NULL)
                  AND enriched_at IS NULL
                ORDER BY created_at ASC
                LIMIT :batch_size
            """)
            
            result = self.db.execute(query, {"batch_size": batch_size})
            leads = result.fetchall()
            
            if not leads:
                logger.info("No leads found that need enrichment")
                return {"processed": 0, "enriched": 0, "skipped": 0}
            
            logger.info(f"Processing {len(leads)} leads for enrichment")
            
            enriched_count = 0
            
            for lead in leads:
                # Add delay between requests to be respectful to the API
                await asyncio.sleep(1)
                
                success = await self.enrich_domain(lead.id, lead.domain)
                if success:
                    enriched_count += 1
                
                # Check rate limit after each request
                if not await self.check_rate_limit():
                    logger.warning("Rate limit reached during batch processing")
                    break
            
            result = {
                "processed": len(leads),
                "enriched": enriched_count,
                "skipped": len(leads) - enriched_count
            }
            
            logger.info(f"Enrichment batch complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in batch enrichment: {str(e)}")
            return {"processed": 0, "enriched": 0, "skipped": 0, "error": str(e)}
    
    async def get_enrichment_stats(self) -> Dict[str, Any]:
        """Get enrichment statistics"""
        try:
            # Total leads by status
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_leads,
                    COUNT(CASE WHEN email NOT LIKE 'unknown@%' AND email IS NOT NULL THEN 1 END) as enriched_leads,
                    COUNT(CASE WHEN domain IS NOT NULL AND (email LIKE 'unknown@%' OR email IS NULL) THEN 1 END) as pending_enrichment,
                    COUNT(CASE WHEN verified = true THEN 1 END) as verified_leads,
                    AVG(CASE WHEN confidence IS NOT NULL THEN confidence END) as avg_confidence
                FROM leads
            """)
            
            result = self.db.execute(stats_query).fetchone()
            
            # Today's activity
            today_query = text("""
                SELECT 
                    COUNT(*) as requests_today,
                    SUM(emails_found) as emails_found_today
                FROM hunter_log 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            
            today_result = self.db.execute(today_query).fetchone()
            
            return {
                "total_leads": result.total_leads,
                "enriched_leads": result.enriched_leads,
                "pending_enrichment": result.pending_enrichment,
                "verified_leads": result.verified_leads,
                "avg_confidence": float(result.avg_confidence or 0),
                "enrichment_rate": (result.enriched_leads / result.total_leads * 100) if result.total_leads > 0 else 0,
                "requests_today": today_result.requests_today or 0,
                "emails_found_today": today_result.emails_found_today or 0,
                "rate_limit_remaining": self.rate_limit_per_day - (today_result.requests_today or 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting enrichment stats: {str(e)}")
            return {}


# Standalone function for scheduled execution
async def run_enrichment_job():
    """Main function to run lead enrichment job"""
    logger.info("Starting Hunter.io enrichment job...")
    
    try:
        async with HunterEnrichmentService() as service:
            result = await service.enrich_pending_leads()
            
            logger.info(f"Enrichment job completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Enrichment job failed: {str(e)}")
        return {"error": str(e)}


# Manual functions for testing
async def enrich_single_domain(domain: str) -> Dict:
    """Manually enrich a single domain for testing"""
    async with HunterEnrichmentService() as service:
        domain_data = await service.domain_search(domain)
        return domain_data


async def get_stats() -> Dict:
    """Get enrichment statistics"""
    async with HunterEnrichmentService() as service:
        return await service.get_enrichment_stats()