from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None

@dataclass
class ResearchOutput:
    query: str
    timestamp: str
    results: List[SearchResult]
    summary: str

class SearchClient(ABC):
    @abstractmethod
    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        ...

class Summariser(ABC):
    @abstractmethod
    async def summarise(self, texts: List[str], max_length: int = 300) -> str:
        ...
