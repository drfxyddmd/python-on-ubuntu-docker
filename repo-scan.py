import os
import csv
from datetime import datetime, timedelta
from github import Github
import yaml
import re

# -------------------- Configuration --------------------

# GitHub Personal Access Token (PAT)
# Ensure your token has the necessary scopes, such as 'repo'
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("Error: GITHUB_TOKEN environment variable not set.")
    exit(1)

# GitHub organization name
ORG_NAME = 'your_organization'  # Replace with your organization name

# Manually specified repository links (full URLs)
# If this list is not empty, the script will process these repositories
REPO_LINKS = [
    # Insert your repository links here, e.g.,
    # 'https://github.com/your_organization/repo1',
    # 'https://github.com/your_organization/repo2',
]

# Output CSV file name
OUTPUT_CSV = 'repo_info.csv'

# -------------------- Script --------------------

def main():
    # Authenticate with GitHub
    g = Github(token)

    # Prepare the list of repositories to process
    repos_to_process = []

    if REPO_LINKS:
        # Manually specified repositories
        for repo_link in REPO_LINKS:
            try:
                # Extract owner and repo name from the URL
                path_parts = repo_link.strip().split('/')
                owner = path_parts[-2]
                repo_name = path_parts[-1]
                repo = g.get_repo(f"{owner}/{repo_name}")
                repos_to_process.append(repo)
            except Exception as e:
                print(f"Error accessing repository '{repo_link}': {e}")
    else:
        try:
            # Get the organization
            org = g.get_organization(ORG_NAME)
        except Exception as e:
            print(f"Error accessing organization '{ORG_NAME}': {e}")
            exit(1)

        # Get all repositories from the organization
        try:
            repos = org.get_repos()
            repos_to_process.extend(repos)
        except Exception as e:
            print(f"Error retrieving repositories: {e}")
            exit(1)

    # Prepare data list
    data = []

    for repo in repos_to_process:
        print(f"Processing repository: {repo.full_name}")
        repo_link = repo.html_url
        catalog_owner = ''
        codeowners = []
        top_contributors = []

        # -------------------- Check for catalog-info.yaml --------------------
        try:
            contents = repo.get_contents("catalog-info.yaml", ref=repo.default_branch)
            catalog_content = contents.decoded_content.decode()
            catalog_yaml = yaml.safe_load(catalog_content)
            catalog_owner = catalog_yaml.get('owner', 'Not Found')
        except Exception:
            # File not found or error in reading/parsing
            catalog_owner = 'Not Found'

        # -------------------- Get Top Contributors --------------------
        try:
            since = datetime.now() - timedelta(days=365 * 2)
            commits = repo.get_commits(since=since.isoformat())
            contributor_counts = {}
            for commit in commits:
                if commit.author and commit.author.login:
                    contributor_counts[commit.author.login] = contributor_counts.get(commit.author.login, 0) + 1
            # Sort contributors by commit count
            sorted_contributors = sorted(contributor_counts.items(), key=lambda x: x[1], reverse=True)
            top_contributors = [login for login, _ in sorted_contributors[:3]]
        except Exception as e:
            top_contributors = []

        # -------------------- Check for CODEOWNERS --------------------
        codeowners_paths = ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"]
        codeowners_found = False
        for path in codeowners_paths:
            try:
                contents = repo.get_contents(path, ref=repo.default_branch)
                codeowners_file = contents.decoded_content.decode()
                codeowners = []
                for line in codeowners_file.split('\n'):
                    match = re.search(r'^\s*\*\s+(.*)$', line)
                    if match:
                        codeowners.extend([
                            o.split('/', maxsplit=1)[-1]
                            for o in re.split(r'\s+', match.group(1))
                            if o.startswith('@company/')
                        ])
                codeowners = list(set(codeowners))  # Remove duplicates
                if codeowners:
                    codeowners_found = True
                    break  # Stop after finding the first CODEOWNERS file with owners
            except Exception:
                continue  # Try the next possible CODEOWNERS path
        if not codeowners_found or not codeowners:
            codeowners = ['Not Found']

        # -------------------- Append Data --------------------
        data.append({
            'Repo Link': repo_link,
            'Catalog Owner': catalog_owner,
            'Codeowners': ', '.join(codeowners),
            'Top Contributors': ', '.join(top_contributors) if top_contributors else 'No contributors found'
        })

    # -------------------- Write to CSV --------------------
    try:
        with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Repo Link', 'Catalog Owner', 'Codeowners', 'Top Contributors']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"Data written to '{OUTPUT_CSV}'.")
    except Exception as e:
        print(f"Error writing to CSV file: {e}")
        exit(1)

# -------------------- Entry Point --------------------

if __name__ == '__main__':
    main()
