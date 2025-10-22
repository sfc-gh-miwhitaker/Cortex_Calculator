-- ============================================================================
-- Cortex Usage Monitoring - Deployment Script
-- ============================================================================
-- Purpose: Deploy read-only monitoring views for Cortex service usage
-- Target: SNOWFLAKE_EXAMPLE.CORTEX_USAGE
-- Prerequisites: IMPORTED PRIVILEGES on SNOWFLAKE database (ACCOUNTADMIN)
-- Safe to run: Idempotent, no data modification, no warehouse creation
-- ============================================================================

-- ============================================================================
-- CONFIGURATION: Serverless Task
-- ============================================================================
-- The daily snapshot task runs serverless (no warehouse required)
-- Snowflake automatically manages compute resources
-- Cost: Charged per-second based on actual usage (~1-5 seconds per day)
-- ============================================================================

-- Step 1: Create database and schema
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_EXAMPLE
    COMMENT = 'Database for Cortex usage monitoring and cost analysis';

CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_EXAMPLE.CORTEX_USAGE
    COMMENT = 'Schema containing views for Cortex service usage tracking';

-- Use the monitoring schema
USE SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_USAGE;

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
-- Purpose: Daily rollup of all Cortex services with unified metrics
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_DAILY_SUMMARY
    COMMENT = 'Daily aggregated summary of all Cortex service usage and costs'
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
-- Historical Snapshot Table: CORTEX_USAGE_SNAPSHOTS
-- Purpose: Daily snapshots of usage data for historical tracking and analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS CORTEX_USAGE_SNAPSHOTS (
    snapshot_date DATE NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    usage_date DATE NOT NULL,
    daily_unique_users NUMBER(38,0),
    total_operations NUMBER(38,0),
    total_credits NUMBER(38,6),
    credits_per_user NUMBER(38,6),
    credits_per_operation NUMBER(38,12),
    inserted_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (snapshot_date, service_type, usage_date)
)
COMMENT = 'Daily snapshots of Cortex usage for historical tracking and cost analysis';

-- ============================================================================
-- Scheduled Task: TASK_DAILY_CORTEX_SNAPSHOT (Serverless)
-- Purpose: Capture daily usage data at 3:00 AM
-- Schedule: Daily at 3:00 AM (after ACCOUNT_USAGE data is typically refreshed)
-- Compute: Serverless (Snowflake-managed, no warehouse required)
-- ============================================================================
CREATE OR REPLACE TASK TASK_DAILY_CORTEX_SNAPSHOT
    SCHEDULE = 'USING CRON 0 3 * * * America/Los_Angeles'
    USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
    COMMENT = 'Daily serverless snapshot of Cortex usage at 3 AM'
AS
MERGE INTO CORTEX_USAGE_SNAPSHOTS AS target
USING (
    SELECT 
        CURRENT_DATE() AS snapshot_date,
        service_type,
        usage_date,
        daily_unique_users,
        total_operations,
        total_credits,
        credits_per_user,
        credits_per_operation
    FROM V_CORTEX_DAILY_SUMMARY
    WHERE usage_date >= DATEADD('day', -2, CURRENT_DATE())  -- Capture last 2 days to handle any delays
) AS source
ON target.snapshot_date = source.snapshot_date
    AND target.service_type = source.service_type
    AND target.usage_date = source.usage_date
WHEN MATCHED THEN
    UPDATE SET
        daily_unique_users = source.daily_unique_users,
        total_operations = source.total_operations,
        total_credits = source.total_credits,
        credits_per_user = source.credits_per_user,
        credits_per_operation = source.credits_per_operation,
        inserted_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (snapshot_date, service_type, usage_date, daily_unique_users, total_operations, 
            total_credits, credits_per_user, credits_per_operation)
    VALUES (source.snapshot_date, source.service_type, source.usage_date, source.daily_unique_users,
            source.total_operations, source.total_credits, source.credits_per_user, source.credits_per_operation);

-- Resume the task to activate it
ALTER TASK TASK_DAILY_CORTEX_SNAPSHOT RESUME;

