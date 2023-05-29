import requests
from collections import Counter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import logging as log
from pprint import pprint

year = 2023

logLevel = 'INFO'
log.basicConfig(level=logLevel,format="%(asctime)s :: %(levelname)s :: %(message)s", datefmt='%Y-%m-%d-%H-%M-%S')



# Will return a dictionary with key pairs of the MLB team and their key number
# Ex. response: {'Los Angeles Angels': 108, 'Arizona Diamondbacks': 109, 'Baltimore Orioles': 110...}
def findTeamKeys():
    mlbTeamKeys = {}
    url = "https://statsapi.mlb.com/api/v1/teams/"
    response = requests.get(url)
    data = response.json()
    for team in data['teams']:
        if team.get('sport', {}).get('name', '') == "Major League Baseball":
            mlbTeamKeys[team.get('name', '')] = team.get('id', -1)
    return mlbTeamKeys
#print(findTeamKeys())
#prints a sorted display of the mlb teams
def printTeams(mlbTeamKeys):
    for index, team in enumerate(sorted(mlbTeamKeys)):
        print(index+1, team)

def normalize_stat(stat, min_stat, max_stat):
    normalized_stat = (stat - min_stat) / (max_stat - min_stat)
    return normalized_stat


# Creates the dateframe of which you want your mlb game id keys
# Currently the end_date is whatever day was yesterday and the beginning_date is exactly a month prior
def calculateDates():
    current_date = datetime.now().date()
    end_date = current_date - timedelta(days=1)
    beginning_date = end_date - relativedelta(months=1)
    print("End Date:", end_date)
    print("Beginning Date:", beginning_date)
    return beginning_date, end_date

# Will return the json schedule of a specified team from the MLB's API for a given date range
def fetchSchedule(mlbTeamKeys, teamSelection, beginning_date, end_date):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={mlbTeamKeys[teamSelection]}&startDate={beginning_date}&endDate={end_date}"
    response = requests.get(url)
    data = response.json()
    return data

# Creates a dictionary where the keys are dates and the values are lists of game IDs for the games played on that date
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

# Retrieves the full roster of a specified team from the MLB's API, categorizing players as hitters or pitchers
# Returns a dictionary with this type of hierarchy ['Team Name']['hitters/pitchers']['Player's Name']
# Calling the player's name will return his player ID
def createPlayerIDDict(mlbTeamKeys, teamSelection):
    playerIDDict = {}
    log.debug(f"Getting roster for {teamSelection}")
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
temp = createPlayerIDDict(findTeamKeys(), 'Pittsburgh Pirates')
temp = temp['Pittsburgh Pirates']['pitchers']['Mitch Keller']
print(temp)
# Retrieves the full roster of a specified team from the MLB's API, categorizing players as hitters or pitchers
# Excludes Pinch Hitters 
# Only pulls the box score for the team requested not both teams
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
                'ID' : [player_data['person']['id']],
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

    columns = ['Team', 'Player', 'ID', 'Batting Order', 'Position', 'AB', 'R', 'H', 'RBI', 'BB', 'SO', 'AVG']
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

# Pulls the team's last 5 games and creates a list of players who have started
def createRosterSample(gameKeyDict, teamSelection):
    rosterSample = []
    for date in list(gameKeyDict.keys())[-5:]:
        log.debug(f'pulling roster for {date}')
        rosterdf = pullRoster(gameKeyDict[date][0], teamSelection)
        rosterSample.append([player for player in rosterdf['Player'].to_list()])
    return rosterSample

# Takes the roster sample and creates a list containing players who have player atleast 3/5 of the last 5 games
# Returns dictionary in the format: {"Team Name" : [player1,player2,player3,...]}
def generateRoster(rosterSample, teamSelection):
    flattened_list = [item for sublist in rosterSample for item in sublist]
    counts = Counter(flattened_list)
    result = [element for element, count in counts.items() if count >= 3]
    roster = {teamSelection : result}
    return roster

# Returns a list of the roster for selected the selected team
def getRosterForTeam(teamSelection):
    mlbTeamKeys = findTeamKeys()
    beginning_date, end_date = calculateDates()
    data = fetchSchedule(mlbTeamKeys, teamSelection, beginning_date, end_date)
    gameKeyDict = createGameKeyDict(data)
    playerIDDict = createPlayerIDDict(mlbTeamKeys, teamSelection)
    rosterSample = createRosterSample(gameKeyDict, teamSelection)
    roster = generateRoster(rosterSample, teamSelection)


    return roster[teamSelection]

