#!/usr/bin/env python3
"""
Seed script to create initial data for PromoHub
- Admin user account
- EZClub and EZDirectory products
- Sample audience segments
- Sample email templates
"""
import sys
import os
import hashlib
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.append('/home/promohub')

from app.core.database import engine
from app.models.platform import Account, Product, AudienceSegment, EmailTemplate

# Create database session
Session = sessionmaker(bind=engine)
session = Session()

def hash_password(password: str) -> str:
    """Simple password hashing using SHA256 (for demo purposes)"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin_user():
    """Create the admin user account"""
    print("Creating admin user...")
    
    # Check if admin user already exists
    existing_admin = session.query(Account).filter(Account.email == "admin@promohub.com").first()
    if existing_admin:
        print("Admin user already exists!")
        return existing_admin
    
    admin_user = Account(
        name="PromoHub Admin",
        email="admin@promohub.com",
        password_hash=hash_password("Securepass"),
        account_type="admin",
        is_active=True,
        is_verified=True,
        plan_type="enterprise",
        max_products=50,
        max_leads_per_month=10000,
        max_emails_per_day=1000,
        timezone="UTC",
        bio="PromoHub system administrator"
    )
    
    session.add(admin_user)
    session.commit()
    print(f"✅ Admin user created: {admin_user.email}")
    return admin_user

def create_products(owner):
    """Create EZClub and EZDirectory products"""
    print("Creating products...")
    
    # Check if products already exist
    existing_ezclub = session.query(Product).filter(Product.name == "EZClub").first()
    existing_ezdirectory = session.query(Product).filter(Product.name == "EZDirectory").first()
    
    products = []
    
    if not existing_ezclub:
        ezclub = Product(
            owner_id=owner.id,
            name="EZClub",
            description="Complete community platform for content creators and businesses to build, manage, and monetize their communities.",
            website_url="https://ezclub.app",
            industry="saas",
            category="community_platform",
            product_type="saas",
            target_audience=["youtube_creators", "content_creators", "online_educators", "gaming_streamers"],
            primary_audience="youtube_creators",
            audience_size_estimate="medium",
            pricing_model="subscription",
            starting_price=29.0,
            price_range="$29-99/month",
            value_proposition="Build, engage, and monetize your community with powerful tools designed for content creators",
            key_features=[
                "Community forums and discussions",
                "Membership tiers and subscriptions",
                "Event planning and management", 
                "Content sharing and media galleries",
                "Direct messaging and chat",
                "Analytics and member insights",
                "Payment processing and monetization",
                "Mobile-responsive design"
            ],
            pain_points_solved=[
                "Scattered community across multiple platforms",
                "Difficulty monetizing audience",
                "Lack of direct communication with fans",
                "No centralized content hub",
                "Limited member engagement tools"
            ],
            competitor_alternatives=["Discord", "Patreon", "Circle", "Mighty Networks"],
            brand_voice="friendly",
            brand_colors={"primary": "#007bff", "secondary": "#6c757d"},
            tagline="Build your community, grow your business",
            elevator_pitch="EZClub helps content creators transform their scattered online following into a thriving, monetized community with all the tools they need in one platform.",
            demo_url="https://ezclub.app/demo",
            trial_url="https://ezclub.app/trial",
            pricing_url="https://ezclub.app/pricing",
            contact_url="https://ezclub.app/contact",
            documentation_url="https://docs.ezclub.app",
            status="active",
            marketing_priority="high",
            auto_campaigns_enabled=True
        )
        session.add(ezclub)
        products.append(ezclub)
    else:
        products.append(existing_ezclub)
        print("EZClub product already exists")
    
    if not existing_ezdirectory:
        ezdirectory = Product(
            owner_id=owner.id,
            name="EZDirectory",
            description="Powerful directory and listing platform for businesses to create searchable databases and marketplaces.",
            website_url="https://ezdirectory.app",
            industry="saas",
            category="directory",
            product_type="saas",
            target_audience=["business_owners", "entrepreneurs", "local_services", "marketplace_creators"],
            primary_audience="business_owners",
            audience_size_estimate="large",
            pricing_model="subscription",
            starting_price=19.0,
            price_range="$19-79/month",
            value_proposition="Create professional directories and marketplaces with advanced search, filtering, and monetization features",
            key_features=[
                "Advanced search and filtering",
                "Business listing management",
                "Review and rating system",
                "Payment processing for listings",
                "SEO optimization tools",
                "Mobile-responsive templates",
                "Analytics and reporting",
                "Multi-language support"
            ],
            pain_points_solved=[
                "Difficulty organizing business information",
                "Poor search functionality",
                "Limited monetization options",
                "Complex setup and maintenance",
                "Poor mobile experience"
            ],
            competitor_alternatives=["WordPress directories", "Custom development", "Yelp", "Yellow Pages"],
            brand_voice="professional",
            brand_colors={"primary": "#28a745", "secondary": "#6c757d"},
            tagline="Organize, search, succeed",
            elevator_pitch="EZDirectory empowers businesses to create professional, searchable directories that connect customers with services while providing multiple monetization opportunities.",
            demo_url="https://ezdirectory.app/demo",
            trial_url="https://ezdirectory.app/trial",
            pricing_url="https://ezdirectory.app/pricing",
            contact_url="https://ezdirectory.app/contact",
            documentation_url="https://docs.ezdirectory.app",
            status="active",
            marketing_priority="medium",
            auto_campaigns_enabled=True
        )
        session.add(ezdirectory)
        products.append(ezdirectory)
    else:
        products.append(existing_ezdirectory)
        print("EZDirectory product already exists")
    
    session.commit()
    print(f"✅ Products created/verified: {len(products)} products")
    return products

def create_audience_segments(owner):
    """Create common audience segments"""
    print("Creating audience segments...")
    
    segments_data = [
        {
            "name": "YouTube Creators 10K+",
            "description": "YouTube content creators with 10,000+ subscribers",
            "filters": {
                "customer_type": ["youtube_creator"],
                "subscriber_count": ["10k-100k", "100k+"],
                "monetization_status": ["monetized", "partner"]
            },
            "estimated_size": 5000
        },
        {
            "name": "Small Business Owners",
            "description": "Local and small business owners looking for directory solutions",
            "filters": {
                "customer_type": ["business_owner"],
                "business_size": ["1-10", "10-50"],
                "industry": ["local_services", "retail", "restaurants"]
            },
            "estimated_size": 15000
        },
        {
            "name": "Gaming Content Creators",
            "description": "Gaming-focused content creators across platforms",
            "filters": {
                "customer_type": ["youtube_creator", "content_creator"],
                "content_niche": ["gaming"],
                "subscriber_count": ["1k-10k", "10k-100k", "100k+"]
            },
            "estimated_size": 3000
        }
    ]
    
    created_segments = []
    for segment_data in segments_data:
        existing = session.query(AudienceSegment).filter(
            AudienceSegment.name == segment_data["name"]
        ).first()
        
        if not existing:
            segment = AudienceSegment(
                owner_id=owner.id,
                name=segment_data["name"],
                description=segment_data["description"],
                filters=segment_data["filters"],
                estimated_size=segment_data["estimated_size"]
            )
            session.add(segment)
            created_segments.append(segment)
        else:
            created_segments.append(existing)
    
    session.commit()
    print(f"✅ Audience segments created/verified: {len(created_segments)} segments")
    return created_segments

def create_email_templates(owner, products):
    """Create sample email templates"""
    print("Creating email templates...")
    
    templates_data = [
        {
            "name": "YouTube Creator Cold Intro",
            "description": "Initial outreach email for YouTube creators",
            "template_type": "cold_intro",
            "subject_line": "Transform Your {{subscriber_count}} Subscribers Into a Thriving Community",
            "email_body": """Hi {{name}},

