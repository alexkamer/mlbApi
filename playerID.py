import requests

def findTeamKeys():
    mlbTeamKeys = {}
    url = "https://statsapi.mlb.com/api/v1/teams/"
    response = requests.get(url)
    data = response.json()
    for team in data['teams']:

        if team.get('sport', {}).get('name', '') == "Major League Baseball":
            print()
            mlbTeamKeys[team.get('name', '')] = team.get('id', -1)
    return mlbTeamKeys.keys()

