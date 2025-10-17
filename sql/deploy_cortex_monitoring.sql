-- ============================================================================
-- Cortex AI Usage Monitoring - Deployment Script
-- ============================================================================
-- Purpose: Deploy read-only monitoring views for Cortex AI service usage
-- Target: SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE
-- Prerequisites: IMPORTED PRIVILEGES on SNOWFLAKE database (ACCOUNTADMIN)
-- Safe to run: Idempotent, no data modification, no warehouse creation
-- ============================================================================

-- Step 1: Create database and schema
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_EXAMPLE
    COMMENT = 'Database for Cortex AI usage monitoring and cost analysis';

CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE
    COMMENT = 'Schema containing views for Cortex AI service usage tracking';

-- Use the monitoring schema
USE SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE;

-- ============================================================================
-- VALIDATION: Check ACCOUNT_USAGE Access
-- ============================================================================
-- Run this manually to verify access before proceeding:
-- SELECT COUNT(*) FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY LIMIT 1;
-- 
-- If you get a permissions error, run as ACCOUNTADMIN:
-- GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <YOUR_ROLE>;
-- ============================================================================

-- ============================================================================
-- View 1: V_CORTEX_ANALYST_DETAIL
-- Purpose: Track Cortex Analyst usage including credits
-- Source: SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
-- Columns: START_TIME, END_TIME, USERNAME, CREDITS, REQUEST_COUNT
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_ANALYST_DETAIL
    COMMENT = 'Cortex Analyst usage metrics'
AS
SELECT 
    'Cortex Analyst' AS service_type,
    DATE_TRUNC('day', start_time) AS usage_date,
    start_time,
    end_time,
    username,
    credits,
    request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
WHERE start_time >= DATEADD('day', -90, CURRENT_TIMESTAMP());

-- ============================================================================
-- View 2: V_CORTEX_SEARCH_DETAIL
-- Purpose: Track Cortex Search service usage
-- Source: SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
-- Columns: USAGE_DATE, DATABASE_NAME, SCHEMA_NAME, SERVICE_NAME, SERVICE_ID, 
--          CONSUMPTION_TYPE, CREDITS, MODEL_NAME, TOKENS
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_SEARCH_DETAIL
    COMMENT = 'Cortex Search service daily usage'
AS
SELECT 
    'Cortex Search' AS service_type,
    usage_date,
    database_name,
    schema_name,
    service_name,
    service_id,
    consumption_type,
    credits,
    model_name,
    tokens
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
WHERE usage_date >= DATEADD('day', -90, CURRENT_TIMESTAMP());

-- ============================================================================
-- View 3: V_CORTEX_SEARCH_SERVING_DETAIL
-- Purpose: Track Cortex Search serving usage
-- Source: SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_SERVING_USAGE_HISTORY
-- Columns: START_TIME, END_TIME, DATABASE_NAME, SCHEMA_NAME, SERVICE_NAME, 
--          SERVICE_ID, CREDITS
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_SEARCH_SERVING_DETAIL
    COMMENT = 'Cortex Search serving usage'
AS
SELECT 
    'Cortex Search Serving' AS service_type,
    DATE_TRUNC('day', start_time) AS usage_date,
    start_time,
    end_time,
    database_name,
    schema_name,
    service_name,
    service_id,
    credits
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_SERVING_USAGE_HISTORY
WHERE start_time >= DATEADD('day', -90, CURRENT_TIMESTAMP());

-- ============================================================================
-- View 4: V_CORTEX_FUNCTIONS_DETAIL
-- Purpose: Track Cortex LLM function usage (aggregated hourly)
-- Source: SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY
-- Columns: START_TIME, END_TIME, FUNCTION_NAME, MODEL_NAME, WAREHOUSE_ID,
--          TOKEN_CREDITS, TOKENS
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_FUNCTIONS_DETAIL
    COMMENT = 'Cortex LLM function usage by model (hourly aggregates)'
