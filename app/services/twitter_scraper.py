"""
X (Twitter) API integration for enhanced creator discovery.
Searches for YouTube creators on X and extracts additional website/social links.
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import re
from requests.auth import HTTPBasicAuth
import base64
import hashlib
import hmac
from urllib.parse import quote, urlencode
import secrets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterCreatorScraper:
    def __init__(self):
        # Load credentials from environment
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_ACCESS_TOKEN')
        
        # API endpoints
        self.base_url = "https://api.twitter.com/2"
        
        # Rate limiting (X API v2 limits)
        self.requests_per_15_min = 300  # User lookup limit
        self.request_count = 0
        self.rate_limit_reset = 0
        
        # Initialize session
        self.session = requests.Session()
        
        logger.info("TwitterCreatorScraper initialized")
    
    def _get_bearer_token(self) -> str:
        """Get bearer token for app-only authentication"""
        if self.bearer_token:
            return self.bearer_token
            
        # Encode credentials
        credentials = base64.b64encode(f"{self.api_key}:{self.api_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        
        data = 'grant_type=client_credentials'
        
        response = requests.post(
            'https://api.twitter.com/oauth2/token',
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            logger.error(f"Failed to get bearer token: {response.status_code} - {response.text}")
            return None
    
    def _make_api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to X API"""
        try:
            # Use bearer token for app-only auth (simpler and sufficient for user lookup)
            bearer_token = self._get_bearer_token()
            if not bearer_token:
                logger.error("No valid bearer token available")
                return None
            
            headers = {
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/{endpoint}"
            
            # Handle rate limiting
            if self.request_count >= self.requests_per_15_min:
                if time.time() < self.rate_limit_reset:
                    wait_time = self.rate_limit_reset - time.time()
                    logger.info(f"Rate limit reached, waiting {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
                self.request_count = 0
            
            response = self.session.get(url, headers=headers, params=params)
            self.request_count += 1
            
            # Update rate limit info from headers
            if 'x-rate-limit-reset' in response.headers:
                self.rate_limit_reset = int(response.headers['x-rate-limit-reset'])
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded
                reset_time = int(response.headers.get('x-rate-limit-reset', time.time() + 900))
                wait_time = reset_time - time.time()
                logger.warning(f"Rate limit exceeded, waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
                return self._make_api_request(endpoint, params)
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            return None
    
    def search_creator_by_username(self, creator_name: str) -> Optional[Dict]:
        """Search for a creator by their potential X username"""
        try:
            # Clean creator name for username search
            username_variations = self._generate_username_variations(creator_name)
            
            for username in username_variations[:3]:  # Try top 3 variations
                # Use users/by/username endpoint
                endpoint = f"users/by/username/{username}"
                params = {
                    'user.fields': 'description,entities,location,public_metrics,url,verified'
                }
                
                result = self._make_api_request(endpoint, params)
                if result and 'data' in result:
                    user_data = result['data']
                    logger.info(f"Found X profile for {creator_name}: @{username}")
                    return self._extract_creator_info(user_data, creator_name)
            
            logger.info(f"No X profile found for creator: {creator_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for creator {creator_name}: {str(e)}")
            return None
    
    def search_creators_by_keywords(self, creator_names: List[str], keywords: str = None) -> List[Dict]:
        """Search for multiple creators and extract their X profile data"""
        results = []
        
        for creator_name in creator_names:
            creator_info = self.search_creator_by_username(creator_name)
            if creator_info:
                results.append(creator_info)
            
            # Add small delay to be respectful
            time.sleep(0.5)
        
        return results
    
    def _generate_username_variations(self, creator_name: str) -> List[str]:
        """Generate possible X usernames from creator name"""
        # Clean the name
        clean_name = re.sub(r'[^\w\s]', '', creator_name.lower())
        words = clean_name.split()
        
        variations = []
        
        # Direct variations
        variations.append(clean_name.replace(' ', ''))  # "business basics" -> "businessbasics"
        variations.append(clean_name.replace(' ', '_'))  # "business basics" -> "business_basics"
        variations.append(''.join(word[:3] for word in words))  # "business basics" -> "busbas"
        
        # Single words
        for word in words:
            if len(word) > 3:
                variations.append(word)
        
        # First word + numbers
        if words:
            first_word = words[0]
            variations.extend([f"{first_word}{i}" for i in range(1, 6)])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen and len(var) >= 3:
                seen.add(var)
                unique_variations.append(var)
        
        return unique_variations
    
    def _extract_creator_info(self, user_data: Dict, original_creator_name: str) -> Dict:
        """Extract relevant information from X user data"""
        try:
            extracted_urls = []
            
            # Extract URL from profile
            if user_data.get('url'):
                extracted_urls.append(user_data['url'])
            
            # Extract URLs from bio/description entities
            entities = user_data.get('entities', {})
            if 'description' in entities and 'urls' in entities['description']:
                for url_entity in entities['description']['urls']:
                    if url_entity.get('expanded_url'):
                        extracted_urls.append(url_entity['expanded_url'])
            
            # Extract and clean URLs
            website_urls = []
            social_urls = []
            
            for url in extracted_urls:
                cleaned_url = self._clean_and_validate_url(url)
                if cleaned_url:
                    domain = urlparse(cleaned_url).netloc.lower()
                    
                    # Categorize URLs
                    if any(social in domain for social in ['youtube.com', 'instagram.com', 'tiktok.com', 'linkedin.com', 'facebook.com']):
                        social_urls.append(cleaned_url)
                    elif not any(platform in domain for platform in ['twitter.com', 'x.com', 't.co']):
                        website_urls.append(cleaned_url)
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(
                user_data.get('description', ''),
                original_creator_name,
                user_data.get('public_metrics', {}).get('followers_count', 0)
            )
            
            return {
                'creator_name': original_creator_name,
                'twitter_username': user_data.get('username'),
                'twitter_display_name': user_data.get('name'),
                'twitter_bio': user_data.get('description', ''),
                'twitter_followers': user_data.get('public_metrics', {}).get('followers_count', 0),
                'twitter_verified': user_data.get('verified', False),
                'website_urls': website_urls,
                'social_urls': social_urls,
                'location': user_data.get('location'),
                'relevance_score': relevance_score,
                'source': 'twitter_api'
            }
            
        except Exception as e:
            logger.error(f"Error extracting creator info: {str(e)}")
            return None
    
    def _clean_and_validate_url(self, url: str) -> Optional[str]:
        """Clean and validate URL"""
        try:
            if not url:
                return None
            
            # Handle t.co redirects and other URL shorteners
            if 't.co/' in url:
                # For t.co links, we'd need to follow redirects
                # For now, skip t.co links as they're often temporary
                return None
            
            # Add https if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            if parsed.netloc and parsed.scheme in ['http', 'https']:
                return url
            
            return None
            
        except Exception:
            return None
    
    def _calculate_relevance_score(self, bio: str, creator_name: str, followers: int) -> float:
        """Calculate relevance score for the match"""
        score = 0.0
        
        # Bio similarity
        bio_lower = bio.lower()
        creator_lower = creator_name.lower()
        
        # Exact name match in bio
        if creator_lower in bio_lower:
            score += 0.4
        
        # Individual words match
        creator_words = creator_lower.split()
        bio_words = bio_lower.split()
        word_matches = sum(1 for word in creator_words if word in bio_words)
        score += (word_matches / len(creator_words)) * 0.3
        
        # Follower count boost (more followers = more likely to be the right creator)
        if followers > 10000:
            score += 0.2
        elif followers > 1000:
            score += 0.1
        
        # Keywords that suggest content creation
        creator_keywords = ['creator', 'youtuber', 'content', 'channel', 'video', 'business', 'entrepreneur']
        keyword_matches = sum(1 for keyword in creator_keywords if keyword in bio_lower)
        score += min(keyword_matches * 0.05, 0.1)
        
        return min(score, 1.0)  # Cap at 1.0
    
    def enhance_youtube_creators(self, creators_data: List[Dict]) -> List[Dict]:
        """Enhance YouTube creator data with X profile information"""
        enhanced_creators = []
        
        for creator in creators_data:
            creator_name = creator.get('channel_title', '')
            
            if creator_name:
                # Search for X profile
                twitter_info = self.search_creator_by_username(creator_name)
                
                # Merge data
                enhanced_creator = {**creator}  # Copy original data
                
                if twitter_info:
                    enhanced_creator.update({
                        'twitter_username': twitter_info.get('twitter_username'),
                        'twitter_display_name': twitter_info.get('twitter_display_name'),
                        'twitter_bio': twitter_info.get('twitter_bio'),
                        'twitter_followers': twitter_info.get('twitter_followers'),
                        'twitter_verified': twitter_info.get('twitter_verified'),
                        'additional_website_urls': twitter_info.get('website_urls', []),
                        'additional_social_urls': twitter_info.get('social_urls', []),
                        'twitter_relevance_score': twitter_info.get('relevance_score'),
                        'enhanced_with_twitter': True
                    })
                    
                    logger.info(f"Enhanced {creator_name} with X data")
                else:
                    enhanced_creator['enhanced_with_twitter'] = False
                
                enhanced_creators.append(enhanced_creator)
                
                # Be respectful with API calls
                time.sleep(1)
        
        return enhanced_creators

def test_twitter_integration():
    """Test the Twitter integration"""
    scraper = TwitterCreatorScraper()
    
    # Test with a few creator names
    test_creators = ['Business Basics', 'Fox Business', 'Smosh Games']
    
    print("Testing X API integration...")
    for creator in test_creators:
        print(f"\nSearching for: {creator}")
        result = scraper.search_creator_by_username(creator)
        if result:
            print(f"✅ Found: @{result.get('twitter_username')}")
            print(f"   Bio: {result.get('twitter_bio', '')[:100]}...")
            print(f"   Followers: {result.get('twitter_followers', 0):,}")
            print(f"   Website URLs: {result.get('website_urls', [])}")
            print(f"   Relevance: {result.get('relevance_score', 0):.2f}")
        else:
            print("❌ Not found")

if __name__ == "__main__":
    test_twitter_integration()