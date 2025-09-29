"""
LinkedIn API integration for enhanced creator discovery.
Searches for YouTube creators on LinkedIn and extracts professional/business information.
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlencode
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInCreatorScraper:
    def __init__(self):
        # Load credentials from environment
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        
        # API endpoints
        self.base_url = "https://api.linkedin.com/v2"
        self.auth_url = "https://www.linkedin.com/oauth/v2"
        
        # Rate limiting (LinkedIn API limits)
        self.requests_per_hour = 500  # Typical limit for Marketing API
        self.request_count = 0
        self.rate_limit_reset = 0
        
        # Initialize session
        self.session = requests.Session()
        
        logger.info("LinkedInCreatorScraper initialized")
    
    def _get_access_token_url(self, redirect_uri: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'r_liteprofile r_emailaddress r_organization_social w_member_social',
            'state': 'linkedin_auth_state'
        }
        
        return f"{self.auth_url}/authorization?{urlencode(params)}"
    
    def _exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[str]:
        """Exchange authorization code for access token"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(f"{self.auth_url}/accessToken", data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            return None
    
    def _make_api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to LinkedIn API"""
        try:
            if not self.access_token:
                logger.error("No access token available")
                return None
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            url = f"{self.base_url}/{endpoint}"
            
            # Handle rate limiting
            if self.request_count >= self.requests_per_hour:
                if time.time() < self.rate_limit_reset:
                    wait_time = self.rate_limit_reset - time.time()
                    logger.info(f"Rate limit reached, waiting {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
                self.request_count = 0
            
            response = self.session.get(url, headers=headers, params=params)
            self.request_count += 1
            
            # Update rate limit info from headers
            if 'x-ratelimit-reset' in response.headers:
                self.rate_limit_reset = int(response.headers['x-ratelimit-reset'])
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded
                reset_time = int(response.headers.get('x-ratelimit-reset', time.time() + 3600))
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
    
    def search_creator_by_name(self, creator_name: str) -> Optional[Dict]:
        """Search for a creator by name on LinkedIn"""
        try:
            # LinkedIn doesn't have a public search API for profiles
            # This would require either:
            # 1. LinkedIn Sales Navigator API (requires partnership)
            # 2. Web scraping (against ToS)
            # 3. Using company search if creator has a business
            
            # For now, we'll implement company search as a proxy
            company_variations = self._generate_company_variations(creator_name)
            
            for company_name in company_variations[:3]:
                result = self._search_company(company_name)
                if result:
                    return self._extract_company_info(result, creator_name)
            
            logger.info(f"No LinkedIn company found for creator: {creator_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for creator {creator_name}: {str(e)}")
            return None
    
    def _search_company(self, company_name: str) -> Optional[Dict]:
        """Search for companies on LinkedIn"""
        try:
            # Use company search endpoint
            params = {
                'q': 'name',
                'name': company_name,
                'count': 10
            }
            
            result = self._make_api_request('companies', params)
            
            if result and 'elements' in result and result['elements']:
                return result['elements'][0]  # Return first match
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching company {company_name}: {str(e)}")
            return None
    
    def _generate_company_variations(self, creator_name: str) -> List[str]:
        """Generate possible company names from creator name"""
        clean_name = re.sub(r'[^\w\s]', '', creator_name)
        words = clean_name.split()
        
        variations = []
        
        # Direct variations
        variations.append(clean_name)  # "Business Basics"
        variations.append(f"{clean_name} LLC")  # "Business Basics LLC"
        variations.append(f"{clean_name} Inc")  # "Business Basics Inc"
        variations.append(f"{clean_name} Media")  # "Business Basics Media"
        variations.append(f"{clean_name} Productions")  # "Business Basics Productions"
        
        # Single word companies
        for word in words:
            if len(word) > 3:
                variations.append(f"{word} Media")
                variations.append(f"{word} Productions")
        
        return variations
    
    def _extract_company_info(self, company_data: Dict, original_creator_name: str) -> Dict:
        """Extract relevant information from LinkedIn company data"""
        try:
            extracted_urls = []
            
            # Extract website URL
            if company_data.get('website'):
                extracted_urls.append(company_data['website'])
            
            # Extract specialties and description for additional context
            specialties = company_data.get('specialties', [])
            description = company_data.get('description', '')
            
            # Calculate relevance score
            relevance_score = self._calculate_company_relevance_score(
                company_data.get('name', ''),
                description,
                original_creator_name,
                company_data.get('followerCount', 0)
            )
            
            return {
                'creator_name': original_creator_name,
                'linkedin_company_name': company_data.get('name'),
                'linkedin_company_id': company_data.get('id'),
                'linkedin_description': description,
                'linkedin_followers': company_data.get('followerCount', 0),
                'linkedin_employees': company_data.get('staffCount', 0),
                'linkedin_website': company_data.get('website'),
                'linkedin_specialties': specialties,
                'linkedin_industry': company_data.get('industry'),
                'website_urls': [url for url in extracted_urls if url],
                'relevance_score': relevance_score,
                'source': 'linkedin_api'
            }
            
        except Exception as e:
            logger.error(f"Error extracting company info: {str(e)}")
            return None
    
    def _calculate_company_relevance_score(self, company_name: str, description: str, creator_name: str, followers: int) -> float:
        """Calculate relevance score for the company match"""
        score = 0.0
        
        # Name similarity
        company_lower = company_name.lower()
        creator_lower = creator_name.lower()
        
        # Exact name match
        if creator_lower in company_lower or company_lower in creator_lower:
            score += 0.5
        
        # Individual words match
        creator_words = creator_lower.split()
        company_words = company_lower.split()
        word_matches = sum(1 for word in creator_words if word in company_words)
        score += (word_matches / len(creator_words)) * 0.3
        
        # Description analysis
        if description:
            desc_lower = description.lower()
            creator_keywords = ['content', 'creator', 'youtube', 'video', 'channel', 'media', 'production']
            keyword_matches = sum(1 for keyword in creator_keywords if keyword in desc_lower)
            score += min(keyword_matches * 0.05, 0.15)
        
        # Follower count boost
        if followers > 1000:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_company_details(self, company_id: str) -> Optional[Dict]:
        """Get detailed company information"""
        try:
            endpoint = f"companies/{company_id}"
            params = {
                'projection': '(id,name,description,website,specialties,industry,staffCount,followerCount)'
            }
            
            return self._make_api_request(endpoint, params)
            
        except Exception as e:
            logger.error(f"Error getting company details: {str(e)}")
            return None
    
    def enhance_youtube_creators_with_linkedin(self, creators_data: List[Dict]) -> List[Dict]:
        """Enhance YouTube creator data with LinkedIn company information"""
        enhanced_creators = []
        
        for creator in creators_data:
            creator_name = creator.get('channel_title', '')
            
            if creator_name:
                # Search for LinkedIn company
                linkedin_info = self.search_creator_by_name(creator_name)
                
                # Merge data
                enhanced_creator = {**creator}  # Copy original data
                
                if linkedin_info and linkedin_info.get('relevance_score', 0) > 0.3:
                    enhanced_creator.update({
                        'linkedin_company_name': linkedin_info.get('linkedin_company_name'),
                        'linkedin_company_id': linkedin_info.get('linkedin_company_id'),
                        'linkedin_description': linkedin_info.get('linkedin_description'),
                        'linkedin_followers': linkedin_info.get('linkedin_followers'),
                        'linkedin_employees': linkedin_info.get('linkedin_employees'),
                        'linkedin_website': linkedin_info.get('linkedin_website'),
                        'linkedin_specialties': linkedin_info.get('linkedin_specialties'),
                        'linkedin_industry': linkedin_info.get('linkedin_industry'),
                        'additional_linkedin_urls': linkedin_info.get('website_urls', []),
                        'linkedin_relevance_score': linkedin_info.get('relevance_score'),
                        'enhanced_with_linkedin': True
                    })
                    
                    logger.info(f"Enhanced {creator_name} with LinkedIn data")
                else:
                    enhanced_creator['enhanced_with_linkedin'] = False
                
                enhanced_creators.append(enhanced_creator)
                
                # Be respectful with API calls
                time.sleep(1)
        
        return enhanced_creators

def test_linkedin_integration():
    """Test the LinkedIn integration"""
    scraper = LinkedInCreatorScraper()
    
    # Check if credentials are available
    if not scraper.client_id or not scraper.access_token:
        print("❌ LinkedIn credentials not configured")
        print("Please set LINKEDIN_CLIENT_ID and LINKEDIN_ACCESS_TOKEN in your .env file")
        return
    
    # Test with a few creator names
    test_creators = ['Business Basics', 'Fox Business', 'TechCrunch']
    
    print("Testing LinkedIn API integration...")
    for creator in test_creators:
        print(f"\nSearching for: {creator}")
        result = scraper.search_creator_by_name(creator)
        if result:
            print(f"✅ Found: {result.get('linkedin_company_name')}")
            print(f"   Description: {result.get('linkedin_description', '')[:100]}...")
            print(f"   Followers: {result.get('linkedin_followers', 0):,}")
            print(f"   Website: {result.get('linkedin_website', 'None')}")
            print(f"   Relevance: {result.get('relevance_score', 0):.2f}")
        else:
            print("❌ Not found")

if __name__ == "__main__":
    test_linkedin_integration()