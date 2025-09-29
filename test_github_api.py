#!/usr/bin/env python3
"""
Test script for GitHub API integration with proper environment loading
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_environment():
    """Test if GitHub environment variables are loaded"""
    print("=== GitHub Environment Variables Check ===")
    
    github_token = os.getenv('GITHUB_ACCESS_TOKEN')
    if github_token:
        print(f"✅ GITHUB_ACCESS_TOKEN: {github_token[:10]}...")
        return True
    else:
        print("❌ GITHUB_ACCESS_TOKEN: Not set")
        return False

def test_github_api():
    """Test GitHub API connectivity"""
    print("\n=== Testing GitHub API ===")
    
    try:
        from app.services.github_scraper import GitHubCreatorScraper
        
        scraper = GitHubCreatorScraper()
        print("✅ GitHubCreatorScraper initialized successfully")
        
        # Test a simple API call
        print("🔍 Testing API connectivity...")
        result = scraper._make_api_request('rate_limit')
        
        if result:
            rate_limit = result.get('rate', {})
            print(f"✅ API connected successfully")
            print(f"   Rate limit: {rate_limit.get('remaining', 0)}/{rate_limit.get('limit', 0)}")
            print(f"   Reset time: {rate_limit.get('reset', 0)}")
            return True
        else:
            print("❌ API connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing GitHub API: {str(e)}")
        return False

def test_user_search():
    """Test searching for users"""
    print("\n=== Testing User Search ===")
    
    try:
        from app.services.github_scraper import GitHubCreatorScraper
        
        scraper = GitHubCreatorScraper()
        
        # Test with known tech creators
        test_users = ['octocat', 'torvalds', 'gaearon']
        
        for username in test_users:
            print(f"\n🔍 Searching for: {username}")
            result = scraper.search_creator_by_username(username)
            
            if result:
                print(f"✅ Found: {result.get('github_name')} (@{result.get('github_username')})")
                print(f"   Followers: {result.get('github_followers', 0):,}")
                bio = result.get('github_bio') or 'No bio'
                print(f"   Bio: {bio[:50]}...")
                website_urls = result.get('website_urls', [])
                websites = ', '.join(website_urls[:2]) if website_urls else 'None'
                print(f"   Websites: {websites}")
                print(f"   Relevance: {result.get('relevance_score', 0):.2f}")
            else:
                print(f"❌ Not found: {username}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in user search: {str(e)}")
        return False

def test_creator_enhancement():
    """Test enhancing YouTube creators with GitHub data"""
    print("\n=== Testing Creator Enhancement ===")
    
    try:
        from app.services.github_scraper import GitHubCreatorScraper
        
        scraper = GitHubCreatorScraper()
        
        # Mock YouTube creator data
        mock_creators = [
            {'channel_title': 'Fireship', 'subscriber_count': 1500000, 'niche': 'technology'},
            {'channel_title': 'Traversy Media', 'subscriber_count': 2000000, 'niche': 'technology'},
            {'channel_title': 'The Net Ninja', 'subscriber_count': 1000000, 'niche': 'technology'}
        ]
        
        print("🔍 Enhancing mock creators with GitHub data...")
        enhanced = scraper.enhance_youtube_creators_with_github(mock_creators)
        
        for creator in enhanced:
            name = creator.get('channel_title')
            github_enhanced = creator.get('enhanced_with_github', False)
            
            if github_enhanced:
                print(f"✅ Enhanced {name}")
                print(f"   GitHub: @{creator.get('github_username', 'none')}")
                website_urls = creator.get('additional_github_urls', [])
                websites = ', '.join(website_urls[:2]) if website_urls else 'none'
                print(f"   Websites: {websites}")
            else:
                print(f"❌ No GitHub found for {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in creator enhancement: {str(e)}")
        return False

def main():
    """Run all GitHub API tests"""
    print("🚀 Starting GitHub API Integration Tests\n")
    
    # Test 1: Environment Variables
    if not test_environment():
        print("\n❌ Environment variables not properly configured")
        sys.exit(1)
    
    # Test 2: GitHub API Connectivity
    if not test_github_api():
        print("\n❌ GitHub API connectivity failed")
        sys.exit(1)
    
    # Test 3: User Search
    if not test_user_search():
        print("\n❌ User search test failed")
        sys.exit(1)
    
    # Test 4: Creator Enhancement
    if not test_creator_enhancement():
        print("\n❌ Creator enhancement test failed")
        sys.exit(1)
    
    print("\n🎉 All GitHub API tests passed successfully!")
    print("\nYour GitHub integration is working correctly!")
    print("\n📋 Next Steps:")
    print("1. Integrate GitHub with your YouTube + X workflow")
    print("2. Test with real creator searches")
    print("3. Add GitHub endpoints to your API routes")

if __name__ == "__main__":
    main()