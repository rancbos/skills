#!/usr/bin/env python3
"""
Scientific Schematics - AI Generation Engine
Uses Nano Banana Pro for image generation and Gemini 3 Pro for quality review.
Implements smart iterative refinement.
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime

import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

IMAGE_MODEL = "nano-banana/nano-banana-pro"
REVIEW_MODEL = "google/gemini-2.5-pro"

REVIEW_PROMPT = """You are a scientific illustration quality reviewer. Evaluate this scientific diagram on the following criteria, each scored 1-10:

1. **Scientific Accuracy** - Are elements depicted correctly?
2. **Clarity & Readability** - Can labels, arrows, and components be clearly read?
3. **Labeling** - Are all components properly labeled?
4. **Layout & Composition** - Is the arrangement logical and well-balanced?
5. **Professional Appearance** - Would this look appropriate in a publication?

Respond ONLY with valid JSON in this exact format:
{
  "scores": {
    "scientific_accuracy": <int>,
    "clarity": <int>,
    "labeling": <int>,
    "layout": <int>,
    "professionalism": <int>
  },
  "overall_score": <float>,
  "strengths": ["<str>", ...],
  "weaknesses": ["<str>", ...],
  "improvement_suggestions": ["<str>", ...]
}

The overall_score should be the weighted average: accuracy(0.25) + clarity(0.25) + labeling(0.20) + layout(0.15) + professionalism(0.15).
"""


class ScientificSchematicGenerator:
    """Generates and iteratively refines scientific diagrams."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/hermes-agent/scientific-schematics",
        }

    def _call_api(self, model: str, messages: list, max_tokens: int = 4096) -> dict:
        """Make a request to OpenRouter API."""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        resp = requests.post(
            OPENROUTER_API_URL,
            headers=self.headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def generate_image(self, prompt: str) -> str:
        """Generate an image using Nano Banana Pro. Returns base64-encoded image data."""
        enhanced_prompt = (
            f"Create a high-quality scientific diagram/schematic illustration. "
            f"Style: clean, professional, publication-ready. "
            f"Use clear labels, well-defined lines, and a white or transparent background. "
            f"Description: {prompt}"
        )

        messages = [
            {"role": "user", "content": enhanced_prompt}
        ]

        result = self._call_api(IMAGE_MODEL, messages)

        # Extract image from response
        choice = result.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")

        # Nano Banana Pro may return base64 image in content or in a special field
        # Handle both inline base64 and content-based responses
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image":
                    return part.get("data", part.get("image_url", {}).get("url", ""))
        # If content is a string, check for base64 data
        if isinstance(content, str):
            # Check if it's raw base64 or a data URI
            if content.startswith("data:image"):
                return content.split(",", 1)[1] if "," in content else content
            if len(content) > 1000 and "/" not in content[:20]:
                return content  # Likely raw base64

        # Fallback: try to get image URL from response
        if isinstance(content, str) and content.startswith("http"):
            img_resp = requests.get(content, timeout=60)
            img_resp.raise_for_status()
            return base64.b64encode(img_resp.content).decode("utf-8")

        # If we got a text response instead of image, the model may have described it
        raise RuntimeError(
            f"Image generation did not return image data. Got: {str(content)[:200]}"
        )

    def review_image(self, image_b64: str, original_prompt: str) -> dict:
        """Review an image using Gemini 3 Pro vision capabilities."""
        messages = [
            {"role": "system", "content": REVIEW_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Review this scientific diagram. Original description: {original_prompt}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        },
                    },
                ],
            },
        ]

        result = self._call_api(REVIEW_MODEL, messages, max_tokens=2048)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parse JSON from response
        try:
            # Try to find JSON in the response
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            return json.loads(content[json_start:json_end])
        except (ValueError, json.JSONDecodeError):
            return {
                "scores": {},
                "overall_score": 0.0,
                "strengths": [],
                "weaknesses": ["Failed to parse review response"],
                "improvement_suggestions": [content[:500]],
            }

    def save_image(self, image_b64: str, output_path: str) -> str:
        """Save base64 image data to file. Returns the path written."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
        # Handle data URIs
        if image_b64.startswith("data:image"):
            image_b64 = image_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(image_b64)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        return output_path

    def generate_iterative(
        self,
        prompt: str,
        output_path: str,
        doc_type: str = "default",
        threshold: float = 7.5,
        max_iterations: int = 3,
        verbose: bool = False,
    ) -> dict:
        """
        Generate a scientific diagram with iterative quality refinement.

        Returns dict with: output_path, final_score, iterations, reviews, success
        """
        base, ext = os.path.splitext(output_path)
        ext = ext or ".png"
        review_log = []
        current_prompt = prompt
        best_score = 0.0
        best_image_b64 = None
        best_path = None

        for iteration in range(1, max_iterations + 1):
            if verbose:
                print(f"\n{'='*50}")
                print(f"Iteration {iteration}/{max_iterations}")
                print(f"{'='*50}")

            # Step 1: Generate image
            if verbose:
                print(f"[{timestamp()}] Generating image...")
                print(f"  Prompt: {current_prompt[:100]}...")

            try:
                image_b64 = self.generate_image(current_prompt)
            except Exception as e:
                if verbose:
                    print(f"  Error generating image: {e}")
                review_log.append({"iteration": iteration, "error": str(e)})
                continue

            # Step 2: Save versioned image
            version_path = f"{base}_v{iteration}{ext}"
            self.save_image(image_b64, version_path)
            if verbose:
                print(f"[{timestamp()}] Saved: {version_path}")

            # Step 3: Review image
            if verbose:
                print(f"[{timestamp()}] Reviewing with Gemini 3 Pro...")

            try:
                review = self.review_image(image_b64, prompt)
            except Exception as e:
                if verbose:
                    print(f"  Error reviewing image: {e}")
                review_log.append({"iteration": iteration, "error": str(e)})
                continue

            score = review.get("overall_score", 0.0)
            review_entry = {
                "iteration": iteration,
                "version_path": version_path,
                "score": score,
                "review": review,
            }
            review_log.append(review_entry)

            if verbose:
                print(f"[{timestamp()}] Score: {score:.1f}/{threshold}")
                print(f"  Strengths: {', '.join(review.get('strengths', []))}")
                print(f"  Weaknesses: {', '.join(review.get('weaknesses', []))}")

            # Track best
            if score > best_score:
                best_score = score
                best_image_b64 = image_b64
                best_path = version_path

            # Step 4: Check threshold
            if score >= threshold:
                if verbose:
                    print(f"\n✓ Quality threshold met ({score:.1f} >= {threshold})")
                break

            # Step 5: Refine prompt for next iteration
            if iteration < max_iterations:
                suggestions = review.get("improvement_suggestions", [])
                weaknesses = review.get("weaknesses", [])
                refinement = "; ".join(suggestions + weaknesses)
                current_prompt = (
                    f"{prompt}\n\nIMPORTANT improvements needed: {refinement}. "
                    f"Address these specific issues while maintaining scientific accuracy."
                )
                if verbose:
                    print(f"\n  Refining prompt for next iteration...")
                    print(f"  Issues to fix: {refinement[:200]}...")

        # Save final image (best version)
        if best_image_b64:
            self.save_image(best_image_b64, output_path)
            if verbose:
                print(f"\n[{timestamp()}] Final image saved: {output_path}")
        else:
            if verbose:
                print("\n✗ No images were successfully generated")

        # Save review log
        log_path = f"{base}_review_log.json"
        with open(log_path, "w") as f:
            json.dump(
                {
                    "prompt": prompt,
                    "doc_type": doc_type,
                    "threshold": threshold,
                    "max_iterations": max_iterations,
                    "final_score": best_score,
                    "final_path": output_path,
                    "reviews": review_log,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )
        if verbose:
            print(f"  Review log: {log_path}")

        success = best_score >= threshold
        return {
            "output_path": output_path,
            "final_score": best_score,
            "iterations": len(review_log),
            "reviews": review_log,
            "success": success,
            "review_log_path": log_path,
        }


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="AI-powered scientific diagram generation engine")
    parser.add_argument("prompt", help="Description of the diagram")
    parser.add_argument("-o", "--output", default="schematic.png", help="Output file path")
    parser.add_argument("--doc-type", default="default", help="Document type label")
    parser.add_argument("--threshold", type=float, default=7.5, help="Quality threshold (1-10)")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max refinement iterations")
    parser.add_argument("--api-key", required=True, help="OpenRouter API key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    generator = ScientificSchematicGenerator(api_key=args.api_key)

    result = generator.generate_iterative(
        prompt=args.prompt,
        output_path=args.output,
        doc_type=args.doc_type,
        threshold=args.threshold,
        max_iterations=args.max_iterations,
        verbose=args.verbose,
    )

    if result["success"]:
        print(f"✓ Success! Score: {result['final_score']:.1f} — {result['output_path']}")
    else:
        print(f"✗ Below threshold. Best score: {result['final_score']:.1f} (needed {args.threshold}) — {result['output_path']}")

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
