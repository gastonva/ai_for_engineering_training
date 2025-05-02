import json

import httpx
from bs4 import BeautifulSoup

from src.settings.settings import settings


# Setup the Serper search engine
async def web_search(query: str) -> dict:
    """
    Perform a web search using the Serper API.

    Args:
        query (str): The search query.

    Returns:
        dict: The search results.
    """
    payload = json.dumps(
        {
            "q": query,
            "num": 3,  # Top 3 results
        }
    )

    headers = {"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"}

    with httpx.AsyncClient() as client:
        response = await client.post(settings.SerperURL, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"organic": []}


async def fetch_url(url: str, timeout: int = 30) -> str:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=timeout)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            return text
        except httpx.TimeoutException as e:
            raise Exception(f"Timeout while fetching {url}: {e}")
