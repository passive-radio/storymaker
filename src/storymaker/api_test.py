import openai
from storymaker.utils import load_api_key

load_api_key()
client = openai.OpenAI()

response = client.models.list()


def filter_by_model_name(model_name: str):
    # filter if response model name partially contains model_name
    return [model for model in response.data if model_name in model.id]


print(filter_by_model_name("o1"))
