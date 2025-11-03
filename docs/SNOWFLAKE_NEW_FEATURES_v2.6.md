# Snowflake Cortex Tracking: New Features Guide (v2.6)

**Last Updated**: November 3, 2024  
**Snowflake Documentation Source**: [Snowflake Docs - Account Usage](https://docs.snowflake.com/en/sql-reference/account-usage)

---

## 🎯 Executive Summary

Snowflake has released several new `ACCOUNT_USAGE` views that dramatically improve Cortex cost tracking and analysis capabilities. Our v2.6 update leverages these features to provide:

- **Query-level cost tracking** - Identify expensive individual queries
- **Unified document processing monitoring** - Track PARSE_DOCUMENT, Document AI, and AI_EXTRACT in one view
- **Fine-tuning cost tracking** - Separate training vs inference costs
- **Enhanced search analytics** - Daily and hourly Cortex Search metrics

---

## 📊 New ACCOUNT_USAGE Views Available

### 1. CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY
**GA Date**: Available with `CORTEX_FUNCTIONS_USAGE_HISTORY` (July 19, 2024)  
**Purpose**: Query-level granularity for LLM function costs

#### What's New
- **Previous**: Hourly aggregated data only - couldn't identify specific expensive queries
- **Now**: Per-query tracking with `QUERY_ID` - pinpoint exact queries consuming credits

#### Schema
```sql
Column Name              Data Type    Description
----------------------- ------------- ------------------------------------------
FUNCTION_NAME            VARCHAR       Function name for the model
MODEL_NAME               VARCHAR       Model used (query can use multiple models)
QUERY_ID                 VARCHAR       Unique query identifier
TOKENS                   NUMBER        Tokens used for this (QUERY_ID, MODEL, WAREHOUSE) combo
TOKEN_CREDITS            NUMBER        Tokens converted to credits
WAREHOUSE_ID             VARCHAR       Warehouse ID used to run the query
```

#### Key Benefits
- **Identify runaway costs**: Find queries consuming excessive tokens
- **Optimize prompts**: See exact token usage per query to refine prompts
- **Debug model selection**: Track when queries use multiple models
- **Chargeback**: Attribute costs to specific teams/applications by query

#### Important Notes
- Query data may take **a few hours** to appear in this view
- If a query uses multiple models, you get **one row per model**
- Example: `SELECT COMPLETE('mistral-7b', ...), COMPLETE('mistral-large', ...)` creates 2 rows
- **Cannot track REST API requests** (only SQL-based usage)

#### Usage Example
```sql
-- Find your 10 most expensive queries
SELECT 
    query_id,
    model_name,
    function_name,
    tokens,
    token_credits,
    (token_credits / tokens) * 1000000 AS cost_per_million_tokens
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY
ORDER BY token_credits DESC
LIMIT 10;

-- Find queries for specific model
SELECT * 
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY
WHERE model_name = 'claude-3-5-sonnet'
ORDER BY token_credits DESC;

-- Get total cost for a specific query
SELECT * 
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY
WHERE query_id = '01b2345c-6789-0def-ghij-klmnop123456';
```

---

### 2. CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY
**GA Date**: March 3, 2025  
**Purpose**: Unified tracking for ALL document processing functions

#### What's New
- **Previous**: Only `DOCUMENT_AI_USAGE_HISTORY` for Document AI operations
- **Now**: Tracks Document AI, `PARSE_DOCUMENT`, `AI_EXTRACT`, and custom models

#### Schema
```sql
Column Name              Data Type       Description
----------------------- --------------- ------------------------------------------
QUERY_ID                 VARCHAR         Unique identifier for the SQL query
CREDITS_USED             NUMBER(38,9)    Credits billed for processing
START_TIME               TIMESTAMP_LTZ   Query start time
END_TIME                 TIMESTAMP_LTZ   Query end time
FUNCTION_NAME            TEXT            Name of the processing function
MODEL_NAME               TEXT            Name of the model used
OPERATION_NAME           TEXT            Type of operation (inference, train)
PAGE_COUNT               NUMBER          Number of pages processed
DOCUMENT_COUNT           NUMBER          Number of documents processed
FEATURE_COUNT            NUMBER          Number of data values for entry extraction
```

#### Key Benefits
- **Complete document cost view**: One place for all document processing
- **Function comparison**: Compare costs between PARSE_DOCUMENT vs Document AI
- **Per-query granularity**: Track exact cost of each document processing job
- **Model tracking**: See which models are used for document operations

#### Functions Tracked
1. **Document AI**: `<model_build_name>!PREDICT`
2. **PARSE_DOCUMENT**: `SNOWFLAKE.CORTEX.PARSE_DOCUMENT()`
3. **AI_EXTRACT**: `SNOWFLAKE.CORTEX.AI_EXTRACT()`

#### Usage Example
```sql
-- Find expensive document processing queries
SELECT 
    query_id,
    function_name,
    model_name,
    credits_used,
    page_count,
    CASE 
        WHEN page_count > 0 THEN credits_used / page_count 
        ELSE 0 
    END AS credits_per_page
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY
WHERE credits_used > 0.072  -- Filter out small costs
ORDER BY credits_used DESC;

-- Compare PARSE_DOCUMENT vs Document AI costs
SELECT 
    function_name,
    COUNT(*) AS query_count,
    SUM(credits_used) AS total_credits,
    SUM(page_count) AS total_pages,
    AVG(credits_used / page_count) AS avg_credits_per_page
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY
WHERE page_count > 0
GROUP BY function_name
ORDER BY total_credits DESC;
```

---

### 3. CORTEX_SEARCH_DAILY_USAGE_HISTORY
**GA Date**: October 10, 2024  
**Purpose**: Daily aggregated Cortex Search costs by consumption type

#### What's New
- **Previous**: Had to query metering views or use service-level monitoring
- **Now**: Dedicated view with breakdown by serving vs embedding costs

#### Schema
```sql
Column Name              Data Type       Description
----------------------- --------------- ------------------------------------------
USAGE_DATE               TIMESTAMP_LTZ   Date of usage
DATABASE_NAME            VARCHAR         Database containing the service
SCHEMA_NAME              VARCHAR         Schema containing the service
SERVICE_NAME             VARCHAR         Name of the Cortex Search Service
SERVICE_ID               NUMBER          ID of the service
CONSUMPTION_TYPE         VARCHAR         "SERVING" or "EMBED_TEXT_TOKENS"
CREDITS                  NUMBER          Credits billed for this consumption type
MODEL_NAME               VARCHAR         For EMBED_TEXT_TOKENS: embedding model name
TOKENS                   VARCHAR         For EMBED_TEXT_TOKENS: input tokens consumed
```

#### Key Benefits
- **Cost breakdown**: Separate serving costs from embedding generation costs
- **Model transparency**: See which embedding models are used
- **Daily trends**: Track day-over-day growth in search usage
- **Per-service tracking**: Monitor costs for each Cortex Search service independently

#### Consumption Types
1. **SERVING**: Ongoing cost based on indexed data size (6.3 credits per GB/month)
2. **EMBED_TEXT_TOKENS**: One-time cost when documents are indexed/updated

#### Usage Example
```sql
-- Daily costs by service
SELECT 
    usage_date,
    service_name,
    consumption_type,
    SUM(credits) AS total_credits,
    SUM(tokens) AS total_tokens
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
WHERE usage_date >= DATEADD('day', -30, CURRENT_DATE())
GROUP BY usage_date, service_name, consumption_type
ORDER BY usage_date DESC, total_credits DESC;

-- Compare serving vs embedding costs
SELECT 
    service_name,
    consumption_type,
    SUM(credits) AS total_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
WHERE usage_date >= DATEADD('day', -30, CURRENT_DATE())
GROUP BY service_name, consumption_type
ORDER BY service_name, total_credits DESC;
```

---

### 4. CORTEX_SEARCH_SERVING_USAGE_HISTORY
**GA Date**: October 10, 2024  
**Purpose**: Hourly Cortex Search serving costs

#### What's New
- **Previous**: Daily aggregates only
- **Now**: Hourly granularity for detailed analysis

#### Schema
```sql
Column Name              Data Type       Description
----------------------- --------------- ------------------------------------------
START_TIME               TIMESTAMP_LTZ   Hour start time
END_TIME                 TIMESTAMP_LTZ   Hour end time
DATABASE_NAME            VARCHAR         Database containing the service
SCHEMA_NAME              VARCHAR         Schema containing the service
SERVICE_NAME             VARCHAR         Name of the Cortex Search Service
SERVICE_ID               NUMBER          ID of the service
CREDITS                  NUMBER          Credits billed for serving during this hour
```

#### Key Benefits
- **Hourly precision**: See exact times of day when costs spike
- **Suspend optimization**: Identify idle periods to suspend services
- **Cost anomalies**: Detect unexpected usage patterns quickly

#### Usage Example
```sql
-- Hourly serving costs for a specific service
SELECT 
    DATE_TRUNC('hour', start_time) AS hour,
    service_name,
    SUM(credits) AS hourly_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_SERVING_USAGE_HISTORY
WHERE service_name = 'MY_SEARCH_SERVICE'
    AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY DATE_TRUNC('hour', start_time), service_name
ORDER BY hour DESC;

-- Find hours with no usage (opportunities to suspend)
SELECT 
    service_name,
    COUNT(*) AS hours_with_cost,
    SUM(credits) AS total_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_SERVING_USAGE_HISTORY
WHERE start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY service_name
ORDER BY total_credits DESC;
```

---

### 5. CORTEX_FINE_TUNING_USAGE_HISTORY
**GA Date**: October 10, 2024  
**Purpose**: Track fine-tuning training costs separately from inference

#### What's New
- **Previous**: Fine-tuning costs mixed with inference in `CORTEX_FUNCTIONS_USAGE_HISTORY`
- **Now**: Dedicated view for training costs only

#### Schema
```sql
Column Name              Data Type       Description
----------------------- --------------- ------------------------------------------
START_TIME               TIMESTAMP_LTZ   Hour when fine-tuning job terminated (start)
END_TIME                 TIMESTAMP_LTZ   Hour when fine-tuning job terminated (end)
WAREHOUSE_ID             NUMBER          Warehouse used by fine-tuning query
MODEL_NAME               VARCHAR         Name of the base model
TOKEN_CREDITS            NUMBER          Credits billed for training
TOKENS                   NUMBER          Tokens billed for training jobs
```

#### Key Benefits
- **Separate training costs**: Distinguish training from inference usage
- **Model comparison**: Compare training costs across base models
- **Budget planning**: Forecast fine-tuning expenses separately

#### Important Notes
- **Only tracks training costs** - inference costs still in `CORTEX_FUNCTIONS_USAGE_HISTORY`
- **Does not include storage costs** or data replication costs
- Aggregated by base model and hour when job **completed**

#### Usage Example
```sql
-- Total fine-tuning costs by model
SELECT 
    model_name,
    COUNT(DISTINCT DATE(start_time)) AS days_with_training,
    SUM(token_credits) AS total_training_credits,
    SUM(tokens) AS total_training_tokens,
    AVG(token_credits) AS avg_credits_per_hour
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FINE_TUNING_USAGE_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY model_name
ORDER BY total_training_credits DESC;

-- Daily training costs
SELECT 
    DATE(start_time) AS training_date,
    model_name,
    SUM(token_credits) AS daily_training_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FINE_TUNING_USAGE_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY DATE(start_time), model_name
ORDER BY training_date DESC;
```

---

## 🚀 New Capabilities Enabled by v2.6

### 1. Query-Level Cost Attribution
**Previous**: "Our Cortex costs went up by $500 this week - why?"  
**Now**: "Query XYZ called claude-3-opus 1,000 times with 50K tokens each - that's the culprit"

```sql
-- Use V_QUERY_COST_ANALYSIS view
SELECT * 
FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_QUERY_COST_ANALYSIS
WHERE credits_used > 1.0  -- Filter for expensive queries
ORDER BY credits_used DESC
LIMIT 20;
```

### 2. Document Processing Cost Optimization
**Previous**: "Document AI is expensive - should we use PARSE_DOCUMENT instead?"  
**Now**: Exact cost comparison with real data

```sql
-- Compare Document AI vs PARSE_DOCUMENT
SELECT 
    function_name,
    COUNT(*) AS queries,
    AVG(credits_per_page) AS avg_cost_per_page,
    SUM(credits_used) AS total_cost
FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_DOCUMENT_PROCESSING_DETAIL
GROUP BY function_name;
```

### 3. Cortex Search Cost Management
**Previous**: "Our search service costs $X/month - is it always running?"  
**Now**: Hourly visibility to identify suspend opportunities

```sql
-- Find idle hours for Cortex Search
SELECT 
    service_name,
    DATE_TRUNC('hour', start_time) AS hour,
    credits
FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_SEARCH_SERVING_DETAIL
WHERE usage_date >= CURRENT_DATE() - 7
ORDER BY service_name, hour;
```

### 4. Fine-Tuning ROI Analysis
**Previous**: "We spent $X on fine-tuning - was it worth it?"  
**Now**: Compare training costs vs inference savings

```sql
-- Training vs inference cost comparison
WITH training AS (
    SELECT 
        model_name,
        SUM(token_credits) AS training_credits
    FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_FINE_TUNING_DETAIL
    GROUP BY model_name
),
inference AS (
    SELECT 
        model_name,
        SUM(token_credits) AS inference_credits
    FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_FUNCTIONS_DETAIL
    WHERE model_name LIKE '%fine_tuned%'
    GROUP BY model_name
)
SELECT 
    t.model_name,
    t.training_credits,
    COALESCE(i.inference_credits, 0) AS inference_credits,
    t.training_credits + COALESCE(i.inference_credits, 0) AS total_credits
FROM training t
LEFT JOIN inference i ON t.model_name = i.model_name;
```

---

## 📋 Migration Guide: v2.5 → v2.6

### Step 1: Deploy New Views
```bash
# Run the new deployment script
snowsql -f sql/deploy_cortex_monitoring_v2.6.sql
```

### Step 2: Verify New Views Exist
```sql
-- Should return 16 (was 10 in v2.5, 13 in older versions)
SELECT COUNT(*) AS view_count
FROM SNOWFLAKE.INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'CORTEX_USAGE'
    AND TABLE_CATALOG = 'SNOWFLAKE_EXAMPLE';
```

### Step 3: Update Your Queries

**Old Query (v2.5)**:
```sql
-- Could only see hourly aggregates
SELECT * FROM V_CORTEX_FUNCTIONS_DETAIL;
```

**New Query (v2.6)**:
```sql
-- Can now drill down to specific queries
SELECT * FROM V_CORTEX_FUNCTIONS_QUERY_DETAIL
WHERE query_id = 'my_expensive_query_id';
```

### Step 4: Update Dashboards

If you have Tableau/PowerBI dashboards or Streamlit apps, update them to use:
- `V_QUERY_COST_ANALYSIS` - for most expensive queries widget
- `V_CORTEX_DOCUMENT_PROCESSING_DETAIL` - for document processing costs
- `V_CORTEX_FINE_TUNING_DETAIL` - for fine-tuning tracking

---

## 💡 Best Practices

### 1. Query-Level Monitoring
**Do**: Set up alerts for queries > 10 credits
```sql
-- Daily check for expensive queries
SELECT query_id, token_credits
FROM V_CORTEX_FUNCTIONS_QUERY_DETAIL
WHERE token_credits > 10
ORDER BY token_credits DESC;
```

**Don't**: Try to optimize hourly aggregates only - you'll miss the specific culprits

### 2. Document Processing
**Do**: Use `CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY` for all document analysis
**Don't**: Mix `DOCUMENT_AI_USAGE_HISTORY` and manual PARSE_DOCUMENT tracking

### 3. Cortex Search
**Do**: Check hourly serving costs to find idle periods
**Don't**: Leave search services running 24/7 in dev/test

### 4. Fine-Tuning
**Do**: Track training vs inference separately for ROI
**Don't**: Assume fine-tuning always saves money - measure it!

---

## 🔗 Additional Resources

- [Snowflake CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY Docs](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_functions_query_usage_history)
- [Snowflake CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY Docs](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_document_processing_usage_history)
- [Snowflake CORTEX_SEARCH_DAILY_USAGE_HISTORY Docs](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_search_daily_usage_history)
- [Snowflake CORTEX_FINE_TUNING_USAGE_HISTORY Docs](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_fine_tuning_usage_history)
- [Snowflake Service Consumption Table (Pricing)](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf)

---

## 📞 Support

For questions about implementing these new features:
1. Check the [CHANGELOG.md](CHANGELOG.md) for v2.6 updates
2. Review [PRICING_REFERENCE.md](PRICING_REFERENCE.md) for cost calculations
3. Contact your Snowflake account team for feature-specific questions

---

**Version**: v2.6  
**Last Updated**: November 3, 2024  
**Compatibility**: Snowflake ACCOUNT_USAGE views as of October 2024

