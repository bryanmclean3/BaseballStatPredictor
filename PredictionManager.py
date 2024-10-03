import statsapi as sa
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.error import HTTPError
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder


def addGameStats(opponent, game_stats):
    runs = game_stats['batting']['runs']
    hits = game_stats['batting']['hits']
    doubles = game_stats['batting']['doubles']
    triples = game_stats['batting']['triples']
    homeRuns = game_stats['batting']['homeRuns']
    rbi = game_stats['batting']['rbi']
    walks = game_stats['batting']['baseOnBalls']
    Ks = game_stats['batting']['strikeOuts']

    return opponent, runs, hits, doubles, triples, homeRuns, rbi, walks, Ks


today = date.today().strftime("%Y-%m-%d")
allowed_game_types = {'R', 'P', 'F', 'D', 'L', 'W', 'C', 'N'}
playername = sa.lookup_player('Jose Altuve')

team_schedule = sa.schedule(
    team=playername[0]['currentTeam']['id'],
    start_date=sa.latest_season()['regularSeasonStartDate'],
    end_date=today
)

prev_games = [
    game for game in team_schedule
    if game['status'] == 'Final' and game['game_type'] in allowed_game_types
]


def fetch_game_stats(game):
    game_id = game['game_id']
    game_date = game['game_date']
    player_stats = sa.boxscore_data(game_id)

    if player_stats['teamInfo']['away']['id'] == playername[0]['currentTeam']['id']:
        opponent = game['home_name']
        game_stats = player_stats['away']['players']['ID' + str(playername[0]['id'])]['stats']
    else:
        opponent = game['away_name']
        game_stats = player_stats['home']['players']['ID' + str(playername[0]['id'])]['stats']

    if game_stats['batting']:
        return addGameStats(opponent, game_stats)


with ThreadPoolExecutor() as executor:
    try:
        rows = list(executor.map(fetch_game_stats, prev_games))
    except HTTPError:
        print("Error fetching")


rows = [row for row in rows if row is not None]

columns = ['opponent', 'Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Ks']
stats_df = pd.DataFrame(rows, columns=columns)

X_train = stats_df['opponent']
y_train = stats_df[['Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Ks']]

encoder = OneHotEncoder(drop='first')
X_encoded = encoder.fit_transform(X_train.values.reshape(-1, 1)).toarray()

next_opponent = 'Pittsburgh Pirates'

ridge = Ridge(alpha=1)

ridge.fit(X_encoded, y_train)
new_opponent = pd.DataFrame({'opponent': [next_opponent]})
new_X_encoded = encoder.transform(new_opponent['opponent'].values.reshape(-1, 1)).toarray()
predicted_stats = ridge.predict(new_X_encoded)

predicted_stats_df = pd.DataFrame(predicted_stats, columns=['Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Ks'])
predicted_stats_df.insert(0, 'opponent', next_opponent)

print(predicted_stats_df)



