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
        display_name = row[1].strip()
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
        team_name = row[0].strip()
        members = [member.strip() for member in row[1:] if member.strip()]
        team_members[team_name] = members

# Prepare a list of member names from the second CSV for matching
second_csv_member_names = set()
for members in team_members.values():
    second_csv_member_names.update(members)
second_csv_member_names = list(second_csv_member_names)  # Convert back to list for rapidfuzz

# Map users to their real teams
for user in users:
    display_name = user['display_name']
    real_teams = set()

    if not display_name:
        user['real_team'] = 'No display name'
        continue  # Skip users without a display name

    match_found = False  # Flag to indicate if a match has been found

    # Step 1: Exact match on full display name
    if display_name in second_csv_member_names:
        for team_name, members in team_members.items():
            if display_name in members:
                real_teams.add(team_name)
        match_found = True

    # Step 2: Fuzzy match on full display name
    if not match_found:
        best_match = process.extractOne(
            display_name, second_csv_member_names, scorer=fuzz.token_set_ratio
        )
        if best_match and best_match[1] >= 90:  # Adjust threshold as needed
            matched_name = best_match[0]
            for team_name, members in team_members.items():
                if matched_name in members:
                    real_teams.add(team_name)
            match_found = True

    # Step 3: Exact match on last name
    if not match_found:
        name_parts = display_name.split()
        if len(name_parts) >= 2:
            last_name = name_parts[-1]
            matching_members = [
                member for member in second_csv_member_names
                if member.split()[-1].lower() == last_name.lower()
            ]
            if matching_members:
                for matched_name in matching_members:
                    for team_name, members in team_members.items():
                        if matched_name in members:
                            real_teams.add(team_name)
                match_found = True

    # Step 4: Fuzzy match on last name
    if not match_found and len(name_parts) >= 2:
        last_name = name_parts[-1]
        member_last_names = [member.split()[-1] for member in second_csv_member_names]
        best_match = process.extractOne(
            last_name, member_last_names, scorer=fuzz.ratio
        )
        if best_match and best_match[1] >= 90:  # Adjust threshold as needed
            matched_last_name = best_match[0]
            matching_members = [
                member for member in second_csv_member_names
                if member.split()[-1] == matched_last_name
            ]
            for matched_name in matching_members:
                for team_name, members in team_members.items():
                    if matched_name in members:
                        real_teams.add(team_name)
            match_found = True

    # Step 5: Exact match on first name
    if not match_found:
        first_name = name_parts[0]
        matching_members = [
            member for member in second_csv_member_names
            if member.split()[0].lower() == first_name.lower()
        ]
        if matching_members:
            for matched_name in matching_members:
                for team_name, members in team_members.items():
                    if matched_name in members:
                        real_teams.add(team_name)
                match_found = True

    # Step 6: Fuzzy match on first name
    if not match_found:
        first_name = name_parts[0]
        member_first_names = [member.split()[0] for member in second_csv_member_names]
        best_match = process.extractOne(
            first_name, member_first_names, scorer=fuzz.ratio
        )
        if best_match and best_match[1] >= 90:  # Adjust threshold as needed
            matched_first_name = best_match[0]
            matching_members = [
                member for member in second_csv_member_names
                if member.split()[0] == matched_first_name
            ]
            for matched_name in matching_members:
                for team_name, members in team_members.items():
                    if matched_name in members:
                        real_teams.add(team_name)
            match_found = True

    # Assign real_team
    if real_teams:
        user['real_team'] = '/'.join(sorted(real_teams))
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
