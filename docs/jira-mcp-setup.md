# Jira MCP Plugin Setup

This guide explains how to connect Claude Code to your Jira instance using the MCP plugin.

## Prerequisites

- A Jira Cloud account (free tier works)
- A Jira project with three board states: TODO, IN PROGRESS, DONE
- Claude Code installed

## Step 1: Get your Atlassian API token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Name it (e.g., `claude-code`) and copy the token — you will not see it again

## Step 2: Find your Jira base URL and email

- Base URL: `https://<your-org>.atlassian.net`
- Email: the email address you use to log in to Jira

## Step 3: Configure the MCP plugin in Claude Code

Add the following to your Claude Code MCP config file.

**Location (Windows):** `%APPDATA%\Claude\claude_desktop_config.json`
**Location (macOS/Linux):** `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://YOUR-ORG.atlassian.net",
        "JIRA_USERNAME": "YOUR_EMAIL@example.com",
        "JIRA_API_TOKEN": "YOUR_API_TOKEN"
      }
    }
  }
}
```

Replace `YOUR-ORG`, `YOUR_EMAIL@example.com`, and `YOUR_API_TOKEN` with your actual values.

## Step 4: Verify the connection

Restart Claude Code. In a new session, ask:

> "List open issues in project DNS"

If Jira responds with your cards, the plugin is working.

## Troubleshooting

- **401 Unauthorized** — check your email and API token
- **404 Not Found** — check your Jira URL (no trailing slash)
- **`uvx` not found** — install `uv` first: `pip install uv` (or `winget install astral-sh.uv` on Windows)
- **Package not found / install error** — verify the package name at https://pypi.org/project/mcp-atlassian or consult the Claude Code MCP documentation
