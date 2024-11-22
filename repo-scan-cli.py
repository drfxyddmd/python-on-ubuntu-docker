#!/bin/bash

# Replace 'your-organization' with your actual GitHub organization name
ORG_NAME="your-organization"

# Number of repositories to scan (set to a large number to scan all)
MAX_REPOS=100  # Adjust as needed

# Output CSV file
OUTPUT_CSV="top_contributors.csv"

# Write CSV headers
echo "Repository,Contributors" > $OUTPUT_CSV

# Get the list of repositories in the organization, excluding archived repositories
echo "Fetching repositories for organization '$ORG_NAME'..."
repos=$(gh repo list $ORG_NAME --no-archived --limit $MAX_REPOS --json name --jq '.[].name')

if [ -z "$repos" ]; then
  echo "No repositories found or unable to fetch repositories."
  exit 1
fi

# Iterate over each repository
for repo in $repos; do
  echo "Processing repository: $repo"

  # Get the top contributors
  contributors=$(gh api repos/$ORG_NAME/$repo/contributors --paginate --jq '.[] | .login')

  if [ -z "$contributors" ]; then
    echo "  No contributors found."
    continue
  fi

  # Get the top 3 contributors
  top_contributors=$(echo "$contributors" | head -n 3 | paste -sd ',' -)

  # Append to CSV
  echo "$repo,\"$top_contributors\"" >> $OUTPUT_CSV
done

echo "Data written to $OUTPUT_CSV"
