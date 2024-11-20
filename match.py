from github import Github
import csv

# Authenticate with your GitHub Personal Access Token (PAT)
g = Github("your_token_here")

# Get the organization
org = g.get_organization("your_organization")

# Get all members of the organization
members = org.get_members()

# Prepare a list of usernames
usernames = [member.login for member in members]

# Prepare a dictionary to hold the mapping
user_team_mapping = {username: [] for username in usernames}

# Convert the list of usernames to a set for faster lookup
usernames_set = set(usernames)

# Get all teams in the organization
teams = org.get_teams()

# Iterate over each team
for team in teams:
    # Get all members of the team
    team_members = team.get_members()
    # Iterate over team members
    for member in team_members:
        # Check if the member's login is in our list
        if member.login in usernames_set:
            user_team_mapping[member.login].append(team.name)

# Save the mapping to a CSV file
output_filename = 'user_team_mapping.csv'
with open(output_filename, mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Write header
    writer.writerow(['Username', 'Teams'])
    # Write user-team mappings
    for username in usernames:
        teams = user_team_mapping.get(username, [])
        row = [username] + teams
        writer.writerow(row)

# Output the mapping (optional)
for username in usernames:
    teams = user_team_mapping.get(username, [])
    print(f"User: {username}, Teams: {', '.join(teams) if teams else 'No team found'}")
