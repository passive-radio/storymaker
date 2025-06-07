import os
import argparse
import random

from storymaker.genre import GENRE_LIST
from storymaker.utils import read_prompt, load_markdown_as_prompt
from storymaker.base_maker import BaseMaker

class CharacterMaker(BaseMaker):
    def __init__(self, manuscript_path: str, env_path: str) -> None:
        super().__init__(manuscript_path, env_path)
        self.system_prompt = read_prompt("system_prompt.md")
        
    def create_character_settings(self, prompt: str, **kwargs) -> str:
        character_creation_kwargs = {
            "model": self.manuscript["characters"]["model"],
            "temperature": self.manuscript["characters"]["temperature"],
            "top_p": self.manuscript["characters"]["top_p"],
        }
        self.character_settings = self.create_chat_completion(prompt, self.system_prompt, **character_creation_kwargs)
        return self.character_settings

    def make_init_prompt(self, news: str, language: str, genre: str) -> str:
        prompt = read_prompt("characters.md")
        prompt = prompt.replace("{news}", news).replace("{language}", language)
        prompt = prompt.replace("{genre}", genre)
        return prompt

    def save_character_settings(self, output_path: str):
        dirpath = os.path.dirname(output_path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(output_path, "w") as f:
            f.write(self.character_settings)

    def process_steps(self, news: str, output_path: str, **kwargs):
        if "language" not in kwargs:
            kwargs["language"] = "日本語"
        if "genre" not in kwargs:
            kwargs["genre"] = random.choice(GENRE_LIST)
        
        prompt = self.make_init_prompt(news, kwargs["language"], kwargs["genre"])
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
    parser.add_argument("--genre", "-g", type=str, required=False, help="Genre of the story")
    
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)
        
    kwargs = {}
    if args.genre is not None:
        kwargs["genre"] = args.genre

    news = load_markdown_as_prompt(args.input)
    character_maker = CharacterMaker(args.manuscript, args.env)
    character_maker.process_steps(news, args.output, **kwargs)


if __name__ == "__main__":
    main()
