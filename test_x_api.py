#!/usr/bin/env python3
"""
Test script for X (Twitter) API integration
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_environment():
    """Test if environment variables are loaded"""
    print("=== Environment Variables Check ===")
    
    required_vars = [
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET', 
        'TWITTER_BEARER_TOKEN',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first 10 chars for security
            display_value = value[:10] + '...' if len(value) > 10 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    return all_set

def test_twitter_scraper():
    """Test the TwitterCreatorScraper initialization"""
    print("\n=== Testing TwitterCreatorScraper ===")
    
    try:
        # Import and initialize
        from app.services.twitter_scraper import TwitterCreatorScraper
        
        scraper = TwitterCreatorScraper()
        print("✅ TwitterCreatorScraper initialized successfully")
        
        # Check credentials are loaded
        if scraper.api_key and scraper.access_token:
            print("✅ API credentials loaded properly")
        else:
            print("❌ API credentials not loaded")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing TwitterCreatorScraper: {str(e)}")
        return False

def test_bearer_token():
    """Test getting bearer token"""
    print("\n=== Testing Bearer Token ===")
    
    try:
        from app.services.twitter_scraper import TwitterCreatorScraper
        
        scraper = TwitterCreatorScraper()
        bearer_token = scraper._get_bearer_token()
        
        if bearer_token:
            print(f"✅ Bearer token obtained: {bearer_token[:20]}...")
            return True
        else:
            print("❌ Failed to get bearer token")
            return False
            
    except Exception as e:
        print(f"❌ Error getting bearer token: {str(e)}")
        return False

def test_api_request():
    """Test a simple API request"""
    print("\n=== Testing API Request ===")
    
    try:
        from app.services.twitter_scraper import TwitterCreatorScraper
        
        scraper = TwitterCreatorScraper()
        
        # Test with a known username
        print("🔍 Searching for 'elonmusk' profile...")
        result = scraper._make_api_request('users/by/username/elonmusk', {
            'user.fields': 'public_metrics,description'
        })
        
        if result and 'data' in result:
            user = result['data']
            print(f"✅ Found user: {user.get('name', 'Unknown')}")
            print(f"   Username: @{user.get('username', 'unknown')}")
            print(f"   Followers: {user.get('public_metrics', {}).get('followers_count', 0):,}")
            return True
        else:
            print(f"❌ API request failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error making API request: {str(e)}")
        return False

def test_creator_search():
    """Test searching for YouTube creators on X"""
    print("\n=== Testing Creator Search ===")
    
    try:
        from app.services.twitter_scraper import TwitterCreatorScraper
        
        scraper = TwitterCreatorScraper()
        
        # Test with some known creators
        test_creators = ['MrBeast', 'PewDiePie']
        
        for creator in test_creators:
            print(f"\n🔍 Searching for creator: {creator}")
            result = scraper.search_creator_by_username(creator)
            
            if result:
                print(f"✅ Found: @{result.get('twitter_username')}")
                print(f"   Followers: {result.get('twitter_followers', 0):,}")
                print(f"   Relevance: {result.get('relevance_score', 0):.2f}")
                print(f"   Websites: {result.get('website_urls', [])}")
            else:
                print(f"❌ Not found: {creator}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in creator search: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting X API Integration Tests\n")
    
    # Test 1: Environment Variables
    if not test_environment():
        print("\n❌ Environment variables not properly configured")
        sys.exit(1)
    
    # Test 2: TwitterCreatorScraper
    if not test_twitter_scraper():
        print("\n❌ TwitterCreatorScraper initialization failed")
        sys.exit(1)
    
    # Test 3: Bearer Token
    if not test_bearer_token():
        print("\n❌ Bearer token test failed")
        sys.exit(1)
    
    # Test 4: API Request
    if not test_api_request():
        print("\n❌ API request test failed")
        sys.exit(1)
    
    # Test 5: Creator Search
    if not test_creator_search():
        print("\n❌ Creator search test failed")
        sys.exit(1)
    
    print("\n🎉 All X API tests passed successfully!")
    print("\nYour X API integration is working correctly!")

if __name__ == "__main__":
    main()