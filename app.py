from flask import Flask, render_template, jsonify, request, redirect, url_for
from playerID import findTeamKeys, roster,teamSelection
import playerID
print(roster)
app = Flask(__name__)

mlb_teams = list(findTeamKeys().keys())
print(mlb_teams)

@app.route('/', methods=['GET', 'POST'])
def index():
    choices = mlb_teams  # List of choices

    if request.method == 'POST':
        selected_choice = request.form.get('choice')
        print(roster[selected_choice])

        # Do something with the selected_choice variable
        return f"You selected: {selected_choice}"
    
    return render_template('index.html', choices=choices)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
