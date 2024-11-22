#!/bin/bash

# Replace 'your-organization' with your actual GitHub organization name
ORG_NAME="your-organization"

# Number of repositories to scan (set to a large number to scan all)
MAX_REPOS=100  # Adjust as needed

# Output CSV file
OUTPUT_CSV="repo_info.csv"

# Write CSV headers
echo "Repo Link,Catalog Owner,Code Owners,Top Contributors" > "$OUTPUT_CSV"

# Get the list of repositories in the organization, excluding archived repositories
echo "Fetching repositories for organization '$ORG_NAME'..."
repos=$(gh repo list "$ORG_NAME" --no-archived --limit "$MAX_REPOS" --json name,sshUrl --jq '.[] | {name: .name, sshUrl: .sshUrl}')

if [ -z "$repos" ]; then
  echo "No repositories found or unable to fetch repositories."
  exit 1
fi

# Iterate over each repository
echo "$repos" | jq -c '.' | while read -r repo_info; do
  repo_name=$(echo "$repo_info" | jq -r '.name')
  repo_ssh_url=$(echo "$repo_info" | jq -r '.sshUrl')
  repo_link="https://github.com/$ORG_NAME/$repo_name"

  echo "Processing repository: $repo_name"

  catalog_owner="Not Found"
  codeowners="Not Found"
  top_contributors="No contributors found"

  # -------------------- Retrieve catalog-info.yaml --------------------
  catalog_content=$(gh api -H "Accept: application/vnd.github.v3.raw" repos/"$ORG_NAME"/"$repo_name"/contents/catalog-info.yaml 2>/dev/null)

  if [ -n "$catalog_content" ]; then
    # Parse catalog-info.yaml to extract 'spec.owner'
    catalog_owner=$(echo "$catalog_content" | yq e '.spec.owner // "Not Found"' -)
  else
    echo "  catalog-info.yaml not found."
  fi

  # -------------------- Retrieve CODEOWNERS --------------------
  codeowners_content=""
  codeowners_paths=("CODEOWNERS" ".github/CODEOWNERS" "docs/CODEOWNERS")

  for path in "${codeowners_paths[@]}"; do
    codeowners_content=$(gh api -H "Accept: application/vnd.github.v3.raw" repos/"$ORG_NAME"/"$repo_name"/contents/"$path" 2>/dev/null)
    if [ -n "$codeowners_content" ]; then
      # Extract code owners from the CODEOWNERS file
      codeowners=$(echo "$codeowners_content" | grep -E '^\s*\*\s+' | awk '{for(i=2;i<=NF;i++) print $i}' | grep '^@' | sed 's/@company\///; s/@//' | tr '\n' ',' | sed 's/,$//')
      if [ -z "$codeowners" ]; then
        codeowners="Not Found"
      fi
      break
    fi
  done

  if [ -z "$codeowners_content" ]; then
    echo "  CODEOWNERS not found."
  fi

  # -------------------- Get Top Contributors --------------------
  contributors=$(gh api repos/"$ORG_NAME"/"$repo_name"/contributors --paginate --jq '.[].login')

  if [ -n "$contributors" ]; then
    # Get the top 3 contributors
    top_contributors=$(echo "$contributors" | head -n 3 | paste -sd ',' -)
  fi

  # -------------------- Append Data to CSV --------------------
  echo "\"$repo_link\",\"$catalog_owner\",\"$codeowners\",\"$top_contributors\"" >> "$OUTPUT_CSV"

done

echo "Data written to $OUTPUT_CSV"
