import os
import openai
import datetime
import zoneinfo
import random
import argparse

from storymaker.utils import (
    load_markdown_as_prompt,
    count_tokens,
    load_api_key,
    read_prompt,
)
from storymaker.classmodel import NovelFrontmatter
from storymaker.theme import THEME_LIST

BASE_MAX_COMPLETION_TOKENS = 3000


class StoryMaker:
    def __init__(self) -> None:
        self.client = openai.OpenAI(api_key=load_api_key())
        self.responses = []

    def create_chat_completion(self, prompt: str, **kwargs) -> str:
        if "model" not in kwargs:
            kwargs["model"] = "o1-mini"
        if "max_completion_tokens" not in kwargs:
            kwargs["max_completion_tokens"] = BASE_MAX_COMPLETION_TOKENS
        if "response_format" not in kwargs:
            kwargs["response_format"] = openai._types.NOT_GIVEN
        response = self.client.beta.chat.completions.parse(
            model=kwargs["model"],
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=kwargs["max_completion_tokens"],
            top_p=1.0,
            response_format=kwargs["response_format"],
        )
        self.responses.append(response)

        if kwargs["response_format"] is not openai._types.NOT_GIVEN:
            return response.choices[0].message.parsed
        else:
            if response.choices[0].message.content == "":
                raise ValueError("Response is ok but content is empty.")

            return response.choices[0].message.content

    def create_story(self, first_story_idea: str, **kwargs) -> str:
        # enhance raw story by story enhancement prompt
        if "count_enhancement" not in kwargs:
            count_enhancement = 1
        else:
            count_enhancement = kwargs["count_enhancement"]

        enhanced_story = self.create_chat_completion(first_story_idea, **kwargs)
        self.initial_story = enhanced_story

        if "theme" not in kwargs:
            raise ValueError("Theme is not specified.")

        enhance_prompt_files = ["enhance_story.md", "enhance_story_two.md"]
        for i in range(count_enhancement):
            enhance_prompt = read_prompt(enhance_prompt_files[i])
            enhance_prompt = enhance_prompt.replace("{story}", enhanced_story)
            enhance_prompt = enhance_prompt.replace("{theme}", kwargs["theme"])
            max_completion_tokens = (
                BASE_MAX_COMPLETION_TOKENS + count_tokens(enhance_prompt, "o1-mini") * 2
            )
            kwargs["max_completion_tokens"] = max_completion_tokens
            enhanced_story = self.create_chat_completion(enhance_prompt, **kwargs)

        self.final_story = enhanced_story
        return enhanced_story

    def create_title_and_synopsis(self) -> str:
        title_and_synopsis_prompt = read_prompt("title_synopsis.md")
        title_and_synopsis_prompt = title_and_synopsis_prompt.replace("{story}", self.final_story)
        self.title_and_synopsis_output = self.create_chat_completion(title_and_synopsis_prompt)
        return self.title_and_synopsis_output

    def create_frontmatter(self) -> str:
        frontmatter_prompt = read_prompt("frontmatter.md")
        frontmatter_prompt = frontmatter_prompt.replace(
            "{title_and_synopsis}", self.title_and_synopsis_output
        )
        self.frontmatter = self.create_chat_completion(
            frontmatter_prompt, model="gpt-4o", response_format=NovelFrontmatter
        )
        print(self.frontmatter)
        return self.frontmatter

    def save_story_as_plain_text(self, story: str, file_name: str):
        dir_path = os.path.dirname(file_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(file_name, "w") as f:
            f.write(story)

    def create_novel_post(self, file_name: str):
        dir_path = os.path.dirname(file_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        today = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d")
        frontmatter_text = "---\n"
        frontmatter_text += f"title: {self.frontmatter.title}\n"
        frontmatter_text += f"description: {self.frontmatter.synopsis}\n"
        frontmatter_text += f"publishDate: {today}\n"
        frontmatter_text += f"author: {self.frontmatter.author}\n"
        frontmatter_text += f"tags:\n"
        for tag in self.frontmatter.tags:
            frontmatter_text += f"  - {tag}\n"
        frontmatter_text += "draft: false\n"
        frontmatter_text += "---\n\n"

        markdown_output = frontmatter_text + self.final_story
        with open(file_name, "w") as f:
            f.write(markdown_output)

    def process_steps(self, characters: str, output_dir: str, **kwargs):
        init_prompt = read_prompt("initial_story.md")
        init_prompt = init_prompt.replace("{characters}", characters)
        if "theme" not in kwargs:
            theme = random.choice(THEME_LIST)
            kwargs["theme"] = theme
        init_prompt = init_prompt.replace("{theme}", kwargs["theme"])

        self.create_story(init_prompt, count_enhancement=2, **kwargs)
        plain_text_file_name = os.path.join(output_dir, "story.md")
        self.save_story_as_plain_text(self.final_story, plain_text_file_name)
        self.create_title_and_synopsis()
        self.create_frontmatter()
        final_file_name = os.path.join(output_dir, "final.md")
        self.create_novel_post(final_file_name)


def main(args=None):
    parser = argparse.ArgumentParser(description="Create a story")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input character file")
    parser.add_argument(
        "--output_dir", "-o", type=str, required=True, help="Output directory for the story"
    )

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    story_maker = StoryMaker()
    characters = load_markdown_as_prompt(args.input)
    story_maker.process_steps(characters, args.output_dir, theme="ディストピア")


if __name__ == "__main__":
    main()
