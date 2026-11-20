"""Create and merge a one-line Geth configuration change through a PR."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env["GH_TOKEN"] = subprocess.check_output(
    ["gh", "auth", "token", "--user", "jaesimin0903"], text=True).strip()


def run(*args, capture=False):
    return subprocess.run(args, cwd=ROOT, env=env, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


if __name__ == "__main__":
    branch, before, after, title, body = sys.argv[1:]
    run("git", "checkout", "main")
    run("git", "checkout", "-b", branch)
    manifest = ROOT / "k8s/geth-dev.yaml"
    text = manifest.read_text()
    if text.count(before) != 1:
        raise SystemExit("Expected exactly one matching value")
    manifest.write_text(text.replace(before, after))
    run("git", "add", "k8s/geth-dev.yaml")
    run("git", "commit", "-m", title)
    run("git", "-c", "credential.helper=", "-c",
        "credential.helper=!gh auth git-credential", "push", "-u", "origin", branch)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md") as draft:
        draft.write(body + "\n")
        draft.flush()
        url = run("gh", "pr", "create", "--base", "main", "--head", branch,
                  "--title", title, "--body-file", draft.name, capture=True).strip()
    run("gh", "pr", "merge", url, "--merge")
    info = json.loads(run("gh", "pr", "view", url, "--json",
                          "url,number,title,mergedAt,mergeCommit,body", capture=True))
    (ROOT / "evidence" / (branch + ".json")).write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    run("git", "checkout", "main")
    run("git", "-c", "credential.helper=", "-c",
        "credential.helper=!gh auth git-credential", "pull", "--ff-only")
    print(url)
