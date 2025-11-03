# Snowflake Cortex Pricing Reference Guide

**Last Updated**: November 3, 2024  
**Effective Date**: October 31, 2025  
**Source**: [Snowflake Service Consumption Table](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf)

---

## Quick Reference: Cost per Request

Based on standard credit pricing of **$3.00 per credit**:

| Service | Credits per Unit | Cost per Unit @ $3/credit | Cost per Unit @ $4/credit |
|---------|------------------|---------------------------|---------------------------|
| **Cortex Analyst** | 0.067 per message | $0.20 | $0.27 |
| **Document AI (Layout)** | 3.33 per 1K pages | $9.99 | $13.32 |
| **Document AI (OCR)** | 0.5 per 1K pages | $1.50 | $2.00 |
| **Cortex Search** | 6.3 per GB/month | $18.90/GB/mo | $25.20/GB/mo |

---

## LLM Models for Text Generation

Used by: `COMPLETE()`, `AI_COMPLETE()`, `AI_CLASSIFY()`, `AI_FILTER()`, `AI_AGG()`

### Anthropic Claude Models

| Model | Input (credits/1M tokens) | Output (credits/1M tokens) | Cost @ $3/credit | Best For |
|-------|---------------------------|----------------------------|------------------|----------|
| **claude-3-5-sonnet** | 3.0 | 15.0 | $9/$45 | High capability, balanced |
| **claude-3-5-haiku** | 1.0 | 5.0 | $3/$15 | Fast & efficient |
| **claude-3-opus** | 15.0 | 75.0 | $45/$225 | Most capable |
| **claude-3-sonnet** | 3.0 | 15.0 | $9/$45 | Balanced performance |
| **claude-3-haiku** | 0.25 | 1.25 | $0.75/$3.75 | Fastest, cheapest |

### Meta Llama Models

| Model | Credits/1M tokens (in/out) | Cost @ $3/credit | Best For |
|-------|----------------------------|------------------|----------|
| **llama3.1-405b** | 3.0 / 3.0 | $9 / $9 | Largest, most capable |
| **llama3.1-70b** | 0.4 / 0.4 | $1.20 / $1.20 | Good balance |
| **llama3.1-8b** | 0.1 / 0.1 | $0.30 / $0.30 | Most efficient |
| **llama3-70b** | 0.4 / 0.4 | $1.20 / $1.20 | Previous generation |
| **llama3-8b** | 0.1 / 0.1 | $0.30 / $0.30 | Previous generation |

### Mistral AI Models

| Model | Input (credits/1M tokens) | Output (credits/1M tokens) | Cost @ $3/credit | Best For |
|-------|---------------------------|----------------------------|------------------|----------|
| **mistral-large2** | 2.0 | 6.0 | $6 / $18 | Latest large model |
| **mistral-large** | 2.0 | 6.0 | $6 / $18 | Large capability |
| **mixtral-8x7b** | 0.15 | 0.15 | $0.45 / $0.45 | MoE, efficient |
| **mistral-7b** | 0.1 | 0.1 | $0.30 / $0.30 | Base model |

### Other Models

| Model | Input (credits/1M tokens) | Output (credits/1M tokens) | Cost @ $3/credit | Notes |
|-------|---------------------------|----------------------------|------------------|-------|
| **jamba-1.5-large** | 2.0 | 8.0 | $6 / $24 | Hybrid SSM architecture |
| **jamba-1.5-mini** | 0.2 | 0.4 | $0.60 / $1.20 | Efficient hybrid |
| **gemma-7b** | 0.1 | 0.1 | $0.30 / $0.30 | Google open model |
| **reka-core** | 3.0 | 15.0 | $9 / $45 | Multimodal capable |
| **reka-flash** | 0.3 | 1.5 | $0.90 / $4.50 | Fast multimodal |

---

## Specialized Text Functions

| Function | Credits per 1M tokens | Cost @ $3/credit | Use Case |
|----------|----------------------|------------------|----------|
| **SENTIMENT** | 0.056 | $0.168 | Sentiment analysis |
| **SUMMARIZE** | 0.056 | $0.168 | Text summarization |
| **TRANSLATE** | 0.056 | $0.168 | Language translation |
| **EXTRACT_ANSWER** | 0.056 | $0.168 | Q&A from text |
| **AI_EXTRACT (standard)** | 0.15 | $0.45 | Entity extraction |
| **AI_EXTRACT (mistral-large)** | 2.0 (in) / 6.0 (out) | $6 / $18 | Advanced extraction |
| **AI_SENTIMENT** | 0.3 | $0.90 | Advanced sentiment |

---

## Embedding Functions

| Function | Credits per 1M tokens | Cost @ $3/credit | Dimensions | Use Case |
|----------|----------------------|------------------|------------|----------|
| **EMBED_TEXT_768** | 0.014 | $0.042 | 768 | Standard embeddings |
| **EMBED_TEXT_1024** | 0.014 | $0.042 | 1024 | High-dim embeddings |
| **AI_EMBED (e5-base-v2)** | 0.014 | $0.042 | 768 | Multilingual |
| **AI_EMBED (multilingual-e5-large)** | 0.014 | $0.042 | 1024 | Large multilingual |
| **AI_EMBED (snowflake-arctic-embed-l-v2.0)** | 0.014 | $0.042 | 1024 | Arctic large |
| **AI_EMBED (snowflake-arctic-embed-m-v2.0)** | 0.014 | $0.042 | 768 | Arctic medium |
| **EMBED_IMAGE_1024** | 0.14 | $0.42 | 1024 | Image embeddings |

---

## Cost Estimation Examples

### Example 1: Cortex Analyst Chatbot

