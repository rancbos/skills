#!/usr/bin/env python3
"""
Research information lookup using Perplexity Sonar models via OpenRouter.

Auto-selects between Sonar Pro Search and Sonar Reasoning Pro based on
query complexity. Uses academic search mode and extracts citations.
"""

import argparse
import json
import os
import re
import sys
from typing import Any

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install with: pip install requests")
    sys.exit(1)


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model IDs
MODEL_SONAR_PRO = "perplexity/sonar-pro"
MODEL_SONAR_REASONING_PRO = "perplexity/sonar-reasoning-pro"

# Keywords that indicate complex/analytical queries requiring reasoning model
COMPLEX_KEYWORDS = [
    "compare", "contrast", "versus", " vs ", "vs.",
    "analyze", "analysis", "evaluate", "assessment",
    "pros and cons", "trade-off", "trade-offs", "tradeoff", "tradeoffs",
    "advantages", "disadvantages",
    "why ", "explain", "reason", "cause", "because",
    "strategy", "approach", "best practice", "best practices",
    "implications", "consequences", "impact",
    "debate", "controversy", "argue", "argument",
    "critique", "criticism", "review",
    "optimize", "optimization",
    "recommend", "recommendation",
    "should i", "which is better", "what should",
]

# Compound query indicators
COMPOUND_INDICATORS = [" and ", " also ", " additionally ", " furthermore ", ";"]


