import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.base import Lead, OutreachLog
from typing import Optional
import openai
import logging

logger = logging.getLogger(__name__)


class OutreachBot:
    """Cold email automation bot"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        
        # OpenAI client for personalization
        openai.api_key = settings.openai_api_key
    
    async def send_personalized_email(self, lead: Lead) -> bool:
        """Send a personalized cold email to a lead"""
        
        try:
            # Generate personalized email content
            subject, body = await self._generate_email_content(lead)
            
            # Create email message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.from_email
            message['To'] = lead.email
            
            # Add HTML and plain text versions
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(self._convert_to_html(body), 'html')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email via SMTP
            await self._send_smtp_email(message, lead.email)
            
            # Log the outreach
            await self._log_outreach(lead, subject, body, "sent")
            
            # Update lead status
            lead.status = "contacted"
            self.db.commit()
            
            logger.info(f"Sent outreach email to {lead.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {lead.email}: {str(e)}")
            await self._log_outreach(lead, subject if 'subject' in locals() else "Failed", 
                                   body if 'body' in locals() else "Failed to generate", "failed")
            return False
    
    async def _generate_email_content(self, lead: Lead) -> tuple[str, str]:
        """Generate personalized email content using OpenAI"""
        
        # Create personalized prompt
        prompt = f"""
        Write a professional, personalized cold outreach email for a YouTube creator:
        
        Lead Details:
        - Name: {lead.name}
        - Email: {lead.email}
        - Channel/Company: {lead.company or 'YouTube Creator'}
        - YouTube Channel: {lead.youtube_channel_url if hasattr(lead, 'youtube_channel_url') else 'Not provided'}
        - Subscriber Count: {lead.subscriber_count if hasattr(lead, 'subscriber_count') else 'Unknown'}
        - Content Niche: {lead.content_niche if hasattr(lead, 'content_niche') else lead.industry or 'General'}
        - Source: {lead.lead_source}
        - Product Interest: {lead.product_interest or 'EZClub community platform'}
        
        EZClub is a community platform specifically designed for content creators to:
        - Build exclusive membership communities around their content
        - Monetize beyond platform ad revenue with recurring subscriptions
        - Engage directly with their most dedicated fans
        - Create member-only content and perks
        - Analytics and insights on community growth
        
        Write a compelling email that:
        1. Acknowledges their creator journey and content niche
        2. Addresses common creator pain points (monetization, community building, platform dependency)
        3. Shows how EZClub complements their YouTube channel (doesn't compete)
        4. Includes a soft call-to-action for a demo or trial
        5. Keep it under 150 words
        6. Professional but creator-friendly tone
        7. Avoid being salesy - focus on value and community building
        
        Return in format:
        SUBJECT: [subject line]
        BODY: [email body]
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse subject and body
            if "SUBJECT:" in content and "BODY:" in content:
                parts = content.split("BODY:")
                subject = parts[0].replace("SUBJECT:", "").strip()
                body = parts[1].strip()
            else:
                # Fallback if format is not followed
                subject = f"Quick question about {lead.company or 'your'} marketing automation"
                body = content
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Fallback template
            subject = f"Hi {lead.name.split()[0]}, quick marketing automation question"
            body = self._get_fallback_template(lead)
        
        return subject, body
    
    def _get_fallback_template(self, lead: Lead) -> str:
        """Fallback email template if OpenAI fails"""
        channel_mention = f" for your {lead.content_niche or 'YouTube'} channel" if hasattr(lead, 'content_niche') else ""
        
        return f"""Hi {lead.name.split()[0]},

I came across your content{channel_mention} and wanted to reach out about something I think could really benefit your creator journey.

Many successful YouTubers are building recurring revenue through exclusive member communities alongside their channels. It's not about replacing YouTube - it's about deepening the connection with your most engaged fans.

EZClub helps creators like you:
• Turn subscribers into paying community members
• Create exclusive content and perks for supporters  
• Build recurring revenue beyond ad payments
• Engage directly with your biggest fans

Would you be interested in a quick 15-minute demo to see how this could work for your channel?

Best regards,
The EZClub Team

P.S. We've helped creators with similar audience sizes build $1K-5K monthly recurring communities. Happy to share some case studies if you're curious."""
    
    def _convert_to_html(self, text: str) -> str:
        """Convert plain text email to basic HTML"""
        html = text.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br>')
        html = f"<p>{html}</p>"
        
        # Style links
        html = html.replace('http://', '<a href="http://')
        html = html.replace('https://', '<a href="https://')
        
        # Basic HTML structure
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            {html}
        </body>
        </html>
        """
    
    async def _send_smtp_email(self, message: MIMEMultipart, to_email: str):
        """Send email via SMTP"""
        try:
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                use_tls=True
            ) as server:
                await server.login(self.smtp_username, self.smtp_password)
                await server.send_message(message)
                
        except Exception as e:
            logger.error(f"SMTP error sending to {to_email}: {str(e)}")
            raise
    
    async def _log_outreach(self, lead: Lead, subject: str, body: str, status: str):
        """Log outreach attempt to database"""
        outreach_log = OutreachLog(
            lead_id=lead.id,
            subject=subject,
            body=body,
            status=status,
            email_provider=self.smtp_server
        )
        
        self.db.add(outreach_log)
        self.db.commit()
    
    async def process_new_leads(self, max_emails_per_run: int = 10) -> int:
        """Process new leads and send outreach emails"""
        
        # Get leads that haven't been contacted
        new_leads = self.db.query(Lead).filter(
            Lead.status == "new"
        ).limit(max_emails_per_run).all()
        
        if not new_leads:
            logger.info("No new leads to process")
            return 0
        
        sent_count = 0
        for lead in new_leads:
            # Rate limiting check
            daily_count = await self._get_daily_email_count()
            if daily_count >= settings.email_rate_limit_per_day:
                logger.warning("Daily email rate limit reached")
                break
            
            success = await self.send_personalized_email(lead)
            if success:
                sent_count += 1
                
            # Small delay between emails to avoid being flagged
            await asyncio.sleep(2)
        
        logger.info(f"Processed {sent_count} new leads")
        return sent_count
    
    async def _get_daily_email_count(self) -> int:
        """Get count of emails sent today"""
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        count = self.db.query(OutreachLog).filter(
            OutreachLog.sent_at >= today,
            OutreachLog.sent_at < today + timedelta(days=1),
            OutreachLog.status == "sent"
        ).count()
        
        return count
    
    async def send_retarget_email(self, lead: Lead, page_visited: str) -> bool:
        """Send retargeting email based on page visit behavior"""
        
        try:
            subject = f"Hi {lead.name.split()[0]}, saw you were interested in {page_visited}"
            
            if "pricing" in page_visited.lower():
                body = f"""Hi {lead.name.split()[0]},

I noticed you were checking out our pricing page. I wanted to personally reach out in case you had any questions about PromoHub.

We offer flexible pricing tiers, and I'd be happy to discuss which plan might work best for your specific needs.

Would you be interested in a quick 15-minute call to go over:
• Your current marketing automation setup
• Which PromoHub features would be most valuable
• Custom pricing options if needed

Feel free to reply to this email or book a time that works for you: [calendar_link]

Best regards,
The PromoHub Team"""

            else:
                body = f"""Hi {lead.name.split()[0]},

I saw you visited our {page_visited} page and wanted to follow up to see if you have any questions.

Many businesses find that marketing automation can seem overwhelming at first, but PromoHub is designed to be simple and straightforward.

Would you like me to send over some case studies of how similar companies have used our platform?

Just reply to let me know what would be most helpful.

Best regards,
The PromoHub Team"""

            # Create and send email
            message = MIMEMultipart()
            message['Subject'] = subject
            message['From'] = self.from_email
            message['To'] = lead.email
            
            message.attach(MIMEText(body, 'plain'))
            message.attach(MIMEText(self._convert_to_html(body), 'html'))
            
            await self._send_smtp_email(message, lead.email)
            await self._log_outreach(lead, subject, body, "sent")
            
            logger.info(f"Sent retarget email to {lead.email} for {page_visited}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send retarget email to {lead.email}: {str(e)}")
            return False