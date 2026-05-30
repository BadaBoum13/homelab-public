---
name: obsidian
description: Manage the homelab Obsidian vault — tickets, knowledge notes, and project context — through the Obsidian MCP server. Use when picking up work, creating or updating a ticket, transitioning ticket status, ticking acceptance criteria, moving a ticket to review, or writing a knowledge/ADR/runbook note for the homelab-k3s project.
---

# Obsidian Vault Protocol

## Vault coordinates
context: homelab-public
project: homelab-k3s

## Relevant knowledge
project/homelab-k3s/

## Identity
This vault is the single source of truth for tickets, knowledge, and
project context. All reads and writes go through the Obsidian MCP
server — never through direct filesystem access.

## Vault layout
tickets/                one .md file per ticket
tickets/_template.md    ticket template — read this before creating any ticket
knowledge/              ADRs, runbooks, architecture notes
projects/               per-project context notes

## Ticket lifecycle

backlog → todo → in-progress → review → [human closes to done]

Valid transitions:
- backlog  → todo        when prioritised and ready to work
- todo     → in-progress when you start working it
- in-progress → review  when all acceptance criteria are checked
- any state → blocked   when a dependency is unresolved

Blocked tickets must have a `depends_on` entry and a worklog note.

## Rules

### 1. Picking work
Pick from `status: todo`, ordered P0 → P3.
Skip any ticket whose `depends_on` list contains a non-done ticket.
Never invent work — create a ticket first, then work it.
To find the next ticket:
  search "status: todo" then read candidates with get_file_contents.

### 2. Every status change must
- Use patch_content to update `status` in frontmatter
- Use patch_content to update `updated` date in frontmatter
- Use append_content to add a dated line to the Worklog section
All three in the same logical operation — never update status silently.

### 3. Creating a ticket
- Read tickets/_template.md with get_file_contents first
- List tickets/ with list_files_in_dir to find the next free TICK-NNNN
- Fill title, goal, project, context, and at least one acceptance criterion
- Set status: backlog unless you are about to work it immediately
- Write the file with patch_content (create) or append_content

### 4. Ticking acceptance criteria
Use patch_content to replace `- [ ]` with `- [x]` for each completed
criterion. Never tick a criterion you have not actually completed.

### 5. Moving to review
When all acceptance criteria are checked:
- patch_content: set status → review, update `updated` date
- append_content: worklog line summarising what was done
- append_content: add a "## How to verify" section at the bottom
- Stop — do not move to done under any circumstances

### 6. Closing tickets
You may NOT set status: done on any ticket.
done is a human-only transition.
When a ticket is ready, move it to review and stop.

### 7. Blocked
Never leave a ticket in-progress across sessions without:
- status set to blocked in frontmatter
- depends_on populated
- a worklog note explaining what is blocking it and where work stands

### 8. Knowledge notes
When completing a ticket produces reusable knowledge (a fix, a pattern,
an architectural decision), create a note in knowledge/ capturing it.
Link it from the ticket with [[note-name]].
This is how the vault becomes useful beyond task tracking.

## Frontmatter reference
status:    backlog | todo | in-progress | review | done | blocked
priority:  P0 (urgent) | P1 (high) | P2 (normal) | P3 (low)
context:   homelab | work | personal
project:   free string — should match the relevant projects/ note
tags:      free list
depends_on: list of TICK-NNNN ids

## Worklog format
Append to the Worklog section using this format:
- YYYY-MM-DD — [status transition or action] [one line summary]

Example:
- 2026-05-24 — in-progress → review — configured SoftHSM2 slot,
  verified unseal on pod restart, all criteria checked

## Project context
Each project repo's CLAUDE.md declares its vault coordinates:
  context: homelab | work | personal
  project: <project-name>
Use these to filter tickets when working within a specific project.
Only read and write tickets matching the current project's coordinates
unless explicitly asked to work across projects.
