import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, Optional

try:
    # Use the standard library tomllib on Python 3.11+
    import tomllib
except ImportError:
    # Fallback to the tomli package on older Python versions
    import tomli as tomllib

import httpx
from mcp.server.fastmcp import FastMCP

# The API endpoint for all requests
API_URL = "https://api.myshows.me/v2/rpc/"


# --- Configuration ---


@dataclass
class Settings:
    """Holds the configuration for the MyShows API client."""

    login: str
    password: str


def load_settings(path: Path = Path("settings.toml")) -> Optional[Settings]:
    """Loads API credentials from a TOML file."""
    if not path.is_file():
        print(f"Error: Configuration file not found at '{path}'.")
        print("Please create it based on the README.md instructions.")
        return None
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)

        myshows_config = data.get("myshows", {})
        login = myshows_config.get("login")
        password = myshows_config.get("password")

        if not login or not password or "your_login_here" in login:
            print(f"Error: 'login' and 'password' are not configured in '{path}'.")
            print("Please fill in your credentials.")
            return None

        return Settings(login=login, password=password)
    except Exception as e:
        print(f"Error parsing configuration file '{path}': {e}")
        return None


# --- API Client ---


class MyShowsAPI:
    """
    An asynchronous client for the myshows.me JSON-RPC API.
    Handles authentication by logging in once and then relies on
    session cookies for subsequent requests, managed automatically by httpx.
    """

    def __init__(self, settings: Settings):
        self._login = settings.login
        self._password = settings.password
        self._client = httpx.AsyncClient(base_url=API_URL, timeout=30.0)
        self._login_attempted = False

    async def _ensure_logged_in(self):
        """Ensures the client is logged in before making a request."""
        if not self._login_attempted:
            await self.login()
            self._login_attempted = True

    async def login(self):
        """Performs the login request to authenticate and establish a session."""
        try:
            response = await self._client.post(
                "/",
                json={
                    "jsonrpc": "2.0",
                    "method": "auth.login",
                    "params": {"login": self._login, "password": self._password},
                    "id": 1,
                },
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise ConnectionError(f"Failed to log in: {data['error']['message']}")
        except httpx.RequestError as e:
            raise ConnectionError(f"Network error during login: {e}")

    async def _make_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """A generic method to make authenticated JSON-RPC requests."""
        await self._ensure_logged_in()
        response = await self._client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": 1,
            },
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise RuntimeError(
                f"API Error for method {method}: {data['error']['message']}"
            )
        return data.get("result", {})

    async def get_profile(self) -> Dict[str, Any]:
        """Fetches the user's profile data."""
        return await self._make_request("profile.get")

    async def search_shows(self, query: str) -> Dict[str, Any]:
        """Searches for shows by a query string."""
        return await self._make_request("shows.search", {"query": query})

    async def get_my_shows(self) -> Dict[str, Any]:
        """Fetches all shows in the user's profile with their watch status."""
        return await self._make_request("profile.Shows")

    async def check_episode(self, episode_id: int) -> Dict[str, Any]:
        """Marks an episode as watched by its ID."""
        return await self._make_request("manage.CheckEpisode", {"id": episode_id})

    async def uncheck_episode(self, episode_id: int) -> Dict[str, Any]:
        """Unmarks an episode as watched by its ID."""
        return await self._make_request("manage.UncheckEpisode", {"id": episode_id})


# --- MCP Server Setup ---

mcp = FastMCP("MyShows")
# This global client is initialized in the main() function after loading settings.
api_client: Optional[MyShowsAPI] = None


def tool_handler(
    func: Callable[..., Coroutine[Any, Any, Any]]
) -> Callable[..., Coroutine[Any, Any, Any]]:
    """A decorator to handle boilerplate for all MCP tools."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        if not api_client:
            return {
                "error": "API client is not configured. Please check server logs."
            }
        try:
            # The first argument is the api_client instance.
            return await func(api_client, *args, **kwargs)
        except Exception as e:
            return {"error": str(e)}

    return wrapper


@mcp.tool()
@tool_handler
async def get_profile(client: MyShowsAPI) -> Dict[str, Any]:
    """Retrieves the user's profile information from myshows.me."""
    return await client.get_profile()


@mcp.tool()
@tool_handler
async def search_shows(client: MyShowsAPI, query: str) -> Dict[str, Any]:
    """Searches for TV shows on myshows.me using a search query."""
    return await client.search_shows(query=query)


@mcp.tool()
@tool_handler
async def get_my_shows(client: MyShowsAPI) -> Dict[str, Any]:
    """Retrieves all shows from the user's profile, including their watch status."""
    return await client.get_my_shows()


@mcp.tool()
@tool_handler
async def check_episode(client: MyShowsAPI, episode_id: int) -> Dict[str, Any]:
    """Marks a specific episode as watched by its ID."""
    return await client.check_episode(episode_id=episode_id)


@mcp.tool()
@tool_handler
async def uncheck_episode(client: MyShowsAPI, episode_id: int) -> Dict[str, Any]:
    """Unmarks a specific episode as watched by its ID."""
    return await client.uncheck_episode(episode_id=episode_id)


def main():
    """Server entry point."""
    global api_client
    print("--- MyShows MCP Server ---")

    settings = load_settings()

    if settings:
        print("Configuration loaded successfully.")
        api_client = MyShowsAPI(settings)
        print(
            "Available tools: get_profile, search_shows, get_my_shows, check_episode, uncheck_episode"
        )
        print("Server is ready to accept requests via stdio.")
        mcp.run(transport="stdio")
    else:
        print("Could not start server due to configuration error. Exiting.")


if __name__ == "__main__":
    main()
