# Finance News API 📈

A powerful FastAPI-based service that aggregates financial news and provides comprehensive market sentiment analysis.

## Features

### 🔍 Data Sources
- **Yahoo Finance**
  - Real-time stock data
  - Company fundamentals
  - Market metrics
  - Financial news
- **Google News**
  - Latest news articles
  - Broader market coverage
  - Multiple perspectives

### 📊 Analytics
- **Sentiment Analysis**
  - Granular classification (very positive to very negative)
  - Subjectivity scoring
  - Time-based trends
  - Source-specific metrics
- **Market Metrics**
  - Price analysis
  - Volume trends
  - Technical indicators
  - Analyst recommendations

### 🚀 Technical Features
- Async processing for improved performance
- Input validation and error handling
- Flexible filtering options
- Comprehensive documentation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/finance-news-api.git
cd finance-news-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the API:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Spec: `http://localhost:8000/openapi.json`

### Endpoints

#### GET /news/{ticker}
Get comprehensive news and analysis for a stock ticker.

**Parameters:**
- `ticker` (path): Stock symbol (e.g., AAPL, MSFT)
- `include_company_info` (query, optional): Include detailed company information (default: true)
- `sentiment_threshold` (query, optional): Filter by minimum sentiment score (-1 to 1)
- `time_range_hours` (query, optional): Filter news from last N hours

**Example Response:**
```json
{
  "ticker": "AAPL",
  "timestamp": "2024-02-20T10:30:00Z",
  "company_info": {
    "company_info": {
      "name": "Apple Inc.",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "description": "...",
      "website": "https://www.apple.com",
      "country": "United States",
      "employees": 164000,
      "ceo": "Tim Cook"
    },
    "market_data": {
      "current_price": 182.31,
      "currency": "USD",
      "market_cap": 2800000000000,
      "price_change_30d": 5.42,
      "price_change_pct_30d": 3.06,
      "pe_ratio": 28.5,
      "dividend_yield": 0.5
    },
    "analyst_data": {
      "target_price": 198.50,
      "recommendation": "buy",
      "num_analysts": 42
    }
  },
  "market_sentiment": {
    "overall_score": 0.35,
    "total_articles": 25,
    "sources": {
      "yahoo": {
        "overall_sentiment": 0.42,
        "sentiment_distribution": {
          "very_positive": 3,
          "positive": 8,
          "neutral": 4,
          "negative": 2,
          "very_negative": 0
        }
      }
    }
  },
  "news": {
    "yahoo": [...],
    "google": [...]
  }
}
```

## Usage Examples

### Python
```python
import requests

# Basic query
response = requests.get("http://localhost:8000/news/AAPL")

# Filtered query
response = requests.get(
    "http://localhost:8000/news/AAPL",
    params={
        "sentiment_threshold": 0.2,
        "time_range_hours": 24,
        "include_company_info": True
    }
)

data = response.json()
```

### cURL
```bash
# Basic query
curl http://localhost:8000/news/AAPL

# Filtered query
curl "http://localhost:8000/news/AAPL?sentiment_threshold=0.2&time_range_hours=24"
```

## Error Handling

The API uses standard HTTP status codes:
- `200`: Successful request
- `400`: Invalid input (e.g., invalid ticker symbol)
- `404`: Resource not found
- `500`: Server error

Error responses include detailed messages:
```json
{
  "detail": "Invalid ticker symbol. Please use 1-5 letter symbol (e.g., AAPL, MSFT, GOOGL)"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details. 