# MyShows MCP Server

This project provides a Model Context Protocol (MCP) server for interacting with the `myshows.me` API. It allows you to connect LangChain or LangGraph agents to your MyShows profile to manage and search for TV shows.

## 1. Configuration

Configuration is handled via environment variables. You must set your `myshows.me` credentials before running the server.

This is a secure method that avoids storing your password in a file.

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

**On Linux or macOS:**
```bash
export MYSHOWS_LOGIN="your_actual_login"
export MYSHOWS_PASSWORD="your_secret_password"
```

**On Windows (Command Prompt):**
```cmd
set MYSHOWS_LOGIN="your_actual_login"
set MYSHOWS_PASSWORD="your_secret_password"
```

You need to set these variables in the same terminal session where you will run the server.

## 2. Installation

Install the project and its dependencies using `pip`. Run this command from the root directory of the project (`myshows_mcp/`):

```bash
pip install .
```

## 3. Running the Server

Once you have set the environment variables and installed the package, you can run the MCP server using the following command:

```bash
python -m myshows_mcp.server
```

The server will start and listen for requests on `stdio`.

## Available Tools

The server exposes the following tools:

*   `get_profile()`: Retrieves your user profile information.
*   `search_shows(query: str, year: int = None, page: int = 0)`: Searches for TV shows by name and optional year.
*   `get_my_shows()`: Fetches a list of all shows in your profile.
*   `check_episode(episode_id: int)`: Marks an episode as watched.
*   `uncheck_episode(episode_id: int)`: Unmarks an episode as watched.
*   `set_movie_watch_status(movie_id: int, status: str)`: Sets the watch status of a movie.
