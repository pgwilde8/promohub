# 🎯 PromoHub: Focused Strategy for EZClub.app & EZDirectory.app

## 🏢 **Simplified Database Schema for Your Products**

Since we're focusing on promoting your two SaaS products, we can simplify the multi-tenant complexity while keeping the flexibility for future growth.

### 📊 **Simplified Core Tables**

#### **Primary Focus Tables:**

1. **`leads`** - Prospects for both products
   - `product_interest` - "ezclub", "ezdirectory", "both"
   - `lead_source` - which product's marketing brought them in
   - `qualification_level` - cold, warm, hot, customer
   - `product_fit_score` - how well they match each product

2. **`campaigns`** - Product-specific marketing campaigns
   - `target_product` - ezclub, ezdirectory, or cross_sell
   - `campaign_goal` - awareness, trial_signup, demo_request, conversion
   - `audience_segment` - restaurant_owners, directory_buyers, etc.

3. **`content`** - Marketing content for both products
   - `primary_product` - which product this content promotes
   - `content_angle` - problem/solution, feature_highlight, case_study, comparison
   - `target_audience` - restaurant_owners, business_owners, directory_seekers

### 🎯 **Product-Specific Marketing Strategy**

#### **EZClub.app Marketing:**
- **Target Audience**: Restaurant owners, bar owners, event venues
- **Content Topics**: 
  - "5 Ways to Build Customer Loyalty"
  - "Restaurant Marketing That Actually Works"
  - "Turn One-Time Diners into Regulars"
- **Lead Sources**: Restaurant industry sites, local business directories
- **Conversion Funnel**: Blog → Demo Request → Free Trial → Paid Plan

#### **EZDirectory.app Marketing:**
- **Target Audience**: Business owners wanting online presence
- **Content Topics**:
  - "Why Your Business Needs an Online Directory"
  - "Local SEO Made Simple"
  - "Get Found by Local Customers"
- **Lead Sources**: Small business forums, local entrepreneur groups
- **Conversion Funnel**: Blog → Directory Demo → Setup Service → Monthly Plan

#### **Cross-Selling Opportunities:**
- EZClub customers → EZDirectory (restaurants need local visibility)
- EZDirectory customers → EZClub (businesses need customer retention)

## 🤖 **Bot Strategy for Your Products**

### **📧 Outreach Bot Campaigns:**

#### **EZClub Cold Email Sequence:**
1. **Email 1**: "Are you losing repeat customers?" (problem awareness)
2. **Email 2**: "Here's how [Local Restaurant] increased repeat visits by 40%" (social proof)
3. **Email 3**: "5-minute demo of our customer loyalty platform" (soft pitch)
4. **Email 4**: "Last chance: Free trial for restaurant owners" (urgency)

#### **EZDirectory Cold Email Sequence:**
1. **Email 1**: "Is your business invisible online?" (problem awareness)
2. **Email 2**: "Local customers can't find you - here's why" (education)
3. **Email 3**: "Get your business listed in 24 hours" (solution)
4. **Email 4**: "Special offer: Complete directory setup for $99" (offer)

### **✍️ Content Bot Topics:**

#### **EZClub Content Calendar:**
- **Week 1**: "Restaurant Marketing Automation 101"
- **Week 2**: "Customer Loyalty Programs That Work"
- **Week 3**: "Case Study: How [Restaurant] Doubled Repeat Visits"
- **Week 4**: "5 Mistakes Restaurant Owners Make with Customer Data"

#### **EZDirectory Content Calendar:**
- **Week 1**: "Local SEO for Small Business"
- **Week 2**: "Online Directory Benefits Explained"  
- **Week 3**: "Business Visibility: Online vs Offline"
- **Week 4**: "Case Study: Local Business Triples Leads"

### **📣 Social Bot Strategy:**

#### **EZClub Social Posts:**
- **Twitter**: Restaurant tips, industry news, customer success stories
- **LinkedIn**: B2B restaurant owner networking, case studies
- **Instagram**: Visual content about restaurant success

#### **EZDirectory Social Posts:**  
- **Twitter**: Small business tips, local marketing advice
- **LinkedIn**: Business networking, local SEO tips
- **Facebook**: Local business community engagement

### **🔁 Retargeting Scenarios:**

#### **High-Intent Actions:**
1. **Visited Pricing Page** → Send pricing comparison email
2. **Downloaded Demo** → Follow up with implementation timeline
3. **Started Free Trial** → Onboarding sequence + success tips
4. **Visited Competitor Pages** → Send differentiation content

## 🎯 **Simplified Database Focus**

Since we're focusing on just your two products, let's adjust the schema:

```sql
-- Core lead tracking focused on your products
ALTER TABLE leads ADD COLUMN product_interest VARCHAR(50); -- 'ezclub', 'ezdirectory', 'both'
ALTER TABLE leads ADD COLUMN customer_type VARCHAR(100); -- 'restaurant_owner', 'business_owner', etc.
ALTER TABLE leads ADD COLUMN business_size VARCHAR(50); -- '1-10', '11-50', '50+' employees
ALTER TABLE leads ADD COLUMN current_solution VARCHAR(255); -- what they use now
ALTER TABLE leads ADD COLUMN pain_points TEXT; -- their specific challenges

-- Campaign tracking for product-specific campaigns  
ALTER TABLE campaigns ADD COLUMN target_product VARCHAR(50); -- 'ezclub', 'ezdirectory', 'both'
ALTER TABLE campaigns ADD COLUMN industry_focus VARCHAR(100); -- 'restaurants', 'retail', 'services'

-- Content categorized by product focus
ALTER TABLE content ADD COLUMN primary_product VARCHAR(50); -- 'ezclub', 'ezdirectory', 'general'
ALTER TABLE content ADD COLUMN secondary_product VARCHAR(50); -- for cross-selling content
```

## 🚀 **Immediate Action Plan**

### **Phase 1: EZClub Focus (Month 1)**
1. **Setup EZClub landing pages** with PromoHub tracking
2. **Create 10 restaurant industry blog posts** 
3. **Build email sequence for restaurant owners**
4. **Launch LinkedIn outreach to restaurant owners**

### **Phase 2: EZDirectory Focus (Month 2)**  
1. **Setup EZDirectory landing pages**
2. **Create small business content series**
3. **Build email sequence for business owners**
4. **Launch Facebook ads to local business groups**

### **Phase 3: Cross-Selling (Month 3)**
1. **Identify EZClub customers for EZDirectory upsell**
2. **Create comparison content (EZClub + EZDirectory = complete solution)**
3. **Build integrated sales funnel**

## 💡 **Key Success Metrics**

### **EZClub KPIs:**
- Restaurant owner leads generated
- Demo requests from restaurant industry
- Free trial signups
- Conversion rate: Trial → Paid

### **EZDirectory KPIs:**  
- Small business leads generated  
- Directory setup requests
- Local SEO consultation bookings
- Monthly recurring revenue

### **Overall PromoHub Performance:**
- Total leads generated across both products
- Cross-sell conversion rate
- Content engagement rates
- Email campaign performance

This focused approach lets you perfect the marketing automation for your own products before potentially offering PromoHub as a service to others. You'll have real case studies and proven results to show future clients.

**Should we adjust the database schema to remove the multi-tenant complexity and focus purely on your two products?**