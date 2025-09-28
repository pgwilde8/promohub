from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Account(Base):
    """User accounts (you, clients, team members)"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Account type and permissions
    account_type = Column(String(50), default="user")  # admin, user, client
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Subscription/billing (if this becomes a paid service)
    plan_type = Column(String(50), default="free")  # free, basic, pro, enterprise
    subscription_status = Column(String(50), default="active")  # active, cancelled, expired
    max_products = Column(Integer, default=3)  # limit based on plan
    max_leads_per_month = Column(Integer, default=1000)
    max_emails_per_day = Column(Integer, default=100)
    
    # Profile and settings
    timezone = Column(String(50), default="UTC")
    avatar_url = Column(String(500))
    bio = Column(Text)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Relationships
    products = relationship("Product", back_populates="owner")
    campaigns = relationship("Campaign", back_populates="owner")
    leads = relationship("Lead", back_populates="owner")


class Product(Base):
    """Products/services to be marketed"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    # Basic product info
    name = Column(String(255), nullable=False)  # "EZClub", "EZDirectory", "Client's SaaS"
    description = Column(Text)
    website_url = Column(String(500), nullable=False)
    logo_url = Column(String(500))
    
    # Product categorization
    industry = Column(String(100))  # saas, ecommerce, consulting, education
    category = Column(String(100))  # community_platform, directory, crm, etc.
    product_type = Column(String(50), default="saas")  # saas, course, service, physical
    
    # Target market
    target_audience = Column(JSON)  # ["youtube_creators", "business_owners"] - array of audiences
    primary_audience = Column(String(100))  # main target audience
    audience_size_estimate = Column(String(50))  # small, medium, large, enterprise
    
    # Pricing and positioning  
    pricing_model = Column(String(50))  # subscription, one_time, freemium, custom
    starting_price = Column(Float)  # lowest price point
    price_range = Column(String(100))  # "$29-99/month", "Free-$500", etc.
    
    # Marketing context
    value_proposition = Column(Text)  # main selling point
    key_features = Column(JSON)  # array of key features
    pain_points_solved = Column(JSON)  # array of problems it solves
    competitor_alternatives = Column(JSON)  # array of competitors
    
    # Marketing assets and messaging
    brand_voice = Column(String(100), default="professional")  # casual, professional, technical, friendly
    brand_colors = Column(JSON)  # {"primary": "#007bff", "secondary": "#6c757d"}
    tagline = Column(String(255))
    elevator_pitch = Column(Text)  # 30-second description
    
    # Campaign URLs and tracking
    demo_url = Column(String(500))
    trial_url = Column(String(500))  
    pricing_url = Column(String(500))
    contact_url = Column(String(500))
    documentation_url = Column(String(500))
    
    # Performance tracking
    monthly_revenue = Column(Float, default=0.0)  # optional: track revenue
    customer_count = Column(Integer, default=0)  # optional: track customers
    conversion_rate = Column(Float, default=0.0)  # trial to paid, etc.
    
    # Status and settings
    status = Column(String(50), default="active")  # active, paused, archived
    marketing_priority = Column(String(50), default="medium")  # high, medium, low
    auto_campaigns_enabled = Column(Boolean, default=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("Account", back_populates="products")
    campaigns = relationship("Campaign", back_populates="product")
    leads = relationship("Lead", back_populates="product")
    content = relationship("Content", foreign_keys="Content.product_id", back_populates="product")


class Campaign(Base):
    """Marketing campaigns for specific products"""
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Campaign basics
    name = Column(String(255), nullable=False)  # "EZClub YouTube Creator Outreach Q4"
    description = Column(Text)
    campaign_type = Column(String(50), nullable=False)  # email_sequence, content_series, social_campaign, cold_outreach
    
    # Targeting
    target_audience = Column(String(100))  # specific audience from product.target_audience
    audience_filters = Column(JSON)  # specific criteria: subscriber_count, industry, etc.
    geographic_targeting = Column(JSON)  # countries, regions
    
    # Campaign content and strategy
    messaging_angle = Column(String(100))  # problem_solution, feature_benefit, social_proof, comparison
    content_themes = Column(JSON)  # ["community_building", "monetization", "creator_tools"]
    call_to_action = Column(String(255))  # "Start Free Trial", "Book Demo", "Download Guide"
    
    # Scheduling and automation
    status = Column(String(50), default="draft")  # draft, active, paused, completed, archived
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    automation_enabled = Column(Boolean, default=True)
    
    # Performance goals and tracking
    primary_goal = Column(String(100))  # lead_generation, brand_awareness, trial_signups, sales
    target_leads = Column(Integer)  # goal number of leads
    target_conversions = Column(Integer)  # goal number of conversions
    budget_allocated = Column(Float, default=0.0)
    
    # Results tracking  
    leads_generated = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0.0)
    cost_per_lead = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)
    
    # Campaign settings
    email_frequency = Column(String(50), default="weekly")  # daily, weekly, biweekly
    max_emails_per_lead = Column(Integer, default=5)  # sequence length
    follow_up_delay_days = Column(Integer, default=3)
    
    # A/B testing
    ab_testing_enabled = Column(Boolean, default=False)
    variants = Column(JSON)  # array of variant configurations
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_executed_at = Column(DateTime(timezone=True))
    
    # Relationships
    owner = relationship("Account", back_populates="campaigns")
    product = relationship("Product", back_populates="campaigns")
    outreach_logs = relationship("OutreachLog", back_populates="campaign")


