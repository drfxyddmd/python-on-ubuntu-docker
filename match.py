from github import Github
import csv

# Authenticate with your GitHub Personal Access Token (PAT)
g = Github("your_token_here")

# Get the organization
org = g.get_organization("your_organization")

# Read the list of usernames from the CSV file
usernames = []
with open('usernames.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        usernames.append(row[0])  # Assuming usernames are in the first column

# Prepare a dictionary to hold the mapping
user_team_mapping = {username: [] for username in usernames}

# Convert the list of usernames to a set for faster lookup
usernames_set = set(usernames)

# Get all teams in the organization
teams = org.get_teams()

# Iterate over each team
for team in teams:
    # Get all members of the team
    members = team.get_members()
    # Iterate over team members
    for member in members:
        # Check if the member's login is in our list
        if member.login in usernames_set:
            user_team_mapping[member.login].append(team.name)

# Output the mapping
for username in usernames:
    teams = user_team_mapping.get(username, [])
    print(f"User: {username}, Teams: {', '.join(teams) if teams else 'No team found'}")
