import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP

from src.helpers.web_search import fetch_url, web_search
from src.settings.settings import settings

mcp = FastMCP(
    name="movie_search_server"
    # For http servers we must set the host and port
)


@mcp.tool(name="search_movies")
async def search_movies(query: str) -> str:
    """
    Search for movies on IMDB, Rotten Tomatoes and Metacritic.
    This function will search for movies on the specified sources and return the results.

    Args:
        query (str): The search query.

    Returns:
        str: The search results.
    """

    query = (
        f" OR ".join([f"site:{source}" for source in settings.SearchSources]) + query
    )
    results = await web_search(query)
    if not results["organic"]:
        return {"error": "No results found."}

    text = ""
    for result in results["organic"]:
        text += await fetch_url(result["link"])

    return text


if __name__ == "__main__":
    mcp.run(transport="stdio")
