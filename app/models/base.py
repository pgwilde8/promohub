from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Lead source and qualification
    lead_source = Column(String(100))  # youtube_outreach, creator_forums, social_media, etc.
    customer_type = Column(String(100))  # youtube_creator, business_owner, entrepreneur, etc.
    business_size = Column(String(50))  # subscriber_count for YouTube: <1k, 1k-10k, 10k-100k, 100k+
    industry = Column(String(100))  # gaming, education, fitness, cooking, tech, business, entertainment
    
    # Contact and company info
    company = Column(String(255))  # Channel name for YouTube creators or business name
    phone = Column(String(50))
    website_url = Column(String(500))  # YouTube channel URL or company website
    
    # Lead qualification
    status = Column(String(50), default="new")  # new, contacted, qualified, demo_scheduled, trial, customer, unsubscribed
    qualification_level = Column(String(50), default="cold")  # cold, warm, hot, customer
    lead_score = Column(Integer, default=0)  # 0-100 scoring
    
    # Context specific to customer type (stored as JSON for flexibility)
    customer_context = Column(JSON)  # Flexible field to store customer-specific data
    # Examples:
    # YouTube Creator: {"youtube_channel_url": "...", "subscriber_count": "10k-100k", "monthly_views": "100k-1M", "content_niche": "gaming", "monetization_status": "monetized"}
    # Business Owner: {"business_type": "restaurant", "location": "NYC", "team_size": "5-10", "current_tools": ["pos_system", "website"]}
    # SaaS Founder: {"company_stage": "seed", "team_size": "10-50", "funding": "series_a", "tech_stack": ["react", "python"]}
    
    # Business context
    current_solution = Column(String(255))  # Discord, Patreon, own website, competitor, etc.
    pain_points = Column(Text)  # main challenges they're facing
    budget_range = Column(String(50))  # $0-50, $50-200, $200-500, $500+
    decision_timeline = Column(String(50))  # immediate, 1-3_months, 3-6_months, exploring
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_contact_date = Column(DateTime(timezone=True))
    next_follow_up_date = Column(DateTime(timezone=True))
    
    # Sales process
    assigned_to = Column(String(255))  # sales person (probably you for now)
    notes = Column(Text)
    conversion_date = Column(DateTime(timezone=True))
    lifetime_value = Column(Float, default=0.0)
    
    # Relationships
    owner = relationship("Account", back_populates="leads")
    product = relationship("Product", back_populates="leads")
    outreach_logs = relationship("OutreachLog", back_populates="lead")
    page_views = relationship("PageView", back_populates="lead")


class OutreachLog(Base):
    __tablename__ = "outreach_log"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)  # optional: link to specific campaign
    email_template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)  # optional: which template was used
    
    # Email content
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="sent")  # sent, delivered, opened, replied, bounced
    
    # Campaign context
    email_type = Column(String(50))  # cold_outreach, follow_up, nurture, promotional, retarget
    sequence_step = Column(Integer, default=1)  # which email in sequence (1, 2, 3, etc.)
    
    # Email tracking
    email_provider = Column(String(100))  # smtp provider used
    message_id = Column(String(255))  # email message ID for tracking
    opens = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    reply_received = Column(Boolean, default=False)
    unsubscribed = Column(Boolean, default=False)
    
    # A/B testing
    variant = Column(String(50))  # A, B, C for A/B testing
    subject_line_variant = Column(String(50))  # if testing subject lines
    
    # Performance metrics
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    response_rate = Column(Float, default=0.0)
    
    # Follow-up tracking
    follow_up_scheduled = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True))
    
    # Relationships
    lead = relationship("Lead", back_populates="outreach_logs")
    campaign = relationship("Campaign", back_populates="outreach_logs")
    email_template = relationship("EmailTemplate", back_populates="outreach_logs")


class Content(Base):
    __tablename__ = "content"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    secondary_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # for cross-selling content
    
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="draft")  # draft, published, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Audience and positioning
    target_audience = Column(String(100))  # specific audience segment
    content_angle = Column(String(100))  # creator_growth, community_building, monetization, platform_comparison
    
    # SEO and metadata
    slug = Column(String(500), unique=True, index=True)
    meta_description = Column(Text)
    tags = Column(String(500))  # comma-separated tags
    
    # Content strategy
    content_type = Column(String(50), default="blog_post")  # blog_post, case_study, guide, comparison
    content_pillar = Column(String(100))  # educational, promotional, entertainment, industry_news
    content_goal = Column(String(100))  # awareness, lead_gen, nurture, conversion, retention
    
    # AI generation info
    ai_prompt = Column(Text)  # the prompt used to generate this content
    target_keywords = Column(String(500))  # SEO keywords
    
    # Performance tracking
    views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    avg_time_on_page = Column(Float, default=0.0)  # seconds
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    leads_generated = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    
    # Call-to-action tracking
    cta_text = Column(String(255))  # "Try [Product] Free", "Get [Product] Demo"
    cta_clicks = Column(Integer, default=0)
    cta_conversion_rate = Column(Float, default=0.0)
    
    # Relationships
    owner = relationship("Account")
    product = relationship("Product", foreign_keys=[product_id], back_populates="content")
    secondary_product = relationship("Product", foreign_keys=[secondary_product_id])
    social_logs = relationship("SocialLog", back_populates="content")


