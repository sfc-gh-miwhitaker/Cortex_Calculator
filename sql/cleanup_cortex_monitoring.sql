-- ============================================================================
-- Cortex AI Usage Monitoring - Cleanup Script
-- ============================================================================
-- Purpose: Remove all monitoring views and optionally the schema/database
-- WARNING: This will permanently remove all monitoring objects
-- Safe to run: Multiple execution safeguards included
-- ============================================================================

-- ============================================================================
-- SAFETY CHECK: Uncomment ONE of the options below to proceed
-- ============================================================================
-- Option 1: DROP VIEWS ONLY (keeps schema for history/redeployment)
-- SET cleanup_mode = 'VIEWS_ONLY';

-- Option 2: DROP SCHEMA (removes all views and the schema)
-- SET cleanup_mode = 'SCHEMA';

-- Option 3: DROP DATABASE (complete removal, including other schemas if any)
-- SET cleanup_mode = 'DATABASE';

-- ============================================================================
-- Verify current objects before cleanup
-- ============================================================================
SHOW VIEWS IN SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE;
SHOW SCHEMAS IN DATABASE SNOWFLAKE_EXAMPLE;

-- ============================================================================
-- Cleanup Option 1: DROP VIEWS ONLY
-- ============================================================================
-- Uncomment the section below to drop only the views (keeps schema)
/*
USE SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE;

DROP VIEW IF EXISTS V_CORTEX_COST_EXPORT;
DROP VIEW IF EXISTS V_CORTEX_DAILY_SUMMARY;
DROP VIEW IF EXISTS V_DOCUMENT_AI_DETAIL;
DROP VIEW IF EXISTS V_CORTEX_FUNCTIONS_QUERY_DETAIL;
DROP VIEW IF EXISTS V_CORTEX_FUNCTIONS_DETAIL;
DROP VIEW IF EXISTS V_CORTEX_SEARCH_SERVING_DETAIL;
DROP VIEW IF EXISTS V_CORTEX_SEARCH_DETAIL;
DROP VIEW IF EXISTS V_CORTEX_ANALYST_DETAIL;
DROP VIEW IF EXISTS V_METERING_AI_SERVICES;

-- Verify cleanup
SHOW VIEWS IN SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE;
*/

-- ============================================================================
-- Cleanup Option 2: DROP SCHEMA (includes all views)
-- ============================================================================
-- Uncomment the section below to drop the entire schema
/*
DROP SCHEMA IF EXISTS SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE CASCADE;

-- Verify cleanup
SHOW SCHEMAS IN DATABASE SNOWFLAKE_EXAMPLE;
*/

-- ============================================================================
-- Cleanup Option 3: DROP DATABASE (complete removal)
-- ============================================================================
-- WARNING: This will remove the entire database including any other schemas
-- Only use if SNOWFLAKE_EXAMPLE database is dedicated to this monitoring
/*
DROP DATABASE IF EXISTS SNOWFLAKE_EXAMPLE CASCADE;

-- Verify cleanup
SHOW DATABASES LIKE 'SNOWFLAKE_EXAMPLE';
*/

-- ============================================================================
-- Post-Cleanup Verification
-- ============================================================================
-- Run these queries to verify cleanup was successful:

-- Check if schema still exists
SELECT 
    COUNT(*) AS schema_exists
FROM SNOWFLAKE.INFORMATION_SCHEMA.SCHEMATA
WHERE CATALOG_NAME = 'SNOWFLAKE_EXAMPLE'
    AND SCHEMA_NAME = 'CORTEX_AI_USAGE';

-- Check if database still exists (should return 0 if fully cleaned)
SELECT 
    COUNT(*) AS database_exists
FROM SNOWFLAKE.INFORMATION_SCHEMA.DATABASES
WHERE DATABASE_NAME = 'SNOWFLAKE_EXAMPLE';

-- ============================================================================
-- Re-deployment
-- ============================================================================
-- To re-deploy after cleanup, simply run:
--   sql/deploy_cortex_monitoring.sql
--
-- The deployment script is idempotent and safe to run multiple times
-- ============================================================================

-- ============================================================================
-- Cleanup Complete
-- ============================================================================
-- What was removed:
--   - All monitoring views (V_CORTEX_*)
--   - Schema (if option 2 or 3 was used)
--   - Database (if option 3 was used)
--
-- What was NOT affected:
--   - Source data in SNOWFLAKE.ACCOUNT_USAGE (read-only)
--   - Customer data and applications
--   - Warehouses, users, roles
--   - Any other databases or schemas
-- ============================================================================