class ResearchLookup:
    """Research information lookup via Perplexity Sonar models."""

    def __init__(self, api_key: str | None = None):
        if not api_key:
            api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "No API key provided. Set OPENROUTER_API_KEY or pass api_key."
            )
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hermes-agent.nousresearch.com",
            "X-Title": "Hermes Agent - Research Lookup",
        }

    @staticmethod
    def select_model(query: str) -> str:
        """Select the best model based on query complexity."""
        query_lower = query.lower()

        # Check for complex keywords
        for keyword in COMPLEX_KEYWORDS:
            if keyword in query_lower:
                return MODEL_SONAR_REASONING_PRO

        # Check for compound queries (multiple questions in one)
        compound_count = sum(
            1 for indicator in COMPOUND_INDICATORS if indicator in query_lower
        )
        if compound_count >= 2:
            return MODEL_SONAR_REASONING_PRO

        # Check for question mark count (multiple questions)
        if query.count("?") >= 2:
            return MODEL_SONAR_REASONING_PRO

        # Check for very long queries (likely complex)
        if len(query.split()) > 25:
            return MODEL_SONAR_REASONING_PRO

        return MODEL_SONAR_PRO

    @staticmethod
    def extract_citations(content: str) -> list[dict[str, str]]:
        """Extract citation URLs and references from response content."""
        citations = []

        # Extract markdown-style links [text](url)
        md_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
        for text, url in md_links:
            citations.append({"text": text, "url": url})

        # Extract bare URLs
        bare_urls = re.findall(r'(?<!\()(https?://[^\s\)\]]+)', content)
        for url in bare_urls:
            # Avoid duplicates from markdown links
            if not any(c["url"] == url for c in citations):
                citations.append({"text": "", "url": url})

        # Deduplicate by URL
        seen = set()
        unique_citations = []
        for c in citations:
            if c["url"] not in seen:
                seen.add(c["url"])
                unique_citations.append(c)

        return unique_citations

    def lookup(
        self,
        query: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Perform a research lookup and return structured results."""
        if model is None:
            model = self.select_model(query)

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ],
            "extra_body": {
                "search_mode": "academic",
            },
        }

        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_body = ""
            try:
                error_body = response.text
            except Exception:
                pass
            return {
                "success": False,
                "query": query,
                "model": model,
                "error": f"API Error ({response.status_code}): {error_body}",
            }
        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "query": query,
                "model": model,
                "error": f"Connection error: {e}",
            }
        except requests.exceptions.Timeout as e:
            return {
                "success": False,
                "query": query,
                "model": model,
                "error": "Request timed out after 60 seconds.",
            }

        result = response.json()

        choices = result.get("choices", [])
        if not choices:
            return {
                "success": False,
                "query": query,
                "model": model,
                "error": f"No choices in response: {json.dumps(result)[:500]}",
            }

        message = choices[0].get("message", {})
        content = message.get("content", "")

        # Handle content that might be a list of parts
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            content = "\n".join(text_parts)

        citations = self.extract_citations(content)

        # Extract usage info if available
        usage = result.get("usage", {})

        return {
            "success": True,
            "query": query,
            "model": model,
            "content": content,
            "citations": citations,
            "citation_count": len(citations),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }

    def batch_lookup(
        self,
        queries: list[str],
        model: str | None = None,
    ) -> list[dict[str, Any]]:
        """Process multiple research queries in sequence."""
        results = []
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Processing: {query[:80]}...")
            result = self.lookup(query, model=model)
            results.append(result)
            if result["success"]:
                print(f"  -> {result['citation_count']} citations found")
            else:
                print(f"  -> Error: {result['error'][:100]}")
        return results


def format_result(result: dict[str, Any], verbose: bool = True) -> str:
    """Format a lookup result for display."""
    lines = []

    if not result["success"]:
        lines.append(f"ERROR: {result['error']}")
        return "\n".join(lines)

    lines.append(f"Query: {result['query']}")
    lines.append(f"Model: {result['model']}")
    lines.append(f"Citations: {result['citation_count']}")
    lines.append("")

    if verbose:
        lines.append("--- Response ---")
        lines.append(result["content"])
        lines.append("")

        if result["citations"]:
            lines.append("--- Citations ---")
            for i, cite in enumerate(result["citations"], 1):
                if cite["text"]:
                    lines.append(f"  [{i}] {cite['text']}: {cite['url']}")
                else:
                    lines.append(f"  [{i}] {cite['url']}")

        usage = result.get("usage", {})
        if usage.get("total_tokens", 0) > 0:
            lines.append("")
            lines.append(
                f"Tokens: {usage['total_tokens']} "
                f"(prompt: {usage['prompt_tokens']}, "
                f"completion: {usage['completion_tokens']})"
            )

    return "\n".join(lines)


def show_model_info():
    """Display information about available models."""
    print("Available Perplexity Sonar Models")
    print("=" * 50)
    print()
    print(f"  {MODEL_SONAR_PRO}")
    print("    Sonar Pro Search")
    print("    Best for: Factual lookups, definitions, current events")
    print("    Features: Web search, citations, fast responses")
    print()
    print(f"  {MODEL_SONAR_REASONING_PRO}")
    print("    Sonar Reasoning Pro")
    print("    Best for: Complex analysis, comparisons, multi-step reasoning")
    print("    Features: Deep reasoning, web search, citations")
    print()
    print("Auto-Selection Logic:")
    print("  - Simple queries -> Sonar Pro")
    print("  - Complex queries (compare, analyze, why, pros/cons, etc.) -> Sonar Reasoning Pro")
    print("  - Multi-part queries (2+ questions) -> Sonar Reasoning Pro")
    print("  - Long queries (25+ words) -> Sonar Reasoning Pro")
    print()
    print("  Override with --force-model")


def main():
    parser = argparse.ArgumentParser(
        description="Research information lookup using Perplexity Sonar models via OpenRouter."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Research query (single query mode).",
    )
    parser.add_argument(
        "--batch",
        nargs="+",
        metavar="QUERY",
        help="Process multiple queries in batch mode.",
    )
    parser.add_argument(
        "--force-model",
        default=None,
        help=f"Override auto model selection. Options: {MODEL_SONAR_PRO}, {MODEL_SONAR_REASONING_PRO}",
    )
    parser.add_argument(
        "--model-info",
        action="store_true",
        help="Display information about available models and exit.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenRouter API key (overrides OPENROUTER_API_KEY env var).",
    )

    args = parser.parse_args()

    if args.model_info:
        show_model_info()
        return

    if args.batch:
        queries = args.batch
    elif args.query:
        queries = [args.query]
    else:
        parser.print_help()
        sys.exit(1)

    try:
        researcher = ResearchLookup(api_key=args.api_key)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if len(queries) == 1:
        # Single query - show model selection info
        model = args.force_model or researcher.select_model(queries[0])
        if not args.force_model:
            print(f"Auto-selected model: {model}")
        else:
            print(f"Forced model: {model}")

        result = researcher.lookup(queries[0], model=model)
        print()
        print(format_result(result))
    else:
        # Batch mode
        print(f"Processing {len(queries)} queries...")
        results = researcher.batch_lookup(queries, model=args.force_model)
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        for result in results:
            print()
            print(format_result(result))
            print("-" * 60)


if __name__ == "__main__":
    main()
