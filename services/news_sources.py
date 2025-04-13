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
    pass

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

async def get_reuters_news(session: aiohttp.ClientSession, ticker: str) -> List[Dict[str, Any]]:
    """Get news from Reuters."""
    url = f"https://www.reuters.com/search/news?blob={ticker}&sortBy=date"
    headers = {"User-Agent": USER_AGENTS[0]}
    
    try:
        content = await fetch_with_retry(session, url, headers)
        soup = BeautifulSoup(content, "html.parser")
        articles = []
        
        for article in soup.select(".search-result-content")[:10]:
            title_elem = article.select_one("h3.search-result-title a")
            time_elem = article.select_one("h5.search-result-timestamp")
            
            if title_elem:
                articles.append({
                    "title": title_elem.text.strip(),
                    "link": f"https://www.reuters.com{title_elem['href']}",
                    "published": time_elem.text.strip() if time_elem else None,
                    "source": "Reuters"
                })
                
        return articles
    except Exception as e:
        logger.error(f"Error fetching Reuters news: {e}")
        return []

async def get_marketwatch_news(session: aiohttp.ClientSession, ticker: str) -> List[Dict[str, Any]]:
    """Get news from MarketWatch."""
    url = f"https://www.marketwatch.com/investing/stock/{ticker.lower()}"
    headers = {"User-Agent": USER_AGENTS[1]}
    
    try:
        content = await fetch_with_retry(session, url, headers)
        soup = BeautifulSoup(content, "html.parser")
        articles = []
        
        for article in soup.select(".article__content")[:10]:
            title_elem = article.select_one("a.link")
            time_elem = article.select_one(".article__timestamp")
            
            if title_elem:
                articles.append({
                    "title": title_elem.text.strip(),
                    "link": title_elem["href"],
                    "published": time_elem.text.strip() if time_elem else None,
                    "source": "MarketWatch"
                })
                
        return articles
    except Exception as e:
        logger.error(f"Error fetching MarketWatch news: {e}")
        return []

async def get_seekingalpha_news(session: aiohttp.ClientSession, ticker: str) -> List[Dict[str, Any]]:
    """Get news from Seeking Alpha RSS feed."""
    url = f"https://seekingalpha.com/api/sa/combined/{ticker}.xml"
    headers = {"User-Agent": USER_AGENTS[2]}
    
    try:
        content = await fetch_with_retry(session, url, headers)
        # Parse RSS feed in thread pool
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, content)
        
        articles = []
        for entry in feed.entries[:10]:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published if hasattr(entry, 'published') else None,
                "source": "Seeking Alpha",
                "summary": entry.get("summary", "")
            })
            
        return articles
    except Exception as e:
        logger.error(f"Error fetching Seeking Alpha news: {e}")
        return []

async def get_bloomberg_news(session: aiohttp.ClientSession, ticker: str) -> List[Dict[str, Any]]:
    """Get news from Bloomberg (public content)."""
    url = f"https://www.bloomberg.com/search?query={ticker}"
    headers = {"User-Agent": USER_AGENTS[0]}
    
    try:
        content = await fetch_with_retry(session, url, headers)
        soup = BeautifulSoup(content, "html.parser")
        articles = []
        
        for article in soup.select(".search-result-story")[:10]:
            title_elem = article.select_one("h3.headline")
            time_elem = article.select_one(".published-at")
            
            if title_elem:
                articles.append({
                    "title": title_elem.text.strip(),
                    "link": f"https://www.bloomberg.com{article.select_one('a')['href']}",
                    "published": time_elem.text.strip() if time_elem else None,
                    "source": "Bloomberg"
                })
                
        return articles
    except Exception as e:
        logger.error(f"Error fetching Bloomberg news: {e}")
        return []

async def get_all_news(ticker: str) -> Dict[str, List[Dict[str, Any]]]:
    """Get news from all sources concurrently using a shared session."""
    async with await create_aiohttp_session() as session:
        tasks = [
            get_reuters_news(session, ticker),
            get_marketwatch_news(session, ticker),
            get_seekingalpha_news(session, ticker),
            get_bloomberg_news(session, ticker)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "reuters": results[0] if not isinstance(results[0], Exception) else [],
            "marketwatch": results[1] if not isinstance(results[1], Exception) else [],
            "seekingalpha": results[2] if not isinstance(results[2], Exception) else [],
            "bloomberg": results[3] if not isinstance(results[3], Exception) else []
        }