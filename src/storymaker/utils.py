import os
import re
import json

import json5
import tiktoken
from dotenv import load_dotenv
import pkg_resources

def load_markdown_as_prompt(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()

models_encoding = {
    "deepseek/deepseek-r1": "o200k_base",
    "deepseek/deepseek-chat": "o200k_base",
    "openai/o1-mini": "o200k_base",
    "openai/gpt-4o": "o200k_base",
    "openai/gpt-4o-mini": "o200k_base",
    "openai/o1": "o200k_base",
    "openai/o3": "o200k_base",
    "google/gemini-2.5-pro-preview": "o200k_base",
    "google/gemini-2.5-pro-preview": "o200k_base",
    "openai/gpt-5": "o200k_base",
    "openai/gpt-5-mini": "o200k_base",
    "openai/gpt-5.1": "o200k_base",
    "openai/gpt-5.2": "o200k_base",
    "google/gemini-2.5-pro": "o200k_base",
    "google/gemini-3-flash-preview": "o200k_base",
    "google/gemini-3-pro-preview": "o200k_base",
}

def count_tokens(text: str, model: str) -> int:
    # if model like "deepseek/deepseek-r1"
    if model in models_encoding:
        encoding = tiktoken.get_encoding(models_encoding[model])
    else:
        encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def count_tokens_from_file(file_path: str, model: str) -> int:
    with open(file_path, "r") as file:
        text = file.read()
    return count_tokens(text, model)


def load_api_key(filepath: str, service: str = "OPENROUTER_API_KEY"):
    if os.path.exists(filepath):
        load_dotenv(filepath)
    else:
        load_dotenv()
    return os.getenv(service)


def get_prompt_path(filename):
    return pkg_resources.resource_filename("storymaker", os.path.join("prompt", filename))


def read_prompt(filename):
    prompt_path = get_prompt_path(filename)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def no_heading_story(story: str) -> str:
    # remove all heading lines starting with # (# abc, ## abc, ### abc, etc.)
    return re.sub(r"^#+ .*\n", "", story, flags=re.MULTILINE)

def load_manuscript(file_path: str) -> dict:
    with open(file_path, "r") as file:
        # return as dict
        return json5.load(file)
