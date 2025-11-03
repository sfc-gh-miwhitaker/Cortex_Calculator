# Release Notes: Cortex Cost Calculator v2.6

**Release Date**: November 3, 2024  
**Status**: Production Ready  
**Breaking Changes**: None (backward compatible with v2.5)

---

## 🎯 What's New in v2.6

Version 2.6 is a major update that combines:
1. **Latest Snowflake Cortex pricing** (effective Oct 31, 2025)
2. **Support for 5 new ACCOUNT_USAGE views** released by Snowflake (July 2024 - March 2025)
3. **Enhanced query-level cost tracking** capabilities

---

## 🚀 Key Features

### 1. Latest Cortex Pricing (Oct 31, 2025)

**Updated Models**:
- Claude 3.5 Sonnet, Haiku (new pricing)
- Llama 3.1 (405b, 70b, 8b) - updated rates
- Mistral Large 2 (new model)
- Jamba 1.5 Large/Mini (new models)
- Reka Core/Flash (new multimodal models)
- Gemma 7B (new model)

**Coverage**: 19 LLM models with full input/output token pricing

**Documentation**: See [`docs/PRICING_REFERENCE.md`](docs/PRICING_REFERENCE.md)

### 2. Query-Level Cost Tracking (NEW)

**Feature**: `CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY`  
**Benefit**: Identify exact queries consuming excessive credits

**Use Cases**:
- "Find my 10 most expensive queries"
- "Which team/application is driving costs?"
- "Should I optimize this prompt or switch models?"

**New Views**:
- `V_CORTEX_FUNCTIONS_QUERY_DETAIL` - Per-query costs
- `V_QUERY_COST_ANALYSIS` - Top expensive queries across all services

**Example**:
```sql
-- Find your most expensive queries
SELECT * 
FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_QUERY_COST_ANALYSIS
WHERE credits_used > 1.0
ORDER BY credits_used DESC
LIMIT 20;
```

### 3. Document Processing Analysis (NEW)

**Feature**: `CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY` (GA: Mar 3, 2025)  
**Benefit**: Compare costs between Document AI, PARSE_DOCUMENT, and AI_EXTRACT

**Use Cases**:
- "Should I use Document AI or PARSE_DOCUMENT?"
- "What's my cost per page for each method?"
- "Which document processing function is most efficient?"

**New View**: `V_CORTEX_DOCUMENT_PROCESSING_DETAIL`

**Example**:
```sql
-- Compare document processing methods
SELECT 
    function_name,
    AVG(credits_per_page) AS avg_cost_per_page,
    SUM(credits_used) AS total_cost
FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_DOCUMENT_PROCESSING_DETAIL
GROUP BY function_name;
```

### 4. Fine-Tuning ROI Tracking (NEW)

**Feature**: `CORTEX_FINE_TUNING_USAGE_HISTORY` (GA: Oct 10, 2024)  
**Benefit**: Calculate ROI of fine-tuning investments

**Use Cases**:
- "Did fine-tuning save us money vs larger base models?"
- "What's our training vs inference cost ratio?"
- "How long until fine-tuning pays for itself?"

**New View**: `V_CORTEX_FINE_TUNING_DETAIL`

**Example**:
```sql
-- Training vs inference cost analysis
SELECT 
    model_name,
    SUM(token_credits) AS training_credits
FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_FINE_TUNING_DETAIL
GROUP BY model_name;
```

### 5. Cortex Search Optimization (NEW)

**Features**: 
- `CORTEX_SEARCH_DAILY_USAGE_HISTORY` (GA: Oct 10, 2024)
- `CORTEX_SEARCH_SERVING_USAGE_HISTORY` (GA: Oct 10, 2024)

**Benefit**: Find idle periods to suspend services and save money

**Use Cases**:
- "My search service runs 24/7 but is only used 8am-6pm"
- "What's the cost breakdown between serving and embedding?"
- "Can I save money by suspending overnight?"

**Enhanced Views**: 
- `V_CORTEX_SEARCH_DETAIL` - Daily costs with breakdown
- `V_CORTEX_SEARCH_SERVING_DETAIL` - Hourly costs

**Example**:
```sql
-- Find idle hours for Cortex Search
SELECT 
    DATE_TRUNC('hour', start_time) AS hour,
    service_name,
    credits
FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_SEARCH_SERVING_DETAIL
WHERE usage_date >= CURRENT_DATE() - 7
    AND credits > 0
ORDER BY service_name, hour;
```

---

## 📊 SQL Deployment Updates

### New Deployment Script

**File**: [`sql/deploy_cortex_monitoring_v2.6.sql`](sql/deploy_cortex_monitoring_v2.6.sql)

**Changes**:
- **16 views** (up from 13 in v2.5)
- **3 new views** for new Snowflake features
- **Enhanced snapshot table** with document processing metrics
- **Enhanced task** to capture all new metrics

### View Count by Version

| Version | Views | New in Version |
|---------|-------|----------------|
| v2.4 | 10 | Initial release |
| v2.5 | 13 | AISQL function tracking |
| v2.6 | 16 | Query-level tracking, document processing, fine-tuning |

