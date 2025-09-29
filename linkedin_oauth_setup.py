"""
LinkedIn OAuth Setup Helper for PromoHub
Generates the OAuth URL and handles token exchange
"""

import os
from urllib.parse import urlencode

def generate_linkedin_oauth_url():
    """Generate LinkedIn OAuth authorization URL"""
    
    # Your app credentials (update these)
    client_id = "YOUR_LINKEDIN_CLIENT_ID"  # Get from LinkedIn app
    redirect_uri = "http://localhost:8005/auth/linkedin/callback"  # Your callback URL
    
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'r_liteprofile r_emailaddress r_organization_social',
        'state': 'linkedin_promohub_auth'
    }
    
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    
    print("LinkedIn OAuth Setup Instructions:")
    print("=" * 50)
    print(f"1. Go to: {auth_url}")
    print("2. Authorize the app")
    print("3. Copy the 'code' parameter from the callback URL")
    print("4. Use that code to get your access token")
    print()
    print("Callback URL to set in LinkedIn app:")
    print(f"   {redirect_uri}")

if __name__ == "__main__":
    generate_linkedin_oauth_url()