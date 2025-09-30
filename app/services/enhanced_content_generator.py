"""
Enhanced Content Generator with Keyword-Driven Blog Creation
"""

import asyncio
import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

import openai
from app.core.config import settings
from app.models.base import Content
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class EnhancedContentGenerator:
    """AI-powered content generator with keyword optimization and social media integration"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or SessionLocal()
        openai.api_key = settings.openai_api_key
        
        # Content templates for different product focuses
        self.content_templates = {
            "ezclub": {
                "audience": "content creators, YouTubers, online educators, course creators",
                "pain_points": ["community building", "monetization", "audience engagement", "platform dependency"],
                "solutions": ["EZClub community platform", "membership tiers", "exclusive content", "direct monetization"],
                "keywords": ["community building", "creator monetization", "membership platform", "audience engagement"]
            },
            "ezdirectory": {
                "audience": "business owners, local services, entrepreneurs, small businesses",
                "pain_points": ["online visibility", "local SEO", "customer discovery", "digital presence"],
                "solutions": ["EZDirectory listings", "local SEO optimization", "business directory", "online presence"],
                "keywords": ["local SEO", "business directory", "online visibility", "small business marketing"]
            },
            "general": {
                "audience": "marketers, entrepreneurs, business owners, content creators",
                "pain_points": ["lead generation", "marketing automation", "customer acquisition", "growth"],
                "solutions": ["marketing automation", "lead generation tools", "customer engagement", "business growth"],
                "keywords": ["marketing automation", "lead generation", "business growth", "customer acquisition"]
            }
        }
    
    async def generate_blog_from_keywords(
        self, 
        keywords: List[str], 
        product_focus: str = "general",
        content_type: str = "blog_post",
        target_audience: str = None,
        word_count: int = 1000
    ) -> Dict:
        """Generate a complete blog post from keywords"""
        
        try:
            # Determine product focus and get template
            template = self.content_templates.get(product_focus, self.content_templates["general"])
            
            # Create comprehensive prompt
            prompt = self._create_content_prompt(
                keywords=keywords,
                template=template,
                target_audience=target_audience or template["audience"],
                content_type=content_type,
                word_count=word_count
            )
            
            # Generate content with OpenAI
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the structured response
            parsed_content = self._parse_content_response(content)
            
            # Create slug from title
            slug = self._create_slug(parsed_content["title"])
            
            # Save to database
            from datetime import datetime
            blog_post = Content(
                title=parsed_content["title"],
                body=parsed_content["content"],
                meta_description=parsed_content["meta_description"],
                tags=parsed_content["tags"],
                slug=slug,
                status="published",  # Publish immediately
                published_at=datetime.now(),
                content_type=content_type,
                target_audience=target_audience or template["audience"],
                content_angle=self._determine_content_angle(keywords, product_focus),
                content_pillar=self._determine_content_pillar(keywords),
                content_goal="lead_gen",
                ai_prompt=prompt[:500],  # Store first 500 chars of prompt
                target_keywords=", ".join(keywords),
                owner_id=1,  # Default owner
                product_id=1 if product_focus == "ezclub" else 2 if product_focus == "ezdirectory" else 1
            )
            
            self.db.add(blog_post)
            self.db.commit()
            self.db.refresh(blog_post)
            
            logger.info(f"Generated blog post: {parsed_content['title']} (ID: {blog_post.id})")
            
            return {
                "success": True,
                "content_id": blog_post.id,
                "title": parsed_content["title"],
                "slug": slug,
                "word_count": len(parsed_content["content"].split()),
                "social_snippets": self._extract_social_snippets(parsed_content["content"]),
                "seo_score": self._calculate_seo_score(parsed_content, keywords)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate blog content: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_content_prompt(
        self, 
        keywords: List[str], 
        template: Dict, 
        target_audience: str,
        content_type: str,
        word_count: int
    ) -> str:
        """Create a comprehensive prompt for content generation"""
        
        keyword_string = ", ".join(keywords)
        
        prompt = f"""
        Write a comprehensive {content_type} targeting {target_audience}.
        
        PRIMARY KEYWORDS: {keyword_string}
        
        AUDIENCE: {target_audience}
        PAIN POINTS: {', '.join(template['pain_points'])}
        SOLUTIONS: {', '.join(template['solutions'])}
        
        CONTENT REQUIREMENTS:
        - Word count: {word_count} words
        - SEO-optimized with natural keyword integration
        - Professional but conversational tone
        - Include actionable takeaways
        - Use subheadings for readability
        - Include relevant examples and case studies
        - End with a strong call-to-action
        
        STRUCTURE:
        1. Compelling introduction that addresses pain points
        2. 3-5 main sections with practical advice
        3. Real-world examples or case studies
        4. Actionable implementation steps
        5. Strong conclusion with CTA
        
        FORMAT YOUR RESPONSE AS:
        TITLE: [SEO-optimized, compelling title under 60 characters]
        META_DESCRIPTION: [150-character meta description with primary keyword]
        TAGS: [5-8 relevant tags, comma-separated]
        CONTENT: [Full blog post with markdown formatting]
        SOCIAL_HOOKS: [3-5 social media post ideas based on this content]
        """
        
        return prompt
    
    def _parse_content_response(self, content: str) -> Dict:
        """Parse the structured AI response"""
        
        # Split by major sections
        sections = content.split("CONTENT:")
        header_section = sections[0] if len(sections) > 1 else ""
        blog_content = sections[1].strip() if len(sections) > 1 else content
        
        # Extract title
        title_match = re.search(r'TITLE:\s*(.+)', header_section)
        title = title_match.group(1).strip() if title_match else "Generated Blog Post"
        
        # Extract meta description
        meta_match = re.search(r'META_DESCRIPTION:\s*(.+)', header_section)
        meta_description = meta_match.group(1).strip() if meta_match else "Generated blog post content"
        
        # Extract tags
        tags_match = re.search(r'TAGS:\s*(.+)', header_section)
        tags = tags_match.group(1).strip() if tags_match else "marketing, business"
        
        # Extract social hooks
        social_hooks = []
        if "SOCIAL_HOOKS:" in content:
            hooks_section = content.split("SOCIAL_HOOKS:")[1].strip()
            social_hooks = [hook.strip() for hook in hooks_section.split('\n') if hook.strip()]
        
        return {
            "title": title,
            "content": blog_content,
            "meta_description": meta_description,
            "tags": tags,
            "social_hooks": social_hooks
        }
    
    def _extract_social_snippets(self, content: str) -> Dict[str, List[str]]:
        """Extract social media snippets from blog content"""
        
        snippets = {
            "twitter": [],
            "linkedin": [],
            "facebook": [],
            "instagram": []
        }
        
        # Clean content and extract meaningful paragraphs
        import re
        
        # Remove markdown headers and clean up
        cleaned_content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_content)  # Remove bold
        cleaned_content = re.sub(r'\*(.*?)\*', r'\1', cleaned_content)     # Remove italic
        
        paragraphs = [p.strip() for p in cleaned_content.split('\n\n') if p.strip()]
        
        # Extract meaningful content (skip very short or very long paragraphs)
        meaningful_paragraphs = []
        for paragraph in paragraphs:
            # Skip headers, lists, and very short content
            if (len(paragraph) > 80 and 
                not paragraph.startswith('##') and 
                not paragraph.startswith('1.') and
                not paragraph.startswith('2.') and
                not paragraph.startswith('3.') and
                not paragraph.startswith('4.') and
                not paragraph.startswith('5.') and
                not paragraph.startswith('-') and
                not paragraph.startswith('*')):
                meaningful_paragraphs.append(paragraph)
        
        # Create platform-specific snippets
        for paragraph in meaningful_paragraphs[:8]:  # Limit to 8 paragraphs
            # Twitter snippets (under 280 characters, engaging)
            if 100 <= len(paragraph) <= 250:
                # Add some engagement elements
                twitter_snippet = paragraph
                if not twitter_snippet.endswith('?'):
                    twitter_snippet += " What's your experience with this?"
                snippets["twitter"].append(twitter_snippet)
            
            # LinkedIn snippets (professional, longer)
            if 150 <= len(paragraph) <= 400:
                linkedin_snippet = paragraph
                if not linkedin_snippet.endswith('.'):
                    linkedin_snippet += "."
                snippets["linkedin"].append(linkedin_snippet)
            
            # Facebook snippets (conversational, medium length)
            if 100 <= len(paragraph) <= 300:
                facebook_snippet = paragraph
                if not facebook_snippet.endswith('!'):
                    facebook_snippet += " What do you think?"
                snippets["facebook"].append(facebook_snippet)
            
            # Instagram snippets (shorter, inspirational)
            if 80 <= len(paragraph) <= 200:
                instagram_snippet = paragraph
                if not instagram_snippet.endswith('.'):
                    instagram_snippet += " ✨"
                snippets["instagram"].append(instagram_snippet)
        
        # Ensure we have at least some content for each platform
        if not snippets["twitter"] and meaningful_paragraphs:
            # Create a summary for Twitter
            summary = meaningful_paragraphs[0][:200] + "..." if len(meaningful_paragraphs[0]) > 200 else meaningful_paragraphs[0]
            snippets["twitter"].append(summary)
        
        if not snippets["linkedin"] and meaningful_paragraphs:
            snippets["linkedin"].append(meaningful_paragraphs[0])
        
        if not snippets["facebook"] and meaningful_paragraphs:
            snippets["facebook"].append(meaningful_paragraphs[0])
        
        if not snippets["instagram"] and meaningful_paragraphs:
            snippets["instagram"].append(meaningful_paragraphs[0])
        
        # Limit to 3-4 snippets per platform
        for platform in snippets:
            snippets[platform] = snippets[platform][:4]
        
        return snippets
    
    def _calculate_seo_score(self, content: Dict, keywords: List[str]) -> int:
        """Calculate basic SEO score for the content"""
        
        score = 0
        title = content["title"].lower()
        body = content["content"].lower()
        
        # Title optimization (30 points)
        if any(keyword.lower() in title for keyword in keywords):
            score += 30
        
        # Keyword density (20 points)
        keyword_count = sum(body.count(keyword.lower()) for keyword in keywords)
        if keyword_count >= 3:
            score += 20
        
        # Meta description (15 points)
        if content["meta_description"] and len(content["meta_description"]) <= 160:
            score += 15
        
        # Content length (15 points)
        word_count = len(body.split())
        if word_count >= 800:
            score += 15
        
        # Headings (10 points)
        if "##" in content["content"] or "###" in content["content"]:
            score += 10
        
        # Tags (10 points)
        if content["tags"] and len(content["tags"].split(',')) >= 3:
            score += 10
        
        return min(score, 100)
    
    def _create_slug(self, title: str) -> str:
        """Create URL-friendly slug from title"""
        
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        
        return slug
    
    def _determine_content_angle(self, keywords: List[str], product_focus: str) -> str:
        """Determine the content angle based on keywords and product focus"""
        
        angle_keywords = {
            "creator_growth": ["growth", "audience", "subscribers", "community"],
            "monetization": ["revenue", "money", "income", "profit", "monetize"],
            "platform_comparison": ["vs", "versus", "compare", "alternative", "better"],
            "how_to": ["how to", "guide", "tutorial", "steps", "process"],
            "case_study": ["case study", "example", "success story", "results"]
        }
        
        keyword_text = " ".join(keywords).lower()
        
        for angle, terms in angle_keywords.items():
            if any(term in keyword_text for term in terms):
                return angle
        
        return "educational"
    
    def _determine_content_pillar(self, keywords: List[str]) -> str:
        """Determine the content pillar based on keywords"""
        
        pillar_keywords = {
            "educational": ["how to", "guide", "tutorial", "learn", "tips"],
            "promotional": ["best", "top", "review", "recommend", "choose"],
            "entertainment": ["fun", "interesting", "amazing", "incredible"],
            "industry_news": ["news", "update", "trend", "latest", "new"]
        }
        
        keyword_text = " ".join(keywords).lower()
        
        for pillar, terms in pillar_keywords.items():
            if any(term in keyword_text for term in terms):
                return pillar
        
        return "educational"
    
    async def generate_content_calendar(
        self, 
        days: int = 30, 
        posts_per_week: int = 3
    ) -> List[Dict]:
        """Generate a content calendar with keyword suggestions"""
        
        # Content ideas based on product focus and seasonality
        content_ideas = [
            {
                "keywords": ["community building", "audience engagement", "creator monetization"],
                "product_focus": "ezclub",
                "title_template": "How to Build a Thriving Community Around Your Content"
            },
            {
                "keywords": ["local SEO", "business directory", "online visibility"],
                "product_focus": "ezdirectory", 
                "title_template": "Local SEO Strategies That Actually Work"
            },
            {
                "keywords": ["marketing automation", "lead generation", "email marketing"],
                "product_focus": "general",
                "title_template": "Marketing Automation for Small Businesses"
            },
            {
                "keywords": ["content creation", "social media", "brand building"],
                "product_focus": "ezclub",
                "title_template": "Content Creation Strategies for Business Growth"
            },
            {
                "keywords": ["small business", "entrepreneurship", "business growth"],
                "product_focus": "ezdirectory",
                "title_template": "Small Business Growth Hacks That Work"
            }
        ]
        
        calendar = []
        for i in range(days):
            if i % (7 // posts_per_week) == 0:  # Distribute posts evenly
                idea = content_ideas[i % len(content_ideas)]
                calendar.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "keywords": idea["keywords"],
                    "product_focus": idea["product_focus"],
                    "suggested_title": idea["title_template"]
                })
        
        return calendar


# Standalone functions for easy API integration
async def generate_blog_from_keywords_api(
    keywords: List[str],
    product_focus: str = "general",
    target_audience: str = None
) -> Dict:
    """API-friendly function to generate blog content"""
    
    generator = EnhancedContentGenerator()
    return await generator.generate_blog_from_keywords(
        keywords=keywords,
        product_focus=product_focus,
        target_audience=target_audience
    )


async def get_content_calendar_api(days: int = 30) -> List[Dict]:
    """API-friendly function to get content calendar"""
    
    generator = EnhancedContentGenerator()
    return await generator.generate_content_calendar(days=days)
