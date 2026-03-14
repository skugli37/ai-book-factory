import asyncio
import aiohttp
import json
import os
from urllib.robotparser import RobotFileParser
from typing import List, Optional, Dict
from trafilatura import extract  # pyre-ignore[21]
from newspaper import Article  # pyre-ignore[21]

class WebScraper:
    """Polite and ethical web scraper with robots.txt compliance."""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.user_agent = "BookFactoryBot/1.0 (https://github.com/skugli37/ai-book-factory; bot@example.com)"
        self.headers = {"User-Agent": self.user_agent}
        self.robot_cache: Dict[str, RobotFileParser] = {}
        
        # Load curated sources
        self.sources_file = os.path.join(os.path.dirname(__file__), "sources.json")
        self.curated_sources = self._load_curated_sources()

    def _load_curated_sources(self) -> Dict[str, List[str]]:
        try:
            if os.path.exists(self.sources_file):
                with open(self.sources_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    async def can_fetch(self, url: str) -> bool:
        """Checks robots.txt for the given URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        if base_url not in self.robot_cache:
            rp = RobotFileParser()
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(base_url, timeout=5) as resp:
                        if resp.status == 200:
                            content = await resp.text()
                            rp.parse(content.splitlines())
                        else:
                            # If no robots.txt, assume it's okay but be polite
                            return True
            except Exception:
                return True
            self.robot_cache[base_url] = rp
            
        return self.robot_cache[base_url].can_fetch(self.user_agent, url)

    async def fetch_article(self, url: str) -> Optional[str]:
        """Fetches and extracts clean text from a URL if allowed."""
        if not await self.can_fetch(url):
            print(f"   🚫 Scraping forbidden by robots.txt: {url}")
            return None
            
        await asyncio.sleep(self.delay)  # Polite delay
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status != 200:
                        return None
                    html = await resp.text()
                    
                    # Try trafilatura first
                    text = extract(html, include_comments=False)
                    if text and len(text) > 400:
                        return str(text)
                    
                    # Fallback to newspaper4k
                    loop = asyncio.get_event_loop()
                    text = await loop.run_in_executor(None, self._newspaper_parse, html, url)
                    if text and len(text) > 400:
                        return str(text)
                    
                    return None
        except Exception:
            return None

    def _newspaper_parse(self, html: str, url: str) -> Optional[str]:
        try:
            article = Article(url)
            article.set_html(html)
            article.parse()
            return article.text
        except Exception:
            return None

    async def get_curated_urls(self, topic: str) -> List[str]:
        """Finds curated URLs based on keywords in the topic."""
        topic_lower = topic.lower()
        matched_urls = []
        for key, urls in self.curated_sources.items():
            if key in topic_lower:
                matched_urls.extend(urls)
        return list(set(matched_urls))

    async def fetch_multiple(self, urls: List[str], limit: int = 3) -> List[str]:
        """Fetches multiple articles in sequence."""
        results = []
        for url in urls[:limit]:
            text = await self.fetch_article(url)
            if text:
                results.append(text)
        return results
