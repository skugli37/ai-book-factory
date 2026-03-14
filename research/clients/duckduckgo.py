import asyncio
from typing import List
from duckduckgo_search import DDGS  # pyre-ignore[21]
from research.interfaces import SearchClient, SearchResult  # pyre-ignore[21]

class DDGSearchClient(SearchClient):
    """DuckDuckGo Search client - 100% Free, no API key required."""
    
    def __init__(self):
        # DDG is anonymous, but we still pace it slightly to avoid blocks
        self.semaphore = asyncio.Semaphore(1)

    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        search_results: List[SearchResult] = []
        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                results = []
                for _ in range(2):
                    # Using current DDGS naming and handling executor 
                    def perform_search(*args, **kwargs):
                        with DDGS(timeout=10) as ddgs:
                            return list(ddgs.text(query, max_results=num_results))

                    try:
                        results = await asyncio.wait_for(
                            loop.run_in_executor(None, perform_search),
                            timeout=15.0
                        ) # pyre-ignore[6]
                    except asyncio.TimeoutError:
                        print("   ⚠️ DuckDuckGo Search timed out")
                        break
                    if results:
                        break
                    await asyncio.sleep(2)
                
                for item in results:
                    search_results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("href", ""),
                        snippet=item.get("body", ""),
                        published_date=None
                    ))
            except Exception as e:
                print(f"   ⚠️ DuckDuckGo Search failed: {e}")
                
        return search_results
