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
