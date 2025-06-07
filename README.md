# Storymaker

A simple library for writing stories in ready-to-publish markdown format using LLMs.

## Overview

Storymaker is a Python tool that helps generate creative stories using Large Language Models (LLMs). It provides a complete workflow from character creation to story generation, enhancement, and publishing-ready output in Markdown format.

## Features

- **Character Creation**: Generate detailed character profiles based on input prompts
- **Story Generation**: Create compelling stories with defined characters and themes
- **Story Enhancement**: Improve generated stories through multiple refinement steps
- **Automatic Formatting**: Generate publication-ready markdown files with proper frontmatter
- **Model Flexibility**: Configure different LLM models for each generation step
- **Theme Selection**: Choose from predefined themes or specify your own

## Installation

```bash
# From PyPI
pip install storymaker

# From source
git clone https://github.com/passive-radio/storymaker.git
cd storymaker
pip install -e .
```

## Requirements

- Python 3.10 or higher
- OpenAI API key (or OpenRouter API key)
- Required packages:
  - openai
  - pydantic
  - python-dotenv
  - tiktoken
  - json5

## Usage

### Command Line Interface

Storymaker provides a simple CLI with two main commands:

#### 1. Creating Characters

```bash
storymaker character -i input_news.md -o characters.md -m manuscript.json5 -e .env
```

- `-i, --input`: Input file containing news or context for character creation
- `-o, --output`: Output file to save the generated character profiles
- `-m, --manuscript`: Optional JSON5 file specifying LLM models for each step
- `-e, --env`: Optional environment file with API keys

#### 2. Creating Stories

```bash
storymaker story -i characters.md -o output_directory -m manuscript.json5 -e .env
```

- `-i, --input`: Input file containing character profiles
- `-o, --output_dir`: Output directory for generated stories
- `-m, --manuscript`: Optional JSON5 file specifying LLM models for each step
- `-e, --env`: Optional environment file with API keys

### Python API

You can also use Storymaker programmatically:

```python
from storymaker.create_character import CharacterMaker
from storymaker.create_story import StoryMaker

# Create characters
character_maker = CharacterMaker("manuscript.json5", ".env")
news = "Some news or context for character creation..."
character_maker.process_steps(news, "characters.md")

# Create story
story_maker = StoryMaker("manuscript.json5", ".env")
with open("characters.md", "r") as f:
    characters = f.read()
story_maker.process_steps(characters, "output_dir", theme="ディストピア")
```

## Configuration

### Manuscript File

The manuscript file (JSON5 format) allows you to configure different models and parameters for each step of the generation process:

```json
{
    "characters": {
        "model": "google/gemini-2.5-pro-preview",
        "temperature": 0.7,
        "top_p": 0.85,
    },
    "story": {
        "model": "openai/o3",
        "temperature": 0.8,
        "top_p": 0.85,
    },
    "title_and_synopsis": {
        "model": "openai/o1-mini",
        "temperature": 0.6,
        "top_p": 0.6,
    },
    "enhance_story1": {
        "model": "openai/o3",
        "temperature": 0.8,
        "top_p": 0.85,
    },
    "enhance_story2": {
        "model": "openai/o3",
        "temperature": 0.8,
        "top_p": 0.85,
    },
    "frontmatter": {
        "model": "openai/gpt-4.1",
        "temperature": 0,
        "top_p": 0,
    },
}
```

### Environment File

Create a `.env` file with your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Output

The library generates two main files:

- `story.md`: The raw story content
- `final.md`: Publication-ready story with proper frontmatter

## License

This project is licensed under the MIT License - see the LICENSE file for details.