---

## 📚 Documentation Updates

### New Documentation

1. **[`docs/SNOWFLAKE_NEW_FEATURES_v2.6.md`](docs/SNOWFLAKE_NEW_FEATURES_v2.6.md)** (NEW)
   - Complete guide to all 5 new ACCOUNT_USAGE views
   - Schema definitions and real-world examples
   - Migration guide from v2.5
   - Best practices

2. **[`docs/PRICING_REFERENCE.md`](docs/PRICING_REFERENCE.md)** (UPDATED)
   - All 19 LLM models with Oct 31, 2025 pricing
   - Model selection guide
   - Cost estimation examples
   - FAQs

3. **[`CHANGELOG.md`](CHANGELOG.md)** (UPDATED)
   - Complete v2.6 feature list
   - Before/after comparisons
   - Upgrade benefits

### Updated Documentation

1. **[`README.md`](README.md)** - Updated to v2.6
2. **[`streamlit/cortex_cost_calculator/streamlit_app.py`](streamlit/cortex_cost_calculator/streamlit_app.py)** - Enhanced pricing tables

---

## 🔄 Migration Guide

### Upgrading from v2.5 to v2.6

**Step 1**: Deploy new views (backward compatible)
```sql
-- Run in your Snowflake account
@sql/deploy_cortex_monitoring_v2.6.sql
```

**Step 2**: Verify deployment
```sql
-- Should return 16 (was 13 in v2.5)
SELECT COUNT(*) AS view_count
FROM SNOWFLAKE.INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'CORTEX_USAGE'
    AND TABLE_CATALOG = 'SNOWFLAKE_EXAMPLE';
```

**Step 3**: Update Streamlit app (optional)
- Pull latest code
- Redeploy Streamlit app with `streamlit/cortex_cost_calculator/streamlit_app.py`

**Time Required**: 5-10 minutes  
**Downtime**: None (views are additive)  
**Data Loss**: None (all existing data preserved)

---

## 🎯 Benefits by Role

### For Solution Engineers

**Before v2.6**: "Customer's Cortex costs are $X/month - here's a rough estimate"  
**After v2.6**: "Here are your top 10 expensive queries, cost per page for document processing, and fine-tuning ROI analysis"

**Key Wins**:
- More accurate proposals with query-level data
- Better optimization recommendations
- Faster time to value in POCs

### For Data Engineers

**Before v2.6**: "Something is costing too much - need to investigate"  
**After v2.6**: "Query XYZ with claude-3-opus is the culprit - switching to haiku will save $X/month"

**Key Wins**:
- Pinpoint expensive queries instantly
- Compare document processing options with real data
- Optimize models based on actual costs

### For Finance/FinOps

**Before v2.6**: "Monthly Cortex spend is $X"  
**After v2.6**: "Cortex costs: $X for LLMs (top 5 queries listed), $Y for documents (can save 40% with PARSE_DOCUMENT), $Z for search (suspend overnight to save 33%)"

**Key Wins**:
- Detailed cost attribution
- Clear optimization opportunities
- ROI tracking for fine-tuning investments

---

## 🐛 Known Issues & Limitations

### Data Latency
- Query-level data may take a few hours to appear in `CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY`
- New models may take up to 2 weeks to appear in hourly aggregate views
- REST API requests are not tracked (SQL-based usage only)

### Compatibility
- `CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY` GA date is March 3, 2025 (may not be available in all regions yet)
- Some features require specific Snowflake versions - check Snowflake docs for availability

### Performance
- For very high-volume accounts (millions of queries/day), consider adding filters to analysis views
- Snapshot table will grow over time - consider archiving old snapshots after 1 year

---

## 📞 Support & Resources

### Documentation
- **Getting Started**: [`help/GETTING_STARTED.md`](../help/GETTING_STARTED.md)
- **New Features Guide**: [`SNOWFLAKE_NEW_FEATURES_v2.6.md`](SNOWFLAKE_NEW_FEATURES_v2.6.md)
- **Pricing Reference**: [`PRICING_REFERENCE.md`](PRICING_REFERENCE.md)
- **Changelog**: [`CHANGELOG.md`](CHANGELOG.md)

### Snowflake Resources
- [Snowflake Docs - CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_functions_query_usage_history)
- [Snowflake Docs - CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_document_processing_usage_history)
- [Snowflake Service Consumption Table](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf)

### Questions?
- Open an issue on GitHub
- Contact your Snowflake account team
- Check the [FAQ section in README.md](../README.md#faq)

---

## 🎉 Thank You

Thank you for using the Cortex Cost Calculator! v2.6 represents the most comprehensive Cortex cost tracking solution available, leveraging the latest Snowflake features to give you unprecedented visibility into your AI workload costs.

**What's Next?**
- More Streamlit visualizations for query-level analysis
- Automated cost optimization recommendations
- Integration with Snowflake budgets and alerts
- Stay tuned for v2.7!

---

**Version**: v2.6  
**Release Date**: November 3, 2024  
**Compatibility**: Snowflake ACCOUNT_USAGE views as of October 2024  
**License**: See LICENSE file

