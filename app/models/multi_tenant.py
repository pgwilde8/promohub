from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
# Import the base classes from the main models
from app.models.base import Base


# Multi-tenant and client management tables

class Client(Base):
    """Clients/customers who use PromoHub for their marketing"""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Company name
    domain = Column(String(255), unique=True, index=True)  # their website domain
    subdomain = Column(String(100), unique=True, index=True)  # client1.promohub.com
    
    # Contact info
    contact_name = Column(String(255))
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))
    
    # Business info  
    industry = Column(String(100))
    business_type = Column(String(100))  # SaaS, ecommerce, agency, etc.
    company_size = Column(String(50))  # 1-10, 11-50, 51-200, etc.
    monthly_revenue = Column(String(50))  # revenue bracket
    
    # Account status
    status = Column(String(50), default="trial")  # trial, active, suspended, cancelled
    plan_type = Column(String(50), default="basic")  # basic, pro, enterprise
    monthly_fee = Column(Float, default=0.0)
    
    # Limits based on plan
    max_leads = Column(Integer, default=1000)
    max_emails_per_day = Column(Integer, default=100)
    max_social_posts_per_day = Column(Integer, default=10)
    max_blog_posts_per_month = Column(Integer, default=4)
    
    # Setup and tracking
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    trial_ends_at = Column(DateTime(timezone=True))
    last_active_at = Column(DateTime(timezone=True))
    
    # Client-specific settings
    branding_settings = Column(JSON)  # logo, colors, etc.
    email_signature = Column(Text)
    social_handles = Column(JSON)  # Twitter, LinkedIn handles
    
    # Relationships
    projects = relationship("Project", back_populates="client")
    users = relationship("User", back_populates="client")
    leads = relationship("Lead", back_populates="client")
    campaigns = relationship("Campaign", back_populates="client")


class User(Base):
    """Users who can access the PromoHub dashboard"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Role and permissions
    role = Column(String(50), default="user")  # admin, user, viewer
    permissions = Column(JSON)  # specific permissions array
    
    # Account info
    is_active = Column(Boolean, default=True)
    is_client_admin = Column(Boolean, default=False)  # can manage client settings
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Profile
    avatar_url = Column(String(500))
    timezone = Column(String(50), default="UTC")
    
    # Relationship
    client = relationship("Client", back_populates="users")


class Project(Base):
    """Different marketing projects/products for each client"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    name = Column(String(255), nullable=False)  # "EZClub Marketing", "Q4 Product Launch"
    description = Column(Text)
    website_url = Column(String(500))
    
    # Project settings
    status = Column(String(50), default="active")  # active, paused, completed
    industry = Column(String(100))
    target_audience = Column(Text)  # description of ideal customer
    
    # Content strategy
    content_topics = Column(JSON)  # array of topics for content generation
    brand_voice = Column(String(100))  # professional, casual, technical, etc.
    key_messaging = Column(Text)
    
    # Goals and KPIs
    primary_goal = Column(String(100))  # lead_generation, brand_awareness, sales
    monthly_lead_goal = Column(Integer)
    target_conversion_rate = Column(Float)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="projects")
    campaigns = relationship("Campaign", back_populates="project")
    leads = relationship("Lead", back_populates="project")


class Campaign(Base):
    """Marketing campaigns (email sequences, content series, etc.)"""
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    campaign_type = Column(String(50))  # email_sequence, content_series, social_campaign
    
    # Campaign status and schedule
    status = Column(String(50), default="draft")  # draft, active, paused, completed
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    # Targeting
    target_audience = Column(Text)
    lead_filters = Column(JSON)  # criteria for lead selection
    
    # Content and settings
    email_templates = Column(JSON)  # array of email templates
    social_templates = Column(JSON)  # social media post templates
    content_calendar = Column(JSON)  # scheduled content
    
    # Performance tracking
    total_sends = Column(Integer, default=0)
    total_opens = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    budget_allocated = Column(Float, default=0.0)
    budget_spent = Column(Float, default=0.0)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="campaigns")
    project = relationship("Project", back_populates="campaigns")


class EmailTemplate(Base):
    """Reusable email templates for different campaigns"""
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50))  # welcome, nurture, promotional, follow_up
    
    # Email content
    subject_line = Column(String(500), nullable=False)
    email_body = Column(Text, nullable=False)
    html_body = Column(Text)
    
    # Template variables
    variables = Column(JSON)  # list of variables like {name}, {company}, etc.
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    avg_open_rate = Column(Float, default=0.0)
    avg_click_rate = Column(Float, default=0.0)
    
    # Metadata
    is_ai_generated = Column(Boolean, default=False)
    ai_prompt = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class LeadList(Base):
    """Segmented lead lists for targeted campaigns"""
    __tablename__ = "lead_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # List criteria (stored as JSON for flexibility)
    filters = Column(JSON)  # industry, company_size, lead_score, etc.
    
    # Stats
    lead_count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True))
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    lead_assignments = relationship("LeadListAssignment", back_populates="lead_list")


class LeadListAssignment(Base):
    """Many-to-many relationship between leads and lists"""
    __tablename__ = "lead_list_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    lead_list_id = Column(Integer, ForeignKey("lead_lists.id"), nullable=False)
    
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(String(255))  # user who assigned or "auto"
    
    # Relationships
    lead_list = relationship("LeadList", back_populates="lead_assignments")


class Integration(Base):
    """Third-party integrations for each client"""
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    integration_type = Column(String(50), nullable=False)  # stripe, hubspot, salesforce, etc.
    name = Column(String(255), nullable=False)
    
    # Connection details (encrypted)
    api_credentials = Column(JSON)  # API keys, tokens, etc. (should be encrypted)
    webhook_url = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True))
    sync_errors = Column(Text)
    
    # Settings
    sync_frequency = Column(String(50), default="hourly")  # hourly, daily, manual
    field_mappings = Column(JSON)  # how fields map between systems
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ActivityLog(Base):
    """System-wide activity log for auditing and debugging"""
    __tablename__ = "activity_log"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    activity_type = Column(String(50), nullable=False)  # email_sent, lead_created, etc.
    entity_type = Column(String(50))  # lead, campaign, content, etc.
    entity_id = Column(Integer)
    
    description = Column(Text, nullable=False)
    metadata = Column(JSON)  # additional context
    
    # Results
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Tracking
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)