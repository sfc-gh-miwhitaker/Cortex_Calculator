# Changelog - Cortex Cost Calculator

## v2.6 (November 3, 2024)

### 🎯 Major Update: New Snowflake Features + Latest Pricing

This release combines the latest Cortex pricing (Oct 31, 2025) with support for new Snowflake ACCOUNT_USAGE views that enable dramatically better cost tracking.

### 🔄 Updated: Latest Snowflake Cortex Pricing (Effective Oct 31, 2025)

**Source**: [Snowflake Service Consumption Table](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf)

#### New/Updated LLM Model Pricing

**Claude Models (Anthropic)**:
- `claude-3-5-sonnet`: 3.0/15.0 credits per 1M tokens (input/output)
- `claude-3-5-haiku`: 1.0/5.0 credits per 1M tokens (input/output) - **NEW**
- `claude-3-opus`: 15.0/75.0 credits per 1M tokens (input/output)
- `claude-3-sonnet`: 3.0/15.0 credits per 1M tokens (input/output)
- `claude-3-haiku`: 0.25/1.25 credits per 1M tokens (input/output)

**Llama Models (Meta)**:
- `llama3.1-405b`: 3.0/3.0 credits per 1M tokens - **UPDATED**
- `llama3.1-70b`: 0.4/0.4 credits per 1M tokens - **UPDATED**
- `llama3.1-8b`: 0.1/0.1 credits per 1M tokens - **UPDATED**
- `llama3-70b`: 0.4/0.4 credits per 1M tokens
- `llama3-8b`: 0.1/0.1 credits per 1M tokens

**Mistral Models**:
- `mistral-large2`: 2.0/6.0 credits per 1M tokens - **NEW**
- `mistral-large`: 2.0/6.0 credits per 1M tokens
- `mixtral-8x7b`: 0.15/0.15 credits per 1M tokens
- `mistral-7b`: 0.1/0.1 credits per 1M tokens

**New Model Families**:
- `jamba-1.5-large`: 2.0/8.0 credits per 1M tokens (Hybrid SSM architecture)
- `jamba-1.5-mini`: 0.2/0.4 credits per 1M tokens (Efficient)
- `gemma-7b`: 0.1/0.1 credits per 1M tokens (Google)
- `reka-core`: 3.0/15.0 credits per 1M tokens (Multimodal)
- `reka-flash`: 0.3/1.5 credits per 1M tokens (Fast multimodal)

#### Document AI & Search Services

- **AI Parse Document (Layout)**: 3.33 credits per 1,000 pages
- **AI Parse Document (OCR)**: 0.5 credits per 1,000 pages
- **Cortex Analyst**: 67 credits per 1,000 messages (0.067 per message)
- **Cortex Search**: 6.3 credits per GB/month
- **Document AI**: 8 credits per hour of compute

#### Specialized Text Functions (per 1M tokens)

- **SENTIMENT**: 0.056 credits
- **SUMMARIZE**: 0.056 credits
- **TRANSLATE**: 0.056 credits
- **EXTRACT_ANSWER**: 0.056 credits
- **AI_EXTRACT (standard)**: 0.15 credits
- **AI_EXTRACT (mistral-large)**: 2.0/6.0 credits (input/output)
- **AI_SENTIMENT**: 0.3 credits

#### Embedding Functions (per 1M tokens)

- **EMBED_TEXT_768**: 0.014 credits
- **EMBED_TEXT_1024**: 0.014 credits
- **AI_EMBED (e5-base-v2)**: 0.014 credits
- **AI_EMBED (multilingual-e5-large)**: 0.014 credits
- **AI_EMBED (snowflake-arctic-embed-l-v2.0)**: 0.014 credits
- **AI_EMBED (snowflake-arctic-embed-m-v2.0)**: 0.014 credits
- **EMBED_IMAGE_1024**: 0.14 credits

### 📊 UI Enhancements

1. **New Tabbed Pricing Reference**: 
   - Organized pricing into 4 categories: Document AI & Search, LLM Functions, Text Functions, Embeddings
   - Each tab shows detailed pricing with model characteristics and use cases

2. **Enhanced Validation**:
   - Updated accuracy checks to use official Oct 31, 2025 rates
   - Improved cost per request calculations
   - Better debugging information for rate validation

3. **Updated Documentation**:
   - Added source link to official Snowflake consumption table
   - Clear effective date displayed (Oct 31, 2025)
   - Model notes explaining capabilities (High capability, Fast & efficient, etc.)

### 🔧 Technical Changes

- Updated all pricing validation logic to use new rates
- Enhanced cost per user calculator with official rate toggle
- Improved accuracy check messaging with current pricing
- Updated version strings and headers to v2.6

### 📚 Reference

All pricing updates sourced from:
- **Document**: Snowflake Service Consumption Table
- **URL**: https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf
- **Effective Date**: October 31, 2025

### 🆕 New Snowflake ACCOUNT_USAGE Views Support

