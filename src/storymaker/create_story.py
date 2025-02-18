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
    no_heading_story,
    load_manuscript,
)
from storymaker.classmodel import NovelFrontmatter
from storymaker.theme import THEME_LIST

BASE_MAX_COMPLETION_TOKENS = 10000


class StoryMaker:
    def __init__(self, manuscript_path: str, env_path: str) -> None:
        self.env_path = env_path
        self.client = openai.OpenAI(api_key=load_api_key(env_path), base_url="https://openrouter.ai/api/v1")
        self.responses = []
        self.manuscript = load_manuscript(manuscript_path)

    def create_chat_completion(self, prompt: str, **kwargs) -> str:
        if "max_completion_tokens" not in kwargs:
            kwargs["max_completion_tokens"] = BASE_MAX_COMPLETION_TOKENS
        if "response_format" not in kwargs:
            response_format = openai._types.NOT_GIVEN
            response = self.client.chat.completions.create(
                model=kwargs["model"],
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=kwargs["max_completion_tokens"],
                top_p=1.0,
            )
        else:
            response_format = kwargs["response_format"]
            print(response_format)
            response = self.client.beta.chat.completions.parse(
                model=kwargs["model"],
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=kwargs["max_completion_tokens"],
                top_p=1.0,
                response_format=response_format,
            )
        
        print(response)
        self.responses.append(response)

        if response_format is not openai._types.NOT_GIVEN:
            return response.choices[0].message.parsed
        else:
            if response.choices[0].message.content == "":
                raise ValueError("Response is ok but content is empty.")

            return response.choices[0].message.content

    def create_story(self, first_story_idea: str, **kwargs) -> str:
        draft_model = self.manuscript["story"]
        story_draft = self.create_chat_completion(first_story_idea, model=draft_model, **kwargs)
        enhanced_story = story_draft
        self.initial_story = story_draft

        if "theme" not in kwargs:
            raise ValueError("Theme is not specified.")
        
        if "count_enhancement" not in kwargs:
            count_enhancement = 1
        else:
            count_enhancement = int(kwargs["count_enhancement"])

        enhance_prompt_files = ["enhance_story.md", "enhance_story2.md"]
        enhance_models = [self.manuscript["enhance_story"], self.manuscript["enhance_story2"]]
        for i in range(count_enhancement):
            enhance_prompt = read_prompt(enhance_prompt_files[i])
            enhance_prompt = enhance_prompt.replace("{story}", enhanced_story)
            enhance_prompt = enhance_prompt.replace("{theme}", kwargs["theme"])
            enhance_model = enhance_models[i]
            max_completion_tokens = (
                BASE_MAX_COMPLETION_TOKENS + count_tokens(enhance_prompt, enhance_model) * 2
            )
            max_completion_tokens = max(max_completion_tokens, 10000)
            kwargs["max_completion_tokens"] = max_completion_tokens
            kwargs["model"] = enhance_model
            enhanced_story = self.create_chat_completion(enhance_prompt, **kwargs)

        self.final_story = enhanced_story
        self.no_heading_final_story = no_heading_story(enhanced_story)
        return enhanced_story

    def create_title_and_synopsis(self) -> str:
        title_and_synopsis_model = self.manuscript["title_and_synopsis"]
        title_and_synopsis_prompt = read_prompt("title_synopsis.md")
        title_and_synopsis_prompt = title_and_synopsis_prompt.replace("{story}", self.final_story)
        self.title_and_synopsis_output = self.create_chat_completion(
            title_and_synopsis_prompt, model=title_and_synopsis_model
        )
        return self.title_and_synopsis_output

    def create_frontmatter(self) -> str:
        frontmatter_model = self.manuscript["frontmatter"]
        frontmatter_prompt = read_prompt("frontmatter.md")
        frontmatter_prompt = frontmatter_prompt.replace(
            "{title_and_synopsis}", self.title_and_synopsis_output
        )
        client = openai.OpenAI(api_key=load_api_key(self.env_path, "OPENAI_API_KEY"))
        response = client.beta.chat.completions.parse(
            model=frontmatter_model,
            messages=[{"role": "user", "content": frontmatter_prompt}],
            response_format=NovelFrontmatter,
        )
        self.frontmatter = response.choices[0].message.parsed
        # self.frontmatter = self.create_chat_completion(
        #     frontmatter_prompt, model=frontmatter_model, 
        #     response_format=NovelFrontmatter
        # )
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

        markdown_output = frontmatter_text + self.no_heading_final_story
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
        self.save_story_as_plain_text(self.no_heading_final_story, plain_text_file_name)
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
    parser.add_argument(
        "--manuscript", "-m", type=str, required=False, help=("Manuscript file." 
                            "This file contains the model name for each step.")
    )
    parser.add_argument(
        "--env", "-e", type=str, required=False, help=("Environment file." 
                            "This file contains the model name for each step.")
    )
    kwargs = {}

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    story_maker = StoryMaker(args.manuscript, args.env)
    characters = load_markdown_as_prompt(args.input)
    story_maker.process_steps(characters, args.output_dir, theme="ディストピア", **kwargs)


if __name__ == "__main__":
    main()
