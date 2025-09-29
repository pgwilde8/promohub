"""
API endpoints for YouTube Creator Scraper
"""

from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.youtube_scraper import run_youtube_creator_scraper, scrape_gaming_creators, scrape_all_niches

router = APIRouter(prefix="/api/scraper", tags=["youtube-scraper"])


@router.get("/youtube/stats")
async def get_scraper_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get YouTube scraper statistics and status"""
    try:
        from sqlalchemy import text
        
        # Count leads from YouTube scraping
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_creator_leads,
                COUNT(CASE WHEN email NOT LIKE 'unknown@%' THEN 1 END) as enriched_creator_leads,
                COUNT(CASE WHEN lead_source = 'youtube_creator_scraper' AND email LIKE 'unknown@%' THEN 1 END) as pending_creator_enrichment,
                COUNT(CASE WHEN verified = true AND lead_source = 'youtube_creator_scraper' THEN 1 END) as verified_creator_leads,
                AVG(CASE WHEN confidence IS NOT NULL AND lead_source = 'youtube_creator_scraper' THEN confidence END) as avg_creator_confidence
            FROM leads 
            WHERE lead_source = 'youtube_creator_scraper'
        """)).fetchone()
        
        return {
            "success": True,
            "data": {
                "total_creator_leads": result.total_creator_leads or 0,
                "enriched_creator_leads": result.enriched_creator_leads or 0,
                "pending_creator_enrichment": result.pending_creator_enrichment or 0,
                "verified_creator_leads": result.verified_creator_leads or 0,
                "avg_creator_confidence": float(result.avg_creator_confidence or 0),
                "creator_enrichment_rate": (result.enriched_creator_leads / result.total_creator_leads * 100) if result.total_creator_leads > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting scraper stats: {str(e)}")


@router.post("/youtube/run")
async def trigger_youtube_scraper(
    background_tasks: BackgroundTasks,
    niches: List[str] = None,
    max_per_niche: int = 25,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Manually trigger YouTube creator scraper"""
    try:
        # Run scraper in background
        background_tasks.add_task(run_youtube_creator_scraper, niches, max_per_niche)
        
        return {
            "success": True,
            "message": f"YouTube creator scraper started in background",
            "niches": niches or ["all"],
            "max_per_niche": max_per_niche
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting YouTube scraper: {str(e)}")


@router.post("/youtube/gaming")
async def scrape_gaming_creators_endpoint(
    background_tasks: BackgroundTasks,
    max_count: int = 25
) -> Dict[str, Any]:
    """Scrape gaming YouTube creators specifically"""
    try:
        background_tasks.add_task(scrape_gaming_creators, max_count)
        
        return {
            "success": True,
            "message": f"Gaming creator scraper started (max {max_count} creators)",
            "niche": "gaming"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting gaming scraper: {str(e)}")


@router.post("/youtube/all-niches")
async def scrape_all_niches_endpoint(
    background_tasks: BackgroundTasks,
    max_per_niche: int = 25
) -> Dict[str, Any]:
    """Scrape all target niches for YouTube creators"""
    try:
        background_tasks.add_task(scrape_all_niches, max_per_niche)
        
        return {
            "success": True,
            "message": f"All niches scraper started ({max_per_niche} per niche)",
            "niches": ["gaming", "education", "fitness", "business", "technology", "creative"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting all niches scraper: {str(e)}")


@router.post("/youtube/conservative")
async def run_conservative_discovery(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Conservative discovery: ~50 creators, ~100 API requests, high-value niches"""
    try:
        from app.bots.scheduler import trigger_youtube_conservative
        
        background_tasks.add_task(trigger_youtube_conservative)
        
        return {
            "success": True,
            "message": "Conservative discovery started (business + education, 25 each)",
            "estimated_quota": "~100 requests",
            "expected_results": "~20-30 business domains"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting conservative discovery: {str(e)}")


@router.post("/youtube/aggressive")  
async def run_aggressive_discovery(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Aggressive discovery: ~300 creators, ~600 API requests, all niches"""
    try:
        from app.bots.scheduler import trigger_youtube_aggressive
        
        background_tasks.add_task(trigger_youtube_aggressive)
        
        return {
            "success": True,
            "message": "Aggressive discovery started (all niches, 50 each)",
            "estimated_quota": "~600 requests", 
            "expected_results": "~100-200 total domains",
            "warning": "High quota usage - use sparingly"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting aggressive discovery: {str(e)}")


@router.post("/youtube/targeted/{niche}")
async def run_targeted_discovery(
    niche: str,
    max_creators: int = 25,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """Targeted discovery: Focus on specific niche"""
    
    valid_niches = ['gaming', 'education', 'fitness', 'business', 'technology', 'creative']
    
    if niche not in valid_niches:
        raise HTTPException(status_code=400, detail=f"Invalid niche. Must be one of: {valid_niches}")
    
    try:
        from app.bots.scheduler import trigger_youtube_targeted
        
        if background_tasks:
            background_tasks.add_task(trigger_youtube_targeted, niche, max_creators)
            message = f"Targeted {niche} discovery started ({max_creators} creators)"
        else:
            result = await trigger_youtube_targeted(niche, max_creators)
            return {
                "success": True,
                "message": f"Targeted {niche} discovery completed",
                "results": result
            }
        
        return {
            "success": True,
            "message": message,
            "niche": niche,
            "max_creators": max_creators,
            "estimated_quota": f"~{max_creators + 10} requests"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting targeted discovery: {str(e)}")


@router.get("/youtube/quota-usage")
async def get_quota_usage_estimates() -> Dict[str, Any]:
    """Get quota usage estimates for different discovery strategies"""
    return {
        "success": True,
        "quota_estimates": {
            "conservative_daily": {
                "creators": 50,
                "requests_per_run": 100,
                "runs_per_day": 2,
                "daily_total": 200,
                "percentage_of_single_key": "2%"
            },
            "aggressive_weekly": {
                "creators": 300,
                "requests_per_run": 600,  
                "runs_per_week": 1,
                "weekly_total": 600,
                "percentage_of_single_key": "6%"
            },
            "targeted_niche": {
                "creators": 25,
                "requests_per_run": 35,
                "description": "Perfect for testing specific niches"
            }
        },
        "recommendations": {
            "daily_production": "Conservative (200 requests/day)",
            "weekly_research": "Aggressive (600 requests/week)",  
            "testing": "Targeted niche (35 requests/test)"
        },
        "current_capacity": {
            "total_daily_quota": 30000,
            "conservative_runs_possible": 150,
            "aggressive_runs_possible": 50
        }
    }


@router.get("/youtube/creators")
async def get_discovered_creators(
    limit: int = 50,
    niche: str = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get list of discovered YouTube creators"""
    try:
        from sqlalchemy import text
        
        query = """
            SELECT name, domain, lead_score, qualification_level, created_at, verified, confidence, organization
            FROM leads 
            WHERE lead_source = 'youtube_creator_scraper'
        """
        params = {}
        
        if niche:
            # This would require storing niche in the database
            # For now, we'll just filter by all
            pass
        
        query += " ORDER BY lead_score DESC, created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        result = db.execute(text(query), params)
        creators = [
            {
                "name": row.name,
                "domain": row.domain,
                "lead_score": row.lead_score,
                "tier": row.qualification_level,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "verified": row.verified,
                "confidence": row.confidence,
                "organization": row.organization
            }
            for row in result.fetchall()
        ]
        
        return {
            "success": True,
            "count": len(creators),
            "creators": creators
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting discovered creators: {str(e)}")


@router.get("/youtube/niches")
async def get_target_niches() -> Dict[str, Any]:
    """Get list of target niches and their keywords"""
    try:
        from app.services.youtube_scraper import YouTubeCreatorScraper
        
        scraper = YouTubeCreatorScraper()
        
        return {
            "success": True,
            "niches": scraper.target_niches,
            "subscriber_thresholds": scraper.min_subscribers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting target niches: {str(e)}")


@router.get("/youtube/test-extraction")
async def test_domain_extraction(url: str) -> Dict[str, Any]:
    """Test domain extraction from a URL"""
    try:
        from app.services.youtube_scraper import YouTubeCreatorScraper
        
        scraper = YouTubeCreatorScraper()
        domain = scraper.extract_domain_from_url(url)
        
        return {
            "success": True,
            "original_url": url,
            "extracted_domain": domain,
            "valid": domain is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing domain extraction: {str(e)}")


@router.post("/youtube/run-sync")
async def run_scraper_sync(
    niche: str = "business",
    max_results: int = 3,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Run the scraper synchronously to see actual results and errors"""
    try:
        from app.services.youtube_scraper import YouTubeCreatorScraper
        
        results = {
            "creators_processed": 0,
            "domains_found": 0,
            "domains_added": 0,
            "errors": [],
            "details": []
        }
        
        # Try without passing db session to match our working debug endpoint
        async with YouTubeCreatorScraper() as scraper:
            # Search for creators in the specified niche
            keywords = scraper.target_niches.get(niche, [niche])
            results["details"].append(f"Searching with keywords: {keywords}")
            
            # Test with just one keyword first to isolate the issue
            test_keyword = [keywords[0]] if keywords else ['business']
            results["details"].append(f"Testing with single keyword: {test_keyword}")
            results["details"].append(f"Scraper API key length: {len(scraper.api_key) if scraper.api_key else 0}")
            
            creator_search_results = await scraper.search_creators_by_keywords(test_keyword, max_results)
            results["details"].append(f"Search returned {len(creator_search_results)} raw results")
            
            if not creator_search_results:
                return {
                    "success": False,
                    "message": f"No creators found for niche: {niche} with keyword: {test_keyword}",
                    "results": results
                }
            
            # Extract channel IDs
            channel_ids = [item['id']['channelId'] for item in creator_search_results if 'id' in item and 'channelId' in item['id']]
            
            # Get detailed channel information
            channel_details = await scraper.get_channel_details(channel_ids)
            
            for channel in channel_details:
                try:
                    # Check subscriber count
                    stats = channel.get('statistics', {})
                    subscriber_count = int(stats.get('subscriberCount', 0))
                    channel_name = channel.get('snippet', {}).get('title', '')
                    
                    results["creators_processed"] += 1
                    
                    if not scraper.meets_subscriber_threshold(subscriber_count):
                        results["details"].append(f"Skipped {channel_name}: {subscriber_count:,} subscribers (below threshold)")
                        continue
                    
                    # Verify niche classification
                    classified_niche = scraper.classify_creator_niche(channel)
                    results["details"].append(f"Channel {channel_name}: classified as '{classified_niche}', searching for '{niche}'")
                    
                    # Temporarily disable strict niche matching to see all results
                    # if classified_niche != niche:
                    #     results["details"].append(f"Skipped {channel_name}: classified as {classified_niche}, not {niche}")
                    #     continue
                    
                    # Extract website domains
                    domains = await scraper.extract_creator_websites(channel)
                    results["domains_found"] += len(domains)
                    
                    if domains:
                        creator_info = {
                            'channel_name': channel_name,
                            'subscriber_count': subscriber_count,
                            'niche': niche,
                            'tier': 'tier3' if subscriber_count >= 100000 else 'tier2' if subscriber_count >= 10000 else 'tier1'
                        }
                        
                        # Add domains to enrichment pipeline
                        added = await scraper.add_domains_to_enrichment(domains, creator_info)
                        results["domains_added"] += added
                        
                        results["details"].append(f"Added {added}/{len(domains)} domains for {channel_name} ({subscriber_count:,} subs)")
                    else:
                        results["details"].append(f"No domains found for {channel_name}")
                    
                except Exception as e:
                    error_msg = f"Error processing {channel.get('snippet', {}).get('title', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    continue
            
            return {
                "success": True,
                "message": f"Synchronous scraper completed for {niche}",
                "results": results
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Synchronous scraper failed"
        }


@router.get("/youtube/debug")
async def debug_scraper() -> Dict[str, Any]:
    """Debug YouTube scraper configuration and API connectivity"""
    try:
        from app.services.youtube_scraper import YouTubeCreatorScraper
        from app.core.config import settings
        
        debug_info = {
            "api_keys_configured": len([k for k in [settings.youtube_api_key, settings.youtube_api_key_2, settings.youtube_api_key_3] if k]),
            "api_key_lengths": [len(k) if k else 0 for k in [settings.youtube_api_key, settings.youtube_api_key_2, settings.youtube_api_key_3]],
            "total_quota_capacity": len([k for k in [settings.youtube_api_key, settings.youtube_api_key_2, settings.youtube_api_key_3] if k]) * 10000
        }
        
        # Test API call with first available key
        try:
            async with YouTubeCreatorScraper() as scraper:
                # Test a simple search
                creators = await scraper.search_creators_by_keywords(['gaming'], 5)
                debug_info["api_test_success"] = True
                debug_info["creators_returned"] = len(creators)
                debug_info["sample_creator"] = creators[0]['snippet']['title'] if creators else None
                debug_info["current_key_index"] = scraper.current_key_index
        except Exception as api_error:
            debug_info["api_test_success"] = False
            debug_info["api_error"] = str(api_error)
        
        return {
            "success": True,
            "debug_info": debug_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error debugging scraper: {str(e)}")


@router.get("/youtube/test-sync")
async def test_scraper_sync(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Run a small synchronous test of the scraper to see detailed results"""
    try:
        from app.services.youtube_scraper import YouTubeCreatorScraper
        from app.core.config import settings
        
        debug_steps = []
        
        # Check if API key is available in settings
        debug_steps.append(f"API keys configured: {len([k for k in [settings.youtube_api_key, settings.youtube_api_key_2, settings.youtube_api_key_3] if k])}")
        debug_steps.append(f"Total quota capacity: {len([k for k in [settings.youtube_api_key, settings.youtube_api_key_2, settings.youtube_api_key_3] if k]) * 10000} requests/day")
        
        async with YouTubeCreatorScraper(db) as scraper:
            # Check if API key is available in scraper instance
            debug_steps.append(f"Scraper API keys available: {len(scraper.api_keys)}")
            debug_steps.append(f"Current API key index: {scraper.current_key_index + 1}/{len(scraper.api_keys)}")
            
            # Step 1: Search for creators
            keywords = scraper.target_niches.get('gaming', ['gaming'])
            debug_steps.append(f"Using keywords: {keywords}")
            
            # Test with just one simple keyword first
            simple_keyword = ['business']  # Changed to business to test channels more likely to have websites
            debug_steps.append(f"Testing with simple keyword: {simple_keyword}")
            
            creator_search_results = await scraper.search_creators_by_keywords(simple_keyword, 3)
            debug_steps.append(f"Search returned {len(creator_search_results)} raw results")
            
            if creator_search_results:
                # Step 2: Extract channel IDs
                channel_ids = [item['id']['channelId'] for item in creator_search_results if 'id' in item and 'channelId' in item['id']]
                debug_steps.append(f"Extracted {len(channel_ids)} channel IDs")
                
                # Step 3: Get detailed channel information
                channel_details = await scraper.get_channel_details(channel_ids)
                debug_steps.append(f"Got details for {len(channel_details)} channels")
                
                # Step 4: Process each channel
                processed_channels = []
                for channel in channel_details:
                    channel_info = {
                        'title': channel.get('snippet', {}).get('title', ''),
                        'subscriber_count': int(channel.get('statistics', {}).get('subscriberCount', 0))
                    }
                    
                    # Check subscriber threshold
                    meets_threshold = scraper.meets_subscriber_threshold(channel_info['subscriber_count'])
                    channel_info['meets_threshold'] = meets_threshold
                    
                    # Check niche classification
                    classified_niche = scraper.classify_creator_niche(channel)
                    channel_info['classified_niche'] = classified_niche
                    channel_info['matches_target'] = classified_niche == 'gaming'
                    
                    # Check for websites
                    domains = await scraper.extract_creator_websites(channel)
                    channel_info['domains_found'] = len(domains)
                    channel_info['domains'] = domains
                    
                    processed_channels.append(channel_info)
                
                debug_steps.append(f"Processed {len(processed_channels)} channels with details")
                
                return {
                    "success": True,
                    "debug_steps": debug_steps,
                    "processed_channels": processed_channels,
                    "message": "Detailed debugging completed"
                }
            else:
                debug_steps.append("No creators found in search")
                return {
                    "success": True,
                    "debug_steps": debug_steps,
                    "message": "No creators found in search"
                }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "debug_steps": debug_steps if 'debug_steps' in locals() else [],
            "message": "Scraper test failed"
        }


@router.post("/youtube/test-twitter-enhancement")
async def test_twitter_enhancement(
    creator_names: List[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Test Twitter/X API enhancement for YouTube creators"""
    
    if not creator_names:
        creator_names = ["Business Basics", "Fox Business", "Smosh Games"]
    
    try:
        from app.services.twitter_scraper import TwitterCreatorScraper
        
        twitter_scraper = TwitterCreatorScraper()
        results = []
        
        for creator_name in creator_names:
            print(f"\n🔍 Testing X enhancement for: {creator_name}")
            
            # Search for creator on X
            twitter_data = twitter_scraper.search_creator_by_username(creator_name)
            
            if twitter_data:
                result = {
                    "creator_name": creator_name,
                    "twitter_found": True,
                    "twitter_username": twitter_data.get('twitter_username'),
                    "twitter_display_name": twitter_data.get('twitter_display_name'),
                    "twitter_followers": twitter_data.get('twitter_followers', 0),
                    "twitter_bio": twitter_data.get('twitter_bio', ''),
                    "website_urls": twitter_data.get('website_urls', []),
                    "social_urls": twitter_data.get('social_urls', []),
                    "relevance_score": twitter_data.get('relevance_score', 0),
                    "status": f"✅ Found @{twitter_data.get('twitter_username')} with {twitter_data.get('twitter_followers', 0):,} followers"
                }
            else:
                result = {
                    "creator_name": creator_name,
                    "twitter_found": False,
                    "status": "❌ Not found on X"
                }
            
            results.append(result)
        
        return {
            "success": True,
            "results": results,
            "message": f"Tested X enhancement for {len(creator_names)} creators"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Twitter enhancement test failed"
        }


@router.post("/youtube/test-github-enhancement")
async def test_github_enhancement(
    creator_names: List[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Test GitHub API enhancement for YouTube creators"""
    
    if not creator_names:
        creator_names = ["Fireship", "Traversy Media", "The Net Ninja", "Business Basics"]
    
    try:
        from app.services.github_scraper import GitHubCreatorScraper
        
        github_scraper = GitHubCreatorScraper()
        results = []
        
        for creator_name in creator_names:
            print(f"\n🔍 Testing GitHub enhancement for: {creator_name}")
            
            # Search for creator on GitHub
            github_data = github_scraper.search_creator_by_name(creator_name)
            
            if github_data and github_data.get('relevance_score', 0) > 0.3:
                result = {
                    "creator_name": creator_name,
                    "github_found": True,
                    "github_username": github_data.get('github_username'),
                    "github_name": github_data.get('github_name'),
                    "github_followers": github_data.get('github_followers', 0),
                    "github_bio": github_data.get('github_bio', ''),
                    "github_public_repos": github_data.get('github_public_repos', 0),
                    "website_urls": github_data.get('website_urls', []),
                    "relevance_score": github_data.get('relevance_score', 0),
                    "status": f"✅ Found @{github_data.get('github_username')} with {github_data.get('github_followers', 0):,} followers"
                }
            else:
                result = {
                    "creator_name": creator_name,
                    "github_found": False,
                    "status": "❌ Not found on GitHub"
                }
            
            results.append(result)
        
        return {
            "success": True,
            "results": results,
            "message": f"Tested GitHub enhancement for {len(creator_names)} creators"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "GitHub enhancement test failed"
        }