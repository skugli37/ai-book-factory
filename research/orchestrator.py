from datetime import datetime, timezone
from typing import Optional, List
from research.interfaces import ResearchOutput, SearchResult  # pyre-ignore[21]
from research.cache import ResearchCache  # pyre-ignore[21]
from research.clients.duckduckgo import DDGSearchClient  # pyre-ignore[21]
from research.clients.wikipedia_client import WikipediaClient  # pyre-ignore[21]
from research.summariser.groq_summariser import GroqSummariser  # pyre-ignore[21]
from research.scraper import WebScraper  # pyre-ignore[21]

class ResearchOrchestrator:
    """Coordinates search, deep scraping, caching, and summarization."""
    
    def __init__(self, ai_writer):
        # 100% Free components (Truly Free ADR Compliant)
        self.ddg = DDGSearchClient()
        self.wiki = WikipediaClient()
        self.scraper = WebScraper()
        self.summariser = GroqSummariser(ai_writer)
        # Using SQLite instead of Redis for zero-setup & 100% local portability
        self.cache = ResearchCache()

    async def research(self, topic: str, force_refresh: bool = False) -> ResearchOutput:
        cache_key = f"research:{topic.lower().replace(' ', '_')}"
        
        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached:
                results = [SearchResult(**r) for r in cached.get("results", [])]
                return ResearchOutput(
                    query=cached["query"],
                    timestamp=cached["timestamp"],
                    results=results,
                    summary=cached["summary"]
                )

        print(f"   🔍 Deep Researching: {topic}...")
        
        # Step 1: Curated Source Discovery
        curated_urls = await self.scraper.get_curated_urls(topic)
        
        # Step 2: Wikipedia (Factual discovery)
        wiki_results = await self.wiki.search(topic, num_results=2)
        
        # Step 3: Global Discovery (DDG)
        ddg_results = await self.ddg.search(topic, num_results=3)
        
        # Merge discovery results
        discovery_results = wiki_results + ddg_results
        discovery_urls = [r.url for r in discovery_results if r.url]
        
        # Prioritize curated -> discovery
        all_target_urls = list(dict.fromkeys(curated_urls + discovery_urls))
        
        if not all_target_urls:
            summary = f"Information on {topic} based on general knowledge."
            final_results = []
        else:
            print(f"   📄 Scraping {len(all_target_urls)} sources for deep context...")
            # Sequential/Polite scraping
            full_texts = await self.scraper.fetch_multiple(all_target_urls, limit=3)
            
            if full_texts:
                summary = await self.summariser.summarise(full_texts)
            else:
                # Fallback to snippets if scraping failed/blocked
                snippets = [r.snippet for r in discovery_results if r.snippet]
                summary = await self.summariser.summarise(snippets) if snippets else f"Factual research on {topic}."
            
            final_results = discovery_results

        output = ResearchOutput(
            query=topic,
            timestamp=datetime.now(timezone.utc).isoformat(),
            results=final_results,
            summary=summary
        )

        # Cache for 48 hours
        cache_data = {
            "query": output.query,
            "timestamp": output.timestamp,
            "results": [r.__dict__ for r in output.results],
            "summary": output.summary
        }
        await self.cache.set(cache_key, cache_data, ttl=172800)
        
        return output
