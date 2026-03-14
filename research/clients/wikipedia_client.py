import aiohttp
import re
from typing import List, Optional
from research.interfaces import SearchClient, SearchResult  # pyre-ignore[21]

class WikipediaClient(SearchClient):
    """Truly Free Wikipedia API client - requires User-Agent."""
    
    API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self):
        self.headers = {
            "User-Agent": "BookFactoryBot/1.0 (https://example.com/bot; bot@example.com)"
        }

    async def search(self, query: str, num_results: int = 3) -> List[SearchResult]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": num_results
        }
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.API_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        search_results = []
                        for item in data.get("query", {}).get("search", []):
                            title = item.get("title", "")
                            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                            snippet = item.get("snippet", "")
                            # Clean up HTML tags in snippet
                            clean_snippet = re.sub('<[^<]+?>', '', snippet)
                            
                            search_results.append(SearchResult(
                                title=title,
                                url=url,
                                snippet=clean_snippet,
                                published_date=None
                            ))
                        return search_results
                    else:
                        print(f"   ⚠️ Wikipedia Search error: {resp.status}")
        except Exception as e:
            print(f"   ⚠️ Wikipedia Search failed: {e}")
        
        return []

    async def fetch_full_text(self, title: str) -> Optional[str]:
        """Fetches full page content from Wikipedia."""
        params = {
            "action": "query",
            "prop": "extracts",
            "exlimit": "1",
            "titles": title,
            "explaintext": "1",
            "format": "json",
            "exintro": "1"
        }
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.API_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pages = data.get("query", {}).get("pages", {})
                        for page_id in pages:
                            return pages[page_id].get("extract")
        except Exception:
            pass
        return None
