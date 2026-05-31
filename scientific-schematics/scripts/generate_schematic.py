#!/usr/bin/env python3
"""
Scientific Schematics - CLI Wrapper
Generates publication-quality scientific diagrams using AI.

Usage:
    python3 generate_schematic.py "prompt" -o output.png --doc-type journal
"""

import argparse
import os
import subprocess
import sys

DOCUMENT_TYPES = {
    "journal": 8.5,
    "conference": 8.0,
    "thesis": 8.0,
    "grant": 8.0,
    "preprint": 7.5,
    "report": 7.5,
    "poster": 7.0,
    "presentation": 6.5,
    "default": 7.5,
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate publication-quality scientific diagrams using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Neural network architecture diagram" -o nn.png --doc-type journal
  %(prog)s "CRISPR mechanism" -o crispr.png --doc-type conference -v
  %(prog)s "Experimental setup" --doc-type poster --iterations 2
        """,
    )
    parser.add_argument("prompt", help="Description of the scientific diagram to generate")
    parser.add_argument("-o", "--output", default="schematic.png", help="Output file path (default: schematic.png)")
    parser.add_argument(
        "--doc-type",
        choices=list(DOCUMENT_TYPES.keys()),
        default="default",
        help=f"Document type for quality threshold (default: default, threshold: {DOCUMENT_TYPES['default']})",
    )
    parser.add_argument("--iterations", type=int, default=3, help="Maximum refinement iterations (default: 3)")
    parser.add_argument("--api-key", help="OpenRouter API key (or set OPENROUTER_API_KEY env var)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed progress")

    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set.", file=sys.stderr)
        print("Set it via: export OPENROUTER_API_KEY='sk-or-...'", file=sys.stderr)
        print("Or pass --api-key sk-or-...", file=sys.stderr)
        sys.exit(1)

    # Resolve script path (same directory as this file)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ai_script = os.path.join(script_dir, "generate_schematic_ai.py")

    if not os.path.exists(ai_script):
        print(f"Error: AI engine not found at {ai_script}", file=sys.stderr)
        sys.exit(1)

    threshold = DOCUMENT_TYPES[args.doc_type]

    # Build subprocess command
    cmd = [
        sys.executable,
        ai_script,
        args.prompt,
        "-o", args.output,
        "--doc-type", args.doc_type,
        "--threshold", str(threshold),
        "--max-iterations", str(args.iterations),
        "--api-key", api_key,
    ]
    if args.verbose:
        cmd.append("-v")

    if args.verbose:
        print(f"Document type: {args.doc_type} (quality threshold: {threshold})")
        print(f"Max iterations: {args.iterations}")
        print(f"Output: {args.output}")
        print("---")

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
