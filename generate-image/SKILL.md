---
name: generate-image
description: "Generate and edit images using OpenRouter API with models like Gemini 3 Pro Image Preview and Flux.2 Pro."
allowed-tools: [Read, Write, Edit, Bash]
---

# Generate Image

## Overview

Generate and edit images using the OpenRouter API. This skill provides access to multiple image generation models including Google's Gemini 3 Pro Image Preview (default), Black Forest Labs' Flux.2 Pro, and Flux.2 Flex. Images are generated via a simple CLI tool that handles API communication, base64 decoding, and file output.

## When to Use

- Creating illustrations, concept art, or visual content from text descriptions
- Generating diagrams or visual aids for documentation
- Editing or transforming existing images with text-based instructions
- Creating variations of existing images
- Quick prototyping of visual ideas

## How to Use

1. Ensure `OPENROUTER_API_KEY` is set in your environment
2. Run the script with a text prompt describing the desired image
3. The generated image is saved to the specified output path (default: `generated_image.png`)

## Models

| Model ID | Name | Best For |
|---|---|---|
| `google/gemini-3-pro-image-preview` | Gemini 3 Pro Image Preview | **Default.** High-quality generation and image editing. Supports multimodal input for editing existing images. |
| `black-forest-labs/flux-2-pro` | Flux.2 Pro | Photorealistic images, artistic styles, fine detail. |
| `black-forest-labs/flux-2-flex` | Flux.2 Flex | Flexible generation with varied artistic interpretations. |

## Command-Line Usage

### Basic Image Generation

```bash
python /root/.hermes/skills/generate-image/scripts/generate_image.py \
  --prompt "A serene Japanese garden with cherry blossoms at sunset"
```

### Specify Model and Output

```bash
python /root/.hermes/skills/generate-image/scripts/generate_image.py \
  --prompt "A futuristic cityscape at night" \
  --model "black-forest-labs/flux-2-pro" \
  --output "cityscape.png"
```

### Edit an Existing Image

```bash
python /root/.hermes/skills/generate-image/scripts/generate_image.py \
  --prompt "Add a rainbow in the sky" \
  --input "landscape.png" \
  --output "landscape_rainbow.png"
```

### Full Options

```
--prompt, -p    Text description of the image to generate (required)
--model, -m     Model ID (default: google/gemini-3-pro-image-preview)
--output, -o    Output file path (default: generated_image.png)
--input, -i     Input image path for editing (base64-encoded and sent to model)
--api-key, -k   OpenRouter API key (overrides OPENROUTER_API_KEY env var)
```

## Image Editing

To edit an existing image, provide the `--input` flag with the path to the source image along with a text prompt describing the desired changes. This works best with `gemini-3-pro-image-preview` which supports multimodal (image + text) input.

The source image is base64-encoded and sent alongside the text prompt. The model returns an edited/transformed version based on your instructions.

## Environment Setup

Set the `OPENROUTER_API_KEY` environment variable with your OpenRouter API key:

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

Alternatively, pass the key directly via `--api-key` on the command line.

Get your API key at: https://openrouter.ai/keys

### Dependencies

- Python 3.8+
- `requests` library (`pip install requests`)
