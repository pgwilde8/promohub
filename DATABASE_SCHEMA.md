# 🏢 **PromoHub Multi-Tenant Database Schema**

## 📊 **Complete Database Tables for Marketing-as-a-Service**

### 🌐 **Multi-Tenant Core Tables**

#### 1. **`clients`** - Your customers who use PromoHub
- **Purpose**: Companies that pay you for marketing automation services
- **Key Fields**:
  - `subdomain` - client1.promohub.com for white-label access
  - `plan_type` - basic, pro, enterprise pricing tiers  
  - `max_leads`, `max_emails_per_day` - usage limits per plan
  - `branding_settings` - custom logos, colors for white-label
  - `industry`, `business_type` - context for better automation

#### 2. **`users`** - Dashboard users for each client
- **Purpose**: People who log into the PromoHub dashboard
- **Key Fields**:
  - `client_id` - which company they belong to
  - `role` - admin, user, viewer permissions
  - `is_client_admin` - can manage client settings
  - `permissions` - granular access control

#### 3. **`projects`** - Marketing projects within each client
- **Purpose**: Different products/campaigns each client is marketing
- **Example**: EZClub project, Q4 Launch project, Product X project
- **Key Fields**:
  - `target_audience` - ideal customer profile
  - `content_topics` - AI content generation focus
  - `brand_voice` - tone for all communications
  - `monthly_lead_goal` - KPI tracking

### 📧 **Campaign & Content Tables**

#### 4. **`campaigns`** - Organized marketing campaigns
- **Purpose**: Email sequences, content series, social campaigns
- **Key Fields**:
  - `campaign_type` - email_sequence, content_series, social_campaign
  - `lead_filters` - criteria for targeting
  - `email_templates`, `social_templates` - campaign assets
  - `total_opens`, `total_conversions` - performance tracking

#### 5. **`email_templates`** - Reusable email templates
- **Purpose**: Client-specific email templates for consistency
- **Key Fields**:
  - `template_type` - welcome, nurture, promotional, follow_up
  - `variables` - personalization fields like {name}, {company}
  - `avg_open_rate` - performance tracking per template

#### 6. **`lead_lists`** + **`lead_list_assignments`** - Lead segmentation
- **Purpose**: Create targeted segments for campaigns
- **Examples**: "High-value prospects", "Pricing page visitors", "Trial users"
- **Key Fields**:
  - `filters` - JSON criteria for auto-segmentation
  - `lead_count` - dynamic count of matching leads

### 🔗 **Integration & Tracking Tables**

#### 7. **`integrations`** - Third-party connections
- **Purpose**: Connect to CRMs, payment processors, etc.
- **Examples**: HubSpot, Salesforce, Stripe, Zapier
- **Key Fields**:
  - `api_credentials` - securely stored API keys
  - `field_mappings` - sync lead data between systems
  - `last_sync_at` - sync status tracking

#### 8. **`activity_log`** - System audit trail
- **Purpose**: Track all actions for debugging and compliance
- **Key Fields**:
  - `activity_type` - email_sent, lead_created, login, etc.
  - `entity_type` + `entity_id` - what was modified
  - `success` + `error_message` - track failures

### 📈 **Enhanced Existing Tables**

#### Updated **`leads`** table now includes:
- `client_id` + `project_id` - multi-tenant assignment
- `lead_score` - qualification scoring
- `assigned_to` - sales person assignment
- `lifetime_value` - revenue tracking

#### Updated **`outreach_log`** includes:
- `campaign_id` + `template_id` - campaign tracking
- `variant` - A/B testing support
- `open_rate`, `click_rate` - performance metrics

#### Updated **`page_views`** includes:
- `utm_*` fields - full UTM campaign tracking
- `country`, `city` - geographic data
- `device_type`, `browser` - device analytics
- `is_demo_page`, `is_contact_page` - conversion funnel tracking

## 🎯 **Multi-Tenant Benefits**

### **For You (Service Provider):**
1. **Revenue Streams**: Monthly recurring revenue per client
2. **Scalability**: Add unlimited clients without code changes  
3. **White-Label**: Each client can have branded experience
4. **Analytics**: Track performance across all clients
5. **Compliance**: Activity logging for audits

### **For Your Clients:**
1. **Project Separation**: Marketing multiple products independently
2. **Team Access**: Multiple users with role-based permissions  
3. **Campaign Organization**: Structured campaigns vs ad-hoc emails
4. **Template Library**: Consistent branding across all emails
5. **Advanced Segmentation**: Targeted campaigns based on behavior

### **Real-World Usage Examples:**

#### **Agency Use Case:**
- **Client**: Local restaurant chain (5 locations)
- **Projects**: "Grand Opening Campaign", "Loyalty Program", "Seasonal Menu"
- **Users**: Marketing manager (admin), 2 location managers (users)
- **Templates**: Welcome series, event invitations, loyalty rewards

#### **SaaS Company Use Case:**  
- **Client**: B2B software company
- **Projects**: "Free Trial Conversion", "Enterprise Outbound", "Product Launch"
- **Integrations**: HubSpot CRM, Stripe billing, Intercom chat
- **Campaigns**: 7-day trial sequence, pricing page retargeting, enterprise nurture

## 🔄 **Data Flow Example:**

1. **Lead Capture**: Visitor fills form on client's website
2. **Page View**: Tracked with UTM parameters and client_id  
3. **Lead Assignment**: Auto-assigned to appropriate project and lists
4. **Campaign Trigger**: Matching campaign sends welcome email
5. **Template Usage**: Email uses client-specific template
6. **Engagement Tracking**: Opens/clicks tracked per campaign
7. **Activity Logging**: All actions logged for reporting
8. **Integration Sync**: Lead data synced to client's CRM

This schema supports everything from simple lead generation to complex multi-campaign, multi-project marketing automation for multiple clients simultaneously.

Would you like me to adjust any of these tables or add additional functionality for specific use cases you have in mind?