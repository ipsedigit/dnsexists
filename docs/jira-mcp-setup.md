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

Run this command (replace the placeholder values with your actual values):

```bash
claude mcp add --transport stdio --scope user \
  --env JIRA_URL=https://YOUR-ORG.atlassian.net \
  --env JIRA_USERNAME=YOUR_EMAIL@example.com \
  --env JIRA_API_TOKEN=YOUR_API_TOKEN \
  atlassian -- cmd /c uvx mcp-atlassian
```

> **Windows note:** The `cmd /c` wrapper is required on Windows. Without it you will get "Connection closed" errors.

To verify it was added:

```bash
claude mcp list
```

## Step 4: Verify the connection

Restart Claude Code. In a new session, ask:

> "List open issues in project DNS"

If Jira responds with your cards, the plugin is working.

## Troubleshooting

- **401 Unauthorized** — check your email and API token
- **404 Not Found** — check your Jira URL (no trailing slash, e.g. `https://your-org.atlassian.net`)
- **Connection closed** — make sure you used `cmd /c uvx` (not just `uvx`) on Windows
- **`uvx` not found** — install `uv` first: `pip install uv` (or `winget install astral-sh.uv` on Windows)
- **Package not found / install error** — verify the package name at https://pypi.org/project/mcp-atlassian or consult the Claude Code MCP documentation
