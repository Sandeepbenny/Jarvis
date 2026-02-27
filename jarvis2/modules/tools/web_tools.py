# modules/tools/web_tools.py
"""
Web-based tools: search, fetch pages, weather, news.
"""

import os
import requests
from langchain_core.tools import tool
from bs4 import BeautifulSoup
from typing import Optional


@tool
def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo (no API key required).
    
    Args:
        query: Search query string
        num_results: Number of results to return (default 5, max 10)
    
    Returns:
        Formatted search results with titles, URLs, and snippets.
    """
    try:
        from duckduckgo_search import DDGS
        
        num_results = min(num_results, 10)
        results = []
        
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                results.append(r)
        
        if not results:
            return f"No results found for: {query}"
        
        lines = [f"🔍 Search results for: '{query}'\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r['title']}**")
            lines.append(f"   {r['href']}")
            lines.append(f"   {r['body'][:200]}...")
            lines.append("")
        
        return "\n".join(lines)
    except ImportError:
        return "❌ Install duckduckgo_search: pip install duckduckgo-search"
    except Exception as e:
        return f"❌ Search failed: {str(e)}"


@tool
def fetch_webpage(url: str, extract_text: bool = True) -> str:
    """
    Fetch and read the content of a webpage.
    
    Args:
        url: Full URL of the webpage to fetch
        extract_text: If True, extract clean text; if False, return raw HTML
    
    Returns:
        Page content as text.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        if not extract_text:
            return response.text[:5000]
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts, styles, nav elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean up excessive newlines
        lines = [line for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)
        
        max_chars = 4000
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + f"\n\n... [truncated, {len(clean_text)} total chars]"
        
        return f"🌐 [{url}]\n\n{clean_text}"
    except requests.Timeout:
        return f"❌ Request timed out: {url}"
    except requests.HTTPError as e:
        return f"❌ HTTP error {e.response.status_code}: {url}"
    except Exception as e:
        return f"❌ Failed to fetch page: {str(e)}"


@tool
def get_weather(city: str, units: str = "metric") -> str:
    """
    Get current weather for a city using Open-Meteo (free, no API key).
    
    Args:
        city: City name (e.g., 'London', 'New York', 'Tokyo')
        units: Temperature units - 'metric' (Celsius) or 'imperial' (Fahrenheit)
    
    Returns:
        Current weather conditions.
    """
    try:
        # Step 1: Geocode the city using Open-Meteo's geocoding API
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": city, "count": 1}, timeout=10)
        geo_data = geo_resp.json()
        
        if not geo_data.get("results"):
            return f"❌ City not found: {city}"
        
        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        display_name = loc.get("name", city)
        country = loc.get("country", "")
        
        # Step 2: Get weather
        temp_unit = "celsius" if units == "metric" else "fahrenheit"
        wind_unit = "kmh" if units == "metric" else "mph"
        
        weather_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "wind_speed_10m", "weather_code", "precipitation"
            ],
            "temperature_unit": temp_unit,
            "wind_speed_unit": wind_unit,
            "timezone": "auto"
        }
        
        w_resp = requests.get(weather_url, params=params, timeout=10)
        w_data = w_resp.json()
        curr = w_data["current"]
        
        # WMO weather code descriptions
        wmo_codes = {
            0: "Clear sky ☀️", 1: "Mainly clear 🌤", 2: "Partly cloudy ⛅",
            3: "Overcast ☁️", 45: "Foggy 🌫", 51: "Light drizzle 🌧",
            61: "Light rain 🌧", 63: "Moderate rain 🌧", 65: "Heavy rain 🌧",
            71: "Light snow ❄️", 73: "Moderate snow ❄️", 80: "Rain showers 🌦",
            95: "Thunderstorm ⛈", 99: "Thunderstorm with hail ⛈"
        }
        
        code = curr.get("weather_code", 0)
        description = wmo_codes.get(code, f"Weather code {code}")
        temp_symbol = "°C" if units == "metric" else "°F"
        speed_unit = "km/h" if units == "metric" else "mph"
        
        lines = [
            f"🌍 Weather in {display_name}, {country}",
            f"{'─' * 35}",
            f"🌡  Temperature:  {curr['temperature_2m']}{temp_symbol} (feels like {curr['apparent_temperature']}{temp_symbol})",
            f"💧 Humidity:     {curr['relative_humidity_2m']}%",
            f"💨 Wind:         {curr['wind_speed_10m']} {speed_unit}",
            f"🌧 Precipitation: {curr.get('precipitation', 0)} mm",
            f"☁️  Condition:    {description}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Weather fetch failed: {str(e)}"


@tool
def get_news(topic: str = "technology", num_articles: int = 5) -> str:
    """
    Get latest news headlines using DuckDuckGo News search.
    
    Args:
        topic: News topic (e.g., 'AI', 'technology', 'sports', 'world')
        num_articles: Number of articles to return (default 5)
    
    Returns:
        Formatted news headlines with links.
    """
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(topic, max_results=num_articles):
                results.append(r)
        
        if not results:
            return f"No news found for: {topic}"
        
        lines = [f"📰 Latest news: '{topic}'\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r['title']}**")
            lines.append(f"   Source: {r.get('source', 'Unknown')} | {r.get('date', '')}")
            lines.append(f"   {r.get('body', '')[:150]}...")
            lines.append(f"   🔗 {r['url']}")
            lines.append("")
        
        return "\n".join(lines)
    except ImportError:
        return "❌ Install: pip install duckduckgo-search"
    except Exception as e:
        return f"❌ News fetch failed: {str(e)}"
