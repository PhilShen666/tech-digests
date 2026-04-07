#!/usr/bin/env python3
"""
Tech Digest - GitHub Actions orchestrator.

Fetches AI/ML/RecSys items, calls the Claude API to produce the digest,
commits the result to the repo, and creates a GitHub issue.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import anthropic

REPO = "PhilShen666/tech-digests"


def main():
    # Date window: last 24 hours
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    since = str(yesterday)
    until = str(today)
    print(f"Date range: {since} to {until}")

    # Fetch items via existing script (full internet access in GH Actions)
    print("Fetching items...")
    result = subprocess.run(
        [sys.executable, "scripts/fetch_items.py", "--since", since, "--until", until],
        capture_output=True, text=True
    )
    items = json.loads(result.stdout or "[]")
    print(f"Fetched {len(items)} items")
    if result.stderr.strip():
        print(f"Source warnings:\n{result.stderr.strip()}")

    # Short-circuit if nothing to digest
    if not items:
        digest_md = (
            f"# Tech Digest - {since} to {until}\n\n"
            "> No items fetched in this window.\n"
        )
    else:
        instructions = Path("digest_prompt.md").read_text()
        user_message = (
            f"{instructions}\n\n"
            f"## Items\n\n"
            f"```json\n{json.dumps(items, indent=2)}\n```\n\n"
            f"Date range: since={since}, until={until}"
        )

        print("Calling Claude API...")
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": user_message}]
        )
        digest_md = response.content[0].text
        print(
            f"Digest generated ({len(digest_md)} chars, "
            f"input={response.usage.input_tokens} output={response.usage.output_tokens} tokens)"
        )

    # Write digest file
    Path("digests").mkdir(exist_ok=True)
    digest_path = Path(f"digests/{until}.md")
    digest_path.write_text(digest_md)
    print(f"Written: {digest_path}")

    # Commit and push
    print("Committing...")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        check=True
    )
    subprocess.run(["git", "add", str(digest_path)], check=True)
    subprocess.run(["git", "commit", "-m", f"Digest {until}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Pushed.")

    # Create GitHub issue
    print("Creating GitHub issue...")
    result = subprocess.run(
        ["gh", "issue", "create",
         "--title", f"Tech Digest {until}",
         "--body", digest_md,
         "--repo", REPO],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"Issue created: {result.stdout.strip()}")
    else:
        print(f"Issue creation failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
