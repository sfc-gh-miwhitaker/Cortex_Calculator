-- ============================================================================
-- Cortex Usage Monitoring - Cleanup Script
-- ============================================================================
-- Purpose: Remove the CORTEX_USAGE schema and all monitoring views
-- WARNING: This will permanently remove all monitoring objects
-- ============================================================================

-- ============================================================================
-- Verify current objects before cleanup
-- ============================================================================
SHOW VIEWS IN SCHEMA SNOWFLAKE_EXAMPLE.CORTEX_USAGE;

-- ============================================================================
-- Drop the CORTEX_USAGE schema (includes all views)
-- ============================================================================
DROP SCHEMA IF EXISTS SNOWFLAKE_EXAMPLE.CORTEX_USAGE CASCADE;

-- ============================================================================
-- Post-Cleanup Verification
-- ============================================================================
-- Verify the schema was removed
SHOW SCHEMAS IN DATABASE SNOWFLAKE_EXAMPLE;

-- Verify no CORTEX_USAGE schema remains
SELECT 
    COUNT(*) AS schema_exists
FROM SNOWFLAKE.INFORMATION_SCHEMA.SCHEMATA
WHERE CATALOG_NAME = 'SNOWFLAKE_EXAMPLE'
    AND SCHEMA_NAME = 'CORTEX_USAGE';
-- Expected result: 0

-- ============================================================================
-- Re-deployment
-- ============================================================================
-- To re-deploy after cleanup, simply run:
--   sql/deploy_cortex_monitoring.sql
--
-- The deployment script is idempotent and safe to run multiple times
-- ============================================================================

-- ============================================================================
-- What was removed:
--   - SNOWFLAKE_EXAMPLE.CORTEX_USAGE schema
--   - All monitoring views (V_CORTEX_*)
--
-- What was NOT affected:
--   - Source data in SNOWFLAKE.ACCOUNT_USAGE (read-only)
--   - Customer data and applications
--   - Warehouses, users, roles
--   - Any other databases or schemas in SNOWFLAKE_EXAMPLE
-- ============================================================================