AS
SELECT 
    'Cortex Functions' AS service_type,
    DATE_TRUNC('day', start_time) AS usage_date,
    start_time,
    end_time,
    function_name,
    model_name,
    warehouse_id,
    token_credits,
    tokens
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY
WHERE start_time >= DATEADD('day', -90, CURRENT_TIMESTAMP());

-- ============================================================================
-- View 5: V_CORTEX_FUNCTIONS_QUERY_DETAIL
-- Purpose: Track query-level Cortex function usage
-- Source: SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY
-- Columns: QUERY_ID, WAREHOUSE_ID, MODEL_NAME, FUNCTION_NAME, TOKENS, TOKEN_CREDITS
-- Note: No timestamp columns - this is per-query, not time-series
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_FUNCTIONS_QUERY_DETAIL
    COMMENT = 'Query-level Cortex function usage'
AS
SELECT 
    'Cortex Functions Query' AS service_type,
    query_id,
    warehouse_id,
    model_name,
    function_name,
    tokens,
    token_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY;

-- ============================================================================
-- View 6: V_DOCUMENT_AI_DETAIL
-- Purpose: Track Document AI usage
-- Source: SNOWFLAKE.ACCOUNT_USAGE.DOCUMENT_AI_USAGE_HISTORY
-- Columns: START_TIME, END_TIME, CREDITS_USED, QUERY_ID, OPERATION_NAME,
--          PAGE_COUNT, DOCUMENT_COUNT, FEATURE_COUNT
-- ============================================================================
CREATE OR REPLACE VIEW V_DOCUMENT_AI_DETAIL
    COMMENT = 'Document AI usage metrics'
AS
SELECT 
    'Document AI' AS service_type,
    DATE_TRUNC('day', start_time) AS usage_date,
    start_time,
    end_time,
    credits_used,
    query_id,
    operation_name,
    page_count,
    document_count,
    feature_count
FROM SNOWFLAKE.ACCOUNT_USAGE.DOCUMENT_AI_USAGE_HISTORY
WHERE start_time >= DATEADD('day', -90, CURRENT_TIMESTAMP());

-- ============================================================================
-- View 7: V_CORTEX_DAILY_SUMMARY
-- Purpose: Daily rollup of all Cortex AI services with unified metrics
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_DAILY_SUMMARY
    COMMENT = 'Daily aggregated summary of all Cortex AI service usage and costs'
AS
WITH all_services AS (
    -- Cortex Analyst
    SELECT 
        usage_date,
        service_type,
        COUNT(DISTINCT username) AS daily_unique_users,
        SUM(request_count) AS total_operations,
        SUM(credits) AS total_credits
    FROM V_CORTEX_ANALYST_DETAIL
    GROUP BY usage_date, service_type
    
    UNION ALL
    
    -- Cortex Search (daily aggregates - no user info)
    SELECT 
        usage_date,
        service_type,
        0 AS daily_unique_users,
        SUM(tokens) AS total_operations,
        SUM(credits) AS total_credits
    FROM V_CORTEX_SEARCH_DETAIL
    GROUP BY usage_date, service_type
    
    UNION ALL
    
    -- Cortex Search Serving
    SELECT 
        usage_date,
        service_type,
        0 AS daily_unique_users,
        COUNT(*) AS total_operations,
        SUM(credits) AS total_credits
    FROM V_CORTEX_SEARCH_SERVING_DETAIL
    GROUP BY usage_date, service_type
    
    UNION ALL
    
    -- Cortex Functions (hourly aggregates - no user info)
    SELECT 
        usage_date,
        service_type,
        0 AS daily_unique_users,
        SUM(tokens) AS total_operations,
        SUM(token_credits) AS total_credits
    FROM V_CORTEX_FUNCTIONS_DETAIL
    GROUP BY usage_date, service_type
    
    UNION ALL
    
    -- Document AI
    SELECT 
        usage_date,
        service_type,
        COUNT(DISTINCT query_id) AS daily_unique_users,
        SUM(page_count) AS total_operations,
        SUM(credits_used) AS total_credits
    FROM V_DOCUMENT_AI_DETAIL
    GROUP BY usage_date, service_type
)
SELECT 
    usage_date,
    service_type,
    SUM(daily_unique_users) AS daily_unique_users,
    SUM(total_operations) AS total_operations,
    SUM(total_credits) AS total_credits,
    CASE 
        WHEN SUM(daily_unique_users) > 0 
        THEN SUM(total_credits) / SUM(daily_unique_users) 
        ELSE 0 
    END AS credits_per_user,
    CASE 
        WHEN SUM(total_operations) > 0 
        THEN SUM(total_credits) / SUM(total_operations) 
        ELSE 0 
    END AS credits_per_operation