# Used for the sake of finding matchups for games
# Will return the starting pitcher and their player ID for a selected team
def findPitcherForGame(game_id, teamWanted):
    # Create the URL
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
    # Fetch the game data
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Retrieve the starting pitchers from the response
        away_pitcher_id = data['liveData']['boxscore']['teams']['away']['pitchers'][0]
        home_pitcher_id = data['liveData']['boxscore']['teams']['home']['pitchers'][0]
        away_pitcher_name = data['liveData']['boxscore']['teams']['away']['players'][f"ID{away_pitcher_id}"]["person"]['fullName']
        home_pitcher_name = data['liveData']['boxscore']['teams']['home']['players'][f"ID{home_pitcher_id}"]["person"]['fullName']
        home_team = data['gameData']['teams']['home']['name']
        away_team = data['gameData']['teams']['away']['name']


        if away_team == teamWanted:
            print("Away team: ", away_team)
            print("Starting pitcher for the away team: ", away_pitcher_name)
            
            return away_pitcher_name, away_pitcher_id
        elif home_team == teamWanted:    
            print("Home team: ", home_team)
            # Print the names of the starting pitchers
            print("Starting pitcher for the home team: ", home_pitcher_name)
            return home_pitcher_name, home_pitcher_id
    else:
        print("Failed to fetch data")

# Returns the player's full season gamelog in the form of a dictionary
# Much quicker and only takes one api per player call compared to advanced
def grabHitterGamelog(player_id, year):

    # Create the URL
    url = f"https://statsapi.mlb.com/api/v1/people?personIds={player_id}&season={year}&hydrate=stats(type=gameLog,season={year},gameType=R)"

    # Fetch the player's gamelog for the year
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Retrieve the stats from the response
        gamelogs = data['people'][0]['stats'][0]['splits']
        #pprint(gamelogs)
        # Loop through the gamelogs
        statLog = {
            "Game ID" : [],
            "Player Name" : [],
            "Team" : [],
            "Date" : [],
            "Opponent" : [],
            "AB" : [],
            "R" : [],
            "H" : [],
            "HR" : [],
            "RBI" : [],
            "SO" : [],
            "AVG" : [],
            "2B" : [],
            "3B" : []
        }
        for gamelog in gamelogs:
            game_id = gamelog['game']['gamePk']
            statLog["Game ID"].append(gamelog['game']['gamePk'])
            statLog["Player Name"].append(gamelog['player']['fullName'])
            statLog["Team"].append(gamelog["team"]['name'])
            statLog["Date"].append(gamelog['date'])
            statLog["Opponent"].append(gamelog['opponent']['name'])
            statLog["AB"].append(gamelog['stat']['atBats'])
            statLog["R"].append(gamelog['stat']['runs'])
            statLog["H"].append(gamelog['stat']['hits'])
            statLog["HR"].append(gamelog['stat']['homeRuns'])
            statLog["RBI"].append(gamelog['stat']['rbi'])
            statLog["SO"].append(gamelog['stat']['strikeOuts'])
            statLog["AVG"].append('{:.3f}'.format(float(gamelog['stat']['avg'])))
            statLog["2B"].append(gamelog['stat']['doubles'])
            statLog["3B"].append(gamelog['stat']['triples'])

        return statLog
        #return pd.DataFrame(statLog)

    else:
        print("Failed to fetch data")


def pitcher_grade(game_stats):
    # Assume game_stats is a dictionary with keys:
    # 'IP', 'ERA', 'WHIP', 'K/9', 'BB/9', 'H/9'
    
    # Define the maximum possible value for each statistic. These are somewhat arbitrary
    # and can be adjusted as necessary.
    max_values = {
        'IP': 9,  # Assuming a 9 inning game
        'ERA': 27,  # Maximum ERA occurs if a pitcher allows 3 runs per inning
        'WHIP': 3,  # Arbitrary max WHIP
        'K/9': 27,  # Maximum K/9 occurs if a pitcher strikes out every batter
        'BB/9': 27,  # Maximum BB/9 occurs if a pitcher walks every batter
        'H/9': 27  # Maximum H/9 occurs if a pitcher gives up a hit to every batter
    }
    
    # Initialize the total grade to zero
    total_grade = 0

    # For each stat, subtract the player's stat from the max possible value (to invert the scale for ERA, WHIP, BB/9, H/9),
    # divide by the max possible value (to normalize to a scale from 0 to 1),
    # and then multiply by 100 (to convert to a scale from 0 to 100).
    # Add this to the total grade.
    for stat, max_value in max_values.items():
        if stat in ['ERA', 'WHIP', 'BB/9', 'H/9']:
            total_grade += ((max_value - game_stats[stat]) / max_value) * 100
        else:  # For IP and K/9, higher is better, so we don't need to invert the scale
            total_grade += (game_stats[stat] / max_value) * 100
    
    # Since there are six stats, divide the total grade by 6 to get the average.
    average_grade = total_grade / 6
    
    return average_grade