class SocialLog(Base):
    __tablename__ = "social_log"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)  # optional: link to campaign
    
    platform = Column(String(50), nullable=False)  # twitter, linkedin, facebook, instagram
    post_text = Column(Text, nullable=False)
    posted_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="posted")  # posted, failed, deleted, scheduled
    
    # Post categorization
    post_type = Column(String(50))  # promotional, educational, engagement, case_study, industry_news
    
    # Platform-specific data
    platform_post_id = Column(String(255))  # ID from the social platform
    platform_url = Column(String(500))  # Direct link to the post
    
    # Content elements
    hashtags = Column(String(500))  # used hashtags
    mentions = Column(String(500))  # mentioned users/brands
    media_urls = Column(JSON)  # attached images/videos
    
    # Engagement metrics (updated from platform APIs)
    engagement_likes = Column(Integer, default=0)
    engagement_shares = Column(Integer, default=0)
    engagement_comments = Column(Integer, default=0)
    engagement_clicks = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    
    # Performance calculations
    engagement_rate = Column(Float, default=0.0)  # (likes + shares + comments) / impressions
    click_through_rate = Column(Float, default=0.0)  # clicks / impressions
    
    # Scheduling and automation
    scheduled_for = Column(DateTime(timezone=True))  # if scheduled
    posted_by = Column(String(50), default="auto")  # auto, manual, user_name
    
    # Lead generation tracking
    profile_visits = Column(Integer, default=0)
    website_clicks = Column(Integer, default=0)
    leads_generated = Column(Integer, default=0)
    
    # Relationships
    owner = relationship("Account")
    content = relationship("Content", back_populates="social_logs")
    campaign = relationship("Campaign")


class PageView(Base):
    __tablename__ = "page_views"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)  # nullable for anonymous views
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # which product this page view relates to
    
    # Page and visit data
    page = Column(String(500), nullable=False)  # URL path visited
    page_title = Column(String(500))  # Page title for better analytics
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(String(255), index=True)  # for tracking user sessions
    
    # Page categorization
    page_category = Column(String(100))  # home, pricing, demo, blog, case_study, signup
    
    # Visitor identification
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    referrer = Column(String(500))
    
    # UTM campaign tracking
    utm_source = Column(String(255))  # google, linkedin, twitter, direct
    utm_medium = Column(String(255))  # cpc, social, email, organic
    utm_campaign = Column(String(255))  # campaign name
    utm_content = Column(String(255))  # button_cta, text_link
    utm_term = Column(String(255))  # targeted keywords
    
    # Conversion funnel tracking
    is_pricing_page = Column(Boolean, default=False)
    is_signup_page = Column(Boolean, default=False)
    is_demo_page = Column(Boolean, default=False)
    is_contact_page = Column(Boolean, default=False)
    is_trial_page = Column(Boolean, default=False)
    
    # Engagement metrics
    time_on_page = Column(Integer)  # seconds spent on page
    scroll_percentage = Column(Float)  # how much of page was scrolled
    clicks_on_page = Column(Integer, default=0)  # interactions
    
    # Geographic and device data
    country = Column(String(100))
    city = Column(String(100))
    region = Column(String(100))
    device_type = Column(String(50))  # desktop, mobile, tablet
    browser = Column(String(100))
    operating_system = Column(String(100))
    
    # Lead scoring factors
    is_return_visitor = Column(Boolean, default=False)
    visit_number = Column(Integer, default=1)  # 1st visit, 2nd visit, etc.
    pages_in_session = Column(Integer, default=1)
    session_duration = Column(Integer)  # total session time in seconds
    
    # Conversion tracking
    converted_on_visit = Column(Boolean, default=False)
    conversion_type = Column(String(50))  # trial_signup, demo_request, contact_form
    conversion_value = Column(Float, default=0.0)
    
    # Relationships
    owner = relationship("Account")
    lead = relationship("Lead", back_populates="page_views")
    product = relationship("Product")