**v2.6** adds support for 5 new Snowflake monitoring views (GA dates: July 2024 - March 2025):

#### 1. CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY (Enhanced)
- **Purpose**: Query-level cost tracking (not just hourly aggregates)
- **Benefit**: Identify exact queries consuming excessive credits
- **Use Case**: "Find my 10 most expensive queries" - impossible before
- **New View**: `V_CORTEX_FUNCTIONS_QUERY_DETAIL` with per-query costs
- **New View**: `V_QUERY_COST_ANALYSIS` - most expensive queries across all services

#### 2. CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY (NEW - Mar 2025)
- **Purpose**: Unified tracking for Document AI, PARSE_DOCUMENT, AI_EXTRACT
- **Benefit**: Compare costs between different document processing methods
- **Use Case**: "Should I use Document AI or PARSE_DOCUMENT?" - now you can compare
- **New View**: `V_CORTEX_DOCUMENT_PROCESSING_DETAIL` with per-page costs

#### 3. CORTEX_SEARCH_DAILY_USAGE_HISTORY (NEW - Oct 2024)
- **Purpose**: Daily Cortex Search costs by consumption type
- **Benefit**: Separate serving costs from embedding generation costs
- **Use Case**: Track which services cost the most
- **Already supported**: `V_CORTEX_SEARCH_DETAIL` updated with new fields

#### 4. CORTEX_SEARCH_SERVING_USAGE_HISTORY (NEW - Oct 2024)
- **Purpose**: Hourly Cortex Search serving costs
- **Benefit**: Find idle periods to suspend services and save money
- **Use Case**: "My search runs 24/7 but only used 8am-6pm" - identify waste
- **Already supported**: `V_CORTEX_SEARCH_SERVING_DETAIL` updated for hourly data

#### 5. CORTEX_FINE_TUNING_USAGE_HISTORY (NEW - Oct 2024)
- **Purpose**: Track fine-tuning training costs separately from inference
- **Benefit**: Calculate ROI of fine-tuning investments
- **Use Case**: "Did fine-tuning save us money vs using larger base models?"
- **New View**: `V_CORTEX_FINE_TUNING_DETAIL` for training cost tracking

### 📊 SQL Monitoring Scripts v2.6

**New Deployment Script**: `sql/deploy_cortex_monitoring_v2.6.sql`

**Enhancements**:
- **16 views** (up from 13 in v2.5, 10 in v2.4)
- **New views**:
  - `V_CORTEX_DOCUMENT_PROCESSING_DETAIL` - All document functions
  - `V_CORTEX_FINE_TUNING_DETAIL` - Fine-tuning costs
  - `V_QUERY_COST_ANALYSIS` - Top expensive queries
- **Enhanced views**:
  - `V_CORTEX_FUNCTIONS_QUERY_DETAIL` - Added cost per million tokens calc
  - `V_CORTEX_DAILY_SUMMARY` - Includes document processing & fine-tuning
  - `V_CORTEX_USAGE_HISTORY` - Added document processing metrics
- **Enhanced snapshot table**: `CORTEX_USAGE_SNAPSHOTS` now stores:
  - Total pages processed
  - Total documents processed
  - Credits per page
  - Credits per document

### 🎯 New Capabilities Unlocked

1. **Query-Level Cost Attribution**
   - Before: "Costs went up $500 - why?"
   - Now: "Query XYZ with claude-3-opus cost $478 - optimize or switch models"

2. **Document Processing Optimization**
   - Before: "Document AI seems expensive"
   - Now: "Document AI: $0.0033/page, PARSE_DOCUMENT: $0.0005/page - switch!"

3. **Cortex Search Cost Management**
   - Before: "Search costs $X/month"
   - Now: "Search idle 16 hours/day - suspend at night, save 67%"

4. **Fine-Tuning ROI Analysis**
   - Before: "We spent on fine-tuning"
   - Now: "Training: $200, Inference savings: $50/month - 4 month payback"

### 📚 New Documentation

1. **docs/SNOWFLAKE_NEW_FEATURES_v2.6.md** (NEW)
   - Complete guide to all 5 new ACCOUNT_USAGE views
   - Schema definitions and use cases for each
   - Real-world examples and SQL queries
   - Migration guide from v2.5 to v2.6
   - Best practices for using new features

2. **docs/PRICING_REFERENCE.md** (Updated)
   - Now includes all Oct 31, 2025 pricing
   - 19 LLM models with input/output token costs
   - Embedding functions pricing
   - Cost estimation examples

---

## v2.5 (Previous Release)

### Complete AISQL Function & Model Analysis
- Detailed function and model tracking
- Token-level cost analysis
- Model efficiency comparison
- Serverless vs warehouse execution tracking

---

## Notes

- All credit rates are based on Snowflake-managed compute
- Token-based pricing includes both input and output tokens where applicable
- Your actual costs may vary based on:
  - Specific usage patterns
  - Token distribution (input vs output ratio)
  - Model configurations
  - Mixed operation types

