# Development Workflow

This project uses a Jira-driven agentic workflow powered by Claude Code and the `superpowers` plugin.

## Overview

You create a Jira card describing a task. You hand it to the agent. The agent brainstorms, gets your approval, then implements using TDD. You review the result and close the card.

The agent never closes cards and never commits code — those are your decisions.

## Before You Start

Make sure the Jira MCP plugin is configured. See `docs/jira-mcp-setup.md`.

## Starting a Task

1. Create a Jira card in the `DNS` project with a description of what you want built. State: **TODO**.
2. Note the card ID (e.g., `DNS-42`).
3. Open Claude Code and run:

```
/jira-workflow DNS-42
```

## What the Agent Does

| Step | What happens |
|------|-------------|
| 1 | Reads the card from Jira |
| 2 | Brainstorms the task with you — asks questions, proposes approaches |
| 3 | Waits for your explicit approval before touching any code |
| 4 | Moves the card to **IN PROGRESS** in Jira |
| 5 | Implements the feature using TDD (tests first, then code) |
| 6 | Reports completion and stops |

## What You Do

| When | Your action |
|------|-------------|
| During brainstorm | Answer questions, approve or request changes. To approve, say one of: "yes", "y", "go", "go ahead", "proceed", "ok", "approve", "approved", "ship it", "lgtm". To request changes, describe them in plain text. To cancel, say "no", "stop", "cancel", or "abort". |
| After implementation | Review the code the agent wrote |
| When satisfied | Move the card to **DONE** in Jira manually |
| If you want to commit | Commit the changes yourself |

## Rules the Agent Follows

- It will **never** move a card to DONE
- It will **never** commit or push code
- It will **never** write code before you approve the plan
- It will **stop and report** any Jira API errors rather than proceeding

## Cancelling or Changing the Plan

At Step 3 (approval gate) you have three options:

- **Approve** — say "yes", "go", "lgtm", etc. The agent proceeds.
- **Request changes** — describe what you want changed. The agent re-enters brainstorming with your feedback and returns to the approval gate.
- **Cancel** — say "no", "stop", "cancel", or "abort". The agent exits, the card stays in TODO.
