from langchain_openai import ChatOpenAI
from typing import Optional, Any
import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are Praxa, an expert theater assistant.
Answer clearly and cite sources when available.
"""


class ChatModel(ChatOpenAI):

    def __init__(
        self,
        model_name: str,
        openai_api_key: Optional[str] = None,
        openai_api_base: str = "https://openrouter.ai/api/v1",
        **kwargs: Any,
    ):
        openai_api_key = openai_api_key or os.getenv("OPENROUTER_API_KEY")

        if not openai_api_key:
            raise ValueError("OPENROUTER_API_KEY is missing")

        super().__init__(
            model=model_name,
            openai_api_key=openai_api_key,
            openai_api_base=openai_api_base,
            temperature=0,
            max_tokens=512,
            **kwargs,
        )


def get_model(model_name="meta-llama/llama-3.1-8b-instruct"):

    use_system_prompt = True

    if "gemma" in model_name.lower():
        use_system_prompt = False

    model = ChatModel(model_name=model_name)

    return model, use_system_prompt