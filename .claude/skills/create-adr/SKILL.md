---
name: create-adr
description: Create a new Architecture Decision Record (ADR) note in the homelab Obsidian vault via the Obsidian MCP server. Use when the user wants to record, document, or write up a design/architecture decision, tradeoff, or "why we did X instead of Y" for the homelab-k3s project — e.g. "write an ADR for...", "document this decision", "record why we chose...".
---

# create-adr

Creates a numbered ADR note under `projects/<project>/knowledge/` in the vault
that the [obsidian](../obsidian/SKILL.md) skill manages. All reads and writes
go through the Obsidian MCP server — never direct filesystem access. This
skill only covers **creating** a new ADR; ticket lifecycle, general knowledge
notes, and everything else stay with the `obsidian` skill.

Read this skill's own instructions fully before writing anything — steps 1-2
below determine facts (the next ADR number, the numbering width) that steps
3-5 depend on, and guessing them produces a broken filename or a duplicate.

## Vault coordinates

Read from the calling repo's `CLAUDE.md` under "Agent Protocol":

```
project: homelab-k3s
```

**Gotcha:** `CLAUDE.md` also lists `context: homelab-public` right above it —
that is the *vault* identifier, not the note field. Every existing note's
frontmatter `context:` value is `homelab` (verified against all 3 existing
ADRs, 4 tickets, and the project map). Use `context: homelab`, not the
`homelab-public` string from CLAUDE.md.

## Process

### 1. Read the template

```
vault_read("projects/homelab-k3s/knowledge/_adr-template.md")
```

It has the exact frontmatter keys, section order, and Templater placeholders
(`<% tp.date.now(...) %>`) — resolve those to today's real date yourself, the
MCP server does not run Templater.

### 2. Find the next free number

```
vault_list("projects/homelab-k3s/knowledge")
```

ADRs are `adr-NNNN-<kebab-slug>.md`, sequential, 4-digit zero-padded, never
reused even if an old ADR is later superseded. Take the highest existing
number and add one. (As of this skill's authoring: `adr-0001`, `adr-0002`,
`adr-0003` exist, so the next is `adr-0004`.) Do not renumber existing ADRs.

### 3. Gather the decision

You need, at minimum:
- **The decision itself** — a short imperative statement ("Use X instead of
  Y"). This becomes the title.
- **Context** — the problem/constraint and the options that were rejected,
  and why.
- **Consequences** — trade-offs accepted, follow-up obligations.

If the user's request doesn't already contain these (they're describing a
decision they just made, or asking you to document one visible in the repo's
code/config/commit history), ask before writing rather than inventing
rationale. A thin ADR with a made-up "Context" section is worse than no ADR.

### 4. Write the note

Path: `projects/homelab-k3s/knowledge/adr-NNNN-<kebab-slug-of-decision>.md`
(slug from the decision statement, e.g. "Ansible configures OpenBao instead
of vault-config-operator" → `adr-0003-ansible-openbao-config-over-vault-config-operator`).

Frontmatter — copy exactly, only the bracketed parts change:

```yaml
---
title: "ADR-NNNN: <decision, as a short statement>"
type: adr
context: homelab
project: homelab-k3s
tags: [adr, <2-4 more specific topic tags>]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Body — same five sections, same order, every time:

```markdown
# ADR-NNNN: <decision, as a short statement>

## Status
Accepted — YYYY-MM-DD

## Context
...

## Decision
...

## Consequences
...

## References
- `path/to/relevant/file`
- [[related-note]]
```

`[[wikilink]]` targets are the note's filename stem, no path, no `.md`. Link
to related ADRs and architecture notes both ways: add the new ADR's
`[[adr-NNNN-...]]` to the **References** section of any ADR it builds on,
supersedes, or is closely related to — that's how the existing three
cross-link (see `adr-0001` ↔ `adr-0003`, both ↔ `openbao-architecture`).

Write with:
```
vault_write("projects/homelab-k3s/knowledge/adr-NNNN-<slug>.md", <content>)
```

### 5. Link it from the project map

Every existing ADR is linked from `projects/homelab-k3s/project map.md`
(currently under "## Secret management"). Check whether the new ADR belongs
under an existing section there or needs a new one, then
`vault_patch`/`vault_append` a `- [[adr-NNNN-...]]` line. An ADR that nothing
links to is effectively lost — the vault has no other index of them.

### 6. Superseding an older ADR (only if applicable)

If the new decision replaces an earlier one, update the **old** ADR too —
don't leave two "Accepted" ADRs contradicting each other:
- Change its `## Status` line to `Superseded by [[adr-NNNN-...]]` (keep the
  original "Accepted — date" line above it as history)
- Bump its frontmatter `updated` date
- Add the new ADR to its References

This vault currently has ADRs whose "Accepted" decisions no longer match the
live infrastructure (see the `run-homelab-k3s` skill's Gotchas section for
specifics) but nothing has formally superseded them yet — don't treat
"Accepted" status as proof the decision still holds; check the code/cluster
when it matters.

## What this skill does not do

- Ticket creation/transitions — that's `obsidian` skill rules 1-7.
- Non-ADR knowledge notes (runbooks, architecture docs) — same frontmatter
  family (`type: adr` → whatever fits) but no numbering scheme; just follow
  `obsidian` skill rule 8.
- Deciding *whether* something deserves an ADR — if unsure, ask the user
  rather than creating one for a decision that's really just an
  implementation detail.
