# Jira-Driven Agentic Workflow — Design Spec

**Date:** 2026-03-12
**Project:** dnsexists
**Status:** Draft

---

## Overview

A structured workflow for agentic development driven by Jira cards. The agent reads a card, brainstorms with the user, develops using TDD, and never autonomously closes a card. The human always decides when work is DONE.

---

## Prerequisites

### 1. Jira Project

- A Jira project (e.g., key `DNS`) with a board configured with exactly three states:
  - `TODO`
  - `IN PROGRESS`
  - `DONE`
- Cards are created manually by the user before handing them to the agent.
- Card descriptions are free-form text.

### 2. Jira MCP Plugin

- The Jira MCP plugin must be configured in Claude Code before using this workflow.
- See `docs/jira-mcp-setup.md` for setup instructions.
- Required MCP tools used by the skill:
  - `get_issue` — read card summary and description
  - `transition_issue` — move card between states (use exact state name as configured on the board)

---

## Skill: `jira-workflow`

### Invocation

```
/jira-workflow <CARD-ID>
```

Example: `/jira-workflow DNS-42`

### Protocol (strict, in order)

| Step | Action | Constraint |
|------|--------|------------|
| 1 | **Read card** — `get_issue(<CARD-ID>)`, extract summary + description | If the call fails, stop and report the error to the user. Do not proceed. |
| 2 | **Brainstorm** — invoke `superpowers:brainstorming` with the card summary and description as context | No code written during this step |
| 3 | **Await user approval** — present a summary of the brainstorm outcome and ask: "Shall I proceed?" | Block until user gives an explicit approval signal (see Approval Signals below) |
| 4 | **Move to IN PROGRESS** — `transition_issue(<CARD-ID>, "IN PROGRESS")` | Only after user approval. If the call fails, report the error and stop. |
| 5 | **Develop with TDD** — invoke `superpowers:test-driven-development` with the card description and brainstorm output as context | No commits, no pushes |
| 6 | **Report completion** — inform the user the implementation is done and that they should review before closing the card | Agent stops here |

### Approval Signals (Step 3)

The agent accepts any of the following as explicit approval to proceed:

- "yes", "y", "go", "go ahead", "proceed", "ok", "approve", "approved", "ship it", "lgtm"

If the user's response is not on this list or is ambiguous, the agent must ask again:
> "I need a clear go-ahead to proceed. Reply 'yes' to continue or describe any changes you'd like to the plan."

### Rejection / Change Path (Step 3)

If the user does not approve:
- If the user requests changes to the plan → re-enter `superpowers:brainstorming` with the feedback as additional context, then return to Step 3.
- If the user says "no", "stop", "cancel", or "abort" → exit the workflow, leave the card in TODO, and inform the user: "Workflow cancelled. Card remains in TODO."

---

## Skill Dependencies

### `superpowers:brainstorming`

A superpowers built-in skill. It takes a topic and context, asks the user clarifying questions one at a time, proposes approaches, and produces an approved design. In this workflow it is given the Jira card summary and description as its starting context. Its output is the approved design/plan that feeds into Step 5.

### `superpowers:test-driven-development`

A superpowers built-in skill. It takes a feature description and writes failing tests first, then implementation to make them pass. In this workflow it receives the card description and the brainstorm-approved plan as its context.

---

## Hard Constraints

- **NEVER** call `transition_issue(..., "DONE")` — moving to DONE is a manual human action
- **NEVER** run `git commit` or `git push`
- **NEVER** write code before Step 2 (brainstorming) is complete and Step 3 (approval) is given
- **NEVER** proceed past any step if a Jira API call fails — always report and stop

---

## File Structure (target state after implementation)

```
dnsexists/
├── docs/
│   ├── workflow.md                          # human-readable workflow guide
│   ├── jira-mcp-setup.md                    # MCP plugin setup guide
│   └── superpowers/
│       └── specs/
│           └── 2026-03-12-jira-workflow-design.md  # this file
├── .claude/
│   ├── rules/
│   │   ├── hermeticism.md
│   │   └── security.md
│   └── skills/
│       └── jira-workflow.md                 # the custom skill
└── README.md
```

---

## What the Human Does

- Creates Jira cards with a description of the task
- Invokes the skill with the card ID: `/jira-workflow <CARD-ID>`
- Reviews the brainstorm outcome and either approves or requests changes
- Manually moves cards to DONE after reviewing and accepting the agent's work

---

## Out of Scope

- Structured card templates (free-form for now)
- Automatic DONE transitions
- Git commits or pushes by the agent
- Multi-card workflows or dependencies
- Comments written back to Jira cards