#Returns pandas series of the pitcher's gamelog
def grabPitcherGamelog(player_id, year):
    # Create the URL
    url = f"https://statsapi.mlb.com/api/v1/people?personIds={player_id}&season={year}&hydrate=stats(type=gameLog,season={year},gameType=R)"
    #print(url)
    # Fetch the player's gamelog for the year
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Retrieve the stats from the response
        gamelogs = data['people'][0]['stats'][0]['splits']
        
        # Loop through the gamelogs
        statLog = {
            "Grade" : [],
            "Date" : [],
            "Opponent" : [],
            "Innings Pitched" : [],
            "Earned Runs" : [],
            "Hits" : [],
            "Strikeouts" : [],
            "PO" : [],
            "Walks" : [],
            "Home Runs" : [],
            "ERA" : [],
            "PC" : [],
            "K/9" : [],
            "BB/9" : [],
            "H/9" : [],
            "WHIP" : [],
            "AVG" : [],
            "K/BB Ratio" : []
        }
        for gamelog in gamelogs:
            statLog["Date"].append(gamelog['date'])
            statLog["Opponent"].append(gamelog['opponent']['name'])
            statLog["Innings Pitched"].append(gamelog['stat']['inningsPitched'])
            statLog["Earned Runs"].append(gamelog['stat']['earnedRuns'])
            statLog["Hits"].append(gamelog['stat']['hits'])
            statLog["Strikeouts"].append(gamelog['stat']['strikeOuts'])
            statLog["PO"].append(gamelog['stat']['outs'])
            statLog["Walks"].append(gamelog['stat']['baseOnBalls'])
            statLog["Home Runs"].append(gamelog['stat']['homeRuns'])
            statLog["ERA"].append(gamelog['stat']['era'])
            statLog["PC"].append(gamelog['stat']['numberOfPitches'])
            statLog["K/9"].append(gamelog['stat']['strikeoutsPer9Inn'])
            statLog["BB/9"].append(gamelog['stat']['walksPer9Inn'])
            statLog["H/9"].append(gamelog['stat']['hitsPer9Inn'])
            statLog["WHIP"].append(gamelog['stat']['whip'])

            avg = float(gamelog['stat']['avg'])
            statLog["AVG"].append(avg)

            batters_faced = gamelog['stat']['battersFaced']
            strikeouts = gamelog['stat']['strikeOuts']
            walks = gamelog['stat']['baseOnBalls']
            hits_allowed = gamelog['stat']['hits']
            num_pitches = gamelog['stat']['numberOfPitches']
            era = float(gamelog['stat']['era'])
            innings_pitched = float(gamelog['stat']['inningsPitched'])
            earned_runs = gamelog['stat']['earnedRuns']
            whip = float(gamelog['stat']['whip'])
            pitching_outs = gamelog['stat']['outs']
            try: strikeout_walk_ratio = float(gamelog['stat']['strikeoutWalkRatio'])
            except ValueError: strikeout_walk_ratio = strikeouts
            statLog["K/BB Ratio"].append(strikeout_walk_ratio)
            
            
            try: kp9 = float(gamelog['stat']['strikeoutsPer9Inn'])
            except ValueError: kp9 = 0
            
            
            try: bbp9 = float(gamelog['stat']['walksPer9Inn'])
            except ValueError: bbp9 = 0
            
            try: hp9 = float(gamelog['stat']['hitsPer9Inn'])
            except ValueError: hp9 = 0
            game_stats = {
                'K/9' : kp9,
                'BB/9': bbp9, 
                'WHIP': whip,  # Walks and hits per innings pitched
                'ERA': era,  # Earned run average
                'IP': innings_pitched,  # Innings pitched
                'H/9': hp9,  # Total hits allowed
            }



            statLog["Grade"].append(pitcher_grade(game_stats))
        try: return pd.DataFrame(statLog)
        except ValueError: return statLog 
    else:
        print("Failed to fetch data")

#print(grabPitcherGamelog(592332, 2023))


