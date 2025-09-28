from sqlalchemy.orm import Session
from app.models.base import Content, SocialLog
from app.core.config import settings
import logging
from typing import List
import re

logger = logging.getLogger(__name__)


class SocialBot:
    """Social media automation bot"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        # Social media API credentials would be loaded from settings
    
    async def process_pending_content(self) -> int:
        """Process published blog posts and create social media posts"""
        
        posts_created = 0
        
        try:
            # Find published content that hasn't been shared on social media yet
            unshared_content = self.db.query(Content).filter(
                Content.status == "published"
            ).all()
            
            for content in unshared_content:
                # Check if already shared on all platforms
                existing_posts = self.db.query(SocialLog).filter(
                    SocialLog.content_id == content.id
                ).all()
                
                shared_platforms = [post.platform for post in existing_posts]
                
                # Create posts for platforms that haven't been used yet
                target_platforms = ["twitter", "linkedin"]
                
                for platform in target_platforms:
                    if platform not in shared_platforms:
                        snippets = self._create_social_snippets(content, platform)
                        
                        for snippet in snippets:
                            success = await self._post_to_platform(platform, snippet, content)
                            if success:
                                posts_created += 1
                                
                            # Small delay between posts
                            await asyncio.sleep(5)
            
            logger.info(f"Social bot created {posts_created} social media posts")
            return posts_created
            
        except Exception as e:
            logger.error(f"Social bot error: {str(e)}")
            return posts_created
    
    def _create_social_snippets(self, content: Content, platform: str) -> List[str]:
        """Create social media snippets from blog content"""
        
        snippets = []
        
        if platform == "twitter":
            # Create 3-5 tweets from the content
            snippets = [
                f"🚀 New blog post: {content.title}\n\n{content.meta_description}\n\nRead more: [blog_link]",
                f"💡 Key insight from our latest post: Marketing automation doesn't have to be complex. Start with one strategy and expand from there.\n\n#MarketingAutomation #SmallBusiness",
                f"📈 Did you know? Businesses using marketing automation see 14.5% increase in sales productivity.\n\nLearn practical strategies in our latest post: [blog_link]",
                f"🎯 Marketing automation tip: Focus on consistency over complexity. Small, consistent actions compound over time.\n\n#Marketing #Automation #Growth"
            ]
            
        elif platform == "linkedin":
            # Create 2-3 LinkedIn posts
            snippets = [
                f"🚀 Just published: {content.title}\n\n{content.meta_description}\n\nFor small and medium businesses, marketing automation can seem overwhelming. But it doesn't have to be.\n\nIn this post, I break down practical strategies you can implement today - no complex tools required.\n\nWhat's your biggest marketing automation challenge? Let me know in the comments.\n\n#MarketingAutomation #SmallBusiness #DigitalMarketing\n\nRead the full post: [blog_link]",
                f"💡 Marketing automation isn't about replacing human connection - it's about enhancing it.\n\nThe best automated campaigns still feel personal and relevant. Here's how to achieve that balance:\n\n✅ Segment your audience thoughtfully\n✅ Personalize based on behavior, not just names\n✅ Always provide value, not just promotions\n✅ Test and optimize continuously\n\nWhat other tips would you add? Share in the comments.\n\n#Marketing #Automation #Strategy"
            ]
        
        return snippets
    
    async def _post_to_platform(self, platform: str, content: str, blog_content: Content) -> bool:
        """Post content to social media platform"""
        
        try:
            # Replace placeholder with actual blog URL
            post_url = f"https://{settings.external_ip}/blog/{blog_content.slug}"
            final_content = content.replace("[blog_link]", post_url)
            
            if platform == "twitter":
                success = await self._post_to_twitter(final_content)
            elif platform == "linkedin":
                success = await self._post_to_linkedin(final_content)
            else:
                logger.warning(f"Unsupported platform: {platform}")
                return False
            
            if success:
                # Log the social media post
                social_log = SocialLog(
                    content_id=blog_content.id,
                    platform=platform,
                    post_text=final_content[:500],  # Truncate for storage
                    status="posted"
                )
                
                self.db.add(social_log)
                self.db.commit()
                
                logger.info(f"Posted to {platform}: {final_content[:50]}...")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to post to {platform}: {str(e)}")
            return False
    
    async def _post_to_twitter(self, content: str) -> bool:
        """Post to Twitter/X (placeholder - would use actual API)"""
        
        # This would use the Twitter API v2
        # For now, we'll just simulate the post
        
        logger.info(f"[SIMULATED] Twitter post: {content[:50]}...")
        
        # In a real implementation:
        # import tweepy
        # api = tweepy.Client(
        #     bearer_token=settings.twitter_bearer_token,
        #     consumer_key=settings.twitter_api_key,
        #     consumer_secret=settings.twitter_api_secret,
        #     access_token=settings.twitter_access_token,
        #     access_token_secret=settings.twitter_access_token_secret
        # )
        # response = api.create_tweet(text=content)
        
        return True  # Simulate success
    
    async def _post_to_linkedin(self, content: str) -> bool:
        """Post to LinkedIn (placeholder - would use actual API)"""
        
        # This would use the LinkedIn API
        logger.info(f"[SIMULATED] LinkedIn post: {content[:50]}...")
        
        # In a real implementation:
        # Use LinkedIn's API to create posts
        # https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/share-api
        
        return True  # Simulate success
    
    async def schedule_post(self, platform: str, content: str, schedule_time: datetime):
        """Schedule a social media post for later"""
        
        # This would integrate with the scheduler to post at a specific time
        # For now, we'll just log the scheduled post
        
        logger.info(f"Scheduled {platform} post for {schedule_time}: {content[:50]}...")
        
        # In a real implementation, you'd store this in the database
        # and have the scheduler pick it up at the right time
        
        return True
    
    def get_platform_limits(self, platform: str) -> dict:
        """Get character limits and posting limits for each platform"""
        
        limits = {
            "twitter": {
                "character_limit": 280,
                "daily_posts": 300,
                "hourly_posts": 300
            },
            "linkedin": {
                "character_limit": 3000,
                "daily_posts": 25,
                "hourly_posts": 25
            },
            "facebook": {
                "character_limit": 63206,
                "daily_posts": 25,
                "hourly_posts": 25
            }
        }
        
        return limits.get(platform, {})


# Import asyncio at the top level to avoid import errors
import asyncio
from datetime import datetime