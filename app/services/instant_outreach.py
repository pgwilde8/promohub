"""
Instant Outreach Service

Automatically sends personalized emails as soon as new creator emails are discovered
and enriched in the database. Triggered by database notifications.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

import asyncpg
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.bots.outreach_bot import OutreachBot

logger = logging.getLogger(__name__)


class InstantOutreachService:
    """Service for instant email outreach when new emails are discovered"""
    
    def __init__(self):
        self.db_url = settings.database_url
        self.connection = None
        self.running = False
        
        # Email templates for different creator types
        self.templates = {
            "coaching": {
                "subject": "Transform Your Coaching Community with EZClub",
                "body": """Hi {creator_name},

I discovered your coaching business at {domain} and was impressed by your work in the coaching space.

As a fellow entrepreneur in the creator economy, I wanted to share something that could transform how you build and monetize your coaching community.

EZClub is a platform specifically designed for coaches like you to:
• Build exclusive member communities around your expertise
• Create tiered membership levels with premium content
• Automate client onboarding and retention
• Generate recurring revenue from your coaching knowledge

Many coaches struggle with fragmented tools (Discord + Patreon + payment processors). EZClub consolidates everything into one professional platform.

Would you be interested in a 10-minute demo to see how coaches are building $10K+ monthly recurring revenue?

I can show you:
✓ How [specific coaching niche] coaches are using EZClub
✓ Community monetization strategies that work
✓ Integration with your existing coaching workflow

Available for a quick call this week?

Best regards,
[Your Name]
PromoHub Team

P.S. I can also share some case studies of coaching communities that grew 300% in their first 6 months on EZClub."""
            },
            
            "business": {
                "subject": "Grow Your Business Community with EZClub",
                "body": """Hi {creator_name},

I came across {domain} and was impressed by your business-focused content and community.

As someone building in the B2B space, I thought you'd be interested in how other business creators are monetizing their expertise through exclusive communities.

EZClub helps business leaders like you:
• Turn your knowledge into recurring revenue
• Build premium membership communities
• Scale your audience into paying customers
• Automate member management and engagement

The business creators seeing the biggest success are those who:
→ Create tiered membership levels ($50/month basic, $200/month premium)
→ Offer exclusive business insights and networking
→ Provide direct access for higher-tier members

Would a 15-minute demo be valuable to see how this could work for your business community?

I can show specific examples of business communities generating $15K+ monthly recurring revenue.

Available for a brief call this week?

Best,
[Your Name]
PromoHub Team"""
            },
            
            "technology": {
                "subject": "Monetize Your Developer Community with EZClub",
                "body": """Hi {creator_name},

Found your work at {domain} - really impressive content for the developer community.

I wanted to share how other tech creators are building sustainable revenue streams from their developer audiences through exclusive communities.

EZClub is designed for tech creators who want to:
• Monetize coding tutorials and technical knowledge
• Create premium developer communities
• Offer exclusive code reviews and mentorship
• Build recurring revenue from teaching

The most successful tech creators are offering:
→ Exclusive coding challenges and solutions
→ Direct access for code reviews and career advice
→ Premium Discord/Slack communities with networking
→ Early access to courses and technical content

Many are generating $5K-$20K monthly recurring revenue.

Interested in a quick 10-minute demo to see how this could work for your developer audience?

I can show you specific examples of how other tech creators structure their communities.

Available for a brief call?

Best,
[Your Name]
PromoHub Team

P.S. Also happy to share our guide on "Developer Community Monetization Strategies" if that would be helpful."""
            },
            
            "default": {
                "subject": "Build Your Premium Community with EZClub",
                "body": """Hi {creator_name},

I discovered your work at {domain} and was impressed by the community you're building.

I wanted to share how other creators in your space are building sustainable recurring revenue through exclusive member communities.

EZClub helps creators like you:
• Transform your audience into paying members
• Create tiered membership levels with exclusive content
• Automate member management and engagement
• Generate predictable monthly recurring revenue

The creators seeing the biggest success are those who offer:
→ Exclusive content and early access
→ Direct interaction and community networking
→ Premium tiers with additional value ($50-$200/month)
→ Member-only events and discussions