# Similar to grabHitterGamelog except it includes an extra api call per game due to examining the pitcher to see if they had a good game
def grabAdvancedHitterGamelog(player_id, year):
    # Create the URL
    url = f"https://statsapi.mlb.com/api/v1/people?personIds={player_id}&season={year}&hydrate=stats(type=gameLog,season={year},gameType=R)"
    print(url)
    # Fetch the player's gamelog for the year
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Retrieve the stats from the response
        gamelogs = data['people'][0]['stats'][0]['splits']
        #pprint(gamelogs)
        # Loop through the gamelogs
        statLog = {
            "Game ID" : [],
            "Player Name" : [],
            "Team" : [],
            "H/A" : [],
            "Team Win?" : [],
            "Date" : [],
            "Opponent" : [],
            "Opposing Pitcher" : [],
            "Opposing Pitcher Grade" : [],
            "AB" : [],
            "R" : [],
            "H" : [],
            "HR" : [],
            "RBI" : [],
            "SO" : [],
            "AVG" : [],
            "2B" : [],
            "3B" : [],
            "Pitches per AB" : []

        }
        for gamelog in gamelogs:
            game_id = gamelog['game']['gamePk']
            statLog["Game ID"].append(gamelog['game']['gamePk'])
            statLog["Player Name"].append(gamelog['player']['fullName'])
            statLog["Team"].append(gamelog["team"]['name'])
            statLog["H/A"].append('H' if gamelog['isHome'] else 'A')
            statLog["Team Win?"].append(gamelog['isWin'])
            statLog["Date"].append(gamelog['date'])
            statLog["Opponent"].append(gamelog['opponent']['name'])
            statLog["AB"].append(gamelog['stat']['atBats'])
            statLog["R"].append(gamelog['stat']['runs'])
            statLog["H"].append(gamelog['stat']['hits'])
            statLog["HR"].append(gamelog['stat']['homeRuns'])
            statLog["RBI"].append(gamelog['stat']['rbi'])
            statLog["SO"].append(gamelog['stat']['strikeOuts'])
            statLog["AVG"].append('{:.3f}'.format(gamelog['stat']['hits'] / gamelog['stat']['atBats'] if gamelog['stat']['atBats'] > 0 else 0))
            statLog["2B"].append(gamelog['stat']['doubles'])
            statLog["3B"].append(gamelog['stat']['triples'])

            #API Call
            opp_pitcher_name, opp_pitcher_id = findPitcherForGame(game_id, gamelog['opponent']['name'])
            statLog["Opposing Pitcher"].append(opp_pitcher_name)
            try:
                statLog["Pitches per AB"].append(round(gamelog['stat']['numberOfPitches'] / gamelog['stat']['atBats'] / gamelog['stat']['gamesPlayed'],1))
            except:
                statLog["Pitches per AB"].append(0)

            opp_pitcher_log = pd.DataFrame(grabPitcherGamelog(opp_pitcher_id, year))
            gradeValue = round(opp_pitcher_log.loc[opp_pitcher_log['Date'] == gamelog['date'], 'Grade'].to_list()[0],2)
            statLog['Opposing Pitcher Grade'].append(gradeValue)
        return statLog
        #return pd.DataFrame(statLog)

    else:
        print("Failed to fetch data")

print(pd.DataFrame(grabAdvancedHitterGamelog(668731, 2023)))

#Play by play for exact game
def inDepthGameInfo(game_id):
    # Create the URL
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
    # Fetch the game data
    response = requests.get(url)
    data = response.json()

    playByPlay = data["liveData"]["plays"]["allPlays"]
    playByPlayDict = {
        "Description" : [],
        "Inning" : [],
        "Pitch Count" : [],
        "Accumulated Pitch Count" : [],
        "Batter" : [],
        "Pitcher" : [],
        "Pitch Hand" : [],
        "Bat Side" : []

    }
    pitcherPCDict = {}
    for play in playByPlay: 
        playByPlayDict["Description"].append(play["result"]["description"])
        playByPlayDict["Inning"].append(f"{play['about']['halfInning']} {play['about']['inning']}")
        playByPlayDict["Pitch Count"].append(play["playEvents"][-1].get("pitchNumber", 0))
        playByPlayDict["Batter"].append(play["matchup"]["batter"]["fullName"])
        playByPlayDict["Pitcher"].append(play["matchup"]["pitcher"]["fullName"])
        pitcherName = play["matchup"]["pitcher"]["fullName"]
        if pitcherName not in pitcherPCDict:
            pitcherPCDict[pitcherName] = 0
        pitcherPCDict[pitcherName] += play["playEvents"][-1].get("pitchNumber", 0)

        playByPlayDict["Accumulated Pitch Count"].append(pitcherPCDict[pitcherName])
        playByPlayDict["Pitch Hand"].append(play["matchup"]['pitchHand']['code'])
        playByPlayDict["Bat Side"].append(play["matchup"]['batSide']['code'])


    print(pd.DataFrame(playByPlayDict))
    print(pitcherPCDict)

#inDepthGameInfo(718006)



