---
name: research-lookup
description: "Research information lookup using Perplexity Sonar models via OpenRouter. Auto-selects between Sonar Pro Search and Sonar Reasoning Pro based on query complexity."
allowed-tools: [Read, Write, Edit, Bash]
---

# Research Lookup

## Overview

Research and look up information using Perplexity's Sonar models via the OpenRouter API. This skill provides an intelligent query router that automatically selects the best Sonar model based on query complexity — using **Sonar Pro Search** for straightforward factual lookups and **Sonar Reasoning Pro** for complex, multi-step analytical queries.

All queries use academic search mode and return structured results with citations.

## When to Use

- Looking up current facts, statistics, or data points
- Researching technical topics with citation-backed answers
- Comparing options or analyzing trade-offs (auto-selects reasoning model)
- Batch research on multiple related questions
- Finding up-to-date information beyond your knowledge cutoff

## Core Capabilities

- **Automatic Model Selection**: Routes queries to the optimal model based on complexity
- **Academic Search Mode**: Prioritizes authoritative, peer-reviewed, and high-quality sources
- **Citation Extraction**: Returns structured citation data alongside answers
- **Batch Processing**: Run multiple research queries in sequence
- **Model Override**: Force a specific model when you know what you need

## Automatic Model Selection

The skill analyzes query text to determine complexity and selects the appropriate model:

### Sonar Pro Search (`perplexity/sonar-pro`)
Used for **simple/straightforward queries**:
- Factual lookups ("What is the capital of...")
- Definitions ("Define...")
- Simple how-to questions ("How do I...")
- Current events and news ("What happened with...")
- Single-entity information ("Tell me about...")

### Sonar Reasoning Pro (`perplexity/sonar-reasoning-pro`)
Used for **complex/analytical queries** — triggered by keywords like:
- compare, contrast, versus, vs
- analyze, analysis, evaluate, evaluate
- pros and cons, trade-offs, advantages, disadvantages
- why, explain, reason, cause
- strategy, approach, best practice
- multi-part questions with "and" conjunctions

You can override auto-selection with `--force-model`.

## Command-Line Usage

### Basic Research Query

```bash
python /root/.hermes/skills/research-lookup/scripts/research_lookup.py \
  "What are the latest developments in quantum computing error correction?"
```

### Complex Query (auto-selects reasoning model)

```bash
python /root/.hermes/skills/research-lookup/scripts/research_lookup.py \
  "Compare the pros and cons of Rust vs Go for systems programming"
```

### Batch Multiple Queries

```bash
python /root/.hermes/skills/research-lookup/scripts/research_lookup.py \
  --batch "query 1" "query 2" "query 3"
```

### Force a Specific Model

```bash
python /root/.hermes/skills/research-lookup/scripts/research_lookup.py \
  --force-model "perplexity/sonar-reasoning-pro" \
  "Explain the current state of fusion energy research"
```

### View Model Information

```bash
python /root/.hermes/skills/research-lookup/scripts/research_lookup.py --model-info
```

### Full Options

```
positional       Query text (single query mode)
--batch          Process multiple queries (each as a separate argument)
--force-model    Override automatic model selection with a specific model ID
--model-info     Display information about available models and exit
--api-key        OpenRouter API key (overrides OPENROUTER_API_KEY env var)
```

## Query Best Practices

1. **Be specific**: "What is the market share of NVIDIA in AI training GPUs in 2025?" is better than "Tell me about NVIDIA"
2. **Use comparison keywords** for complex analysis: "Compare...", "Analyze...", "What are the trade-offs..."
3. **Batch related queries** rather than sending multiple separate requests
4. **Use `--force-model`** when you know you need deep reasoning even for short queries
5. **Review citations**: The tool returns source URLs — always verify critical information

## Environment Setup

Set the `OPENROUTER_API_KEY` environment variable:

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

Alternatively, pass the key directly via `--api-key`.

Get your API key at: https://openrouter.ai/keys

### Dependencies

- Python 3.8+
- `requests` library (`pip install requests`)
