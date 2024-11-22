import csv

# -------------------- Configuration --------------------

# Input CSV files
USER_TEAM_CSV = 'user_team.csv'  # Replace with your user-team CSV file path
REPO_INFO_CSV = 'repo_info.csv'  # Replace with your repo info CSV file path

# Output CSV file
OUTPUT_CSV = 'repo_info_with_teams.csv'

# -------------------- Script --------------------

def main():
    # Read the user-team CSV and build a mapping from username to real team
    user_team_mapping = {}
    with open(USER_TEAM_CSV, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row['username'].strip()
            real_team = row['real team'].strip()
            user_team_mapping[username] = real_team

    # Read the repo info CSV and process each row
    data = []
    with open(REPO_INFO_CSV, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames + ['Contributor Team']
        for row in reader:
            top_contributors = row['Top Contributors']
            contributor_teams = []
            if top_contributors and top_contributors.strip() != '':
                contributors = [u.strip() for u in top_contributors.split(',')]
                for username in contributors:
                    real_team = user_team_mapping.get(username, 'Unknown')
                    contributor_teams.append(real_team)
                # Remove duplicates and sort
                unique_teams = sorted(set(contributor_teams))
                contributor_team_str = ', '.join(unique_teams)
            else:
                contributor_team_str = 'No contributors found'

            # Add the new column to the row
            row['Contributor Team'] = contributor_team_str
            data.append(row)

    # Write the updated data to the output CSV
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"Data written to '{OUTPUT_CSV}'.")

# -------------------- Entry Point --------------------

if __name__ == '__main__':
    main()
