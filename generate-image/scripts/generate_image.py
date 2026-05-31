#!/usr/bin/env python3
"""
Generate and edit images using OpenRouter API.

Supports multiple image generation models including Gemini 3 Pro Image Preview,
Flux.2 Pro, and Flux.2 Flex.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install with: pip install requests")
    sys.exit(1)


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3-pro-image-preview"
DEFAULT_OUTPUT = "generated_image.png"


def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """Read an image file and return base64-encoded data and MIME type."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    suffix = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(suffix, "image/png")

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return data, mime_type


def build_messages(prompt: str, input_image: str | None = None) -> list[dict]:
    """Build the messages payload for the API request."""
    if input_image:
        img_data, mime_type = encode_image_to_base64(input_image)
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{img_data}"
                        },
                    },
                ],
            }
        ]
    return [{"role": "user", "content": prompt}]


def generate_image(
    prompt: str,
    model: str = DEFAULT_MODEL,
    output_path: str = DEFAULT_OUTPUT,
    input_image: str | None = None,
    api_key: str | None = None,
) -> str:
    """Generate or edit an image via OpenRouter API and save to file."""
    if not api_key:
        api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "No API key provided. Set OPENROUTER_API_KEY or use --api-key."
        )

    messages = build_messages(prompt, input_image)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hermes-agent.nousresearch.com",
        "X-Title": "Hermes Agent - Image Generation",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    print(f"Generating image with model: {model}")
    print(f"Prompt: {prompt}")
    if input_image:
        print(f"Editing image: {input_image}")

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error_body = ""
        try:
            error_body = response.text
        except Exception:
            pass
        print(f"API Error ({response.status_code}): {error_body}")
        raise SystemExit(1) from e
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        raise SystemExit(1) from e
    except requests.exceptions.Timeout as e:
        print("Request timed out after 120 seconds.")
        raise SystemExit(1) from e

    result = response.json()

    # Extract image from response
    # OpenRouter returns base64 images in the message content
    choices = result.get("choices", [])
    if not choices:
        print(f"Error: No choices in response. Full response:\n{json.dumps(result, indent=2)}")
        raise SystemExit(1)

    message = choices[0].get("message", {})
    content = message.get("content", "")

    image_saved = False

    # Check for inline_data in content parts (multimodal response)
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                # Check for inline_data format
                if "inline_data" in part:
                    img_data = part["inline_data"].get("data", "")
                    if img_data:
                        with open(output_path, "wb") as f:
                            f.write(base64.b64decode(img_data))
                        image_saved = True
                        break
                # Check for image_url format
                if part.get("type") == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    if url.startswith("data:"):
                        # Extract base64 from data URI
                        _, b64data = url.split(",", 1)
                        with open(output_path, "wb") as f:
                            f.write(base64.b64decode(b64data))
                        image_saved = True
                        break

    # Check if content is a string containing base64 image data
    if not image_saved and isinstance(content, str):
        # Some models return base64 in the text content
        # Try to find and decode base64 image data
        import re
        # Look for data URI pattern
        data_uri_match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', content)
        if data_uri_match:
            b64data = data_uri_match.group(1)
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(b64data))
            image_saved = True

    if not image_saved:
        # Print what we got for debugging
        print(f"Could not extract image from response. Content type: {type(content)}")
        if isinstance(content, str):
            print(f"Content preview: {content[:500]}")
        else:
            print(f"Content: {json.dumps(content, indent=2)[:500]}")
        print("\nFull response:")
        print(json.dumps(result, indent=2)[:2000])
        raise SystemExit(1)

    abs_path = str(Path(output_path).resolve())
    print(f"Image saved to: {abs_path}")
    return abs_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate and edit images using OpenRouter API."
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Text description of the image to generate or edit instructions.",
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT,
        help=f"Output file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        dest="input_image",
        help="Input image path for editing.",
    )
    parser.add_argument(
        "--api-key", "-k",
        default=None,
        help="OpenRouter API key (overrides OPENROUTER_API_KEY env var).",
    )

    args = parser.parse_args()

    generate_image(
        prompt=args.prompt,
        model=args.model,
        output_path=args.output,
        input_image=args.input_image,
        api_key=args.api_key,
    )


if __name__ == "__main__":
    main()
