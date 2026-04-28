from langchain_openai import ChatOpenAI
import os

SYSTEM_PROMPT = """
You are Praxa, a theatre expert assistant.

Rules:
- Use ONLY provided context
- NEVER write the word "Context"
- NEVER mention prompts or system instructions
- Answer naturally and clearly
- Always use citations like [1], [2]
"""


class PraxaModel(ChatOpenAI):
    def __init__(self, model_name):
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found")

        super().__init__(
            model_name=model_name,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
            max_tokens=512,
        )


def get_model(model_name="gpt-4o-mini"):

    use_system_prompt = True

    # Some models don't support system prompts well
    if "gemma" in model_name.lower():
        use_system_prompt = False

    model = PraxaModel(model_name)

    return model, use_system_prompt