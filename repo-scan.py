import os
import csv
import re
import yaml
import itertools
from github import Github, GithubException

# -------------------- Configuration --------------------

# GitHub Personal Access Token (PAT)
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("Error: GITHUB_TOKEN environment variable not set.")
    exit(1)

# Authenticate with GitHub
g = Github(token)

# GitHub organization name
ORG_NAME = 'your_organization'  # Replace with your organization name

# Number of repositories to scan
MAX_REPOS = 10  # Change this value as needed

# Output CSV file name
OUTPUT_CSV = 'repo_data.csv'

# -------------------- Script --------------------

# Get the organization
try:
    org = g.get_organization(ORG_NAME)
except GithubException as e:
    print(f"Error accessing organization '{ORG_NAME}': {e}")
    exit(1)

# Initialize CSV file with headers
with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Repository', 'Catalog Team', 'Codeowners', 'Top Committers']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

# Get repositories sorted by last push date in descending order
repos = org.get_repos(sort='pushed', direction='desc')

for repo in itertools.islice(repos, MAX_REPOS):
    print(f"Processing repository: {repo.full_name}")
    catalog_team = None
    codeowners = []
    top_committers = []

    if repo.archived:
        print('Repository is archived. Skipping.')
        continue

    # -------------------- Process catalog-info.yaml --------------------
    try:
        contents = repo.get_contents('catalog-info.yaml', ref=repo.default_branch)
        catalog_content = contents.decoded_content.decode()
        catalog_info = yaml.safe_load(catalog_content)
        if 'spec' in catalog_info and 'owner' in catalog_info['spec']:
            catalog_team = catalog_info['spec']['owner']
    except GithubException:
        print(f"catalog-info.yaml not found or error in repository {repo.full_name}")

    # -------------------- Process CODEOWNERS --------------------
    codeowners_paths = ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"]
    for path in codeowners_paths:
        try:
            contents = repo.get_contents(path, ref=repo.default_branch)
            codeowners_file = contents.decoded_content.decode()
            for line in codeowners_file.split('\n'):
                match = re.search(r'^\s*\*\s+(.*)$', line)
                if match:
                    codeowners.extend([
                        o.split('/', maxsplit=1)[-1]
                        for o in re.split(r'\s+', match.group(1))
                        if o.startswith('@company/')
                    ])
            codeowners = list(set(codeowners))  # Remove duplicates
            break  # Stop after finding the CODEOWNERS file
        except GithubException:
            continue  # Try the next possible CODEOWNERS path
    else:
        print(f"CODEOWNERS not found in repository {repo.full_name}")

    # -------------------- Get Top Committers --------------------
    try:
        commits = repo.get_commits()
        committer_counts = {}
        for commit in commits:
            if commit.author and commit.author.login:
                committer_counts[commit.author.login] = committer_counts.get(commit.author.login, 0) + 1
        # Sort committers by commit count
        sorted_committers = sorted(committer_counts.items(), key=lambda x: x[1], reverse=True)
        top_committers = [login for login, _ in sorted_committers[:3]]
    except GithubException:
        print(f"Error retrieving commits for repository {repo.full_name}")

    # -------------------- Write Data to CSV --------------------
    with open(OUTPUT_CSV, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({
            'Repository': repo.full_name,
            'Catalog Team': catalog_team if catalog_team else 'Not Found',
            'Codeowners': ', '.join(codeowners) if codeowners else 'Not Found',
            'Top Committers': ', '.join(top_committers) if top_committers else 'No committers found'
        })
