---
name: scientific-schematics
description: "Create publication-quality scientific diagrams using Nano Banana Pro AI with smart iterative refinement. Uses Gemini 3 Pro for quality review."
allowed-tools: [Read, Write, Edit, Bash]
---

# Scientific Schematics

## Overview

Generate publication-quality scientific diagrams and schematics using AI. This skill uses **Nano Banana Pro** for image generation and **Gemini 3 Pro** for automated quality review, with smart iterative refinement — only regenerating when the quality score falls below the document-type threshold.

## Quick Start

```bash
# Set your API key
export OPENROUTER_API_KEY="sk-or-..."

# Generate a diagram
python3 ~/.hermes/skills/scientific-schematics/scripts/generate_schematic.py \
  "Diagram of a neural network with 3 hidden layers showing forward propagation" \
  -o neural_net.png \
  --doc-type journal
```

## When to Use

- Creating figures for journal papers, conference submissions, or grant applications
- Generating schematic diagrams of experimental setups
- Illustrating scientific concepts, workflows, or system architectures
- Producing diagrams that meet specific publication quality standards
- Prototyping figure ideas before final polish in dedicated software

## How to Use

### Via Claude/Hermes Agent

Simply describe the diagram you need:

> "Create a journal-quality diagram showing the CRISPR-Cas9 gene editing mechanism"

The agent will invoke the skill, generate the image, review it, and iterate if needed.

### Command-Line Usage

```bash
python3 ~/.hermes/skills/scientific-schematics/scripts/generate_schematic.py \
  "your prompt here" \
  -o output.png \
  --doc-type journal \
  --iterations 3 \
  -v
```

**Arguments:**

| Arg | Description | Default |
|-----|-------------|---------|
| `prompt` | Description of the diagram | (required) |
| `-o, --output` | Output file path | `schematic.png` |
| `--doc-type` | Document type for quality threshold | `default` |
| `--iterations` | Maximum refinement iterations | `3` |
| `--api-key` | OpenRouter API key (or set `OPENROUTER_API_KEY` env var) | env var |
| `-v, --verbose` | Show detailed progress | off |

**Document Types & Quality Thresholds:**

| Type | Threshold | Use Case |
|------|-----------|----------|
| `journal` | 8.5 | Peer-reviewed journal figures |
| `conference` | 8.0 | Conference paper figures |
| `thesis` | 8.0 | Thesis/dissertation figures |
| `grant` | 8.0 | Grant proposal figures |
| `preprint` | 7.5 | Preprint server figures |
| `report` | 7.5 | Technical reports |
| `poster` | 7.0 | Poster presentations |
| `presentation` | 6.5 | Slide decks |
| `default` | 7.5 | General purpose |

## AI Generation Mode

The generation pipeline works as follows:

1. **Generate**: Nano Banana Pro creates an image from your prompt via OpenRouter
2. **Review**: Gemini 3 Pro evaluates the image on scientific accuracy, clarity, labeling, and aesthetics
3. **Decide**: If the quality score meets the document threshold, accept. Otherwise, refine the prompt with Gemini's feedback and regenerate.
4. **Iterate**: Repeat until quality threshold is met or max iterations reached
5. **Output**: Final image saved with version history and review log

### Programmatic Usage

```python
from generate_schematic_ai import ScientificSchematicGenerator

gen = ScientificSchematicGenerator(api_key="sk-or-...")
result = gen.generate_iterative(
    prompt="Flowchart of mRNA vaccine mechanism of action",
    output_path="vaccine_flowchart.png",
    doc_type="journal",
    max_iterations=3,
    verbose=True
)
print(f"Final score: {result['final_score']}")
```

## Best Practices

- **Be specific**: Include details about layout, components, arrows, labels, and style
- **Mention orientation**: "horizontal flowchart" vs "vertical diagram"
- **Specify labels**: List exact text labels for components
- **Set style**: "clean minimalist style" or "detailed technical illustration"
- **Choose appropriate doc-type**: Higher thresholds mean more iterations and stricter review

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `OPENROUTER_API_KEY not set` | Export the env var or pass `--api-key` |
| `requests not installed` | Run `pip3 install requests` |
| Low quality score after all iterations | Try a more detailed prompt or lower the doc-type |
| API rate limits | Wait and retry; reduce max iterations |
| Image looks wrong | Add more descriptive detail to the prompt |

## Environment Setup

**Required:**

```bash
# Install dependencies
pip3 install requests

# Set OpenRouter API key (get one at https://openrouter.ai/keys)
export OPENROUTER_API_KEY="sk-or-v1-..."
```

**API Models Used:**
- Image generation: `nano-banana/nano-banana-pro` (via OpenRouter)
- Quality review: `google/gemini-2.5-pro` (via OpenRouter)

## Getting Started

1. Get an API key from [OpenRouter](https://openrouter.ai/keys)
2. Export it: `export OPENROUTER_API_KEY="sk-or-..."`
3. Install requests: `pip3 install requests`
4. Run your first generation:
   ```bash
   python3 ~/.hermes/skills/scientific-schematics/scripts/generate_schematic.py \
     "Simple block diagram of a spectrophotometer showing light source, monochromator, sample, detector" \
     -o spectrophotometer.png \
     -v
   ```
5. Check the output image and review log
