# MyShows MCP Server

This project provides a Model Context Protocol (MCP) server for interacting with the `myshows.me` API. It allows you to connect LangChain or LangGraph agents to your MyShows profile to manage and search for TV shows.

## 1. Configuration

Before running the server, you need to provide your `myshows.me` credentials.

1.  Open the `settings.toml` file in the root of the project.
2.  Replace `"your_login_here"` and `"your_password_here"` with your actual login and password.

```toml
# settings.toml
[myshows]
login = "your_actual_login"
password = "your_secret_password"
```

**Note:** The `settings.toml` file is included in `.gitignore` to prevent you from accidentally committing your credentials.

## 2. Installation

Install the project and its dependencies using `pip`. Run this command from the root directory of the project (`myshows_mcp/`):

```bash
pip install .
```

## 3. Running the Server

Once installed, you can run the MCP server using the following command:

```bash
python -m myshows_mcp.server
```

The server will start and listen for requests on `stdio`.

## Available Tools

The server exposes the following tools:

*   `get_profile()`: Retrieves your user profile information.
*   `search_shows(query: str)`: Searches for TV shows by a given query.
*   `get_my_shows()`: Fetches a list of all shows in your profile.
*   `check_episode(episode_id: int)`: Marks an episode as watched.
*   `uncheck_episode(episode_id: int)`: Unmarks an episode as watched.
