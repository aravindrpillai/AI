from cv.llm.openai_extractor import OpenAIExtractor
from cv.llm.ollama_extractor import OllamaExtractor


def get_extractor(llm):
    match(llm):
        case "ollama":
            return OllamaExtractor(model = "qwen2.5:14b")
        case "openai": 
            return OpenAIExtractor()
        case _:
            raise Exception("Invalid model use either [ollama or openai]")
