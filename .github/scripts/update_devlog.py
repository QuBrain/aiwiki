"""Generate a devlog entry from the latest commit and append to .labnotebook/."""

import subprocess
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
NOTEBOOK_DIR = REPO / ".labnotebook"


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO).stdout.strip()


def main():
    today = date.today().isoformat()
    notebook_file = NOTEBOOK_DIR / f"{today}.md"

    # Get latest commit details
    sha = run(["git", "log", "-1", "--format=%H"])
    short_sha = sha[:7]
    author = run(["git", "log", "-1", "--format=%an"])
    timestamp = run(["git", "log", "-1", "--format=%ad", "--date=iso"])
    subject = run(["git", "log", "-1", "--format=%s"])
    body = run(["git", "log", "-1", "--format=%b"])
    files_raw = run(["git", "diff-tree", "--no-commit-id", "-r", "--name-status", sha])

    # Skip if this commit is already a devlog update
    if "[devlog]" in subject.lower():
        print("Skipping — commit is a devlog update itself")
        return

    # Format files changed
    files_lines = []
    for line in files_raw.splitlines():
        if line.strip():
            files_lines.append(f"- {line}")

    # Build entry
    entry = f"""## {short_sha} — {timestamp[:10]} {timestamp[11:16]}

**Author:** {author}

**Message:** {subject}

"""
    if body.strip():
        entry += f"{body.strip()}\n\n"
    entry += "**Files changed:**\n" + "\n".join(files_lines) + "\n\n"

    # Append to today's devlog or create new
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    if notebook_file.exists():
        existing = notebook_file.read_text()
        # Insert after the title line
        lines = existing.splitlines()
        insert_at = 1
        for i, line in enumerate(lines):
            if line.startswith("## ") and i > 0:
                insert_at = i
                break
        lines.insert(insert_at, "")
        lines.insert(insert_at, entry.strip())
        notebook_file.write_text("\n".join(lines) + "\n")
    else:
        with open(notebook_file, "w") as f:
            f.write(f"# Devlog — {today}\n\n{entry.strip()}\n")

    # Commit and push
    run(["git", "add", str(notebook_file.relative_to(REPO))])
    run(["git", "commit", "-m", f"docs: update devlog for {short_sha} [skip ci]"])
    run(["git", "push"])

    print(f"Devlog updated for {short_sha}: {subject}")


if __name__ == "__main__":
    main()
