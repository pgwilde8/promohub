from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # External IP
    external_ip: str
    
    # OpenAI
    openai_api_key: str
    
    # SMTP Configuration
    smtp_server: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    
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
    
    # Product-specific URLs
    ezclub_url: str = "https://ezclub.app"
    ezdirectory_url: str = "https://ezdirectory.app"
    promohub_blog_url: str = "https://blog.promohub.com"
    
    # Marketing Configuration
    email_rate_limit_per_day: int = 100
    blog_generation_frequency_days: int = 7
    social_posts_per_day: int = 6
    
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


settings = Settings()