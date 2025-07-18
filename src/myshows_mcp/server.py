import os
import functools
from typing import Any, Callable, Coroutine
from fastmcp import FastMCP
from myshows_mcp.api.myshows_api import MyShowsAPI
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
async def get_viewed_episodes(myshows_item_id: int):
    """Retrieves the viewed episodes of a TV show by its ID.
    :param myshows_item_id: The ID of the TV show to retrieve episodes for.
    :return: A dictionary containing the episodes of the TV show.
    """
    return await api_client.get_viewed_tv_episodes(myshows_item_id=myshows_item_id)

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

@mcp.tool()
@tool_handler
async def get_calendar_episodes():
    """Retrieves the calendar episodes from MyShows with information about the next episodes.
    This method fetches the next episodes scheduled to air, including their details.
    :return: A dictionary containing the calendar episodes.
    """
    return await api_client.get_calendar_episodes()


@mcp.tool()
@tool_handler
async def get_myshows_recomendations(self):
    """Retrieves recommendations from MyShows.
    :return: A dictionary containing the recommendations.
    """
    return await api_client.get_myshows_recomendations()

@mcp.tool()
@tool_handler
async def get_myshows_profile_shows_list():
    """Retrieves the list of tv shows from the MyShows profile.
    :return: A dictionary containing the list of tv shows.
    """
    return await api_client.get_myshows_profile_shows_list()

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
