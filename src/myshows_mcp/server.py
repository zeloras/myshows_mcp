import os
import functools
from typing import Any, Callable, Coroutine, Dict, Optional
import httpx
from fastmcp import FastMCP, Client
import asyncio


# The API endpoint for all requests
API_URL = "https://myshows.me/v3/rpc/"
LOGIN_URL = "https://myshows.me/api/session"


# --- API Client ---


class MyShowsAPI:
    """
    An asynchronous client for the myshows.me JSON-RPC API.
    Handles authentication by logging in once and then relies on
    session cookies for subsequent requests, managed automatically by httpx.
    """

    def __init__(self, login: str, password: str):
        self._login = login
        self._password = password
        self._login_attempted = False
        self._bearer_token = None
        self._client = self._init_client()

    def _init_client(self, headers: Optional[Dict[str, str]] = None):
        """Initializes the HTTP client with the base URL and default headers."""
        headers = headers or {}
        headers.update({
            "Content-Type": "application/json",
            "User-Agent": "MyShowsAPI/1.0",
        })

        return httpx.AsyncClient(
            base_url=API_URL,
            timeout=30.0,
            headers=headers,
        )

    async def _ensure_logged_in(self):
        """Ensures the client is logged in before making a request."""
        if not self._login_attempted:
            await self.login()
            self._login_attempted = True
            self._client = self._init_client({
                "authorization2": f"Bearer {self._bearer_token}" if self._bearer_token else "",
            })

    async def login(self):
        """Performs the login request to authenticate and establish a session."""
        try:
            response = await httpx.AsyncClient(timeout=30.0).post(
                LOGIN_URL,  # Используем полный URL
                json={"login": self._login, "password": self._password},
            )
            response.raise_for_status()
            data = response.json()
            self._bearer_token = data.get("token", None)
            if "error" in data:
                raise ConnectionError(f"Failed to log in: {data['error']['message']}")
        except httpx.RequestError as e:
            raise ConnectionError(f"Network error during login: {e}")

    async def _make_request(
            self, method: str, id: int, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """A generic method to make authenticated JSON-RPC requests."""
        await self._ensure_logged_in()

        payload = [{
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": id
        }]

        response = await self._client.post("/", json=payload)
        return {
            "result": response.json()
        }

    async def get_watched_movies(self, page: int = 1) -> Dict[str, Any]:
        """Retrieves a list of watched movies from MyShows."""
        return await self._make_request(
            method="profile.WatchedMovies",
            id=80,
            params={
                "page": page,
                "pageSize": 20,
                "login": "",
                "search": {
                    "sort": "watchedAt_desc"
                }
            }
        )

    async def search_shows(self, query: str, year: int|None = None, page: int = 1) -> Dict[str, Any]:
        """Search for TV shows/movie on MyShows by year and/or query.
        :param query: The search query string.
        :param year: Optional year to filter the search results.
        :param page: The page number to retrieve (default is 1).
        :return: A dictionary containing the search results.
        """
        return await self._make_request(method="shows.GetCatalog", id=63, params={
            "search": {
                "network": None,
                "genre": None,
                "country": None,
                "year": year,
                "startYear": None,
                "endYear": None,
                "watching": None,
                "category": None,
                "status": None,
                "sort": None,
                "query": query,
                "watchStatus": None,
                "embed": None,
                "providers": None,
                "jwProviders": None
            },
            "page": page,
            "pageSize": 30
        })

    async def get_by_id(self, myshows_item_id: int):
        """Retrieves a show by its MyShows ID, including episodes and season counts.
        :param myshows_item_id: The MyShows ID of the show to retrieve.
        :return: A dictionary containing the show's details, including episodes and season counts.
        """
        return self._make_request(method="shows.GetById", id=87, params={
            "showId": myshows_item_id,
            "withEpisodes": True,
            "withSeasonCounts": True
        })

    async def set_movie_watch_status(self, movie_id: int, status: str):
        """Sets the watch status of a movie by its ID.
        :param movie_id: The ID of the movie to set the watch status for.
        :param status: The watch status to set ("watching", "cancelled", "later", "remove").
        :return: A dictionary containing the result of the operation.
        """
        return await self._make_request(
            "manage.SetShowStatus",
            params={"id": movie_id, "status": status},
            id=5
        )

    async def get_viewed_tv_episodes(self, episode_id: int):
        """Get viewed tv show's episodes
        :param episode_id: The ID of the TV show to retrieve episodes for.
        :return: A dictionary containing the episodes of the TV show.
        """
        return await self._make_request(
            "profile.Episodes", params={"showId": episode_id}, id=96
        )

    async def uncheck_episode(self, episode_id: int) -> Dict[str, Any]:
        """Unmarks an episode as watched by its ID.
        :param episode_id: The ID of the episode to uncheck.
        :return: A dictionary containing the result of the uncheck operation.
        """
        return await self._make_request(
            "manage.UncheckEpisode", params={"id": episode_id}, id=111
        )

    async def check_episode(self, episode_id: int) -> Dict[str, Any]:
        """Marks an episode as watched by its ID.
        :param episode_id: The ID of the episode to check.
        :return: A dictionary containing the result of the check operation.
        """
        return await self._make_request(
            "manage.CheckEpisode", params={"id": episode_id}, id=113
        )


# --- MCP Server Setup ---

mcp = FastMCP("MyShows MCP Server")
api_client: MyShowsAPI = MyShowsAPI(login="", password="")

def tool_handler(
    func: Callable[..., Coroutine[Any, Any, Any]]
) -> Callable[..., Coroutine[Any, Any, Any]]:
    """A decorator to handle boilerplate for all MCP tools."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any):
        if not api_client:
            return {
                "error": "API client is not configured. Please check server logs."
            }
        try:
            # The wrapped function will use the global api_client
            return await func(*args, **kwargs)
        except Exception as e:
            return {"error": str(e)}

    return wrapper



@mcp.tool()
@tool_handler
async def search_shows(query: str, year: int|None = None, page: int = 0):
    """Searches for TV shows/movies on MyShows by a query and optional year.
    :param query: The search query string.
    :param year: Optional year to filter the search results.
    :param page: The page number to retrieve (default is 0).
    :return: A dictionary containing the search results.
    """
    return await api_client.search_shows(query=query,year=year, page=page)

@mcp.tool()
@tool_handler
async def watched_movies(page: int = 0):
    """Retrieves a list of watched movies from MyShows.
    :param page: The page number to retrieve (default is 0).
    :return: A dictionary containing the list of watched movies.
    """
    return await api_client.get_watched_movies(page=page)


@mcp.tool()
@tool_handler
async def get_movie_show_by_id(myshows_item_id: int):
    """Retrieves a show or movie by its MyShows ID.
    :param myshows_item_id: The MyShows ID of the show or movie to retrieve.
    :return: A dictionary containing the show's details, including episodes and season counts.
    """
    return await api_client.get_by_id(myshows_item_id=myshows_item_id)


@mcp.tool()
@tool_handler
async def get_viewed_episodes(episode_id: int):
    """Retrieves the viewed episodes of a TV show by its ID.
    :param episode_id: The ID of the TV show to retrieve episodes for.
    :return: A dictionary containing the episodes of the TV show.
    """
    return await api_client.get_viewed_tv_episodes(episode_id=episode_id)

@mcp.tool()
@tool_handler
async def check_episode(episode_id: int):
    """Marks a specific episode as watched by its ID."""
    return await api_client.check_episode(episode_id=episode_id)


@mcp.tool()
@tool_handler
async def uncheck_episode(episode_id: int):
    """Unmarks a specific episode as watched by its ID."""
    return await api_client.uncheck_episode(episode_id=episode_id)


@mcp.tool()
@tool_handler
async def set_movie_watch_status(movie_id: int, status: str):
    """Sets the watch status of a movie by its ID.
    :param movie_id: The ID of the movie to set the watch status for.
    :param status: The watch status to set (
        "watching" - watching the movie,
        "cancelled" - stop watching the movie,
        "later" - the movie to watch later,
        "remove" - have not watched the movie yet
    )
    :return: A dictionary containing the result of the operation.
    """
    return await api_client.set_movie_watch_status(movie_id=movie_id, status=status)


def main():
    """Server entry point."""
    global api_client

    login = os.environ.get("MYSHOWS_LOGIN")
    password = os.environ.get("MYSHOWS_PASSWORD")

    if login and password:
        api_client = MyShowsAPI(login=login, password=password)
        mcp.run()

    else:
        print("Error: MYSHOWS_LOGIN and MYSHOWS_PASSWORD environment variables not set.")
        print("Could not start server due to missing configuration. Exiting.")


if __name__ == "__main__":
    main()

