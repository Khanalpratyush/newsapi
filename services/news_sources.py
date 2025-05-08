import aiohttp
from bs4 import BeautifulSoup
import asyncio
import feedparser
from datetime import datetime
from typing import List, Dict, Any
from aiohttp import ClientTimeout
import ssl
import certifi
import logging
from playwright.async_api import async_playwright
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common configuration
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
RETRY_DELAY = 1
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

class NewsSourceError(Exception):
    """Custom exception for news source errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


async def create_aiohttp_session():
    """Create an aiohttp session with proper SSL context and timeout."""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    timeout = ClientTimeout(total=TIMEOUT_SECONDS)
    return aiohttp.ClientSession(
        timeout=timeout,
        connector=aiohttp.TCPConnector(ssl=ssl_context)
    )

async def fetch_with_retry(session: aiohttp.ClientSession, url: str, headers: dict) -> str:
    """Fetch URL content with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', RETRY_DELAY))
                    await asyncio.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                return await response.text()
                
        except aiohttp.ClientError as e:
            if attempt == MAX_RETRIES - 1:
                raise NewsSourceError(f"Failed to fetch {url}: {str(e)}")
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    
    raise NewsSourceError(f"Max retries exceeded for {url}")

async def get_news_from_google_rss(session: aiohttp.ClientSession, ticker: str, source_domain: str, source_name: str) -> List[Dict[str, Any]]:
    """Get news from Google News RSS feed with site-specific search.
    
    Args:
        session: aiohttp client session
        ticker: Stock ticker symbol
        source_domain: Domain name of the news source (e.g., reuters.com)
        source_name: Display name of the source (e.g., Reuters)
    """
    url = f"https://news.google.com/rss/search?q={ticker.upper()}+site:{source_domain}"
    headers = {"User-Agent": USER_AGENTS[0]}
    
    try:
        content = await fetch_with_retry(session, url, headers)
        # Parse RSS feed in thread pool
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, content)
        
        articles = []
        for entry in feed.entries[:20]:
            published_parsed = None
            if hasattr(entry, 'published_parsed'):
                try:
                    published_parsed = datetime.fromtimestamp(
                        datetime(*entry.published_parsed[:6]).timestamp()
                    ).isoformat()
                except (ValueError, TypeError):
                    pass
                    
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published if hasattr(entry, 'published') else None,
                "source": source_name,
                "summary": entry.get("description", ""),
                "published_parsed": published_parsed
            })
            
        return articles
    except Exception as e:
        logger.error(f"Error fetching {source_name} news: {e}")
        return []

async def get_all_news(
    ticker: str, 
    sources: List[str] = None,
    custom_sources: Dict[str, Dict[str, str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Get news from all specified sources concurrently using a shared session.
    
    Args:
        ticker: Stock ticker symbol
        sources: List of news source names to fetch from. If None, fetches from all available sources.
        custom_sources: Dictionary of custom sources in the format:
            {
                "source_name": {
                    "domain": "example.com",
                    "display_name": "Example News"
                }
            }
    """
    # Define default available sources and their domains
    DEFAULT_SOURCES = {
        "reuters": {"domain": "reuters.com", "display_name": "Reuters"},
        "marketwatch": {"domain": "marketwatch.com", "display_name": "MarketWatch"},
        "bloomberg": {"domain": "bloomberg.com", "display_name": "Bloomberg"},
        "seekingalpha": {"domain": "seekingalpha.com", "display_name": "Seeking Alpha"}
    }
    
    # Merge default and custom sources
    SOURCE_CONFIG = DEFAULT_SOURCES.copy()
    if custom_sources:
        # Validate custom sources format
        for source_name, config in custom_sources.items():
            if not isinstance(config, dict) or 'domain' not in config or 'display_name' not in config:
                logger.warning(f"Invalid custom source configuration for {source_name}. Skipping.")
                continue
            SOURCE_CONFIG[source_name] = config
    
    # If no sources specified, use all available sources including custom ones
    if sources is None:
        sources = list(SOURCE_CONFIG.keys())
    
    # Filter out any invalid sources
    valid_sources = [s for s in sources if s in SOURCE_CONFIG]
    
    if not valid_sources:
        logger.warning("No valid sources found. Please check your source configuration.")
        return {}
    
    async with await create_aiohttp_session() as session:
        tasks = [
            get_news_from_google_rss(
                session, 
                ticker, 
                SOURCE_CONFIG[source]["domain"],
                SOURCE_CONFIG[source]["display_name"]
            )
            for source in valid_sources
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            source: result if not isinstance(result, Exception) else []
            for source, result in zip(valid_sources, results)
        }