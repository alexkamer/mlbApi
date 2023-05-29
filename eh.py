from flask import Flask, render_template, jsonify, request, redirect, url_for
from main import findTeamKeys, calculateDates, fetchSchedule, createGameKeyDict, createPlayerIDDict, pullRoster, createRosterSample, generateRoster, printTeams,getRosterForTeam, grabHitterGamelog
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    mlb_teams = list(findTeamKeys().keys())

    if request.method == 'POST':
        teamSelection = request.form.get('team')
        playerSelection = request.form.get('player')

        roster = getRosterForTeam(teamSelection)
        game_log_df = grabHitterGamelog(playerSelection, 2023)

        tables = [game_log_df.to_html(classes='data', header=True, index=False)]

        # Do something with the selected_choice variable
        return render_template('test.html', tables=tables, team_names=mlb_teams)
    else:
        return render_template('test.html', team_names=mlb_teams)

@app.route('/get_players', methods=['POST'])
def get_players():
    teamSelection = request.form['team']
    players = getRosterForTeam(teamSelection)

    return {'players' : players}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