**Scenario**: 100 users, 20 messages per day each

**Calculation**:
- Daily messages: 100 users × 20 messages = 2,000 messages
- Daily cost: 2,000 × 0.067 credits × $3 = **$402/day**
- Monthly cost: $402 × 30 = **$12,060/month**
- Cost per user per month: $12,060 ÷ 100 = **$120.60/user/month**

### Example 2: Document Processing Pipeline

**Scenario**: 10,000 pages per day (mixed Layout + OCR)

**Calculation** (assuming 50/50 split):
- Layout: 5,000 pages ÷ 1,000 × 3.33 credits × $3 = **$49.95/day**
- OCR: 5,000 pages ÷ 1,000 × 0.5 credits × $3 = **$7.50/day**
- Total daily: **$57.45/day**
- Monthly: **$1,723.50/month**

### Example 3: LLM Text Generation (Claude 3 Haiku)

**Scenario**: 1M input tokens, 200K output tokens per day

**Calculation**:
- Input: 1.0 × 0.25 credits × $3 = **$0.75/day**
- Output: 0.2 × 1.25 credits × $3 = **$0.75/day**
- Total daily: **$1.50/day**
- Monthly: **$45/month**

### Example 4: Mixed Workload

**Scenario**: Enterprise AI application

- **Cortex Analyst**: 500 users × 15 msg/day = 7,500 messages
  - Cost: 7,500 × 0.067 × $3 = **$1,507.50/day**
  
- **Document Processing**: 5,000 pages/day (Layout)
  - Cost: 5 × 3.33 × $3 = **$49.95/day**
  
- **Text Generation**: 2M tokens/day (Llama 3.1-8b, split 70/30 in/out)
  - Input: 1.4M × 0.1 credits × $3 = $0.42
  - Output: 0.6M × 0.1 credits × $3 = $0.18
  - Cost: **$0.60/day**
  
- **Embeddings**: 5M tokens/day (EMBED_TEXT_768)
  - Cost: 5 × 0.014 × $3 = **$0.21/day**

**Total Daily**: $1,558.26  
**Total Monthly**: **$46,747.80**

---

## Model Selection Guide

### When to Use Each Model Type

#### **High Volume, Simple Tasks** → Use Llama 3.1-8b or Mistral-7b
- Classification
- Simple extraction
- Tagging
- **Why**: 10x cheaper than larger models

#### **Balanced Workloads** → Use Claude 3.5 Haiku or Llama 3.1-70b
- Conversational AI
- Summarization
- Q&A
- **Why**: Good capability-to-cost ratio

#### **Complex Reasoning** → Use Claude 3.5 Sonnet or Llama 3.1-405b
- Multi-step reasoning
- Code generation
- Complex analysis
- **Why**: Worth the premium for quality

#### **Maximum Capability** → Use Claude 3 Opus
- Research tasks
- Creative writing
- Nuanced understanding
- **Why**: Highest accuracy when cost is secondary

#### **Multimodal Tasks** → Use Reka models
- Image + text analysis
- Visual Q&A
- **Why**: Native multimodal support

---

## Tips for Cost Optimization

### 1. **Choose the Smallest Model That Works**
- Start with small models (Llama 3.1-8b, Mistral-7b)
- Only upgrade if quality is insufficient
- Can save 10-50x on costs

### 2. **Optimize Token Usage**
- Use shorter prompts where possible
- Implement prompt caching strategies
- Limit output token generation

### 3. **Batch Processing**
- Process multiple items in single requests
- Reduces overhead and API calls
- More efficient use of context window

### 4. **Use Specialized Functions**
- `SENTIMENT` is 40x cheaper than `COMPLETE` for sentiment
- `SUMMARIZE` is optimized for summaries
- Don't use LLMs for tasks with dedicated functions

### 5. **Monitor and Analyze**
- Use the Cortex Cost Calculator regularly
- Track cost per user, cost per operation
- Identify high-cost patterns early

---

## Frequently Asked Questions

### Q: What credit price should I use for estimates?

**A**: Standard Snowflake credit pricing ranges from $2-$4 per credit depending on:
- Account type (On-Demand vs Capacity)
- Region
- Volume discounts
- Enterprise agreements

For estimates, use **$3.00** as a baseline. Check with your account team for exact pricing.

### Q: Are input and output tokens charged differently?

**A**: Yes, for most LLM models. Output tokens typically cost 5x more than input tokens (e.g., Claude 3 Haiku: 0.25 in / 1.25 out).

### Q: How do I calculate monthly costs from daily usage?

**A**: Use this formula:
```
Monthly Cost = (Daily Operations × Credits per Operation × Credit Price × 30.4)
```

Note: 30.4 = average days per month (365 ÷ 12)

### Q: What's included in "tokens"?

**A**: Tokens include:
- Input text (prompt)
- Output text (response)
- System messages
- Function definitions (for AI_CLASSIFY, etc.)

Roughly: 1 token ≈ 4 characters ≈ 0.75 words

### Q: Can I reduce Cortex Search costs?

**A**: Cortex Search charges by indexed data size (GB/month). To optimize:
- Only index necessary columns
- Use efficient data types
- Remove stale or unused data
- Monitor index size with `SHOW CORTEX SEARCH SERVICES`

---

## Resources

- **Official Pricing**: https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf
- **Cortex Documentation**: https://docs.snowflake.com/en/user-guide/ml-powered-analysis
- **Cost Calculator Tool**: `SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_*` views
- **Support**: Contact your Snowflake account team

---

**Disclaimer**: Pricing information is subject to change. Always refer to your Snowflake contract and the official consumption table for contractually binding rates. This guide is for estimation purposes only.