FROM all_services
GROUP BY usage_date, service_type
ORDER BY usage_date DESC, total_credits DESC;

-- ============================================================================
-- View 8: V_CORTEX_COST_EXPORT
-- Purpose: Pre-formatted data for cost calculator input
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_COST_EXPORT
    COMMENT = 'Pre-formatted export view for cost calculator'
AS
SELECT 
    usage_date AS date,
    service_type,
    daily_unique_users,
    daily_unique_users AS weekly_active_users,
    daily_unique_users AS monthly_active_users,
    total_operations,
    total_credits,
    credits_per_user,
    credits_per_operation,
    ROUND(credits_per_user, 4) AS avg_daily_cost_per_user,
    ROUND(credits_per_user * 30, 2) AS projected_monthly_cost_per_user,
    ROUND(total_credits * 30, 2) AS projected_monthly_total_credits
FROM V_CORTEX_DAILY_SUMMARY
-- No date filter here - let the extraction query control the date range
ORDER BY date DESC, total_credits DESC;

-- ============================================================================
-- View 10: V_METERING_AI_SERVICES
-- Purpose: High-level AI services usage from metering for validation
-- Source: SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
-- ============================================================================
CREATE OR REPLACE VIEW V_METERING_AI_SERVICES
    COMMENT = 'High-level AI services metering data for validation and comparison'
AS
SELECT 
    usage_date,
    service_type,
    SUM(credits_used) AS total_credits,
    SUM(credits_used_compute) AS compute_credits,
    SUM(credits_used_cloud_services) AS cloud_services_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
WHERE service_type = 'AI_SERVICES'
    AND usage_date >= DATEADD('day', -90, CURRENT_TIMESTAMP())
GROUP BY usage_date, service_type
ORDER BY usage_date DESC;

-- ============================================================================
-- DEPLOYMENT VALIDATION (Quick Check)
-- ============================================================================

-- Verify 9 views were created
SELECT COUNT(*) AS view_count
FROM SNOWFLAKE.INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'CORTEX_AI_USAGE'
    AND TABLE_CATALOG = 'SNOWFLAKE_EXAMPLE';
-- Expected: 9

-- Test data access (will be empty if no Cortex AI usage yet)
SELECT COUNT(*) AS row_count 
FROM SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE.V_CORTEX_DAILY_SUMMARY;

-- If errors occur above, check ACCOUNT_USAGE permissions
-- GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <YOUR_ROLE>;

-- ============================================================================
-- Created Views:
-- 1. V_CORTEX_ANALYST_DETAIL - Cortex Analyst usage (has USERNAME)
-- 2. V_CORTEX_SEARCH_DETAIL - Cortex Search daily usage (no user tracking)
-- 3. V_CORTEX_SEARCH_SERVING_DETAIL - Cortex Search serving usage (no user tracking)
-- 4. V_CORTEX_FUNCTIONS_DETAIL - Cortex Functions hourly aggregates (no user tracking)
-- 5. V_CORTEX_FUNCTIONS_QUERY_DETAIL - Cortex Functions query-level (no timestamps)
-- 6. V_DOCUMENT_AI_DETAIL - Document AI usage (has QUERY_ID as proxy for users)
-- 7. V_CORTEX_DAILY_SUMMARY - Daily rollup across all services
-- 8. V_CORTEX_COST_EXPORT - Pre-formatted for calculator
-- 9. V_METERING_AI_SERVICES - AI services metering rollup
-- ============================================================================

