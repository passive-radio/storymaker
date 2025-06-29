"""Base class for all makers."""

import openai

from storymaker.utils import load_api_key, read_prompt, load_markdown_as_prompt, load_manuscript

BASE_MAX_COMPLETION_TOKENS = 10000

class BaseMaker:
    def __init__(self, manuscript_path: str, env_path: str) -> None:
        self.env_path = env_path
        self.manuscript = load_manuscript(manuscript_path)
        
        if not "api_base_path" in self.manuscript:
            raise ValueError("api_base_path is not set in manuscript.")
        
        self.client = openai.OpenAI(api_key=load_api_key(env_path), base_url=self.manuscript["api_base_path"])
        self.responses = []

    def create_chat_completion(self, prompt: str, system_prompt: str, **kwargs) -> str:
        if prompt in ("", None) and system_prompt in ("", None):
            raise ValueError("prompt or system_prompt is not set.")
        
        if "temperature" not in kwargs:
            kwargs["temperature"] = 0.7
        if "top_p" not in kwargs:
            kwargs["top_p"] = 0.85
        if "max_completion_tokens" not in kwargs:
            kwargs["max_completion_tokens"] = BASE_MAX_COMPLETION_TOKENS
        if "response_format" not in kwargs:
            response_format = openai._types.NOT_GIVEN
            response = self.client.chat.completions.create(
                model=kwargs["model"],
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_completion_tokens=kwargs["max_completion_tokens"],
                top_p=kwargs["top_p"],
                temperature=kwargs["temperature"],
                stream=False,
            )
        else:
            response_format = kwargs["response_format"]
            print(response_format)
            response = self.client.beta.chat.completions.parse(
                model=kwargs["model"],
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_completion_tokens=kwargs["max_completion_tokens"],
                top_p=kwargs["top_p"],
                temperature=kwargs["temperature"],
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