import os
import argparse

import openai

from storymaker.utils import load_api_key, read_prompt, load_markdown_as_prompt, load_manuscript


class CharacterMaker:
    def __init__(self, manuscript_path: str, env_path: str) -> None:
        self.client = openai.OpenAI(api_key=load_api_key(env_path), base_url="https://openrouter.ai/api/v1")
        self.manuscript = load_manuscript(manuscript_path)

    def create_character_settings(self, prompt: str, **kwargs) -> str:
        model = self.manuscript["characters"]
        if "max_completion_tokens" not in kwargs:
            kwargs["max_completion_tokens"] = 5000
        if "top_p" not in kwargs:
            kwargs["top_p"] = 0.85
        if "temperature" not in kwargs:
            kwargs["temperature"] = 0.7
        response = self.client.beta.chat.completions.parse(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=kwargs["max_completion_tokens"],
            top_p=kwargs["top_p"],
            temperature=kwargs["temperature"],
        )
        self.character_settings = response.choices[0].message.content
        return self.character_settings

    def make_init_prompt(self, news: str, language: str = "日本語") -> str:
        prompt = read_prompt("characters.md")
        prompt = prompt.replace("{news}", news).replace("{language}", language)
        return prompt

    def save_character_settings(self, output_path: str):
        dirpath = os.path.dirname(output_path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(output_path, "w") as f:
            f.write(self.character_settings)

    def process_steps(self, news: str, output_path: str, **kwargs):
        prompt = self.make_init_prompt(news, **kwargs)
        self.create_character_settings(prompt, **kwargs)
        self.save_character_settings(output_path)


def main(args=None):
    parser = argparse.ArgumentParser(description="Create character settings")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input news file")
    parser.add_argument(
        "--output", "-o", type=str, required=True, help="Output character settings file"
    )
    parser.add_argument("--manuscript", "-m", type=str, required=False, help="Manuscript file")
    parser.add_argument("--env", "-e", type=str, required=False, help="Environment file")
    
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    news = load_markdown_as_prompt(args.input)
    character_maker = CharacterMaker(args.manuscript, args.env)
    character_maker.process_steps(news, args.output)


if __name__ == "__main__":
    main()
