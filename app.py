from flask import Flask, render_template, jsonify, request, redirect, url_for
from playerID import findTeamKeys
app = Flask(__name__)

def getTeams():
    return ['Team 1', 'Team 2', 'Team 3', 'Team 4']


@app.route('/')
def index():
    teams = findTeamKeys()
    return render_template('index.html', teams=teams)

@app.route('/second_function', methods=['POST'])
def second_function():
    selected_option = request.form['dropdown']
    # Process the selected option
    # ...
    # Redirect to some page when done
    return redirect(url_for('index'))  # assuming you have a route function named 'index'

if __name__ == '__main__':
    app.run(debug=True, port=8000) 