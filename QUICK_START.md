# Quick Start Guide: Cortex AI Cost Calculator

**Get cost projections in 15 minutes**

---

## What You'll Get

- ✅ Real-time tracking of all Cortex AI services
- ✅ Historical usage analysis with charts
- ✅ Multi-scenario cost projections (3, 6, 12, 24 months)
- ✅ Export-ready credit estimates

**Time to value:** 15 minutes

---

## Prerequisites

Before starting, make sure you have:

- ✅ Snowflake account with Cortex AI usage (ideally 7-14 days)
- ✅ `ACCOUNTADMIN` role OR role with `IMPORTED PRIVILEGES` on `SNOWFLAKE` database
- ✅ Active warehouse
- ✅ Access to Snowflake Snowsight UI

---

## Step 1: Deploy Monitoring (5 minutes)

### 1.1 Log into Snowflake

1. Navigate to [https://app.snowflake.com](https://app.snowflake.com)
2. Log in with your credentials
3. Click **Worksheets** in left navigation
4. Create a new worksheet

### 1.2 Verify Access

Run this test query:

```sql
SELECT COUNT(*) 
FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY 
WHERE usage_date >= DATEADD('day', -7, CURRENT_DATE());
```

**Expected:** A number (even if 0) - not an error

**If error:** Grant privileges:
```sql
USE ROLE ACCOUNTADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <YOUR_ROLE>;
```

### 1.3 Deploy Views

1. Open `sql/deploy_cortex_monitoring.sql` in a text editor
2. Copy the entire file
3. Paste into your Snowflake worksheet
4. Click **"Run All"** or press `Ctrl+Enter` on all statements

**Watch for:**
- ✅ Database `SNOWFLAKE_EXAMPLE` created
- ✅ Schema `CORTEX_AI_USAGE` created
- ✅ 9 views created successfully

**Validation:** Check the output at the end of the script for success messages.

---

## Step 2: Deploy Calculator (5 minutes)

### 2.1 Create Streamlit App

In Snowsight:
1. Click **"Projects"** in left navigation
2. Click **"Streamlit"**
3. Click **"Apps"**
4. Click **"+ Streamlit App"** button

### 2.2 Configure App

Fill in the form:

| Field | Value |
|-------|-------|
| **App name** | `CORTEX_COST_CALCULATOR` |
| **App location** | `SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE` |
| **Warehouse** | Select your warehouse (SMALL is fine) |

### 2.3 Add Code

1. Open `streamlit/cortex_cost_calculator/streamlit_app.py`
2. Copy entire file contents
3. Paste into Snowflake code editor (replace default code)

### 2.4 Add Packages

1. Click **"Packages"** tab in editor
2. Open `streamlit/cortex_cost_calculator/environment.yml`
3. Copy the dependencies section
4. Add packages to Snowflake packages field

### 2.5 Launch

1. Click **"Create"** button
2. Wait 30 seconds for app to initialize
3. App will launch automatically

---

## Step 3: Analyze Your Usage (5 minutes)

### 3.1 Configure Calculator

In the sidebar:
- **Data Source:** Select **"Query Views (Same Account)"**
- **Lookback Period:** Keep at 30 days (or adjust)
- **Credit Cost:** Update to your actual credit price (default: $3.00)

### 3.2 Review Historical Analysis

Click **"📈 Historical Analysis"** tab:
- View total credits and costs
- Check service breakdown chart
- Review usage trends over time

### 3.3 Generate Projections

Click **"🔮 Cost Projections"** tab:
- Select projection period (3, 6, 12, or 24 months)
- Choose growth scenario:
  - **Conservative:** 10% monthly growth
  - **Moderate:** 25% monthly growth
  - **Aggressive:** 50% monthly growth
  - **Rapid:** 100% monthly growth

### 3.4 Compare Scenarios

Click **"📊 Scenario Comparison"** tab:
- See all scenarios side-by-side
- Build custom scenarios with specific growth rates
- Export comparison table

### 3.5 Export Estimates

Click **"📋 Summary Report"** tab:
- Review credit breakdown by service
- Click **"Download Credit Estimate (CSV)"**
- Open in Excel for further analysis or proposals

---

## Troubleshooting

### No Data Showing

**If views return 0 rows:**
1. Check if Cortex AI has been used: `SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY WHERE service_type = 'AI_SERVICES' ORDER BY usage_date DESC LIMIT 10;`
2. Wait 3 hours for data latency
3. Extend lookback period to 90 days in deployment script

### Permission Errors

**If "Object does not exist":**
```sql
USE ROLE ACCOUNTADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <YOUR_ROLE>;
```

### Calculator Won't Load

1. Verify warehouse is running
2. Check app location matches where views were deployed
3. Refresh browser page

### Need More Help?

See `TROUBLESHOOTING.md` for comprehensive troubleshooting guide.

---

## What's Next?

### Use the Calculator

- **Monthly:** Review actual usage against projections
- **Quarterly:** Update growth assumptions based on actuals
- **For budgets:** Export credit estimates for finance team
- **For planning:** Use scenario comparison for capacity planning

### Share with Your Team

Grant access to other users:

```sql
-- Grant view access
GRANT USAGE ON DATABASE SNOWFLAKE_EXAMPLE TO ROLE <ROLE_NAME>;
GRANT USAGE ON SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE TO ROLE <ROLE_NAME>;
GRANT SELECT ON ALL VIEWS IN SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE TO ROLE <ROLE_NAME>;

-- Grant Streamlit access
GRANT USAGE ON STREAMLIT CORTEX_COST_CALCULATOR TO ROLE <ROLE_NAME>;
```

### Learn More

- **Full Guide:** See `README.md` for complete documentation
- **Troubleshooting:** See `TROUBLESHOOTING.md` for issue resolution
- **Walkthrough:** See `DEPLOYMENT_WALKTHROUGH.md` for detailed guide
- **Snowflake Docs:** [Cortex AI Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)

---

## Cleanup (When Finished)

To remove all monitoring:

```sql
-- Run cleanup script
@sql/cleanup_cortex_monitoring.sql
```

Choose one option:
1. Drop views only (keeps schema)
2. Drop schema (removes all monitoring objects)
3. Drop database (complete removal)

---

**Questions?** Contact your Snowflake Solutions Engineer or see the complete documentation in `README.md`.

---

*From deployment to projection in 15 minutes.*

