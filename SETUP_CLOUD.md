# Cloud Model Setup Guide

This guide explains how to configure cloud LLM routing to handle complex queries without overloading your local machine.

## Why Cloud Routing?

**Problem:** The local 7B model (qwen2-math:7b) is resource-intensive and can slow down or crash your machine.

**Solution:** Route complex queries to powerful cloud models (like DeepSeek V3) while keeping simple queries on the fast local 1.5B model.

**Benefits:**
- ✅ No local resource overload
- ✅ Better answers for complex questions
- ✅ Fast responses for simple questions
- ✅ Cost-effective (only pay for complex queries)

## Routing Strategy

```
Simple Questions → Local 1.5B Model (Free, Fast)
      ↓
Complex Questions → Cloud Model (Paid, Powerful)
```

**Simple questions:**
- "What is a derivative?"
- "Define a limit"
- "Find the derivative of x²"

**Complex questions:**
- "Prove the chain rule"
- "Explain the fundamental theorem of calculus"
- "Derive the Taylor series expansion"

## Supported Cloud Providers

### 1. Ollama Cloud

**Pros:**
- Official Ollama cloud service
- Seamless integration with local Ollama
- Access to powerful models like DeepSeek V3.1 671B
- Same API format as local Ollama

**Pricing:**
- Check Ollama Cloud pricing at https://ollama.com/pricing

**Get started:**
1. Sign up at: https://ollama.com/
2. Get API key from your account dashboard
3. Use model format: `deepseek-v3.1:671b-cloud`

### 2. OpenRouter

**Pros:**
- Single API for 200+ models (DeepSeek, Claude, GPT-4, etc.)
- No separate accounts needed
- Competitive pricing
- Simple billing

**Pricing:**
- DeepSeek V3: ~$0.27 per 1M input tokens, ~$1.10 per 1M output tokens
- Llama 3.3 70B: ~$0.18 per 1M input tokens, ~$0.18 per 1M output tokens

**Get started:**
1. Create account: https://openrouter.ai/
2. Get API key: https://openrouter.ai/keys
3. Add credits: https://openrouter.ai/credits

### 3. DeepSeek API (Direct)

**Pros:**
- Direct access to DeepSeek models
- Slightly cheaper than OpenRouter
- Official provider

**Pricing:**
- DeepSeek Chat: ~$0.14 per 1M input tokens, ~$0.28 per 1M output tokens

**Get started:**
1. Create account: https://platform.deepseek.com/
2. Get API key from dashboard
3. Add credits

## Configuration Steps

### Step 1: Install Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install new dependencies (httpx for cloud API)
pip install -e ".[dev]"

# Or with uv (faster)
~/.local/bin/uv pip install -e ".[dev]"
```

### Step 2: Configure Environment Variables

Edit your `.env` file (create from `.env.example` if needed):

**For Ollama Cloud:**
```bash
CLOUD_LLM_ENABLED=true
CLOUD_LLM_PROVIDER=ollama-cloud
CLOUD_LLM_API_KEY=your-ollama-api-key
CLOUD_LLM_MODEL=deepseek-v3.1:671b-cloud
CLOUD_LLM_TIMEOUT=180
```

**For OpenRouter:**
```bash
CLOUD_LLM_ENABLED=true
CLOUD_LLM_PROVIDER=openrouter
CLOUD_LLM_API_KEY=sk-or-v1-xxx  # Your OpenRouter API key
CLOUD_LLM_MODEL=deepseek/deepseek-chat  # Or try: anthropic/claude-sonnet-4-5
CLOUD_LLM_TIMEOUT=180
```

**For DeepSeek Direct:**
```bash
CLOUD_LLM_ENABLED=true
CLOUD_LLM_PROVIDER=deepseek
CLOUD_LLM_API_KEY=sk-xxx  # Your DeepSeek API key
CLOUD_LLM_MODEL=deepseek-chat
CLOUD_LLM_TIMEOUT=180
```

### Step 3: Test the Setup

**Terminal test:**
```bash
python scripts/interactive_rag.py
```

Try asking:
1. Simple question: "What is a derivative?" (should use Fast-1.5B)
2. Complex question: "Prove the chain rule" (should use cloud model)

**Web interface:**
```bash
./run_app.sh
# Or: streamlit run app.py
```

Check the sidebar - it should show "Cloud Model: deepseek-chat" instead of "Powerful Model: qwen2-math:7b"

After each answer, look for the model indicator (e.g., "🤖 Model: Cloud-deepseek-chat")

## Available Cloud Models

### Via OpenRouter

**Math-focused:**
- `deepseek/deepseek-chat` - Excellent for math reasoning (recommended)
- `deepseek/deepseek-reasoner` - Enhanced reasoning capabilities

**General-purpose:**
- `anthropic/claude-sonnet-4-5` - Very capable, good at explanations
- `meta-llama/llama-3.3-70b-instruct` - Strong and cost-effective
- `openai/gpt-4o` - Excellent but pricier

**Find more models:** https://openrouter.ai/models

### Via DeepSeek Direct

- `deepseek-chat` - Main chat model (V3)
- `deepseek-reasoner` - Enhanced reasoning

## Cost Estimation

**Typical calculus question:**
- Input: ~300-500 tokens (context + question)
- Output: ~200-400 tokens (answer)

**Example costs (DeepSeek V3 via OpenRouter):**
- Simple question → Local 1.5B → **FREE**
- Complex question → Cloud → **$0.0002-0.0005 per answer** (~$1 for 2,000-5,000 complex questions)

## Troubleshooting

### Issue: "Cloud API call failed"

**Check:**
1. API key is correct in `.env`
2. You have credits in your account
3. Network connection is working

**Test API key:**
```bash
# For OpenRouter
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $CLOUD_LLM_API_KEY"

# For DeepSeek
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $CLOUD_LLM_API_KEY"
```

### Issue: "Still using local 7B model"

**Check:**
1. `CLOUD_LLM_ENABLED=true` in `.env`
2. `CLOUD_LLM_API_KEY` is not empty
3. Restart the Streamlit app after changing `.env`

### Issue: "LaTeX not rendering properly"

**Fixed!** The new version automatically converts LaTeX delimiters:
- `\[ equation \]` → `$$ equation $$`
- `\( inline \)` → `$ inline $`

If issues persist, try:
1. Refresh the browser
2. Clear Streamlit cache (press 'C' in the app)

## Disabling Cloud Routing

To go back to local-only mode:

```bash
# In .env file
CLOUD_LLM_ENABLED=false
```

The app will automatically fall back to the local 7B model for complex queries.

## Next Steps

1. ✅ Configure your API key
2. ✅ Test with a complex question
3. ✅ Monitor costs in your provider dashboard
4. Consider upgrading to faster models (Claude Sonnet, GPT-4) for even better answers

## Support

- **OpenRouter Docs:** https://openrouter.ai/docs
- **DeepSeek Docs:** https://platform.deepseek.com/docs
- **Issues:** Check the project GitHub issues page
