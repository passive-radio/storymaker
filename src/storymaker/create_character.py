import os
import argparse

from storymaker.utils import read_prompt, load_markdown_as_prompt
from storymaker.base_maker import BaseMaker

class CharacterMaker(BaseMaker):
    def __init__(self, manuscript_path: str, env_path: str) -> None:
        super().__init__(manuscript_path, env_path)

    def create_character_settings(self, prompt: str, **kwargs) -> str:
        character_creation_kwargs = {
            "model": self.manuscript["characters"]["model"],
            "temperature": self.manuscript["characters"]["temperature"],
            "top_p": self.manuscript["characters"]["top_p"],
        }
        self.character_settings = self.create_chat_completion(prompt, **character_creation_kwargs)
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
