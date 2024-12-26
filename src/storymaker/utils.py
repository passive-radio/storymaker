import os
import tiktoken
from dotenv import load_dotenv
import pkg_resources


def load_markdown_as_prompt(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def count_tokens(text: str, model: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def count_tokens_from_file(file_path: str, model: str) -> int:
    with open(file_path, "r") as file:
        text = file.read()
    return count_tokens(text, model)


def load_api_key():
    if os.path.exists(".env.local"):
        load_dotenv(".env.local")
    else:
        load_dotenv()
    return os.getenv("OPENAI_API_KEY")


def get_prompt_path(filename):
    return pkg_resources.resource_filename("storymaker", os.path.join("prompt", filename))


def read_prompt(filename):
    prompt_path = get_prompt_path(filename)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