class AudienceSegment(Base):
    """Reusable audience segments for targeting"""
    __tablename__ = "audience_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    name = Column(String(255), nullable=False)  # "YouTube Creators 10K+", "SaaS Founders", "Local Businesses"
    description = Column(Text)
    
    # Segment criteria (stored as JSON for flexibility)
    filters = Column(JSON, nullable=False)
    # Example: {
    #   "customer_type": ["youtube_creator"],
    #   "subscriber_count": ["10k-100k", "100k+"], 
    #   "industry": ["gaming", "education"],
    #   "geographic": ["US", "CA", "UK"]
    # }
    
    # Segment size and performance
    estimated_size = Column(Integer)  # how many leads match this segment
    actual_size = Column(Integer, default=0)  # current matched leads
    avg_conversion_rate = Column(Float, default=0.0)  # historical performance
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_shared = Column(Boolean, default=False)  # if other users can see/use this segment
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EmailTemplate(Base):
    """Reusable email templates for campaigns"""
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # optional: product-specific
    
    # Template basics
    name = Column(String(255), nullable=False)  # "YouTube Creator Cold Intro"
    description = Column(Text)
    template_type = Column(String(50))  # cold_intro, follow_up, nurture, promotional, retarget
    
    # Email content
    subject_line = Column(String(500), nullable=False)
    email_body = Column(Text, nullable=False)
    html_body = Column(Text)  # optional HTML version
    
    # Template configuration
    personalization_fields = Column(JSON)  # ["name", "company", "subscriber_count", etc.]
    merge_tags = Column(JSON)  # available {{variable}} tags
    
    # Audience targeting
    target_audiences = Column(JSON)  # which audiences this template is designed for
    industries = Column(JSON)  # which industries/niches this works for
    
    # Performance tracking
    times_used = Column(Integer, default=0)
    avg_open_rate = Column(Float, default=0.0)
    avg_click_rate = Column(Float, default=0.0)
    avg_response_rate = Column(Float, default=0.0)
    
    # Template settings
    is_active = Column(Boolean, default=True)
    is_ai_generated = Column(Boolean, default=False)
    ai_prompt = Column(Text)  # if AI generated, store the prompt
    
    # Sharing and collaboration
    is_public = Column(Boolean, default=False)  # available to all users
    is_featured = Column(Boolean, default=False)  # featured in template library
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    
    # Relationships
    outreach_logs = relationship("OutreachLog", back_populates="email_template")