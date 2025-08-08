import os
import datetime
import zoneinfo
import random
import argparse
import logging

from storymaker.utils import (
    load_markdown_as_prompt,
    count_tokens,
    read_prompt,
    no_heading_story,
)
from storymaker.classmodel import NovelFrontmatter
from storymaker.genre import GENRE_LIST
from storymaker.base_maker import BaseMaker
BASE_MAX_COMPLETION_TOKENS = 100000

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

class StoryMaker(BaseMaker):
    def __init__(self, manuscript_path: str, env_path: str) -> None:
        super().__init__(manuscript_path, env_path)
        self.system_prompt = read_prompt("system_prompt.md")

    def create_story(self, first_story_idea: str, **kwargs) -> str:
        logger.info("Creating story...")
        
        try:
            if "genre" not in kwargs:
                raise ValueError("Genre is not specified.")
            
            draft_model = self.manuscript["story"]["model"]
            story_creation_kwargs = {
                "model": draft_model,
                "temperature": self.manuscript["story"]["temperature"],
                "top_p": self.manuscript["story"]["top_p"],
                "reasoning_effort": self.manuscript["story"]["reasoning_effort"],
            }
            story_draft = self.create_chat_completion(first_story_idea, self.system_prompt, **story_creation_kwargs)
            logger.info(f"Story draft generated.")

            enhanced_story = story_draft
            self.initial_story = story_draft
            
            self.count_story_tokens = count_tokens(story_draft, draft_model)
            
            if "count_enhancement" not in kwargs:
                count_enhancement = 1
            else:
                count_enhancement = int(kwargs["count_enhancement"])

            enhance_prompt_files = ["enhance_story1.md", "enhance_story2.md"]
            enhance_models = [self.manuscript["enhance_story1"]["model"], self.manuscript["enhance_story2"]["model"]]
            reasoning_effort = [self.manuscript["enhance_story1"]["reasoning_effort"], self.manuscript["enhance_story2"]["reasoning_effort"]]
            for i in range(count_enhancement):
                logger.info(f"Enhancing story {i+1}...")
                enhance_prompt = read_prompt(enhance_prompt_files[i])
                enhance_prompt = enhance_prompt.replace("{story}", enhanced_story)
                enhance_prompt = enhance_prompt.replace("{genre}", kwargs["genre"])
                
                # Calculate token counts for debugging
                story_tokens = self.count_story_tokens
                prompt_tokens = count_tokens(enhance_prompt, enhance_models[i])
                calculated_max_tokens = story_tokens * 5 + prompt_tokens
                
                # Apply reasonable limits for reasoning models (need space for thinking + output)
                # Minimum 40000 for reasoning tokens, but cap at a reasonable maximum
                max_safe_tokens = min(max(calculated_max_tokens, 40000), 200000)
                
                logger.info(f"Token calculation: story_tokens={story_tokens}, prompt_tokens={prompt_tokens}")
                logger.info(f"Calculated max_tokens={calculated_max_tokens}, using safe_limit={max_safe_tokens}")
                
                enhancement_kwargs = {
                    "model": enhance_models[i],
                    "temperature": self.manuscript[f"enhance_story{i+1}"]["temperature"],
                    "top_p": self.manuscript[f"enhance_story{i+1}"]["top_p"],
                    "reasoning_effort": reasoning_effort[i],
                    "max_completion_tokens": max_safe_tokens,
                }
                
                enhanced_story = self.create_chat_completion(enhance_prompt, self.system_prompt, **enhancement_kwargs)
                self.count_story_tokens = count_tokens(enhanced_story, enhance_models[i])
                
                logger.info(f"Story enhancement {i+1} completed.")
                
            self.final_story = enhanced_story
            self.no_heading_final_story = no_heading_story(enhanced_story)
            return enhanced_story
        except Exception as e:
            logger.error(f"Error creating story: {e}")
            raise e

    def create_title_and_synopsis(self) -> str:
        logger.info("Creating title and synopsis...")
        try:
            title_and_synopsis_model = self.manuscript["title_and_synopsis"]["model"]
            title_and_synopsis_kwargs = {
                "model": title_and_synopsis_model,
                "temperature": self.manuscript["title_and_synopsis"]["temperature"],
                "top_p": self.manuscript["title_and_synopsis"]["top_p"],
                "reasoning_effort": self.manuscript["title_and_synopsis"].get("reasoning_effort", "medium"),
            }
            title_and_synopsis_prompt = read_prompt("title_synopsis.md")
            title_and_synopsis_prompt = title_and_synopsis_prompt.replace("{story}", self.final_story)
            self.title_and_synopsis_output = self.create_chat_completion(
                title_and_synopsis_prompt, self.system_prompt, **title_and_synopsis_kwargs
            )
            return self.title_and_synopsis_output
        except Exception as e:
            logger.error(f"Error creating title and synopsis: {e}")
            raise e

    def create_frontmatter(self) -> str:
        logger.info("Creating frontmatter...")
        try:
            frontmatter_model = self.manuscript["frontmatter"]["model"]
            frontmatter_kwargs = {
                "model": frontmatter_model,
                "temperature": self.manuscript["frontmatter"]["temperature"],
                "top_p": self.manuscript["frontmatter"]["top_p"],
                "response_format": NovelFrontmatter,
            }
            frontmatter_prompt = read_prompt("frontmatter.md")
            frontmatter_prompt = frontmatter_prompt.replace(
                "{title_and_synopsis}", self.title_and_synopsis_output
            )
            # client = openai.OpenAI(api_key=load_api_key(self.env_path, "OPENAI_API_KEY"))
            # response = client.beta.chat.completions.parse(
            #     model=frontmatter_model,
            #     messages=[{"role": "user", "content": frontmatter_prompt}],
            #     response_format=NovelFrontmatter,
            # )
            response = self.create_chat_completion(frontmatter_prompt, self.system_prompt, **frontmatter_kwargs)
            self.frontmatter = response
            # self.frontmatter = self.create_chat_completion(
            #     frontmatter_prompt, model=frontmatter_model, 
            #     response_format=NovelFrontmatter
            # )
            print(self.frontmatter)
            return self.frontmatter
        except Exception as e:
            logger.error(f"Error creating frontmatter: {e}")
            raise e

    def save_story_as_plain_text(self, story: str, file_name: str):
        logger.info(f"Saving story as plain text to {file_name}...")
        
        try:
            dir_path = os.path.dirname(file_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            with open(file_name, "w") as f:
                f.write(story)
        except Exception as e:
            logger.error(f"Error saving story as plain text: {e}")
            raise e

    def create_novel_post(self, file_name: str):
        logger.info(f"Creating novel post to {file_name}...")
        
        try:
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
        except Exception as e:
            logger.error(f"Error creating novel post: {e}")
            raise e

    def process_steps(self, characters: str, output_dir: str, **kwargs):
        logger.info("Processing steps...")
        
        try:
            init_prompt = read_prompt("initial_story.md")
            init_prompt = init_prompt.replace("{characters}", characters)
            if "genre" not in kwargs:
                genre = random.choice(GENRE_LIST)
                kwargs["genre"] = genre
            init_prompt = init_prompt.replace("{genre}", kwargs["genre"])

            self.create_story(init_prompt, count_enhancement=2, **kwargs)
            plain_text_file_name = os.path.join(output_dir, "story.md")
            self.save_story_as_plain_text(self.no_heading_final_story, plain_text_file_name)
            self.create_title_and_synopsis()
            self.create_frontmatter()
            final_file_name = os.path.join(output_dir, "final.md")
            self.create_novel_post(final_file_name)
        except Exception as e:
            logger.error(f"Error processing steps: {e}")
            raise e

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
    parser.add_argument(
        "--genre", "-g", type=str, required=False, help=("Genre of the story.")
    )
    kwargs = {}

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)
        
    if args.genre is not None:
        kwargs["genre"] = args.genre

    story_maker = StoryMaker(args.manuscript, args.env)
    characters = load_markdown_as_prompt(args.input)
    story_maker.process_steps(characters, args.output_dir, **kwargs)


if __name__ == "__main__":
    main()
