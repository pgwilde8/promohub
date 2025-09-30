"""
Enhanced Enrichment Service with Instant Outreach Integration

This service enriches leads and automatically triggers instant outreach emails
when new verified email addresses are discovered.
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.enrichment_service import HunterEnrichmentService
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class EnhancedEnrichmentService(HunterEnrichmentService):
    """Enhanced enrichment service that triggers instant outreach"""
    
    async def update_lead_with_enrichment_simple(self, lead_id: int, email: str) -> bool:
        """Update lead with email using current database schema"""
        try:
            # Check if this lead already has a manually added email
            lead_check = self.db.execute(
                text("SELECT email, lead_source FROM leads WHERE id = :lead_id"),
                {"lead_id": lead_id}
            ).fetchone()
            
            # Only update email if it's appropriate
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
                    return True  # Success but no update needed
            
            if should_update_email:
                # Simple update that works with current schema
                update_query = text("UPDATE leads SET email = :email WHERE id = :lead_id")
                
                self.db.execute(update_query, {
                    "email": email,
                    "lead_id": lead_id
                })
                
                self.db.commit()
                logger.info(f"✅ Updated lead {lead_id} with email: {email}")
                
                # Trigger instant outreach
                await self.trigger_instant_outreach(lead_id, email)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating lead {lead_id}: {str(e)}")
            self.db.rollback()
            return False
    
    async def trigger_instant_outreach(self, lead_id: int, email: str):
        """Trigger instant outreach for newly discovered email"""
        try:
            # Get lead details
            result = self.db.execute(text("SELECT name, domain FROM leads WHERE id = :id"), {"id": lead_id})
            lead_data = result.fetchone()
            
            if not lead_data:
                logger.error(f"Lead {lead_id} not found")
                return
            
            name, domain = lead_data
            
            logger.info(f"🚀 TRIGGERING INSTANT OUTREACH for {email}")
            
            # Import and use instant outreach service
            from app.services.instant_outreach import InstantOutreachService
            
            outreach_service = InstantOutreachService()
            success = await outreach_service.send_instant_outreach(
                lead_id=lead_id,
                email=email,
                domain=domain,
                name=name
            )
            
            if success:
                logger.info(f"✅ Instant outreach sent to {email}")
            else:
                logger.error(f"❌ Failed to send instant outreach to {email}")
                
        except Exception as e:
            logger.error(f"❌ Error triggering instant outreach: {str(e)}")
    
    async def enrich_domain_with_outreach(self, lead_id: int, domain: str) -> bool:
        """Enrich a domain and trigger instant outreach if successful"""
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
            
            # Find the best email
            best_email = self.select_best_email(emails)
            
            if not best_email:
                logger.info(f"No suitable emails found for domain: {domain}")
                return False
            
            # Update lead with simple schema and trigger outreach
            success = await self.update_lead_with_enrichment_simple(
                lead_id, 
                best_email['value']
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error enriching domain {domain} with outreach: {str(e)}")
            return False


async def run_enhanced_enrichment_job():
    """Enhanced enrichment job with instant outreach"""
    logger.info("🚀 Starting enhanced enrichment with instant outreach...")
    
    try:
        db = SessionLocal()
        service = EnhancedEnrichmentService(db)
        
        # Get leads that need enrichment
        result = db.execute(text("""
            SELECT id, domain, name
            FROM leads 
            WHERE domain IS NOT NULL 
            AND email LIKE 'unknown@%'
            ORDER BY created_at ASC
            LIMIT 10
        """))
        
        leads = result.fetchall()
        
        if not leads:
            logger.info("No leads found that need enrichment")
            return {"processed": 0, "enriched": 0}
        
        logger.info(f"Processing {len(leads)} leads for enhanced enrichment...")
        
        enriched_count = 0
        
        for lead in leads:
            lead_id, domain, name = lead
            logger.info(f"🎯 Processing: {domain}")
            
            # Add delay between requests
            await asyncio.sleep(1)
            
            # Enrich with instant outreach
            success = await service.enrich_domain_with_outreach(lead_id, domain)
            if success:
                enriched_count += 1
                logger.info(f"✅ Enriched and triggered outreach for {domain}")
            
            # Check rate limit
            if not await service.check_rate_limit():
                logger.warning("Rate limit reached")
                break
        
        result = {
            "processed": len(leads),
            "enriched": enriched_count,
            "outreach_triggered": enriched_count
        }
        
        logger.info(f"Enhanced enrichment complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Enhanced enrichment job failed: {str(e)}")
        return {"error": str(e)}
    finally:
        await service.client.aclose()
        db.close()


# Manual test function
async def test_enhanced_enrichment():
    """Test enhanced enrichment with one domain"""
    logger.info("🧪 Testing enhanced enrichment with instant outreach...")
    
    try:
        db = SessionLocal()
        service = EnhancedEnrichmentService(db)
        
        # Test with one of our pending domains
        test_lead_id = 13  # coaching-sa.com
        test_domain = "coaching-sa.com"
        
        success = await service.enrich_domain_with_outreach(test_lead_id, test_domain)
        
        logger.info(f"Test result: {'Success' if success else 'Failed'}")
        return success
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False
    finally:
        await service.client.aclose()
        db.close()


if __name__ == "__main__":
    # Test the enhanced enrichment
    asyncio.run(test_enhanced_enrichment())