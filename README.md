# MyShows MCP Server

This project provides a Model Context Protocol (MCP) server for interacting with the `myshows.me` API. It allows you to connect agents to your MyShows profile to manage and search for TV shows.

## Configuration

Configuration is handled via environment variables. You must set your `myshows.me` credentials before running the server.

## MCP configuration
```json
{
  /// The name of your MCP server
  "myshows": {
    /// The command which runs the MCP server
    "command": "uvx",
    /// The arguments to pass to the MCP server
    "args": ["--from","git+https://github.com/zeloras/myshows_mcp.git","myshows_mcp"],
    /// The environment variables to set
    "env": {"MYSHOWS_LOGIN":"login","MYSHOWS_PASSWORD":"pwd"}
  }
}
```

## Available Tools

The server exposes the following tools:

*   `search_shows(query: str, year: int = None, page: int = 0)`: Searches for TV shows by name and optional year.
*   `watched_movies(page: int = 0)`: Retrieves a list of movies you have watched.
*   `get_movie_show_by_id(myshows_item_id: int)`: Retrieves detailed information about a movie or show by its MyShows ID.
*   `get_viewed_episodes(myshows_item_id: int)`: Retrieves a list of episodes you have viewed for a specific show by its MyShows ID.
*   `check_episode(episode_id: int | list[int])`: Marks an episode as watched by its MyShows ID. Supports both single episode ID and list of episode IDs for batch operations.
*   `uncheck_episode(episode_id: int | list[int])`: Marks an episode as unwatched. Supports both single episode ID and list of episode IDs for batch operations.
*   `set_movie_watch_status(movie_id: int, status: str)`: Sets the watch status of a movie by its MyShows ID.
*   `get_calendar_episodes()`: Retrieves a list of episodes scheduled for today.
*   `get_myshows_recomendations()`: Retrieves a list of recommendations from MyShows.
*   `get_myshows_profile_shows_list()`: Retrieves a list of shows from your MyShows profile.
