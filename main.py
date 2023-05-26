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
            mlbTeamKeys[team.get('name', '')] = team.get('id', -1)
    return mlbTeamKeys

def printTeams(mlbTeamKeys):
    for index, team in enumerate(sorted(mlbTeamKeys)):
        print(index+1, team)



def calculateDates():
    current_date = datetime.now().date()
    end_date = current_date - timedelta(days=1)
    beginning_date = end_date - relativedelta(months=1)
    print("End Date:", end_date)
    print("Beginning Date:", beginning_date)
    return beginning_date, end_date

def fetchSchedule(mlbTeamKeys, teamSelection, beginning_date, end_date):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={mlbTeamKeys[teamSelection]}&startDate={beginning_date}&endDate={end_date}"
    response = requests.get(url)
    data = response.json()
    return data

def createGameKeyDict(data):
    gameKeyDict = {}
    for dateDict in data['dates']:
        if dateDict['totalGames'] == 1:
            gameKeyDict[dateDict['date']] = [dateDict['games'][0]['gamePk']]
        else:
            gameKeyDict[dateDict['date']] = []
            for game in range(dateDict['totalGames']):
                gameKeyDict[dateDict['date']].append(dateDict['games'][game]['gamePk'])
    return gameKeyDict

def createPlayerIDDict(mlbTeamKeys, teamSelection):
    playerIDDict = {}
    print(f"Getting roster for {teamSelection}")
    url = f"https://statsapi.mlb.com/api/v1/teams/{mlbTeamKeys[teamSelection]}/roster/fullRoster?season=2023"
    response = requests.get(url)
    data = response.json()
    playerIDDict[teamSelection] = {'hitters' : {}, 'pitchers' : {}}
    for player in data["roster"]:
        playerName = player['person']['fullName']
        playerID = player['person']['id']
        playerStatus = player['status']['code']
        playerPosition  = player['position']['abbreviation']

        if playerStatus == 'A':
            if playerPosition == 'P':
                playerIDDict[teamSelection]['pitchers'][playerName] = playerID
            else:
                playerIDDict[teamSelection]['hitters'][playerName] = playerID
    return playerIDDict

def pullRoster(gameID, teamSelection):
    url = f'https://statsapi.mlb.com/api/v1/game/{gameID}/boxscore'
    response = requests.get(url)
    data = response.json()

    teams = ['home', 'away']
    box_score = pd.DataFrame()

    for team in teams:
        team_data = data['teams'][team]
        team_name = team_data['team']['name']
        players = team_data['players']

        for player_id, player_data in players.items():
            if player_data['position']['abbreviation'] == 'P':
                continue

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

            box_score = pd.concat([box_score, player_row], ignore_index=True)

    columns = ['Team', 'Player', 'Batting Order', 'Position', 'AB', 'R', 'H', 'RBI', 'BB', 'SO', 'AVG']
    box_score = box_score[columns]

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

def createRosterSample(gameKeyDict, teamSelection):
    rosterSample = []
    for date in list(gameKeyDict.keys())[-5:]:
        print(f'pulling roster for {date}')
        rosterdf = pullRoster(gameKeyDict[date][0], teamSelection)
        rosterSample.append([player for player in rosterdf['Player'].to_list()])
    return rosterSample

def generateRoster(rosterSample, teamSelection):
    flattened_list = [item for sublist in rosterSample for item in sublist]
    counts = Counter(flattened_list)
    result = [element for element, count in counts.items() if count >= 3]
    roster = {teamSelection : result}
    print(roster)
    return roster

def getRosterForTeam(teamSelection):
    mlbTeamKeys = findTeamKeys()
    beginning_date, end_date = calculateDates()
    data = fetchSchedule(mlbTeamKeys, teamSelection, beginning_date, end_date)
    gameKeyDict = createGameKeyDict(data)
    playerIDDict = createPlayerIDDict(mlbTeamKeys, teamSelection)
    rosterSample = createRosterSample(gameKeyDict, teamSelection)
    roster = generateRoster(rosterSample, teamSelection)


    return roster[teamSelection]

def main():
    mlbTeamKeys = findTeamKeys()
    printTeams(mlbTeamKeys)
    teamSelection = "Chicago Cubs"
    beginning_date, end_date = calculateDates()
    data = fetchSchedule(mlbTeamKeys, teamSelection, beginning_date, end_date)
    gameKeyDict = createGameKeyDict(data)
    playerIDDict = createPlayerIDDict(mlbTeamKeys, teamSelection)
    rosterSample = createRosterSample(gameKeyDict, teamSelection)
    roster = generateRoster(rosterSample, teamSelection)

    print(roster)

if __name__ == '__main__':
    main()

