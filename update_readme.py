#!/usr/bin/env python3
"""Update README.md with a table of public repos in the 'con' organization."""

import os
import re

import requests

ORG = "con"
README_PATH = "README.md"

TABLE_START = "<!-- TABLE_START -->"
TABLE_END = "<!-- TABLE_END -->"

# Repos whose names form a compound word when prefixed with "con".
# Maps repo name -> display label (e.g. "cierge" -> "con/cierge" = concierge).
CON_WORDPLAY_DISPLAY = {
    "catenate": "con/catenate",       # concatenate
    "cierge": "con/cierge",           # concierge
    "CONveyor": "con/veyor",          # conveyor
    "duct": "con/duct",               # conduct
    "ference": "con/ference",         # conference
    "flux": "con/flux",               # conflux
    "job": "con/job",                 # con job
    "noisseur": "con/noisseur",       # connoisseur
    "quest": "con/quest",             # conquest
    "serve": "con/serve",             # conserve
    "tents": "con/tents",             # contents
    "tinuous": "con/tinuous",         # continuous
    "tinuous-template": "con/tinuous-template",
    "tinuum": "con/tinuum",           # continuum
    "tributors": "con/tributors",     # contributors
    "versations": "con/versations",   # conversations
}


def get_headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_org_repos(headers):
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/orgs/{ORG}/repos",
            headers=headers,
            params={"per_page": 100, "page": page, "type": "public"},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def get_open_prs_count(repo_name, headers):
    """Return the number of open pull requests for a repo."""
    resp = requests.get(
        f"https://api.github.com/repos/{ORG}/{repo_name}/pulls",
        headers=headers,
        params={"state": "open", "per_page": 1},
    )
    resp.raise_for_status()
    link = resp.headers.get("Link", "")
    if 'rel="last"' in link:
        match = re.search(r'[?&]page=(\d+)>;\s*rel="last"', link)
        if match:
            return int(match.group(1))
    return len(resp.json())


def build_table(repos, headers):
    rows = [
        "| Name | Description | Issues | PRs | Stars | Forks |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for repo in sorted(repos, key=lambda r: r["name"].lower()):
        name = repo["name"]
        url = repo["html_url"]
        desc = (repo.get("description") or "").replace("|", "\\|")
        stars = repo["stargazers_count"]
        forks = repo["forks_count"]
        prs = get_open_prs_count(name, headers)
        # open_issues_count includes both issues and PRs
        issues = max(0, repo["open_issues_count"] - prs)
        display = CON_WORDPLAY_DISPLAY.get(name, name)
        rows.append(f"| [{display}]({url}) | {desc} | {issues} | {prs} | {stars} | {forks} |")
    return "\n".join(rows)


def update_readme(table):
    with open(README_PATH, "r") as f:
        content = f.read()

    new_section = f"{TABLE_START}\n{table}\n{TABLE_END}"

    if TABLE_START in content and TABLE_END in content:
        updated = re.sub(
            re.escape(TABLE_START) + r".*?" + re.escape(TABLE_END),
            new_section,
            content,
            flags=re.DOTALL,
        )
    else:
        updated = content.rstrip() + "\n\n" + new_section + "\n"

    with open(README_PATH, "w") as f:
        f.write(updated)


def main():
    headers = get_headers()
    print(f"Fetching repos for org '{ORG}'...")
    repos = get_org_repos(headers)
    print(f"Found {len(repos)} public repos. Building table...")
    table = build_table(repos, headers)
    print("Updating README.md...")
    update_readme(table)
    print("Done.")


if __name__ == "__main__":
    main()
