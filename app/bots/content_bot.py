from sqlalchemy.orm import Session
from app.models.base import Content
from app.core.config import settings
import openai
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class ContentBot:
    """AI-powered content generation bot"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        openai.api_key = settings.openai_api_key
    
    async def generate_weekly_post(self) -> bool:
        """Generate a weekly blog post if needed"""
        
        # Check if we already have a post this week
        week_start = datetime.now() - timedelta(days=7)
        recent_post = self.db.query(Content).filter(
            Content.created_at >= week_start,
            Content.status.in_(["published", "draft"])
        ).first()
        
        if recent_post:
            logger.info("Recent post exists, skipping content generation")
            return False
        
        try:
            # Generate blog post content
            title, body, meta_description, tags = await self._generate_blog_content()
            
            # Create slug from title
            slug = self._create_slug(title)
            
            # Create content record
            content = Content(
                title=title,
                body=body,
                meta_description=meta_description,
                tags=tags,
                slug=slug,
                status="draft",
                ai_prompt="Weekly automated blog post generation",
                target_keywords="marketing automation, lead generation, email marketing"
            )
            
            self.db.add(content)
            self.db.commit()
            self.db.refresh(content)
            
            logger.info(f"Generated new blog post: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate blog content: {str(e)}")
            return False
    
    async def _generate_blog_content(self) -> tuple[str, str, str, str]:
        """Generate blog content using OpenAI"""
        
        prompt = """
        Write a comprehensive blog post about marketing automation for small to medium businesses.
        
        Focus on practical, actionable advice. Include:
        1. Common marketing challenges businesses face
        2. How automation can solve these problems
        3. Specific tools and strategies
        4. Real-world examples or case studies
        5. Implementation tips
        
        The post should be:
        - 800-1200 words
        - SEO-friendly with good headings
        - Professional but conversational tone
        - Include actionable takeaways
        
        Format the response as:
        TITLE: [compelling title]
        META_DESCRIPTION: [150-character meta description]
        TAGS: [comma-separated tags]
        CONTENT: [full blog post with markdown headers]
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the response
            parts = content.split("CONTENT:")
            header_section = parts[0]
            blog_content = parts[1].strip() if len(parts) > 1 else content
            
            # Extract title, meta description, and tags
            title_match = re.search(r'TITLE:\s*(.+)', header_section)
            meta_match = re.search(r'META_DESCRIPTION:\s*(.+)', header_section)
            tags_match = re.search(r'TAGS:\s*(.+)', header_section)
            
            title = title_match.group(1).strip() if title_match else "Marketing Automation Best Practices"
            meta_description = meta_match.group(1).strip() if meta_match else "Learn how marketing automation can streamline your business processes and boost efficiency."
            tags = tags_match.group(1).strip() if tags_match else "marketing automation, lead generation, email marketing, business growth"
            
            return title, blog_content, meta_description, tags
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return self._get_fallback_content()
    
    def _get_fallback_content(self) -> tuple[str, str, str, str]:
        """Fallback content if OpenAI fails"""
        title = "5 Marketing Automation Strategies That Actually Work"
        
        body = """
# 5 Marketing Automation Strategies That Actually Work

Marketing automation doesn't have to be complicated. Here are five proven strategies that small and medium businesses can implement today.

## 1. Welcome Email Sequences

Set up a series of 3-5 welcome emails that automatically send when someone joins your list. This builds trust and introduces your brand.

## 2. Lead Scoring and Segmentation  

Automatically score leads based on their actions (email opens, website visits, downloads) and segment them accordingly.

## 3. Abandoned Cart Recovery

For e-commerce businesses, automated cart abandonment emails can recover 10-15% of lost sales.

## 4. Social Media Scheduling

Plan and schedule your social media posts in advance to maintain consistent presence across platforms.

## 5. Retargeting Based on Behavior

Send targeted emails based on specific pages visited or actions taken on your website.

## Getting Started

The key is to start simple. Pick one strategy, implement it well, then expand. Marketing automation is about consistency and relevance, not complexity.

Remember: automation should enhance human connection, not replace it. Always maintain a personal touch in your communications.
        """
        
        meta_description = "Discover 5 practical marketing automation strategies that small businesses can implement today to boost efficiency and growth."
        tags = "marketing automation, lead generation, email marketing, small business, digital marketing"
        
        return title, body, meta_description, tags
    
    def _create_slug(self, title: str) -> str:
        """Create URL-friendly slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    async def publish_draft_content(self, content_id: int) -> bool:
        """Publish a draft blog post"""
        content = self.db.query(Content).filter(Content.id == content_id).first()
        if not content:
            return False
        
        content.status = "published"
        content.published_at = datetime.now()
        self.db.commit()
        
        logger.info(f"Published blog post: {content.title}")
        return True