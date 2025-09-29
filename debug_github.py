#!/usr/bin/env python3
"""
Quick debug test for GitHub API to isolate the issue
"""
import os
from dotenv import load_dotenv

load_dotenv()

def debug_github_user_data():
    """Debug the exact user data returned by GitHub API"""
    print("=== GitHub API Debug Test ===")
    
    try:
        from app.services.github_scraper import GitHubCreatorScraper
        
        scraper = GitHubCreatorScraper()
        
        # Test direct API call
        print("1. Testing direct API call...")
        raw_data = scraper._make_api_request('users/octocat')
        
        if raw_data:
            print("✅ Raw API response received")
            print(f"   Keys in response: {list(raw_data.keys())}")
            print(f"   Login: {raw_data.get('login')}")
            print(f"   Name: {raw_data.get('name')}")
            print(f"   Followers: {raw_data.get('followers')}")
            print(f"   Bio: {raw_data.get('bio')}")
            print(f"   Blog: {raw_data.get('blog')}")
        else:
            print("❌ No raw data returned")
            return
        
        # Test data extraction
        print("\n2. Testing data extraction...")
        try:
            extracted = scraper._extract_creator_info(raw_data, 'octocat')
            
            if extracted:
                print("✅ Data extraction successful")
                print(f"   Creator name: {extracted.get('creator_name')}")
                print(f"   GitHub username: {extracted.get('github_username')}")
                print(f"   GitHub name: {extracted.get('github_name')}")
                print(f"   Followers: {extracted.get('github_followers')}")
                print(f"   Website URLs: {extracted.get('website_urls')}")
                print(f"   Relevance score: {extracted.get('relevance_score')}")
            else:
                print("❌ Data extraction returned None")
                
        except Exception as e:
            print(f"❌ Error in data extraction: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Test full search method
        print("\n3. Testing full search method...")
        try:
            result = scraper.search_creator_by_username('octocat')
            
            if result:
                print("✅ Full search successful")
                print(f"   Result type: {type(result)}")
                print(f"   Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            else:
                print("❌ Full search returned None")
                
        except Exception as e:
            print(f"❌ Error in full search: {str(e)}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_github_user_data()