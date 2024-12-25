import tiktoken


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
