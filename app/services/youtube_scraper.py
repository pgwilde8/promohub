"""
YouTube Creator Domain Scraper

This service automatically finds YouTube creator websites and adds them to the 
Hunter.io enrichment pipeline based on the YouTube Creator Strategy.

Target niches: Gaming, Education, Fitness, Business, Technology, Creative
"""

import os
import re
import asyncio
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import json
from datetime import datetime

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


@dataclass
class CreatorProfile:
    """Data structure for YouTube creator information"""
    channel_id: str
    channel_name: str
    subscriber_count: int
    website_url: Optional[str] = None
    social_links: List[str] = None
    niche: Optional[str] = None
    description: Optional[str] = None
    

class YouTubeCreatorScraper:
    """Scraper for finding YouTube creator domains and adding them to enrichment pipeline"""
    
    def __init__(self, db_session: Session = None):
        self.api_key = settings.youtube_api_key
        self.db = db_session or SessionLocal()
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Target niches from strategy document
        self.target_niches = {
            'gaming': ['gaming', 'gamer', 'esports', 'streamer', 'gameplay', 'let\'s play'],
            'education': ['tutorial', 'education', 'learning', 'course', 'teach', 'how to'],
            'fitness': ['fitness', 'workout', 'gym', 'health', 'nutrition', 'wellness'],
            'business': ['business', 'entrepreneur', 'startup', 'marketing', 'sales', 'coaching'],
            'technology': ['tech', 'coding', 'programming', 'software', 'developer', 'review'],
            'creative': ['art', 'design', 'music', 'creative', 'drawing', 'craft']
        }
        
        # Minimum subscriber thresholds from strategy
        self.min_subscribers = {
            'tier1': 1000,    # Growing creators
            'tier2': 10000,   # Established creators  
            'tier3': 100000   # Large creators
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        if not self.db.bind.pool.checkedout():
            self.db.close()
    
    def extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract clean domain from URL"""
        if not url:
            return None
            
        try:
            # Handle various URL formats
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Skip social media and common platforms
            skip_domains = {
                'youtube.com', 'twitter.com', 'instagram.com', 'facebook.com',
                'tiktok.com', 'linkedin.com', 'discord.gg', 'twitch.tv',
                'patreon.com', 'ko-fi.com', 'linktr.ee', 'bit.ly', 'gmail.com'
            }
            
            if domain in skip_domains or not domain:
                return None
                
            # Basic domain validation - must have at least one dot and proper TLD
            if '.' not in domain or len(domain) < 4:
                return None
            
            # Check if domain ends with a proper TLD (at least 2 characters)
            parts = domain.split('.')
            if len(parts) < 2 or len(parts[-1]) < 2:
                return None
                
            return domain
            
        except Exception as e:
            logger.warning(f"Error extracting domain from {url}: {str(e)}")
            return None
    
    def classify_creator_niche(self, channel_data: Dict) -> Optional[str]:
        """Classify creator into target niches based on channel info"""
        title = channel_data.get('snippet', {}).get('title', '').lower()
        description = channel_data.get('snippet', {}).get('description', '').lower()
        text_to_analyze = f"{title} {description}"
        
        # Score each niche based on keyword matches
        niche_scores = {}
        for niche, keywords in self.target_niches.items():
            score = 0
            # Give higher weight to title matches
            for keyword in keywords:
                if keyword in title:
                    score += 2  # Title match is worth 2 points
                elif keyword in description:
                    score += 1  # Description match is worth 1 point
            
            if score > 0:
                niche_scores[niche] = score
        
        # Special handling for obvious gaming channels
        gaming_indicators = ['games', 'gaming', 'game', 'esports', 'streamer', 'gameplay']
        for indicator in gaming_indicators:
            if indicator in title:
                niche_scores['gaming'] = niche_scores.get('gaming', 0) + 3
        
        # Return the niche with the highest score
        if niche_scores:
            return max(niche_scores, key=niche_scores.get)
        
        return None
    
    async def search_creators_by_keywords(self, keywords: List[str], max_results: int = 50) -> List[Dict]:
        """Search for YouTube creators using specific keywords"""
        if not self.api_key:
            logger.error("YouTube API key not configured")
            return []
        
        all_creators = []
        
        for keyword in keywords:
            try:
                url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    'key': self.api_key,
                    'q': keyword,
                    'type': 'channel',
                    'part': 'snippet',
                    'maxResults': max(1, min(max_results // len(keywords), 10)),  # Ensure at least 1 result per keyword
                    'order': 'relevance'
                }
                
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                creators = data.get('items', [])
                all_creators.extend(creators)
                
                logger.info(f"Found {len(creators)} creators for keyword: {keyword}")
                
                # Add delay to respect API rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error searching for keyword {keyword}: {str(e)}")
                continue
        
        return all_creators
    
    async def get_channel_details(self, channel_ids: List[str]) -> List[Dict]:
        """Get detailed information for multiple channels"""
        if not self.api_key or not channel_ids:
            return []
        
        try:
            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                'key': self.api_key,
                'id': ','.join(channel_ids[:50]),  # API limit
                'part': 'snippet,statistics,brandingSettings',
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('items', [])
            
        except Exception as e:
            logger.error(f"Error fetching channel details: {str(e)}")
            return []
    
    async def extract_creator_websites(self, channel_data: Dict) -> List[str]:
        """Extract website URLs from channel data using multiple sources"""
        websites = []
        
        # 1. Check channel description for URLs
        description = channel_data.get('snippet', {}).get('description', '')
        
        # Multiple URL patterns to catch different formats
        url_patterns = [
            r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
            r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.)+[a-zA-Z]{2,}',
            r'\b[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}\b'
        ]
        
        all_found_urls = set()
        for pattern in url_patterns:
            found_urls = re.findall(pattern, description, re.IGNORECASE)
            all_found_urls.update(found_urls)
        
        # Process found URLs
        for url in all_found_urls:
            domain = self.extract_domain_from_url(url)
            if domain:
                websites.append(domain)
        
        # 2. Check branding settings for custom URL
        branding = channel_data.get('brandingSettings', {})
        if 'channel' in branding:
            custom_url = branding['channel'].get('customUrl', '')
            if custom_url and not custom_url.startswith('@'):
                domain = self.extract_domain_from_url(custom_url)
                if domain:
                    websites.append(domain)
        
        # 3. Predict likely domains based on channel name
        channel_title = channel_data.get('snippet', {}).get('title', '')
        predicted_domains = self.predict_creator_domains(channel_title)
        websites.extend(predicted_domains)
        
        return list(set(websites))  # Remove duplicates
    
    def predict_creator_domains(self, channel_name: str) -> List[str]:
        """Predict likely domains based on channel name patterns"""
        if not channel_name:
            return []
        
        predicted = []
        clean_name = re.sub(r'[^\w\s]', '', channel_name.lower())
        
        # Common domain patterns
        patterns = [
            clean_name.replace(' ', ''),  # "Business Tips" -> "businesstips"
            clean_name.replace(' ', '-'), # "Business Tips" -> "business-tips" 
            ''.join(word[:3] for word in clean_name.split()[:3]), # "Business Marketing Tips" -> "busmarki"
        ]
        
        tlds = ['.com', '.net', '.org', '.co']
        
        for pattern in patterns:
            if len(pattern) >= 4 and len(pattern) <= 20:  # Reasonable domain length
                for tld in tlds:
                    domain = pattern + tld
                    # Only suggest if it could be a real business domain
                    if any(biz_word in channel_name.lower() for biz_word in ['business', 'entrepreneur', 'marketing', 'consulting', 'coach', 'agency']):
                        predicted.append(domain)
        
        return predicted[:2]  # Limit to 2 predictions
    
    def meets_subscriber_threshold(self, subscriber_count: int) -> bool:
        """Check if creator meets minimum subscriber threshold"""
        return subscriber_count >= self.min_subscribers['tier1']
    
    async def add_domains_to_enrichment(self, domains: List[str], creator_info: Dict) -> int:
        """Add discovered domains to the leads table for enrichment"""
        added_count = 0
        
        for domain in domains:
            try:
                # Check if domain already exists
                existing = self.db.execute(
                    text("SELECT id FROM leads WHERE domain = :domain"),
                    {"domain": domain}
                ).fetchone()
                
                if existing:
                    logger.info(f"Domain already exists: {domain}")
                    continue
                
                # Insert new lead
                self.db.execute(text("""
                    INSERT INTO leads (
                        owner_id, product_id, name, email, domain, status, 
                        lead_source, qualification_level, lead_score, verified, created_at
                    )
                    VALUES (
                        :owner_id, :product_id, :name, :email, :domain, :status, 
                        :lead_source, :qualification_level, :lead_score, :verified, NOW()
                    )
                """), {
                    "owner_id": 1,
                    "product_id": 1,  # EZClub
                    "name": f"YouTube Creator - {creator_info.get('channel_name', domain)}",
                    "email": f"unknown@{domain}",
                    "domain": domain,
                    "status": "new",
                    "lead_source": "youtube_creator_scraper",
                    "qualification_level": creator_info.get('tier', 'unqualified'),
                    "lead_score": min(creator_info.get('subscriber_count', 0) // 1000, 100),
                    "verified": False
                })
                
                self.db.commit()
                added_count += 1
                logger.info(f"Added domain: {domain} for creator: {creator_info.get('channel_name')}")
                
            except Exception as e:
                logger.error(f"Error adding domain {domain}: {str(e)}")
                self.db.rollback()
        
        return added_count
    
    async def log_scraper_run(self, results: Dict):
        """Log scraper execution results"""
        try:
            # Create a scraper log table entry (you might want to create this table)
            log_data = {
                "run_date": datetime.now(),
                "creators_found": results.get('creators_found', 0),
                "domains_found": results.get('domains_found', 0),
                "domains_added": results.get('domains_added', 0),
                "niches_targeted": results.get('niches_targeted', [])
            }
            
            logger.info(f"Scraper run completed: {log_data}")
            
        except Exception as e:
            logger.error(f"Error logging scraper run: {str(e)}")
    
    async def run_creator_discovery(self, target_niches: List[str] = None, max_creators_per_niche: int = 25) -> Dict:
        """Main function to discover YouTube creators and extract their domains"""
        logger.info("Starting YouTube creator domain discovery...")
        
        if not target_niches:
            target_niches = list(self.target_niches.keys())
        
        results = {
            'creators_found': 0,
            'domains_found': 0,
            'domains_added': 0,
            'niches_targeted': target_niches
        }
        
        for niche in target_niches:
            logger.info(f"Discovering creators in niche: {niche}")
            
            # Get search keywords for this niche
            keywords = self.target_niches.get(niche, [niche])
            
            # Search for creators
            creator_search_results = await self.search_creators_by_keywords(keywords, max_creators_per_niche)
            
            if not creator_search_results:
                logger.warning(f"No creators found for niche: {niche}")
                continue
            
            # Extract channel IDs
            channel_ids = [item['id']['channelId'] for item in creator_search_results if 'id' in item and 'channelId' in item['id']]
            
            # Get detailed channel information
            channel_details = await self.get_channel_details(channel_ids)
            
            for channel in channel_details:
                try:
                    # Check subscriber count
                    stats = channel.get('statistics', {})
                    subscriber_count = int(stats.get('subscriberCount', 0))
                    
                    if not self.meets_subscriber_threshold(subscriber_count):
                        logger.debug(f"Skipping channel with {subscriber_count} subscribers (below threshold)")
                        continue
                    
                    # Verify niche classification
                    classified_niche = self.classify_creator_niche(channel)
                    if classified_niche != niche:
                        logger.debug(f"Channel doesn't match target niche {niche}, classified as {classified_niche}")
                        continue
                    
                    # Extract website domains
                    domains = await self.extract_creator_websites(channel)
                    
                    if domains:
                        creator_info = {
                            'channel_name': channel.get('snippet', {}).get('title', ''),
                            'subscriber_count': subscriber_count,
                            'niche': niche,
                            'tier': 'tier3' if subscriber_count >= 100000 else 'tier2' if subscriber_count >= 10000 else 'tier1'
                        }
                        
                        # Add domains to enrichment pipeline
                        added = await self.add_domains_to_enrichment(domains, creator_info)
                        
                        results['creators_found'] += 1
                        results['domains_found'] += len(domains)
                        results['domains_added'] += added
                        
                        logger.info(f"Processed creator: {creator_info['channel_name']} ({subscriber_count:,} subs, {len(domains)} domains)")
                    
                    # Add delay between channels
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error processing channel: {str(e)}")
                    continue
            
            # Delay between niches
            await asyncio.sleep(1)
        
        # Log the results
        await self.log_scraper_run(results)
        
        logger.info(f"Creator discovery completed: {results}")
        return results


# Standalone execution function
async def run_youtube_creator_scraper(target_niches: List[str] = None, max_per_niche: int = 25) -> Dict:
    """Main function to run the YouTube creator scraper"""
    logger.info("Starting YouTube Creator Domain Scraper...")
    
    try:
        async with YouTubeCreatorScraper() as scraper:
            return await scraper.run_creator_discovery(target_niches, max_per_niche)
            
    except Exception as e:
        logger.error(f"YouTube creator scraper failed: {str(e)}")
        return {"error": str(e)}


# Manual execution functions
async def scrape_gaming_creators(max_count: int = 25):
    """Scrape gaming YouTube creators specifically"""
    return await run_youtube_creator_scraper(['gaming'], max_count)


async def scrape_all_niches(max_per_niche: int = 25):
    """Scrape all target niches"""
    return await run_youtube_creator_scraper(None, max_per_niche)