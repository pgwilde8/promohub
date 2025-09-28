# PromoHub

**Self-hosted marketing automation hub for SaaS businesses**

PromoHub is a comprehensive marketing automation platform that runs on your own infrastructure. It powers lead generation, cold outreach, content marketing, and retargeting campaigns for your SaaS products.

## 🚀 Features

### 📧 Outreach Bot
- AI-personalized cold emails via SMTP
- Rate-limited sending (50-200 emails/day)
- Lead status tracking and management
- Integration with MXroute and other SMTP providers

### ✍️ Content Bot
- Weekly automated blog post generation using OpenAI
- SEO-friendly content with meta descriptions and tags
- Automatic publishing to your blog

### 📣 Social Bot
- Automatic social media posting to Twitter/X and LinkedIn
- Content snippets from blog posts
- Engagement tracking and analytics

### 💬 Chat Demo Bot
- Interactive chat widget for lead capture
- AI-powered FAQ responses
- Seamless integration with lead management

### 🔁 Retarget Bot
- Behavioral tracking and retargeting
- Automated follow-up emails based on page visits
- Conversion tracking and optimization

### 📊 Admin Dashboard
- Comprehensive lead management
- Email campaign analytics
- Content performance tracking
- Real-time bot status monitoring

## 🛠️ Tech Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** Jinja2 templates + Bootstrap 5
- **Automation:** APScheduler for background tasks
- **AI:** OpenAI API for content generation and personalization
- **Email:** SMTP integration (MXroute compatible)
- **Deployment:** systemd service on Linux VM

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- SMTP email service (MXroute recommended)
- OpenAI API key
- Linux server with systemd (for production)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url> promohub
cd promohub
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `SMTP_*`: Email server configuration
- `SECRET_KEY`: Secret key for sessions

### 3. Initialize Database

```bash
# Initialize Alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 4. Run the Application

```bash
# Development
python main.py

# Production with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Access the Dashboard

Open `http://your-server-ip:8000` to access the admin dashboard.

## 📁 Project Structure

```
promohub/
├── app/
│   ├── bots/           # Automation bots
│   │   ├── outreach_bot.py
│   │   ├── content_bot.py
│   │   ├── social_bot.py
│   │   ├── retarget_bot.py
│   │   └── scheduler.py
│   ├── core/           # Core configuration
│   │   ├── config.py
│   │   └── database.py
│   ├── models/         # Database models
│   │   └── base.py
│   └── routes/         # API and web routes
│       ├── dashboard.py
│       ├── leads.py
│       ├── blog.py
│       └── api.py
├── templates/          # Jinja2 HTML templates
├── static/            # CSS, JS, and assets
├── alembic/           # Database migrations
├── main.py           # FastAPI application
└── requirements.txt  # Python dependencies
```

## 🔧 Configuration

### Bot Scheduling

The scheduler runs these bots automatically:
- **Outreach Bot:** Every 2 hours during business hours
- **Content Bot:** Weekly on Mondays at 8 AM
- **Social Bot:** Daily at 10 AM and 2 PM  
- **Retarget Bot:** Every 4 hours

### Email Rate Limits

Default limits (configurable in `.env`):
- 50 emails per day per SMTP account
- 2-second delay between emails
- Automatic retry for failed sends

### Database Schema

Core tables:
- `leads`: Lead information and status
- `outreach_log`: Email campaign tracking
- `content`: Blog posts and content
- `social_log`: Social media post tracking
- `page_views`: Website analytics and retargeting data

## 🚀 Production Deployment

### 1. Systemd Service

Create `/etc/systemd/system/promohub.service`:

```ini
[Unit]
Description=PromoHub Marketing Automation
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/promohub
Environment=PATH=/path/to/promohub/venv/bin
ExecStart=/path/to/promohub/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable promohub
sudo systemctl start promohub
```

### 2. Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /path/to/promohub/static/;
    }
}
```

### 3. SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

## 📊 Monitoring

### Health Checks

- `/health` - API health status
- `/api/health` - Detailed system status
- Scheduler status via dashboard

### Logs

- Application logs via Python logging
- Bot execution logs
- Email delivery tracking

## 🔌 API Endpoints

### Lead Management
- `POST /api/leads` - Create new lead
- `POST /api/demo-bot` - Chat bot interaction
- `POST /api/track-page-view` - Page view tracking

### Bot Control
- `POST /api/trigger-outreach/{lead_id}` - Manual outreach
- Bot status via dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the configuration examples

## 🔮 Roadmap

- [ ] Advanced A/B testing for email campaigns
- [ ] Integration with more social media platforms
- [ ] Advanced analytics and reporting
- [ ] Webhook integrations
- [ ] Multi-tenant support
- [ ] Docker containerization

---

**PromoHub** - Making marketing automation simple and self-hosted.