import json
from cv.llm.base import CVExtractor
from cv.schema import CVExtractResult
from cv.prompts.helper import PromptHelper
from llama_index.llms.ollama import Ollama

class OllamaExtractor(CVExtractor):
    def __init__(self, model: str = "qwen2.5:14b"):
        self.llm = Ollama(model=model, request_timeout=180.0)

    def extract(self, cv_text: str) -> dict:
        prompt = PromptHelper.get("cv_summary.prompt")

        response = self.llm.complete(f"{prompt}\n\nCV TEXT:\n{cv_text}").text.strip()

        # Ollama can sometimes wrap JSON
        if response.startswith("```"):
            response = response.strip("`")
            response = response.replace("json", "", 1).strip()

        data = json.loads(response)

        # Hard validation (same as OpenAI)
        CVExtractResult(**data)
        return data
