# Jira Workflow Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `jira-workflow` skill and supporting documentation that enables the Jira-driven agentic development workflow.

**Architecture:** Three files are created: the skill (`.claude/skills/jira-workflow.md`) encodes the strict protocol; two docs (`docs/workflow.md`, `docs/jira-mcp-setup.md`) serve as human references. No Python code is written in this plan — this plan only sets up the agentic workflow infrastructure.

**Tech Stack:** Claude Code skills (Markdown), Jira MCP plugin (Atlassian API)

**Hard project constraints (apply to ALL tasks):**
- NEVER run `git commit` or `git push`
- NEVER move a Jira card to DONE

---

## Chunk 1: Skill and Setup Doc

### Task 1: Write the `jira-workflow` skill

**Files:**
- Create: `.claude/skills/jira-workflow.md`

- [ ] **Step 1: Create `.claude/skills/` directory (if not present) and write the skill file**

The skill file must contain exactly this content:

```markdown
---
name: jira-workflow
description: Jira-driven agentic development workflow. Reads a Jira card, brainstorms with the user, moves the card IN PROGRESS on approval, then develops with TDD. NEVER moves card to DONE. NEVER commits or pushes.
---

# Jira Workflow Skill

Invoked as: `/jira-workflow <CARD-ID>`

## Protocol (strict, follow in order)

### Step 1 — Read card
Call `get_issue(<CARD-ID>)` and extract the summary and description.

If the call fails for any reason: stop immediately, report the exact error to the user, do not proceed.

### Step 2 — Brainstorm
Invoke `superpowers:brainstorming` with the card summary and description as context.

Do NOT write any code during this step.

### Step 3 — Await approval
Present a brief summary of the brainstorm outcome. Ask the user:

> "Shall I proceed with implementation?"

**Accepted approval signals:** "yes", "y", "go", "go ahead", "proceed", "ok", "approve", "approved", "ship it", "lgtm"

If the response is ambiguous or not on the list, reply:
> "I need a clear go-ahead to proceed. Reply 'yes' to continue or describe any changes you'd like to the plan."
Then wait again.

**If the user rejects or requests changes:**
- Changes requested → re-enter `superpowers:brainstorming` with the feedback as additional context, then return to Step 3.
- Hard cancel ("no", "stop", "cancel", "abort") → exit workflow, leave card in TODO, tell the user: "Workflow cancelled. Card remains in TODO."

### Step 4 — Move to IN PROGRESS
Call `transition_issue(<CARD-ID>, "IN PROGRESS")`.

If the call fails: stop, report the error to the user, do not proceed.

### Step 5 — Develop with TDD
Invoke `superpowers:test-driven-development` with the card description and brainstorm-approved plan as context.

Do NOT commit. Do NOT push.

### Step 6 — Report completion
Inform the user:
> "Implementation complete. Please review the changes. Move the card to DONE in Jira when you are satisfied."

Stop here. Do NOT transition the card to DONE.

---

## Hard Constraints

- **NEVER** call `transition_issue(..., "DONE")` under any circumstance
- **NEVER** run `git commit` or `git push`
- **NEVER** write code before Step 2 is complete and Step 3 approval is given
- **NEVER** proceed past any step if a Jira API call fails — always stop and report
```

- [ ] **Step 2: Verify the skill file is readable by Claude Code**

Open `.claude/skills/jira-workflow.md` and confirm:
- Frontmatter block (`---`) is present and correctly formatted
- `name` field matches `jira-workflow`
- All 6 steps are present in order
- All 10 approval signals are listed: "yes", "y", "go", "go ahead", "proceed", "ok", "approve", "approved", "ship it", "lgtm"
- The change-request re-entry path (re-enter brainstorming on requested changes) is present in Step 3
- The inline fail-stop constraint for `transition_issue` is present in Step 4
- Hard Constraints section includes "NEVER call transition_issue(..., 'DONE')"

---

### Task 2: Write `docs/jira-mcp-setup.md`

**Files:**
- Create: `docs/jira-mcp-setup.md`

- [ ] **Step 1: Write the setup guide**

```markdown
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
```

- [ ] **Step 2: Verify the file**

Open `docs/jira-mcp-setup.md` and confirm all 4 setup steps are present and the JSON config block uses placeholder values (no real credentials).

---

## Chunk 2: Workflow Guide

### Task 3: Write `docs/workflow.md`

**Files:**
- Create: `docs/workflow.md`

- [ ] **Step 1: Write the workflow guide**

```markdown
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
```

- [ ] **Step 2: Verify the file**

Open `docs/workflow.md` and confirm:
- The 6-step agent protocol table is present
- The "What You Do" table is present
- The rules section explicitly states the agent never moves to DONE and never commits
- Cancellation instructions are present

---

## Completion Checklist

After all tasks are done, verify the following files exist:

- [ ] `.claude/skills/jira-workflow.md` (created by this plan)
- [ ] `docs/jira-mcp-setup.md` (created by this plan)
- [ ] `docs/workflow.md` (created by this plan)
- [ ] `docs/superpowers/specs/2026-03-12-jira-workflow-design.md` (pre-existing)
- [ ] `.claude/rules/hermeticism.md` (pre-existing, must be unmodified)
- [ ] `.claude/rules/security.md` (pre-existing, must be unmodified)
- [ ] `README.md` (pre-existing, must be unmodified)

**Do NOT commit or push any of these files.** Committing is the user's responsibility.

Hand off to the user for review and for configuring the Jira MCP plugin with the actual npm package name.
