import requests
from pprint import pprint
import pandas as pd
# Set the player ID
player_id = 668731  # Mike Trout's player ID
year = 2023

# Set the game ID
game_id = 718027

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
            print(home_pitcher_id)
            # Print the names of the starting pitchers
            print("Starting pitcher for the home team: ", home_pitcher_name)
            return home_pitcher_name, home_pitcher_id
    else:
        print("Failed to fetch data")
findPitcherForGame(718667, "Detroit Tigers")

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
            "Opposing Pitcher" : [],
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
            opp_pitcher_name, opp_pitcher_id = findPitcherForGame(game_id, gamelog['opponent']['name'])
            statLog["Opposing Pitcher"].append(opp_pitcher_name)

        return pd.DataFrame(statLog)

    else:
        print("Failed to fetch data")

#print(grabHitterGamelog(player_id, year))
# Set the player ID
player_id = 666214  # Justin Verlander's player ID
year = 2023

def grabPitcherGamelog(player_id, year):
    # Create the URL
    url = f"https://statsapi.mlb.com/api/v1/people?personIds={player_id}&season={year}&hydrate=stats(type=gameLog,season={year},gameType=R)"
    # Fetch the player's gamelog for the year
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Retrieve the stats from the response
        gamelogs = data['people'][0]['stats'][0]['splits']
        
        # Loop through the gamelogs
        statLog = {
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
            "H/9" : []
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


        return pd.DataFrame(statLog)

    else:
        print("Failed to fetch data")

print(grabPitcherGamelog(player_id, year))


