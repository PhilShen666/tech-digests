# Phone-triggered Digest via GitHub Remote Trigger

## Context

User wants to manually trigger the `/digest` skill from their phone and read the result on both phone (skim) and desktop (deep-read), without requiring their Mac to be on.

Skills only work in the local Claude Code CLI harness, so phone-issued `/digest` commands sent through Claude.ai web/mobile arrive as literal strings and do nothing. The fix is to move execution to Anthropic's cloud via a `RemoteTrigger`, with GitHub as the delivery + archive layer.

## Architecture

```
Phone tap "Run" at claude.ai/code/scheduled
    │
    ▼
RemoteTrigger spawns CCR session (Anthropic cloud sandbox)
    │
    │  Sources cloned: github.com/PhilShen666/tech-digests
    │  MCP: github connector attached
    │  Tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch + mcp__github__*
    │
    ▼
Agent executes digest_workflow.md:
    1. pip install -r requirements.txt
    2. python scripts/fetch_items.py --since <YYYY-MM-DD> --until <YYYY-MM-DD>
    3. Categorize items, score, pick spotlights
    4. WebFetch spotlight pages (arxiv abs+html, blog posts)
    5. curl figures into assets/<until>/<slug>-fig<n>.<ext>
    6. Write digest markdown text
    7. mcp__github__push_files: commit digests/<until>.md + assets/<until>/* in one commit
    8. mcp__github__create_issue: title "Tech Digest <until>", body = digest markdown
    │
    ▼
GitHub mobile push notification → user's phone
    │
    ▼
Tap → rendered markdown digest with embedded figures
       (same issue URL works on laptop for deep-reading)
```

## Repo: PhilShen666/tech-digests (private)

```
tech-digests/
├── README.md
├── requirements.txt
├── scripts/
│   ├── fetch_items.py
│   └── sources.py
├── digest_workflow.md
├── digests/
│   └── .gitkeep
└── assets/
    └── .gitkeep
```

## Trigger setup

- Environment: `env_01GUBduHKxpCvHekkbAQ4c8j` (claude-code-default)
- Model: claude-sonnet-4-6
- Source: `https://github.com/PhilShen666/tech-digests` cloned into working directory
- MCP: GitHub connector (requires cloud connector UUID from claude.ai/settings/connectors)
- Cron: `0 0 1 1 *` (manually triggered via Run button — cron is a no-op placeholder)

## Important constraints

- Strictly honor the 24-hour window. Do not silently widen.
- Never fabricate affiliations.
- Skip figures gracefully if unavailable.
- Use mcp__github__ tools for repo writes — do NOT shell out to `git push`.
