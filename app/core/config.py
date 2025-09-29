from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # External IP
    external_ip: str
    
    # OpenAI
    openai_api_key: str
    openai_model: Optional[str] = "gpt-4"
    openai_max_tokens: Optional[int] = 2000
    
    # Hunter.io Configuration
    hunter_api_key: Optional[str] = None
    hunter_rate_limit_per_day: int = 25  # Free tier limit
    hunter_min_confidence: int = 50  # Minimum confidence score for emails
    
    # SMTP Configuration
    smtp_server: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: Optional[str] = "PromoHub Marketing"
    smtp_use_tls: Optional[bool] = True
    
    # Social Media
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_access_token: Optional[str] = None
    
    # Security
    secret_key: str
    
    # App Configuration
    app_name: str = "PromoHub"
    app_version: str = "1.0.0"
    debug: bool = True
    port: int = 8000
    host: Optional[str] = "0.0.0.0"
    environment: Optional[str] = "development"
    log_level: Optional[str] = "INFO"
    
    # Product-specific URLs
    ezclub_url: str = "https://ezclub.app"
    ezdirectory_url: str = "https://ezdirectory.app"
    promohub_blog_url: str = "https://blog.promohub.com"
    
    # Marketing Configuration
    email_rate_limit_per_day: int = 100
    email_rate_limit_per_hour: Optional[int] = 10
    blog_generation_frequency_days: int = 7
    social_posts_per_day: int = 6
    max_leads_per_campaign: Optional[int] = 1000
    
    # Product Focus Settings
    primary_products: str = "ezclub,ezdirectory"  # comma-separated
    default_lead_assignment: str = "ezclub"
    
    # Target Audiences (comma-separated)
    ezclub_target_audience: str = "youtube_creators,content_creators,online_educators,gaming_streamers"
    ezdirectory_target_audience: str = "business_owners,entrepreneurs,local_services"
    
    # Campaign Settings
    ezclub_trial_url: str = "https://ezclub.app/trial"
    ezdirectory_demo_url: str = "https://ezdirectory.app/demo"
    support_email: str = "support@promohub.com"
    
    # Content Strategy
    content_focus_ratio: float = 0.6  # 60% EZClub, 40% EZDirectory content
    cross_sell_enabled: bool = True
    
    # Paths
    upload_folder: str = "./uploads"
    log_folder: str = "./logs"
    
    @property
    def primary_products_list(self) -> List[str]:
        """Get primary products as a list"""
        return [p.strip() for p in self.primary_products.split(",")]
    
    @property
    def ezclub_audiences(self) -> List[str]:
        """Get EZClub target audiences as a list"""
        return [a.strip() for a in self.ezclub_target_audience.split(",")]
    
    @property
    def ezdirectory_audiences(self) -> List[str]:
        """Get EZDirectory target audiences as a list"""
        return [a.strip() for a in self.ezdirectory_target_audience.split(",")]
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from .env file


settings = Settings()