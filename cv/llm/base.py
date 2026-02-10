from abc import ABC, abstractmethod

class CVExtractor(ABC):
    @abstractmethod
    def extract(self, cv_text: str) -> dict:
        pass
