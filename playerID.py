import requests
from collections import Counter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

year = 2023

def findTeamKeys():
    mlbTeamKeys = {}
    url = "https://statsapi.mlb.com/api/v1/teams/"
    response = requests.get(url)
    data = response.json()
    for team in data['teams']:

        if team.get('sport', {}).get('name', '') == "Major League Baseball":
            print()
            mlbTeamKeys[team.get('name', '')] = team.get('id', -1)
    return mlbTeamKeys

mlbTeamKeys = findTeamKeys()


for index, team in enumerate(sorted(mlbTeamKeys)):
    print(index+1, team)
#teamSelection = sorted(mlbTeamKeys)[int(input("Select a number to select what team you would like: "))-1]
teamSelection = "Texas Rangers"
print(teamSelection)




# Get the current date
current_date = datetime.now().date()

# Calculate the end date as the previous day
end_date = current_date - timedelta(days=1)

# Calculate the beginning date as exactly one month before the end date
beginning_date = end_date - relativedelta(months=1)

# Print the results
print("End Date:", end_date)
print("Beginning Date:", beginning_date)


#Pull json to get the game id's from startdate-enddate
url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={mlbTeamKeys[teamSelection]}&startDate={beginning_date}&endDate={end_date}"
response = requests.get(url)
data = response.json()

#Assign each date to their respective game key, if there was a double-header played on that date then both id's will be added
gameKeyDict = {}
for dateDict in data['dates']:

    if dateDict['totalGames'] == 1:
        gameKeyDict[dateDict['date']] = [dateDict['games'][0]['gamePk']]
    else:
        gameKeyDict[dateDict['date']] = []
        for game in range(dateDict['totalGames']):
            gameKeyDict[dateDict['date']].append(dateDict['games'][game]['gamePk'])



playerIDDict = {}
for team in mlbTeamKeys.keys():
    url = f"https://statsapi.mlb.com/api/v1/teams/{mlbTeamKeys[team]}/roster/fullRoster?season=2023"
    response = requests.get(url)
    data = response.json()
    playerIDDict[team] = {'hitters' : {}, 'pitchers' : {}}
    for player in data["roster"]:
        playerName = player['person']['fullName']
        playerID = player['person']['id']
        playerStatus = player['status']['code']
        playerPosition  = player['position']['abbreviation']


        if playerStatus == 'A':
            if playerPosition == 'P':
                playerIDDict[team]['pitchers'][playerName] = playerID
            else:
                playerIDDict[team]['hitters'][playerName] = playerID

#print(mlbTeamKeys)


def pullRoster(gameID):
    # Fetch the data
    url = f'https://statsapi.mlb.com/api/v1/game/{gameID}/boxscore'
    response = requests.get(url)
    data = response.json()

    # Prepare the teams
    teams = ['home', 'away']

    # Prepare an empty dataframe for the box score
    box_score = pd.DataFrame()

    # Loop over the teams
    for team in teams:
        # Get the team data
        team_data = data['teams'][team]

        # Get the team name
        team_name = team_data['team']['name']

        # Get the players
        players = team_data['players']

        # Loop over the players
        for player_id, player_data in players.items():
            # Skip if the player is a pitcher
            if player_data['position']['abbreviation'] == 'P':
                continue

            # Prepare a row for the player
            player_row = pd.DataFrame({
                'Team': [team_name],
                'Player': [player_data['person']['fullName']],
                'Batting Order' : [player_data.get('battingOrder', 'N/A')],
                'Position': [player_data['position']['abbreviation']],
                'AB': [player_data['stats']['batting'].get('atBats', 'N/A')],
                'R': [player_data['stats']['batting'].get('runs', 'N/A')],
                'H': [player_data['stats']['batting'].get('hits', 'N/A')],
                'RBI': [player_data['stats']['batting'].get('rbi', 'N/A')],
                'BB': [player_data['stats']['batting'].get('baseOnBalls', 'N/A')],
                'SO': [player_data['stats']['batting'].get('strikeOuts', 'N/A')],
                'AVG': [player_data['seasonStats']['batting'].get('avg', 'N/A')],
            })
            player_row['Batting Order'] = pd.to_numeric(player_row['Batting Order'], errors='coerce').astype('Int64')

            # Add the row to the box score
            box_score = pd.concat([box_score, player_row], ignore_index=True)

    # Set the column order
    columns = ['Team', 'Player', 'Batting Order', 'Position', 'AB', 'R', 'H', 'RBI', 'BB', 'SO', 'AVG']
    box_score = box_score[columns]




    # Display the box score
    box_score.replace('N/A', np.nan, inplace=True)
    box_score.dropna(inplace=True)

    df = pd.DataFrame(box_score)
    rosterdf = box_score[box_score['Team'] == teamSelection]
    rosterdf = rosterdf.sort_values('Batting Order')

    for index, value in rosterdf['Batting Order'].items():
        if value %100:
            rosterdf.loc[index, 'Position'] = 'PH'
    rosterdf = rosterdf.loc[rosterdf['Position'] != 'PH']

    return rosterdf



rosterSample = []

for date in list(gameKeyDict.keys())[-5:]:
    rosterdf = pullRoster(gameKeyDict[date][0])
    rosterSample.append([player for player in rosterdf['Player'].to_list()])
rosterSample
flattened_list = [item for sublist in rosterSample for item in sublist]
flattened_list
counts = Counter(flattened_list)
result = [element for element, count in counts.items() if count >= 3]


roster = {teamSelection : result}


print(roster)





