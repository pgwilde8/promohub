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

# Import Twitter scraper for enhanced creator discovery
try:
    from app.services.twitter_scraper import TwitterCreatorScraper
except ImportError:
    TwitterCreatorScraper = None

# Import GitHub scraper for enhanced creator discovery
try:
    from app.services.github_scraper import GitHubCreatorScraper
except ImportError:
    GitHubCreatorScraper = None

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
        # Collect all available API keys
        self.api_keys = []
        if settings.youtube_api_key:
            self.api_keys.append(settings.youtube_api_key)
        if settings.youtube_api_key_2:
            self.api_keys.append(settings.youtube_api_key_2)
        if settings.youtube_api_key_3:
            self.api_keys.append(settings.youtube_api_key_3)
        
        self.current_key_index = 0
        self.db = db_session or SessionLocal()
        self.client = httpx.AsyncClient(timeout=30.0)
        
        if not self.api_keys:
            logger.error("No YouTube API keys configured")
        else:
            logger.info(f"Initialized with {len(self.api_keys)} YouTube API keys")
        
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
    
    def get_current_api_key(self) -> Optional[str]:
        """Get current API key with rotation support"""
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index]
    
    def rotate_api_key(self) -> bool:
        """Rotate to next API key if available"""
        if len(self.api_keys) <= 1:
            return False
        
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Rotated to API key {self.current_key_index + 1} of {len(self.api_keys)}")
        return True
    
    async def make_api_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make API request with automatic key rotation on quota exceeded"""
        max_attempts = len(self.api_keys) if self.api_keys else 1
        
        for attempt in range(max_attempts):
            current_key = self.get_current_api_key()
            if not current_key:
                logger.error("No API keys available")
                return None
            
            params['key'] = current_key
            
            try:
                response = await self.client.get(url, params=params)
                
                if response.status_code == 403:
                    error_data = response.json()
                    if 'quotaExceeded' in str(error_data):
                        logger.warning(f"Quota exceeded for key {self.current_key_index + 1}, trying next key...")
                        if not self.rotate_api_key():
                            logger.error("All API keys exhausted")
                            return None
                        continue
                
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.error(f"API request failed with key {self.current_key_index + 1}: {str(e)}")
                if not self.rotate_api_key():
                    logger.error("All API keys failed")
                    return None
        
        return None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        if not self.db.bind.pool.checkedout():
            self.db.close()
    
    def get_current_api_key(self) -> Optional[str]:
        """Get the current API key for rotation"""
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index % len(self.api_keys)]
    
    def rotate_api_key(self):
        """Rotate to the next API key"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
    async def handle_quota_exceeded(self):
        """Handle quota exceeded by rotating API key"""
        self.rotate_api_key()
        current_key = self.get_current_api_key()
        if current_key:
            logger.info(f"Quota exceeded, switched to API key #{self.current_key_index + 1}")
            return True
        else:
            logger.error("All API keys exhausted")
            return False
    
    async def make_api_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make API request with automatic key rotation on quota exceeded"""
        retry_count = 0
        max_retries = len(self.api_keys)  # Try each API key once
        
        while retry_count < max_retries:
            try:
                current_key = self.get_current_api_key()
                if not current_key:
                    logger.error("No valid API key available")
                    return None
                
                params['key'] = current_key
                response = await self.client.get(url, params=params)
                
                if response.status_code == 403:
                    # Check if it's a quota exceeded error
                    error_data = response.json()
                    if 'quota' in error_data.get('error', {}).get('message', '').lower():
                        logger.warning(f"Quota exceeded for API key #{self.current_key_index + 1}")
                        if await self.handle_quota_exceeded():
                            retry_count += 1
                            continue
                        else:
                            logger.error("All API keys quota exceeded")
                            return None
                
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.error(f"API request error with key #{self.current_key_index + 1}: {str(e)}")
                if retry_count < max_retries - 1:
                    self.rotate_api_key()
                    retry_count += 1
                else:
                    return None
        
        return None
    
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
        """Search for YouTube creators using specific keywords with API key rotation"""
        if not self.api_keys:
            logger.error("No YouTube API keys configured")
            return []
        
        all_creators = []
        
        for keyword in keywords:
            try:
                url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    'q': keyword,
                    'type': 'channel',
                    'part': 'snippet',
                    'maxResults': max(1, min(max_results // len(keywords), 10)),
                    'order': 'relevance'
                }
                
                data = await self.make_api_request(url, params)
                if not data:
                    logger.error(f"Failed to get data for keyword: {keyword}")
                    continue
                
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
        """Get detailed information for multiple channels with API key rotation"""
        if not self.api_keys or not channel_ids:
            return []
        
        try:
            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                'id': ','.join(channel_ids[:50]),  # API limit
                'part': 'snippet,statistics,brandingSettings',
            }
            
            data = await self.make_api_request(url, params)
            return data.get('items', []) if data else []
            
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
    
    async def enhance_with_twitter_data(self, creator_info: Dict) -> List[str]:
        """Enhance creator data with Twitter/X profile information"""
        additional_domains = []
        
        if not TwitterCreatorScraper:
            logger.debug("Twitter scraper not available, skipping X enhancement")
            return additional_domains
        
        try:
            # Initialize Twitter scraper
            twitter_scraper = TwitterCreatorScraper()
            
            # Search for creator on Twitter/X
            creator_name = creator_info.get('channel_name', '')
            twitter_data = twitter_scraper.search_creator_by_username(creator_name)
            
            if twitter_data and twitter_data.get('relevance_score', 0) > 0.3:
                # Extract website URLs from Twitter profile
                website_urls = twitter_data.get('website_urls', [])
                
                for url in website_urls:
                    try:
                        domain = urlparse(url).netloc
                        if domain and domain not in additional_domains:
                            additional_domains.append(domain)
                            logger.info(f"Found additional domain from X profile: {domain}")
                    except Exception as e:
                        logger.debug(f"Error parsing URL {url}: {str(e)}")
                
                # Update creator info with Twitter data
                creator_info.update({
                    'twitter_username': twitter_data.get('twitter_username'),
                    'twitter_followers': twitter_data.get('twitter_followers', 0),
                    'twitter_bio': twitter_data.get('twitter_bio', ''),
                    'twitter_relevance_score': twitter_data.get('relevance_score', 0)
                })
                
                logger.info(f"Enhanced {creator_name} with X data: @{twitter_data.get('twitter_username')} ({twitter_data.get('twitter_followers', 0)} followers)")
            
        except Exception as e:
            logger.error(f"Error enhancing creator with Twitter data: {str(e)}")
        
        return additional_domains
    
    async def enhance_with_github_data(self, creator_info: Dict) -> List[str]:
        """Enhance creator data with GitHub profile information"""
        additional_domains = []
        
        if not GitHubCreatorScraper:
            logger.debug("GitHub scraper not available, skipping GitHub enhancement")
            return additional_domains
        
        try:
            # Initialize GitHub scraper
            github_scraper = GitHubCreatorScraper()
            
            # Search for creator on GitHub
            creator_name = creator_info.get('channel_name', '')
            github_data = github_scraper.search_creator_by_name(creator_name)
            
            if github_data and github_data.get('relevance_score', 0) > 0.3:
                # Extract website URLs from GitHub profile
                website_urls = github_data.get('website_urls', [])
                
                for url in website_urls:
                    try:
                        domain = urlparse(url).netloc
                        if domain and domain not in additional_domains:
                            additional_domains.append(domain)
                            logger.info(f"Found additional domain from GitHub profile: {domain}")
                    except Exception as e:
                        logger.debug(f"Error parsing URL {url}: {str(e)}")
                
                # Update creator info with GitHub data
                creator_info.update({
                    'github_username': github_data.get('github_username'),
                    'github_followers': github_data.get('github_followers', 0),
                    'github_bio': github_data.get('github_bio', ''),
                    'github_public_repos': github_data.get('github_public_repos', 0),
                    'github_relevance_score': github_data.get('relevance_score', 0)
                })
                
                logger.info(f"Enhanced {creator_name} with GitHub data: @{github_data.get('github_username')} ({github_data.get('github_followers', 0)} followers)")
            
        except Exception as e:
            logger.error(f"Error enhancing creator with GitHub data: {str(e)}")
        
        return additional_domains
    
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
                    
                    # Initialize creator info
                    creator_info = {
                        'channel_name': channel.get('snippet', {}).get('title', ''),
                        'subscriber_count': subscriber_count,
                        'niche': niche,
                        'tier': 'tier3' if subscriber_count >= 100000 else 'tier2' if subscriber_count >= 10000 else 'tier1'
                    }
                    
                    # Enhance with Twitter/X data if available
                    twitter_domains = await self.enhance_with_twitter_data(creator_info)
                    if twitter_domains:
                        domains.extend(twitter_domains)
                        domains = list(set(domains))  # Remove duplicates
                    
                    # Enhance with GitHub data if available
                    github_domains = await self.enhance_with_github_data(creator_info)
                    if github_domains:
                        domains.extend(github_domains)
                        domains = list(set(domains))  # Remove duplicates
                    
                    if domains:
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