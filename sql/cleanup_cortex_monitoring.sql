-- ============================================================================
-- Cortex Usage Monitoring - Cleanup Script
-- ============================================================================
-- Purpose: Remove the CORTEX_USAGE schema and all monitoring objects
-- WARNING: This will permanently remove all monitoring views, tables, and tasks
-- Safe to run: Multiple times (uses IF EXISTS), no impact on source data
-- Follows: Cleanup Rule - Must drop ONLY project-created objects, preserve database
-- ============================================================================

-- ============================================================================
-- Step 1: Verify current objects before cleanup
-- ============================================================================
-- Show all views in the schema
SHOW VIEWS IN SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_USAGE;

-- Show all tasks (must be suspended before dropping schema)
SHOW TASKS IN SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_USAGE;

-- Show all tables
SHOW TABLES IN SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_USAGE;

-- ============================================================================
-- Step 2: Suspend all tasks before dropping (required)
-- ============================================================================
-- Tasks must be suspended before dropping schema
ALTER TASK IF EXISTS SNOWFLAKE_EXAMPLE.CORTEX_USAGE.TASK_DAILY_CORTEX_SNAPSHOT SUSPEND;

-- ============================================================================
-- Step 3: Drop the CORTEX_USAGE schema (includes all views, tables, tasks)
-- ============================================================================
-- CASCADE will drop all objects in the schema
-- Safe to run multiple times (uses IF EXISTS)
DROP SCHEMA IF EXISTS SNOWFLAKE_EXAMPLE.CORTEX_USAGE CASCADE;

-- ============================================================================
-- Step 4: Post-Cleanup Verification
-- ============================================================================
-- Verify the schema was removed
SHOW SCHEMAS IN DATABASE SNOWFLAKE_EXAMPLE;

-- Verify no CORTEX_USAGE schema remains
SELECT 
    COUNT(*) AS schema_exists,
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ Cleanup successful - schema removed'
        ELSE '❌ Schema still exists - check permissions'
    END AS status
FROM SNOWFLAKE.INFORMATION_SCHEMA.SCHEMATA
WHERE CATALOG_NAME = 'SNOWFLAKE_EXAMPLE'
    AND SCHEMA_NAME = 'CORTEX_USAGE';
-- Expected result: schema_exists = 0

-- ============================================================================
-- Re-deployment
-- ============================================================================
-- To re-deploy after cleanup, simply run:
--   sql/deploy_cortex_monitoring.sql
--
-- The deployment script is idempotent and safe to run multiple times
-- ============================================================================

-- ============================================================================
-- Summary: What Was Removed
-- ============================================================================
--   ✅ SNOWFLAKE_EXAMPLE.CORTEX_USAGE schema
--   ✅ 16 monitoring views (V_CORTEX_ANALYST_DETAIL, V_CORTEX_SEARCH_DETAIL, etc.)
--   ✅ 1 snapshot table (CORTEX_USAGE_SNAPSHOTS)
--   ✅ 1 serverless task (TASK_DAILY_CORTEX_SNAPSHOT)
--
-- What Was PRESERVED (Cleanup Rule):
--   ✅ SNOWFLAKE_EXAMPLE database (preserved per cleanup rule)
--   ✅ Source data in SNOWFLAKE.ACCOUNT_USAGE (read-only, untouched)
--   ✅ Customer data and applications (not affected)
--   ✅ Warehouses, users, roles (not affected)
--   ✅ All other schemas in SNOWFLAKE_EXAMPLE (not affected)
-- ============================================================================

