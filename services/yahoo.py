import feedparser
import yfinance as yf
import aiohttp
import asyncio
from datetime import datetime, timedelta

async def get_yahoo_news(ticker: str):
    """Get news from Yahoo Finance RSS feed."""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    
    # feedparser doesn't support async, but it's fast enough to run in the main thread
    feed = feedparser.parse(url)

    headlines = []
    for entry in feed.entries:
        headlines.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "source": "Yahoo",
            "summary": entry.get("summary", ""),
            "published_parsed": datetime.fromtimestamp(
                datetime(*entry.published_parsed[:6]).timestamp()
            ).isoformat()
        })

    return headlines

async def get_ticker_info(ticker: str):
    """Get detailed company and stock information using yfinance."""
    try:
        # yfinance operations are blocking, run them in a thread pool
        loop = asyncio.get_event_loop()
        stock = await loop.run_in_executor(None, yf.Ticker, ticker)
        info = await loop.run_in_executor(None, lambda: stock.info)
        
        # Get historical data for price analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        history = await loop.run_in_executor(
            None, 
            lambda: stock.history(start=start_date, end=end_date)
        )
        
        # Calculate price metrics
        if not history.empty:
            current_price = history['Close'].iloc[-1]
            price_change = current_price - history['Close'].iloc[0]
            price_change_pct = (price_change / history['Close'].iloc[0]) * 100
            high_30d = history['High'].max()
            low_30d = history['Low'].min()
            avg_volume = history['Volume'].mean()
        else:
            current_price = price_change = price_change_pct = high_30d = low_30d = avg_volume = None

        return {
            "company_info": {
                "name": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "description": info.get("longBusinessSummary"),
                "website": info.get("website"),
                "country": info.get("country"),
                "employees": info.get("fullTimeEmployees"),
                "ceo": info.get("companyOfficers", [{}])[0].get("name") if info.get("companyOfficers") else None
            },
            "market_data": {
                "current_price": current_price,
                "currency": info.get("currency"),
                "market_cap": info.get("marketCap"),
                "price_change_30d": price_change,
                "price_change_pct_30d": price_change_pct,
                "high_30d": high_30d,
                "low_30d": low_30d,
                "avg_volume_30d": avg_volume,
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow")
            },
            "analyst_data": {
                "target_price": info.get("targetMeanPrice"),
                "recommendation": info.get("recommendationKey"),
                "num_analysts": info.get("numberOfAnalystOpinions"),
                "profit_margins": info.get("profitMargins")
            }
        }
    except Exception as e:
        print(f"Error fetching ticker info: {e}")
        return {
            "company_info": {
                "name": None,
                "sector": None,
                "industry": None,
                "description": None
            },
            "market_data": {},
            "analyst_data": {}
        } 