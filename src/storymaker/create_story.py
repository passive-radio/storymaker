import os
import sys
import openai
from dotenv import load_dotenv
import datetime, zoneinfo
import pkg_resources
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storymaker.utils import load_markdown_as_prompt, count_tokens
from storymaker.classmodel import NovelFrontmatter

BASE_MAX_COMPLETION_TOKENS = 3000


def load_api_key():
    if os.path.exists(".env.local"):
        load_dotenv(".env.local")
    else:
        load_dotenv()
    return os.getenv("OPENAI_API_KEY")


def get_prompt_path(filename):
    return pkg_resources.resource_filename(
        "storymaker", os.path.join("prompt", filename)
    )


def read_prompt(filename):
    prompt_path = get_prompt_path(filename)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


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

        for i in range(count_enhancement):
            enhance_prompt = read_prompt("enhance_story.md")
            enhance_prompt = enhance_prompt.replace("{story}", enhanced_story)
            max_completion_tokens = (
                BASE_MAX_COMPLETION_TOKENS + count_tokens(enhance_prompt, "o1-mini") * 2
            )
            kwargs["max_completion_tokens"] = max_completion_tokens
            enhanced_story = self.create_chat_completion(enhance_prompt, **kwargs)

        self.final_story = enhanced_story
        return enhanced_story

    def create_title_and_synopsis(self) -> str:
        title_and_synopsis_prompt = read_prompt("title_synopsis.md")
        title_and_synopsis_prompt = title_and_synopsis_prompt.replace(
            "{story}", self.final_story
        )
        self.title_and_synopsis_output = self.create_chat_completion(
            title_and_synopsis_prompt
        )
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
        today = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Tokyo")).strftime(
            "%Y-%m-%d"
        )
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

    def process_steps(self, characters: str, output_dir: str):
        init_prompt = read_prompt("initial_story.md")
        init_prompt = init_prompt.replace("{characters}", characters)
        self.create_story(init_prompt, count_enhancement=2)
        plain_text_file_name = os.path.join(output_dir, "story.md")
        self.save_story_as_plain_text(self.final_story, plain_text_file_name)
        self.create_title_and_synopsis()
        self.create_frontmatter()
        final_file_name = os.path.join(output_dir, "final.md")
        self.create_novel_post(final_file_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", type=str)
    parser.add_argument("--output_dir", "-o", type=str)
    args = parser.parse_args()
    story_maker = StoryMaker()
    characters = load_markdown_as_prompt(args.input)
    story_maker.process_steps(characters, args.output_dir)


if __name__ == "__main__":
    main()
