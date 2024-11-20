from github import Github
import csv

# Authenticate with your GitHub Personal Access Token (PAT)
g = Github("your_token_here")

# Get the organization
org = g.get_organization("your_organization")

# Get all members of the organization
members = org.get_members()

# Prepare a list of user information (username and display name)
user_info_list = [(member.login, member.name or '') for member in members]

# Prepare a dictionary to hold the mapping
user_team_mapping = {login: {'name': name, 'teams': []} for login, name in user_info_list}

# Convert the list of usernames to a set for faster lookup
usernames_set = set(login for login, _ in user_info_list)

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
            user_team_mapping[member.login]['teams'].append(team.name)

# Save the mapping to a CSV file
output_filename = 'user_team_mapping.csv'
with open(output_filename, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    # Write header
    writer.writerow(['Username', 'Display Name', 'Teams'])
    # Write user-team mappings
    for login, info in user_team_mapping.items():
        name = info['name']
        teams = info['teams']
        row = [login, name] + teams
        writer.writerow(row)

# Output the mapping (optional)
for login, info in user_team_mapping.items():
    name = info['name']
    teams = info['teams']
    print(f"User: {login}, Name: {name}, Teams: {', '.join(teams) if teams else 'No team found'}")