I've been following your {{content_niche}} content and love what you're doing with your channel! With {{subscriber_count}} subscribers, you've built an amazing audience.

I wanted to reach out because I think you'd be interested in EZClub - a platform specifically designed for content creators like you to build and monetize their communities beyond just YouTube.

Many creators struggle with:
• Scattered community across multiple platforms (YouTube comments, Discord, social media)
• Difficulty monetizing their audience directly
• Limited ways to engage with their most dedicated fans

EZClub solves this by giving you a dedicated community platform where you can:
✅ Create membership tiers and recurring revenue
✅ Host exclusive content and discussions
✅ Direct communication with your biggest fans
✅ Built-in payment processing and analytics

Would you be interested in a quick 15-minute demo to see how {{name}} could use EZClub to grow their community and revenue?

Best regards,
PromoHub Team

P.S. We're offering a 30-day free trial for YouTube creators - no credit card required.""",
            "target_audiences": ["youtube_creators", "content_creators"],
            "personalization_fields": ["name", "subscriber_count", "content_niche"],
            "product_specific": "EZClub"
        },
        {
            "name": "Business Directory Follow-up",
            "description": "Follow-up email for business owners interested in directory solutions",
            "template_type": "follow_up",
            "subject_line": "Quick question about your {{business_type}} directory needs",
            "email_body": """Hi {{name}},

I sent you an email last week about EZDirectory and how it can help {{company}} create a professional directory solution.

I know you're busy running your {{business_type}} business, so I'll keep this short.

Many business owners tell us they struggle with:
• Customers can't easily find what they're looking for
• Competitors are getting more visibility online
• Managing business listings is time-consuming and confusing

That's exactly why we built EZDirectory. It takes 5 minutes to set up and immediately gives you:
✅ Professional, searchable directory
✅ Advanced filtering and search tools
✅ Mobile-optimized design
✅ Built-in SEO optimization

Would a quick 10-minute demo this week work for you? I can show you exactly how other {{business_type}} businesses are using EZDirectory to organize their services and attract more customers.

Let me know what works!

Best,
PromoHub Team""",
            "target_audiences": ["business_owners", "entrepreneurs"],
            "personalization_fields": ["name", "company", "business_type"],
            "product_specific": "EZDirectory"
        }
    ]
    
    created_templates = []
    for template_data in templates_data:
        existing = session.query(EmailTemplate).filter(
            EmailTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            # Find the product for this template
            product = None
            if template_data.get("product_specific"):
                product = next((p for p in products if p.name == template_data["product_specific"]), None)
            
            template = EmailTemplate(
                owner_id=owner.id,
                product_id=product.id if product else None,
                name=template_data["name"],
                description=template_data["description"],
                template_type=template_data["template_type"],
                subject_line=template_data["subject_line"],
                email_body=template_data["email_body"],
                personalization_fields=template_data["personalization_fields"],
                target_audiences=template_data["target_audiences"],
                industries=template_data.get("industries", [])
            )
            session.add(template)
            created_templates.append(template)
        else:
            created_templates.append(existing)
    
    session.commit()
    print(f"✅ Email templates created/verified: {len(created_templates)} templates")
    return created_templates

def main():
    """Main seeding function"""
    print("🌱 Starting PromoHub data seeding...")
    
    try:
        # Create admin user
        admin_user = create_admin_user()
        
        # Create products
        products = create_products(admin_user)
        
        # Create audience segments
        segments = create_audience_segments(admin_user)
        
        # Create email templates
        templates = create_email_templates(admin_user, products)
        
        print("\n🎉 Seeding completed successfully!")
        print(f"✅ Admin user: {admin_user.email}")
        print(f"✅ Products: {len(products)}")
        print(f"✅ Audience segments: {len(segments)}")
        print(f"✅ Email templates: {len(templates)}")
        
        print("\n🔐 Login credentials:")
        print("Email: admin@promohub.com")
        print("Password: Securepass")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()