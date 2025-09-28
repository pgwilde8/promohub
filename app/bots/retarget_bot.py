from sqlalchemy.orm import Session
from app.models.base import PageView, Lead, OutreachLog
from app.bots.outreach_bot import OutreachBot
from app.core.config import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RetargetBot:
    """Retargeting automation bot based on user behavior"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.outreach_bot = OutreachBot(db_session)
    
    async def check_retarget_opportunities(self) -> int:
        """Check for retargeting opportunities and send emails"""
        
        emails_sent = 0
        
        try:
            # Find visitors who viewed pricing but didn't sign up (last 24 hours)
            pricing_visitors = await self._find_pricing_page_visitors()
            
            for visitor in pricing_visitors:
                # Check if we already sent a retarget email recently
                recent_outreach = self._has_recent_outreach(visitor.lead_id)
                if recent_outreach:
                    continue
                
                # Get lead information
                lead = self.db.query(Lead).filter(Lead.id == visitor.lead_id).first()
                if not lead:
                    continue
                
                # Send retargeting email
                success = await self.outreach_bot.send_retarget_email(lead, visitor.page)
                if success:
                    emails_sent += 1
                    
                    # Update lead status if it was new
                    if lead.status == "new":
                        lead.status = "contacted"
                        self.db.commit()
            
            # Check for other retargeting scenarios
            demo_visitors = await self._find_demo_page_visitors()
            for visitor in demo_visitors:
                if self._has_recent_outreach(visitor.lead_id):
                    continue
                    
                lead = self.db.query(Lead).filter(Lead.id == visitor.lead_id).first()
                if lead:
                    success = await self._send_demo_follow_up(lead)
                    if success:
                        emails_sent += 1
            
            logger.info(f"Retarget bot processed opportunities, sent {emails_sent} emails")
            return emails_sent
            
        except Exception as e:
            logger.error(f"Retarget bot error: {str(e)}")
            return emails_sent
    
    async def _find_pricing_page_visitors(self):
        """Find users who visited pricing page in last 24 hours but didn't convert"""
        
        # Look for pricing page visits in the last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        pricing_visits = self.db.query(PageView).filter(
            PageView.is_pricing_page == True,
            PageView.viewed_at >= cutoff_time,
            PageView.lead_id.isnot(None)  # Must have associated lead
        ).all()
        
        # Filter out those who already signed up
        retarget_candidates = []
        for visit in pricing_visits:
            # Check if they visited signup page after pricing
            signup_after_pricing = self.db.query(PageView).filter(
                PageView.lead_id == visit.lead_id,
                PageView.is_signup_page == True,
                PageView.viewed_at >= visit.viewed_at
            ).first()
            
            if not signup_after_pricing:
                retarget_candidates.append(visit)
        
        return retarget_candidates
    
    async def _find_demo_page_visitors(self):
        """Find users who visited demo page but didn't book"""
        
        cutoff_time = datetime.now() - timedelta(hours=48)  # Longer window for demo
        
        demo_visits = self.db.query(PageView).filter(
            PageView.page.contains("demo"),
            PageView.viewed_at >= cutoff_time,
            PageView.lead_id.isnot(None)
        ).all()
        
        return demo_visits
    
    def _has_recent_outreach(self, lead_id: int) -> bool:
        """Check if lead has received outreach in the last 48 hours"""
        
        cutoff_time = datetime.now() - timedelta(hours=48)
        
        recent_outreach = self.db.query(OutreachLog).filter(
            OutreachLog.lead_id == lead_id,
            OutreachLog.sent_at >= cutoff_time
        ).first()
        
        return recent_outreach is not None
    
    async def _send_demo_follow_up(self, lead: Lead) -> bool:
        """Send follow-up email for demo page visitors"""
        
        subject = f"Hi {lead.name.split()[0]}, questions about the PromoHub demo?"
        
        body = f"""Hi {lead.name.split()[0]},

I noticed you were looking at our demo page and wanted to personally reach out.

Many people find it helpful to see PromoHub in action before making a decision. I'd be happy to give you a personalized walkthrough of the features that would be most relevant for your business.

The demo takes about 15 minutes and I can show you:
• How the lead management system works
• Setting up your first email automation
• Creating and scheduling social media posts
• Generating blog content with AI

Would you prefer a live demo this week, or would you like me to send you a recorded walkthrough?

Just reply to let me know what works best for you.

Best regards,
The PromoHub Team

P.S. If you have specific questions about implementation or pricing, I'm happy to address those during the demo too."""

        try:
            # Use the outreach bot to send the email
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart()
            message['Subject'] = subject
            message['From'] = settings.smtp_from_email
            message['To'] = lead.email
            
            message.attach(MIMEText(body, 'plain'))
            message.attach(MIMEText(self.outreach_bot._convert_to_html(body), 'html'))
            
            await self.outreach_bot._send_smtp_email(message, lead.email)
            await self.outreach_bot._log_outreach(lead, subject, body, "sent")
            
            logger.info(f"Sent demo follow-up email to {lead.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send demo follow-up to {lead.email}: {str(e)}")
            return False
    
    async def track_conversion(self, lead_id: int, conversion_type: str):
        """Track when a lead converts (signs up, purchases, etc.)"""
        
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.status = "converted"
            lead.notes = f"{lead.notes or ''}\nConverted: {conversion_type} at {datetime.now()}"
            self.db.commit()
            
            logger.info(f"Tracked conversion for lead {lead_id}: {conversion_type}")