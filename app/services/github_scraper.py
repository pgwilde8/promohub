"""
GitHub API integration for enhanced creator discovery.
Searches for YouTube creators on GitHub and extracts website/portfolio links.
Perfect for tech, coding, and developer-focused creators.
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import re
import logging

# Import settings for proper configuration loading
try:
    from app.core.config import settings
except ImportError:
    settings = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubCreatorScraper:
    def __init__(self):
        # Load credentials from settings if available, otherwise fallback to environment
        if settings:
            self.access_token = settings.github_access_token
            self.api_url = settings.github_api_url or 'https://api.github.com'
            self.rate_limit_per_hour = settings.github_rate_limit_per_hour or 5000
        else:
            # Fallback to environment variables
            self.access_token = os.getenv('GITHUB_ACCESS_TOKEN')
            self.api_url = os.getenv('GITHUB_API_URL', 'https://api.github.com')
            self.rate_limit_per_hour = int(os.getenv('GITHUB_RATE_LIMIT_PER_HOUR', '5000'))
        
        # Rate limiting tracking
        self.request_count = 0
        self.rate_limit_reset = 0
        self.remaining_requests = self.rate_limit_per_hour
        
        # Initialize session
        self.session = requests.Session()
        
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PromoHub-Creator-Discovery/1.0'
            })
        
        logger.info("GitHubCreatorScraper initialized")
    
    def _make_api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to GitHub API"""
        try:
            if not self.access_token:
                logger.error("No GitHub access token available")
                return None
            
            url = f"{self.api_url}/{endpoint}"
            
            # Check rate limiting
            if self.remaining_requests <= 10:
                if time.time() < self.rate_limit_reset:
                    wait_time = self.rate_limit_reset - time.time()
                    logger.info(f"Rate limit low, waiting {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
            
            response = self.session.get(url, params=params)
            
            # Update rate limit info from headers
            self.remaining_requests = int(response.headers.get('X-RateLimit-Remaining', 0))
            self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # Rate limit exceeded
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))
                wait_time = reset_time - time.time()
                logger.warning(f"GitHub rate limit exceeded, waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
                return self._make_api_request(endpoint, params)
            elif response.status_code == 404:
                logger.debug(f"GitHub user not found: {endpoint}")
                return None
            else:
                logger.error(f"GitHub API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making GitHub API request: {str(e)}")
            return None
    
    def search_users(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for GitHub users by name/username"""
        try:
            params = {
                'q': f'{query} in:login,name',
                'type': 'Users',
                'per_page': min(max_results, 100)
            }
            
            result = self._make_api_request('search/users', params)
            
            if result and 'items' in result:
                return result['items']
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching GitHub users: {str(e)}")
            return []
    
    def get_user_details(self, username: str) -> Optional[Dict]:
        """Get detailed information about a GitHub user"""
        try:
            endpoint = f"users/{username}"
            return self._make_api_request(endpoint)
            
        except Exception as e:
            logger.error(f"Error getting GitHub user details for {username}: {str(e)}")
            return None
    
    def get_user_repositories(self, username: str, max_repos: int = 10) -> List[Dict]:
        """Get user's repositories to analyze for additional website links"""
        try:
            params = {
                'per_page': min(max_repos, 100),
                'sort': 'updated',
                'direction': 'desc'
            }
            
            endpoint = f"users/{username}/repos"
            result = self._make_api_request(endpoint, params)
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting repositories for {username}: {str(e)}")
            return []
    
    def search_creator_by_name(self, creator_name: str) -> Optional[Dict]:
        """Search for a creator by their name on GitHub"""
        try:
            # Generate username variations
            username_variations = self._generate_username_variations(creator_name)
            
            # Try direct username lookup first
            for username in username_variations[:3]:
                user_details = self.get_user_details(username)
                if user_details:
                    enhanced_data = self._extract_creator_info(user_details, creator_name)
                    if enhanced_data and enhanced_data.get('relevance_score', 0) > 0.3:
                        logger.info(f"Found GitHub profile for {creator_name}: @{username}")
                        return enhanced_data
            
            # If direct lookup fails, try search
            search_results = self.search_users(creator_name, 5)
            
            for user in search_results:
                username = user.get('login')
                if username:
                    user_details = self.get_user_details(username)
                    if user_details:
                        enhanced_data = self._extract_creator_info(user_details, creator_name)
                        if enhanced_data and enhanced_data.get('relevance_score', 0) > 0.4:
                            logger.info(f"Found GitHub profile via search for {creator_name}: @{username}")
                            return enhanced_data
            
            logger.info(f"No relevant GitHub profile found for creator: {creator_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for creator {creator_name}: {str(e)}")
            return None
    
    def search_creator_by_username(self, username: str) -> Optional[Dict]:
        """Search for a creator by exact GitHub username"""
        try:
            # Direct username lookup
            user_data = self._make_api_request(f'users/{username}')
            
            if user_data:
                creator_info = self._extract_creator_info(user_data, username)
                logger.info(f"Found GitHub profile: @{username}")
                return creator_info
            else:
                logger.info(f"No GitHub profile found for username: {username}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for username {username}: {str(e)}")
            return None
    
    def _generate_username_variations(self, creator_name: str) -> List[str]:
        """Generate possible GitHub usernames from creator name"""
        # Clean the name
        clean_name = re.sub(r'[^\w\s]', '', creator_name.lower())
        words = clean_name.split()
        
        variations = []
        
        # Direct variations
        variations.append(clean_name.replace(' ', ''))  # "business basics" -> "businessbasics"
        variations.append(clean_name.replace(' ', '-'))  # "business basics" -> "business-basics"
        variations.append(clean_name.replace(' ', '_'))  # "business basics" -> "business_basics"
        variations.append(''.join(word[:3] for word in words))  # "business basics" -> "busbas"
        
        # Single words
        for word in words:
            if len(word) > 3:
                variations.append(word)
        
        # First word + common suffixes
        if words:
            first_word = words[0]
            variations.extend([
                f"{first_word}dev",
                f"{first_word}code", 
                f"{first_word}tech",
                f"the{first_word}",
                f"{first_word}official"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen and len(var) >= 3:
                seen.add(var)
                unique_variations.append(var)
        
        return unique_variations
    
    def _extract_creator_info(self, user_data: Dict, original_creator_name: str) -> Dict:
        """Extract relevant information from GitHub user data"""
        try:
            extracted_urls = []
            
            # Extract blog/website URL
            if user_data.get('blog'):
                blog_url = user_data['blog']
                if not blog_url.startswith(('http://', 'https://')):
                    blog_url = 'https://' + blog_url
                extracted_urls.append(blog_url)
            
            # Get repositories for additional website links
            username = user_data.get('login')
            if username:
                repos = self.get_user_repositories(username, 5)
                for repo in repos:
                    if repo.get('homepage'):
                        homepage = repo['homepage']
                        if not homepage.startswith(('http://', 'https://')):
                            homepage = 'https://' + homepage
                        extracted_urls.append(homepage)
            
            # Clean and categorize URLs
            website_urls = []
            for url in extracted_urls:
                cleaned_url = self._clean_and_validate_url(url)
                if cleaned_url:
                    domain = urlparse(cleaned_url).netloc.lower()
                    # Skip GitHub domains and common dev platforms
                    if not any(skip in domain for skip in ['github.com', 'github.io', 'localhost', '127.0.0.1']):
                        website_urls.append(cleaned_url)
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(
                user_data.get('name', ''),
                user_data.get('bio', ''),
                original_creator_name,
                user_data.get('followers', 0),
                user_data.get('public_repos', 0)
            )
            
            return {
                'creator_name': original_creator_name,
                'github_username': user_data.get('login'),
                'github_name': user_data.get('name'),
                'github_bio': user_data.get('bio', ''),
                'github_followers': user_data.get('followers', 0),
                'github_following': user_data.get('following', 0),
                'github_public_repos': user_data.get('public_repos', 0),
                'github_company': user_data.get('company'),
                'github_location': user_data.get('location'),
                'github_created_at': user_data.get('created_at'),
                'website_urls': list(set(website_urls)),  # Remove duplicates
                'relevance_score': relevance_score,
                'source': 'github_api'
            }
            
        except Exception as e:
            logger.error(f"Error extracting GitHub creator info: {str(e)}")
            return None
    
    def _clean_and_validate_url(self, url: str) -> Optional[str]:
        """Clean and validate URL"""
        try:
            if not url or url in ['', 'null', 'undefined']:
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
    
    def _calculate_relevance_score(self, github_name: str, bio: str, creator_name: str, followers: int, repos: int) -> float:
        """Calculate relevance score for the GitHub profile match"""
        score = 0.0
        
        # Name similarity
        if github_name:
            name_lower = github_name.lower()
            creator_lower = creator_name.lower()
            
            # Exact name match
            if creator_lower in name_lower or name_lower in creator_lower:
                score += 0.4
            
            # Individual words match
            creator_words = creator_lower.split()
            name_words = name_lower.split()
            word_matches = sum(1 for word in creator_words if word in name_words)
            if creator_words:
                score += (word_matches / len(creator_words)) * 0.3
        
        # Bio analysis
        if bio:
            bio_lower = bio.lower()
            creator_lower = creator_name.lower()
            
            # Creator name in bio
            if creator_lower in bio_lower:
                score += 0.2
            
            # Keywords that suggest content creation
            creator_keywords = ['youtube', 'creator', 'content', 'video', 'channel', 'developer', 'programmer', 'coder']
            keyword_matches = sum(1 for keyword in creator_keywords if keyword in bio_lower)
            score += min(keyword_matches * 0.05, 0.15)
        
        # Activity indicators (followers and repos suggest active developer)
        if followers > 100:
            score += 0.1
        if repos > 10:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def enhance_youtube_creators_with_github(self, creators_data: List[Dict]) -> List[Dict]:
        """Enhance YouTube creator data with GitHub profile information"""
        enhanced_creators = []
        
        for creator in creators_data:
            creator_name = creator.get('channel_title', '')
            
            if creator_name:
                # Search for GitHub profile
                github_info = self.search_creator_by_name(creator_name)
                
                # Merge data
                enhanced_creator = {**creator}  # Copy original data
                
                if github_info and github_info.get('relevance_score', 0) > 0.3:
                    enhanced_creator.update({
                        'github_username': github_info.get('github_username'),
                        'github_name': github_info.get('github_name'),
                        'github_bio': github_info.get('github_bio'),
                        'github_followers': github_info.get('github_followers'),
                        'github_public_repos': github_info.get('github_public_repos'),
                        'github_company': github_info.get('github_company'),
                        'github_location': github_info.get('github_location'),
                        'additional_github_urls': github_info.get('website_urls', []),
                        'github_relevance_score': github_info.get('relevance_score'),
                        'enhanced_with_github': True
                    })
                    
                    logger.info(f"Enhanced {creator_name} with GitHub data")
                else:
                    enhanced_creator['enhanced_with_github'] = False
                
                enhanced_creators.append(enhanced_creator)
                
                # Be respectful with API calls
                time.sleep(0.2)  # GitHub allows higher rates than X
        
        return enhanced_creators

def test_github_integration():
    """Test the GitHub integration"""
    scraper = GitHubCreatorScraper()
    
    # Check if credentials are available
    if not scraper.access_token:
        print("❌ GitHub access token not configured")
        print("Please set GITHUB_ACCESS_TOKEN in your .env file")
        return
    
    print(f"🔍 GitHub API - Remaining requests: {scraper.remaining_requests}")
    
    # Test with tech-focused creators
    test_creators = [
        'Fireship',      # Known tech YouTuber with GitHub
        'Traversy Media', # Web dev YouTuber  
        'Coding Train',   # Creative coding
        'Business Basics' # Test with non-tech creator
    ]
    
    print("Testing GitHub API integration...")
    for creator in test_creators:
        print(f"\n🔍 Searching for: {creator}")
        result = scraper.search_creator_by_name(creator)
        if result:
            print(f"✅ Found: @{result.get('github_username')}")
            if result.get('github_name'):
                print(f"   Name: {result.get('github_name')}")
            print(f"   Followers: {result.get('github_followers', 0):,}")
            print(f"   Repos: {result.get('github_public_repos', 0)}")
            print(f"   Website URLs: {result.get('website_urls', [])}")
            print(f"   Relevance: {result.get('relevance_score', 0):.2f}")
            if result.get('github_bio'):
                print(f"   Bio: {result.get('github_bio', '')[:100]}...")
        else:
            print("❌ Not found")

if __name__ == "__main__":
    test_github_integration()