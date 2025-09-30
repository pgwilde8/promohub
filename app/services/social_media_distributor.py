"""
Enhanced Social Media Distribution System
Automatically extracts snippets from blog content and posts to multiple platforms
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import openai
from app.core.config import settings
from app.models.base import Content, SocialLog
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class SocialMediaDistributor:
    """Enhanced social media distribution with platform-specific optimization"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or SessionLocal()
        openai.api_key = settings.openai_api_key
        
        # Platform-specific configurations
        self.platform_configs = {
            "twitter": {
                "max_length": 280,
                "hashtag_limit": 2,
                "optimal_length": 200,
                "character_style": "concise, punchy, engaging",
                "emoji_usage": "moderate",
                "link_placement": "end"
            },
            "linkedin": {
                "max_length": 3000,
                "hashtag_limit": 5,
                "optimal_length": 500,
                "character_style": "professional, informative, value-driven",
                "emoji_usage": "minimal",
                "link_placement": "middle"
            },
            "facebook": {
                "max_length": 63206,
                "hashtag_limit": 3,
                "optimal_length": 200,
                "character_style": "conversational, friendly, engaging",
                "emoji_usage": "frequent",
                "link_placement": "end"
            },
            "instagram": {
                "max_length": 2200,
                "hashtag_limit": 30,
                "optimal_length": 150,
                "character_style": "visual, inspiring, hashtag-rich",
                "emoji_usage": "frequent",
                "link_placement": "bio_only"
            }
        }
    
    async def process_content_for_social(
        self, 
        content_id: int, 
        platforms: List[str] = None
    ) -> Dict:
        """Process a blog post and create social media content for specified platforms"""
        
        if platforms is None:
            platforms = ["twitter", "linkedin", "facebook"]
        
        try:
            # Get the blog content
            content = self.db.query(Content).filter(Content.id == content_id).first()
            if not content:
                return {"success": False, "error": "Content not found"}
            
            # Extract social snippets
            social_content = await self._extract_social_content(content)
            
            # Create platform-specific posts
            posts_created = []
            for platform in platforms:
                platform_posts = await self._create_platform_posts(
                    content, social_content, platform
                )
                
                for post in platform_posts:
                    # Save to database
                    social_log = SocialLog(
                        content_id=content_id,
                        platform=platform,
                        post_content=post["content"],
                        post_type=post["type"],
                        scheduled_at=post.get("scheduled_at"),
                        status="ready"
                    )
                    
                    self.db.add(social_log)
                    posts_created.append({
                        "platform": platform,
                        "content": post["content"],
                        "type": post["type"],
                        "length": len(post["content"])
                    })
            
            self.db.commit()
            
            logger.info(f"Created {len(posts_created)} social media posts for content {content_id}")
            
            return {
                "success": True,
                "content_id": content_id,
                "posts_created": len(posts_created),
                "platforms": platforms,
                "posts": posts_created
            }
            
        except Exception as e:
            logger.error(f"Failed to process content for social media: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _extract_social_content(self, content: Content) -> Dict:
        """Extract and structure content for social media"""
        
        # Use AI to extract key insights and create social hooks
        prompt = f"""
        Extract key insights and create social media content from this blog post:
        
        TITLE: {content.title}
        CONTENT: {content.body[:2000]}  # First 2000 chars
        
        Create:
        1. 3-5 key insights (1-2 sentences each)
        2. 3-5 quotable statements
        3. 3-5 call-to-action ideas
        4. 5-10 relevant hashtags
        5. 3-5 engaging questions for audience interaction
        
        Format as:
        KEY_INSIGHTS:
        - [insight 1]
        - [insight 2]
        
        QUOTABLE_STATEMENTS:
        - [quote 1]
        - [quote 2]
        
        CALL_TO_ACTIONS:
        - [CTA 1]
        - [CTA 2]
        
        HASHTAGS:
        #hashtag1 #hashtag2 #hashtag3
        
        ENGAGEMENT_QUESTIONS:
        - [question 1]
        - [question 2]
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_content = response.choices[0].message.content.strip()
            return self._parse_social_content(ai_content)
            
        except Exception as e:
            logger.error(f"Failed to extract social content with AI: {str(e)}")
            return self._fallback_social_extraction(content)
    
    def _parse_social_content(self, ai_content: str) -> Dict:
        """Parse AI-generated social content"""
        
        content = {
            "key_insights": [],
            "quotable_statements": [],
            "call_to_actions": [],
            "hashtags": [],
            "engagement_questions": []
        }
        
        # Extract key insights
        insights_match = re.search(r'KEY_INSIGHTS:(.*?)(?=QUOTABLE_STATEMENTS:|$)', ai_content, re.DOTALL)
        if insights_match:
            insights_text = insights_match.group(1).strip()
            content["key_insights"] = [line.strip('- ').strip() for line in insights_text.split('\n') if line.strip()]
        
        # Extract quotable statements
        quotes_match = re.search(r'QUOTABLE_STATEMENTS:(.*?)(?=CALL_TO_ACTIONS:|$)', ai_content, re.DOTALL)
        if quotes_match:
            quotes_text = quotes_match.group(1).strip()
            content["quotable_statements"] = [line.strip('- ').strip() for line in quotes_text.split('\n') if line.strip()]
        
        # Extract call-to-actions
        cta_match = re.search(r'CALL_TO_ACTIONS:(.*?)(?=HASHTAGS:|$)', ai_content, re.DOTALL)
        if cta_match:
            cta_text = cta_match.group(1).strip()
            content["call_to_actions"] = [line.strip('- ').strip() for line in cta_text.split('\n') if line.strip()]
        
        # Extract hashtags
        hashtags_match = re.search(r'HASHTAGS:(.*?)(?=ENGAGEMENT_QUESTIONS:|$)', ai_content, re.DOTALL)
        if hashtags_match:
            hashtags_text = hashtags_match.group(1).strip()
            content["hashtags"] = re.findall(r'#\w+', hashtags_text)
        
        # Extract engagement questions
        questions_match = re.search(r'ENGAGEMENT_QUESTIONS:(.*?)$', ai_content, re.DOTALL)
        if questions_match:
            questions_text = questions_match.group(1).strip()
            content["engagement_questions"] = [line.strip('- ').strip() for line in questions_text.split('\n') if line.strip()]
        
        return content
    
    def _fallback_social_extraction(self, content: Content) -> Dict:
        """Fallback method to extract social content without AI"""
        
        # Simple extraction from content
        paragraphs = content.body.split('\n\n')
        key_insights = [p.strip() for p in paragraphs if 50 <= len(p.strip()) <= 200][:3]
        
        # Extract hashtags from tags
        hashtags = [f"#{tag.strip()}" for tag in content.tags.split(',') if tag.strip()][:5]
        
        return {
            "key_insights": key_insights,
            "quotable_statements": key_insights[:2],
            "call_to_actions": [
                f"Read the full article: {content.title}",
                "What are your thoughts on this?",
                "Share your experience in the comments!"
            ],
            "hashtags": hashtags,
            "engagement_questions": [
                "What's your biggest challenge with this?",
                "Have you tried this approach?",
                "What would you add to this list?"
            ]
        }
    
    async def _create_platform_posts(
        self, 
        content: Content, 
        social_content: Dict, 
        platform: str
    ) -> List[Dict]:
        """Create platform-specific social media posts"""
        
        config = self.platform_configs[platform]
        posts = []
        
        # Create different types of posts for each platform
        post_types = self._get_platform_post_types(platform)
        
        for post_type in post_types:
            post_content = await self._create_platform_post(
                content, social_content, platform, post_type, config
            )
            
            if post_content:
                posts.append({
                    "content": post_content,
                    "type": post_type,
                    "platform": platform
                })
        
        return posts
    
    def _get_platform_post_types(self, platform: str) -> List[str]:
        """Get appropriate post types for each platform"""
        
        post_types = {
            "twitter": ["insight", "quote", "question", "cta"],
            "linkedin": ["insight", "article_promo", "question", "professional_tip"],
            "facebook": ["insight", "quote", "question", "community_engagement"],
            "instagram": ["quote", "tip", "question", "story"]
        }
        
        return post_types.get(platform, ["insight", "quote"])
    
    async def _create_platform_post(
        self, 
        content: Content, 
        social_content: Dict, 
        platform: str, 
        post_type: str, 
        config: Dict
    ) -> Optional[str]:
        """Create a specific type of post for a platform"""
        
        try:
            # Use AI to create platform-optimized content
            prompt = f"""
            Create a {post_type} post for {platform} based on this blog content:
            
            BLOG TITLE: {content.title}
            BLOG URL: https://promohub.ezdirectory.app/blog/{content.slug}
            
            KEY INSIGHTS: {social_content['key_insights']}
            QUOTABLE STATEMENTS: {social_content['quotable_statements']}
            HASHTAGS: {social_content['hashtags']}
            
            PLATFORM REQUIREMENTS:
            - Max length: {config['max_length']} characters
            - Style: {config['character_style']}
            - Emoji usage: {config['emoji_usage']}
            - Hashtag limit: {config['hashtag_limit']}
            
            POST TYPE: {post_type}
            
            Create an engaging, platform-appropriate post that drives traffic to the blog.
            Include relevant hashtags and a call-to-action.
            """
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.8
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Validate length
            if len(post_content) <= config["max_length"]:
                return post_content
            else:
                # Truncate if too long
                return post_content[:config["max_length"]-3] + "..."
                
        except Exception as e:
            logger.error(f"Failed to create {post_type} post for {platform}: {str(e)}")
            return self._create_fallback_post(content, social_content, platform, post_type, config)
    
    def _create_fallback_post(
        self, 
        content: Content, 
        social_content: Dict, 
        platform: str, 
        post_type: str, 
        config: Dict
    ) -> str:
        """Create a fallback post without AI"""
        
        if post_type == "insight" and social_content["key_insights"]:
            insight = social_content["key_insights"][0]
            hashtags = " ".join(social_content["hashtags"][:config["hashtag_limit"]])
            return f"{insight}\n\n{hashtags}"
        
        elif post_type == "quote" and social_content["quotable_statements"]:
            quote = social_content["quotable_statements"][0]
            hashtags = " ".join(social_content["hashtags"][:config["hashtag_limit"]])
            return f'"{quote}"\n\n{hashtags}'
        
        elif post_type == "question" and social_content["engagement_questions"]:
            question = social_content["engagement_questions"][0]
            hashtags = " ".join(social_content["hashtags"][:config["hashtag_limit"]])
            return f"{question}\n\n{hashtags}"
        
        else:
            # Default post
            title = content.title
            hashtags = " ".join(social_content["hashtags"][:config["hashtag_limit"]])
            return f"Check out our latest article: {title}\n\n{hashtags}"
    
    async def schedule_social_posts(
        self, 
        content_id: int, 
        platforms: List[str],
        schedule_delay_hours: int = 2
    ) -> Dict:
        """Schedule social media posts with delays between platforms"""
        
        try:
            # Get ready posts for this content
            posts = self.db.query(SocialLog).filter(
                SocialLog.content_id == content_id,
                SocialLog.status == "ready",
                SocialLog.platform.in_(platforms)
            ).all()
            
            scheduled_count = 0
            current_time = datetime.now()
            
            for i, post in enumerate(posts):
                # Schedule with delay between posts
                scheduled_time = current_time + timedelta(hours=i * schedule_delay_hours)
                
                post.scheduled_at = scheduled_time
                post.status = "scheduled"
                scheduled_count += 1
            
            self.db.commit()
            
            logger.info(f"Scheduled {scheduled_count} social media posts for content {content_id}")
            
            return {
                "success": True,
                "scheduled_count": scheduled_count,
                "platforms": platforms
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule social posts: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_social_analytics(self, content_id: int) -> Dict:
        """Get analytics for social media posts of a specific content"""
        
        try:
            posts = self.db.query(SocialLog).filter(
                SocialLog.content_id == content_id
            ).all()
            
            analytics = {
                "total_posts": len(posts),
                "platforms": {},
                "engagement_rate": 0,
                "total_reach": 0
            }
            
            for post in posts:
                platform = post.platform
                if platform not in analytics["platforms"]:
                    analytics["platforms"][platform] = {
                        "posts": 0,
                        "scheduled": 0,
                        "published": 0,
                        "failed": 0
                    }
                
                analytics["platforms"][platform]["posts"] += 1
                analytics["platforms"][platform][post.status] += 1
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get social analytics: {str(e)}")
            return {"error": str(e)}


# Standalone functions for API integration
async def process_content_for_social_api(
    content_id: int,
    platforms: List[str] = None
) -> Dict:
    """API-friendly function to process content for social media"""
    
    distributor = SocialMediaDistributor()
    return await distributor.process_content_for_social(content_id, platforms)


async def schedule_social_posts_api(
    content_id: int,
    platforms: List[str],
    delay_hours: int = 2
) -> Dict:
    """API-friendly function to schedule social posts"""
    
    distributor = SocialMediaDistributor()
    return await distributor.schedule_social_posts(content_id, platforms, delay_hours)