-- ============================================================================
-- View 10: V_CORTEX_USAGE_HISTORY
-- Purpose: Historical snapshot view matching V_CORTEX_COST_EXPORT structure
-- Optimized for Streamlit cost calculator queries
-- ============================================================================
CREATE OR REPLACE VIEW V_CORTEX_USAGE_HISTORY
    COMMENT = 'Historical snapshot view for cost calculator (optimized performance)'
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
    ROUND(total_credits * 30, 2) AS projected_monthly_total_credits,
    snapshot_date,
    inserted_at,
    -- Trend analysis metrics
    LAG(total_credits, 7) OVER (PARTITION BY service_type ORDER BY usage_date) AS credits_7d_ago,
    ROUND(((total_credits - LAG(total_credits, 7) OVER (PARTITION BY service_type ORDER BY usage_date)) / 
           NULLIF(LAG(total_credits, 7) OVER (PARTITION BY service_type ORDER BY usage_date), 0)) * 100, 2) AS credits_wow_growth_pct
FROM CORTEX_USAGE_SNAPSHOTS
ORDER BY date DESC, total_credits DESC;

-- ============================================================================
-- DEPLOYMENT VALIDATION (Quick Check)
-- ============================================================================

-- Verify 10 views were created
SELECT COUNT(*) AS view_count
FROM SNOWFLAKE.INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'CORTEX_USAGE'
    AND TABLE_CATALOG = 'SNOWFLAKE_EXAMPLE';
-- Expected: 10

-- Verify 1 table was created
SELECT COUNT(*) AS table_count
FROM SNOWFLAKE.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'CORTEX_USAGE'
    AND TABLE_CATALOG = 'SNOWFLAKE_EXAMPLE'
    AND TABLE_TYPE = 'BASE TABLE';
-- Expected: 1

-- Verify task was created and is running
SHOW TASKS LIKE 'TASK_DAILY_CORTEX_SNAPSHOT' IN SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_USAGE;
-- Expected: STATE = 'started', SCHEDULE should show CRON expression

-- Check task execution history (if any runs have occurred)
SELECT 
    NAME,
    STATE,
    SCHEDULED_TIME,
    COMPLETED_TIME,
    RETURN_VALUE
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    TASK_NAME => 'SNOWFLAKE_EXAMPLE.CORTEX_USAGE.TASK_DAILY_CORTEX_SNAPSHOT',
    SCHEDULED_TIME_RANGE_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
ORDER BY SCHEDULED_TIME DESC
LIMIT 5;
-- Note: Will be empty if task hasn't run yet (first run at 3 AM)

-- Test data access (will be empty if no Cortex usage yet)
SELECT COUNT(*) AS row_count 
FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_DAILY_SUMMARY;

-- If errors occur above, check ACCOUNT_USAGE permissions
-- GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <YOUR_ROLE>;

-- ============================================================================
-- Created Objects:
-- VIEWS (10):
-- 1. V_CORTEX_ANALYST_DETAIL - Cortex Analyst usage (has USERNAME)
-- 2. V_CORTEX_SEARCH_DETAIL - Cortex Search daily usage (no user tracking)
-- 3. V_CORTEX_SEARCH_SERVING_DETAIL - Cortex Search serving usage (no user tracking)
-- 4. V_CORTEX_FUNCTIONS_DETAIL - Cortex Functions hourly aggregates (no user tracking)
-- 5. V_CORTEX_FUNCTIONS_QUERY_DETAIL - Cortex Functions query-level (no timestamps)
-- 6. V_DOCUMENT_AI_DETAIL - Document AI usage (has QUERY_ID as proxy for users)
-- 7. V_CORTEX_DAILY_SUMMARY - Daily rollup across all services
-- 8. V_CORTEX_COST_EXPORT - Pre-formatted for calculator
-- 9. V_METERING_AI_SERVICES - AI services metering rollup
-- 10. V_CORTEX_USAGE_HISTORY - Historical snapshots with trend analysis
--
-- TABLES (1):
-- 1. CORTEX_USAGE_SNAPSHOTS - Daily snapshots of usage data
--
-- TASKS (1):
-- 1. TASK_DAILY_CORTEX_SNAPSHOT - Runs daily at 3 AM to capture snapshots
-- ============================================================================

