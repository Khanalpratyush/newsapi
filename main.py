from fastapi import FastAPI
from routers import news
from typing import Dict, Any

description = """
# Finance News API 📈

A powerful API that aggregates financial news and provides comprehensive market sentiment analysis.

## Features

### 🔍 Comprehensive Data Sources
* Yahoo Finance - Real-time market data and news
* Reuters - Global financial news and analysis
* Bloomberg - Market insights and breaking news
* MarketWatch - Financial news and market commentary
* Seeking Alpha - In-depth analysis and research
* Company information and fundamentals
* Market metrics and analyst recommendations

### 📊 Advanced Analytics
* Sentiment analysis with granular classification
* Subjectivity analysis
* Time-based sentiment trends
* Market sentiment aggregation
* Multi-source news comparison and analysis
* Source-specific sentiment tracking

### 📈 Market Data
* Real-time and historical price data
* Volume analysis
* Key market metrics (P/E ratio, market cap, etc.)
* Analyst recommendations
* Company fundamentals

### ⚡ Performance Features
* Async processing
* Input validation
* Comprehensive error handling
* Flexible filtering options
* Customizable news sources

## Usage Examples

### Basic Stock Information
```python
import requests

# Get basic news and sentiment for Apple stock from all sources
response = requests.get("http://localhost:8000/news/AAPL")
```

### Filtered Results
```python
# Get only positive news from specific sources in the last 24 hours
response = requests.get(
    "http://localhost:8000/news/AAPL",
    params={
        "sentiment_threshold": 0.2,
        "time_range_hours": 24,
        "sources": ["reuters", "bloomberg"]
    }
)
```

### Lightweight Query
```python
# Get only news without company information from Yahoo Finance
response = requests.get(
    "http://localhost:8000/news/AAPL",
    params={
        "include_company_info": false,
        "sources": ["yahoo"]
    }
)
```

### Source Selection
```python
# Get news from specific sources
response = requests.get(
    "http://localhost:8000/news/AAPL",
    params={
        "sources": ["reuters", "seekingalpha", "marketwatch"]
    }
)
```
"""

tags_metadata = [
    {
        "name": "news",
        "description": "Financial news and sentiment analysis endpoints with multiple source support",
        "externalDocs": {
            "description": "News Analytics Specification",
            "url": "https://github.com/yourusername/finance-news-api/blob/main/README.md",
        },
    }
]

app = FastAPI(
    title="Finance News API",
    description=description,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://github.com/pratyushkhanal",
        "email": "pratyushkhanal95@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

# Include routers
app.include_router(
    news.router,
    prefix="/news",
    tags=["news"]
)

@app.get("/", response_model=Dict[str, Any], tags=["root"])
async def root():
    """
    Root endpoint providing API information and available endpoints.
    
    Returns:
        dict: API information including version, documentation URLs, and available endpoints
    """
    return {
        "name": "Finance News API",
        "version": "1.0.0",
        "description": "Financial news aggregation and sentiment analysis API",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        },
        "endpoints": [
            {
                "path": "/news/{ticker}",
                "description": "Get news and analysis for a stock ticker",
                "parameters": {
                    "ticker": "Stock symbol (e.g., AAPL, MSFT)",
                    "include_company_info": "Include detailed company information (default: true)",
                    "sentiment_threshold": "Filter by minimum sentiment score (-1 to 1)",
                    "time_range_hours": "Filter news from last N hours",
                    "sources": "List of news sources to include (yahoo, reuters, bloomberg, marketwatch, seekingalpha)"
                },
                "example": "/news/AAPL?sentiment_threshold=0.2&time_range_hours=24&sources=reuters,bloomberg"
            }
        ]
    } 