Many are building $5K-$25K monthly recurring revenue communities.

Would a 15-minute demo be valuable to see how this could work for your audience?

I can share specific examples of creators in similar spaces and their monetization strategies.

Available for a quick call this week?

Best regards,
[Your Name]
PromoHub Team"""
            }
        }
    
    async def connect_to_database(self):
        """Connect to PostgreSQL for listening to notifications"""
        try:
            # Parse database URL for asyncpg
            db_url = settings.database_url.replace("postgresql://", "")
            
            self.connection = await asyncpg.connect(f"postgresql://{db_url}")
            logger.info("✅ Connected to database for instant outreach notifications")
            
            # Set up the listener for new email notifications
            await self.connection.add_listener('new_email_discovered', self.handle_new_email)
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database for notifications: {str(e)}")
            raise
    
    async def create_database_trigger(self):
        """Create PostgreSQL trigger to notify when new emails are discovered"""
        db = SessionLocal()
        try:
            # Create the notification function
            trigger_function = """
            CREATE OR REPLACE FUNCTION notify_new_email()
            RETURNS trigger AS $$
            BEGIN
                -- Only notify if email changed from unknown@ pattern to a real email
                IF OLD.email LIKE 'unknown@%' AND NEW.email IS NOT NULL AND NEW.email NOT LIKE 'unknown@%' THEN
                    PERFORM pg_notify('new_email_discovered', json_build_object(
                        'lead_id', NEW.id,
                        'email', NEW.email,
                        'domain', NEW.domain,
                        'name', NEW.name,
                        'timestamp', NOW()
                    )::text);
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            # Create the trigger
            trigger_sql = """
            DROP TRIGGER IF EXISTS instant_outreach_trigger ON leads;
            CREATE TRIGGER instant_outreach_trigger
                AFTER UPDATE ON leads
                FOR EACH ROW
                EXECUTE FUNCTION notify_new_email();
            """
            
            db.execute(text(trigger_function))
            db.execute(text(trigger_sql))
            db.commit()
            
            logger.info("✅ Database trigger created for instant outreach")
            
        except Exception as e:
            logger.error(f"❌ Failed to create database trigger: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    async def handle_new_email(self, connection, pid, channel, payload):
        """Handle notification when a new email is discovered"""
        try:
            # Parse the notification payload
            data = json.loads(payload)
            lead_id = data['lead_id']
            email = data['email']
            domain = data['domain']
            name = data['name']
            
            logger.info(f"🚨 NEW EMAIL DISCOVERED: {email} from {domain}")
            
            # Send instant outreach email
            success = await self.send_instant_outreach(lead_id, email, domain, name)
            
            if success:
                logger.info(f"✅ Instant outreach sent to {email}")
            else:
                logger.error(f"❌ Failed to send instant outreach to {email}")
                
        except Exception as e:
            logger.error(f"❌ Error handling new email notification: {str(e)}")
    
    async def send_instant_outreach(self, lead_id: int, email: str, domain: str, name: str) -> bool:
        """Send personalized outreach email immediately"""
        try:
            # Determine creator type from domain/name
            creator_type = self.detect_creator_type(domain, name)

            # Get the appropriate template
            template = self.templates.get(creator_type, self.templates["default"])

            # Extract creator name from full name
            creator_name = self.extract_creator_name(name)

            # Personalize the email
            subject = template["subject"]
            body = template["body"].format(
                creator_name=creator_name,
                domain=domain
            )

            # Construct a temporary Lead object
            from app.models.base import Lead
            lead = Lead(
                id=lead_id,
                name=creator_name,
                email=email,
                company=domain,
                lead_source="instant_outreach",
                industry=creator_type,
                status="new"
            )
            # Add product_interest attribute for OutreachBot compatibility
            setattr(lead, "product_interest", "EZClub community platform")

            db = SessionLocal()
            try:
                outreach_bot = OutreachBot(db)
                success = await outreach_bot.send_personalized_email(lead)
                if success:
                    await self.log_instant_outreach(lead_id, email, creator_type, subject)
                return success
            finally:
                db.close()
        except Exception as e:
            logger.error(f"❌ Error sending instant outreach to {email}: {str(e)}")
            return False
    
    def detect_creator_type(self, domain: str, name: str) -> str:
        """Detect the type of creator based on domain and name"""
        domain_lower = domain.lower()
        name_lower = name.lower()
        
        # Check for coaching keywords
        if any(keyword in domain_lower or keyword in name_lower for keyword in 
               ['coaching', 'coach', 'mentor', 'consulting', 'consultant']):
            return "coaching"
        
        # Check for business keywords
        if any(keyword in domain_lower or keyword in name_lower for keyword in 
               ['business', 'entrepreneur', 'startup', 'marketing', 'sales']):
            return "business"
        
        # Check for technology keywords
        if any(keyword in domain_lower or keyword in name_lower for keyword in 
               ['code', 'programming', 'developer', 'tech', 'software', 'dev']):
            return "technology"
        
        return "default"
    
    def extract_creator_name(self, full_name: str) -> str:
        """Extract a friendly name from the full lead name"""
        # Remove "YouTube Creator - " prefix if present
        if "YouTube Creator - " in full_name:
            creator_name = full_name.replace("YouTube Creator - ", "")
        elif "Lead from " in full_name:
            # For business leads, extract from domain
            creator_name = "there"
        else:
            creator_name = full_name
        
        # If it's a company name, use "there" for personalization
        if any(word in creator_name.lower() for word in ['coaching', 'llc', 'inc', 'corp', 'company']):
            return "there"
        
        return creator_name
    
    async def log_instant_outreach(self, lead_id: int, email: str, creator_type: str, subject: str):
        """Log the instant outreach for tracking"""
        db = SessionLocal()
        try:
            log_query = text("""
                INSERT INTO outreach_log (lead_id, subject, body, email_type, sequence_step, sent_at, status)
                VALUES (:lead_id, :subject, :body, :email_type, 1, NOW(), 'sent')
            """)
            
            db.execute(log_query, {
                "lead_id": lead_id,
                "subject": subject,
                "body": f"Instant outreach email ({creator_type} template)",
                "email_type": "instant_outreach"
            })
            db.commit()
            
            logger.info(f"📝 Logged instant outreach for lead {lead_id}")
            
        except Exception as e:
            logger.error(f"❌ Error logging instant outreach: {str(e)}")
        finally:
            db.close()
    
    async def start_listening(self):
        """Start listening for new email notifications"""
        logger.info("🚀 Starting instant outreach service...")
        
        try:
            # Create database trigger if it doesn't exist
            await self.create_database_trigger()
            
            # Connect to database for notifications
            await self.connect_to_database()
            
            self.running = True
            logger.info("✅ Instant outreach service is running and listening for new emails")
            
            # Keep the service running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error in instant outreach service: {str(e)}")
        finally:
            if self.connection:
                await self.connection.close()
    
    async def stop_listening(self):
        """Stop the instant outreach service"""
        logger.info("🛑 Stopping instant outreach service...")
        self.running = False
        
        if self.connection:
            await self.connection.close()
    
    async def test_instant_outreach(self, test_email: str = "test@example.com"):
        """Test the instant outreach system"""
        logger.info(f"🧪 Testing instant outreach system with {test_email}")
        
        # Simulate a new email discovery
        success = await self.send_instant_outreach(
            lead_id=999,
            email=test_email,
            domain="testcoaching.com",
            name="YouTube Creator - Test Coaching"
        )
        
        return success


# Standalone function to run the service
async def run_instant_outreach_service():
    """Main function to run the instant outreach service"""
    service = InstantOutreachService()
    
    try:
        await service.start_listening()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await service.stop_listening()


# Function to manually trigger instant outreach for testing
async def trigger_instant_outreach_test():
    """Test the instant outreach system"""
    service = InstantOutreachService()
    
    # Test with a coaching creator
    result = await service.test_instant_outreach("joe@coaching.com")
    
    logger.info(f"Test result: {result}")
    return result


if __name__ == "__main__":
    # Run the service
    asyncio.run(run_instant_outreach_service())