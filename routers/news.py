from fastapi import APIRouter, HTTPException, Query
from services.yahoo import get_yahoo_news, get_ticker_info
from services.news_sources import get_all_news
from services.sentiment import enrich_news_with_sentiment
from typing import Optional, List
import re
from datetime import datetime

router = APIRouter()

def validate_ticker(ticker: str) -> str:
    """Validate and format ticker symbol."""
    # Remove any whitespace and convert to uppercase
    ticker = ticker.strip().upper()
    
    # Check if ticker matches basic stock symbol pattern
    if not re.match(r'^[A-Z]{1,5}$', ticker):
        raise HTTPException(
            status_code=400,
            detail="Invalid ticker symbol. Please use 1-5 letter symbol (e.g., AAPL, MSFT, GOOGL)"
        )
    return ticker

@router.get("/{ticker}")
async def get_unified_news(
    ticker: str,
    include_company_info: bool = Query(True, description="Include detailed company information"),
    sentiment_threshold: Optional[float] = Query(
        None, 
        description="Filter by minimum sentiment score (-1 to 1)",
        ge=-1, 
        le=1
    ),
    time_range_hours: Optional[int] = Query(
        None,
        description="Filter news from last N hours",
        gt=0
    ),
    sources: List[str] = Query(
        ["yahoo", "reuters", "bloomberg", "marketwatch", "seekingalpha"],
        description="List of news sources to include"
    )
):
    """
    Get comprehensive financial news and analysis for a stock ticker.
    
    Parameters:
    - ticker: Stock symbol (e.g., AAPL, MSFT)
    - include_company_info: Whether to include detailed company information
    - sentiment_threshold: Filter news by minimum sentiment score (-1 to 1)
    - time_range_hours: Get news from the last N hours
    - sources: List of news sources to include (default: all sources)
    
    Available sources:
    - yahoo: Yahoo Finance
    - reuters: Reuters News
    - bloomberg: Bloomberg News
    - marketwatch: MarketWatch
    - seekingalpha: Seeking Alpha
    
    Returns:
    - Detailed company and market information
    - News articles from multiple sources
    - Sentiment analysis and trends
    - Market sentiment summary
    """
    try:
        # Validate ticker
        ticker = validate_ticker(ticker)
        
        # Get company information if requested
        company_info = await get_ticker_info(ticker) if include_company_info else None
        
        # Get news from Yahoo Finance
        yahoo_news = await get_yahoo_news(ticker) if "yahoo" in sources else []
        
        # Get news from other sources
        other_news = await get_all_news(ticker)
        
        # Filter other news sources based on user selection
        filtered_news = {
            source: news_list
            for source, news_list in other_news.items()
            if source in sources
        }
        
        # Process all news sources with sentiment analysis
        news_results = {}
        all_articles = []
        
        # Process Yahoo news
        if yahoo_news:
            yahoo_results = await enrich_news_with_sentiment(yahoo_news)
            news_results["yahoo"] = yahoo_results
            all_articles.extend(yahoo_results["articles"])
        
        # Process other sources
        for source, articles in filtered_news.items():
            if articles:
                source_results = await enrich_news_with_sentiment(articles)
                news_results[source] = source_results
                all_articles.extend(source_results["articles"])
        
        # Apply filters if specified
        if sentiment_threshold is not None:
            for source in news_results:
                news_results[source]["articles"] = [
                    article for article in news_results[source]["articles"]
                    if article["sentiment"]["score"] >= sentiment_threshold
                ]
        
        # Calculate overall metrics
        total_articles = sum(len(source["articles"]) for source in news_results.values())
        overall_sentiment = None
        if total_articles > 0:
            sentiment_sum = sum(
                source["summary"]["overall_sentiment"] * len(source["articles"])
                for source in news_results.values()
                if len(source["articles"]) > 0
            )
            overall_sentiment = sentiment_sum / total_articles
        
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "company_info": company_info,
            "market_sentiment": {
                "overall_score": overall_sentiment,
                "total_articles": total_articles,
                "sources": {
                    source: results["summary"]
                    for source, results in news_results.items()
                }
            },
            "news": {
                source: results["articles"]
                for source, results in news_results.items()
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )