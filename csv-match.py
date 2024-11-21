import csv
from rapidfuzz import process, fuzz

# File paths
first_csv_file = 'first.csv'   # The CSV file with username, display name, team1, team2, ...
second_csv_file = 'second.csv' # The CSV file with team name, member1, member2, ...
output_csv_file = 'final.csv'  # The output CSV file

# Read the first CSV file and build a list of users
users = []
with open(first_csv_file, mode='r', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)  # Skip the header row
    for row in reader:
        username = row[0]
        display_name = row[1]
        teams = row[2:]
        users.append({
            'username': username,
            'display_name': display_name,
            'teams': teams,
            'real_team': ''  # To be filled later
        })

# Read the second CSV file and build a mapping of team names to member names
team_members = {}
with open(second_csv_file, mode='r', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if not row:
            continue  # Skip empty rows
        team_name = row[0]
        members = row[1:]
        # Flatten member names into a single list
        team_members[team_name] = [member.strip() for member in members if member.strip()]

# Prepare a list of member names from the second CSV for matching
second_csv_member_names = []
for members in team_members.values():
    second_csv_member_names.extend(members)
second_csv_member_names = list(set(second_csv_member_names))  # Remove duplicates

# Function to find the best match for a display name
def find_best_match(name, choices):
    # Using partial_ratio to allow for partial matches
    match = process.extractOne(
        name, choices, scorer=fuzz.partial_ratio
    )
    return match  # Returns (matched_name, score, index)

# Map users to their real teams
for user in users:
    display_name = user['display_name']
    if not display_name:
        continue  # Skip users without a display name
    # Find the best match for the display name in the second CSV member names
    best_match = find_best_match(display_name, second_csv_member_names)
    if best_match and best_match[1] >= 80:  # Adjust threshold as needed
        matched_name = best_match[0]
        # Find the team(s) that this matched name belongs to
        matched_teams = []
        for team_name, members in team_members.items():
            if matched_name in members:
                matched_teams.append(team_name)
        if matched_teams:
            user['real_team'] = '; '.join(matched_teams)
    else:
        user['real_team'] = 'No match found'

# Write the output to the final CSV
with open(output_csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    # Write header
    header = ['Username', 'Display Name', 'Real Team'] + ['Team' + str(i+1) for i in range(len(users[0]['teams']))]
    writer.writerow(header)
    # Write user data
    for user in users:
        row = [user['username'], user['display_name'], user['real_team']] + user['teams']
        writer.writerow(row)

print(f"Final CSV file '{output_csv_file}' has been created.")
