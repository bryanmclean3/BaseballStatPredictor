import statsapi as sa
from datetime import date
import pandas as pd

today = date.today().strftime("%Y-%m-%d")

# Get Aaron Judge season stats
playername = sa.lookup_player('Aaron Judge')
player = sa.player_stat_data(playername[0]['id'], 'hitting', 'season')

# print(player['stats'][0]['stats']['homeRuns'])

# ----------------------------------------------------------------------------------

# Get Aaron Judge stats for last 5 games
# reuse the playername variable to get player id
last_5_gameLogs = sa.player_stat_data(playername[0]['id'], 'hitting', 'gameLog')
last_5_games = last_5_gameLogs['stats'][-5:]

hits = 0
homeRuns = 0
rbis = 0
ks = 0
walks = 0
for recent_game in last_5_games:
    # print(f"Hits: {recent_game['stats']['hits']}")
    hits += recent_game['stats']['hits']
    # print(f"Home Runs: {recent_game['stats']['homeRuns']}")
    homeRuns += recent_game['stats']['homeRuns']
    # print(f"RBIs: {recent_game['stats']['rbi']}")
    rbis += recent_game['stats']['rbi']
    # print(f"Strikeouts: {recent_game['stats']['strikeOuts']}")
    ks += recent_game['stats']['strikeOuts']
    # print(f"Walks: {recent_game['stats']['baseOnBalls']}")
    walks += recent_game['stats']['baseOnBalls']

# print('Hits: ' + str(hits))
# print('Home Runs: ' + str(homeRuns))
# print('RBIS: ' + str(rbis))
# print('KS: ' + str(ks))
# print('Walks: ' + str(walks))

# ----------------------------------------------------------------------------------

# Get the list of matchups for Tuesday, September 17th
games = sa.schedule(start_date=today, end_date=today)
print(type(games))

# for game in games:
#     print("{} at {}".format(game['away_name'], game['home_name']))

# ----------------------------------------------------------------------------------

# Get Aaron Judge's stats for last 5 games against the Blue Jays
yankees_bluejays_schedule = sa.schedule(
    team=playername[0]['currentTeam']['id'],
    opponent=sa.lookup_team('blue jays')[0]['id'],
    start_date='2024-01-01',
    end_date=today
)

# last_n_games = yankees_bluejays_schedule[-5:]
#
# for game in last_n_games:
#     game_id = game['game_id']
#     game_date = game['game_date']
#
#     player_stats = sa.boxscore_data(game_id)
#     print(game_date)
#
#     # if yankees are away, search away dict for aaron judge's stats
#     if player_stats['teamInfo']['away']['id'] == playername[0]['currentTeam']['id']:
#         print(player_stats['away']['players']['ID' + str(playername[0]['id'])]['stats'])
#     else:
#         print(player_stats['home']['players']['ID' + str(playername[0]['id'])]['stats'])


# --------------------------------------------------------------------------------

game_types = sa.meta('gameTypes')

# Print all available game types
# for game_type in game_types:
#     print(f"ID: {game_type['id']}, Description: {game_type['description']}")


# def addGameStats(opponent, game_stats):
#     runs = game_stats['batting']['runs']
#     hits = game_stats['batting']['hits']
#     doubles = game_stats['batting']['doubles']
#     triples = game_stats['batting']['triples']
#     homeRuns = game_stats['batting']['homeRuns']
#     rbi = game_stats['batting']['rbi']
#     walks = game_stats['batting']['baseOnBalls']
#     Ks = game_stats['batting']['strikeOuts']
#
#     return opponent, runs, hits, doubles, triples, homeRuns, rbi, walks, Ks
#
#
# team_schedule = sa.schedule(
#         team=playername[0]['currentTeam']['id'],
#         start_date=sa.latest_season()['regularSeasonStartDate'],
#         end_date=today
#     )
#
# prev_games = [
#     game for game in team_schedule if game['status'] == 'Final' and game['game_type'] == 'R' or game['game_type'] == 'P' or game['game_type'] == 'F' or game['game_type'] == 'D' or game['game_type'] == 'L' or game['game_type'] == 'W' or game['game_type'] == 'C'
# ]
#
# rows = []
# for game in prev_games:
#     game_id = game['game_id']
#     game_date = game['game_date']
#
#     player_stats = sa.boxscore_data(game_id)
#
#     if player_stats['teamInfo']['away']['id'] == playername[0]['currentTeam']['id']:
#         opponent = game['home_name']
#         game_stats = player_stats['away']['players']['ID' + str(playername[0]['id'])]['stats']
#         if game_stats['batting']:
#             rows.append(addGameStats(opponent, game_stats))
#     else:
#         opponent = game['away_name']
#         game_stats = player_stats['home']['players']['ID' + str(playername[0]['id'])]['stats']
#         if game_stats['batting']:
#             rows.append(addGameStats(opponent, game_stats))
#
# columns = ['opponent', 'Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBis', 'Walks', 'Ks']
# stats_df = pd.DataFrame(rows, columns=columns)
#
# print(stats_df['Runs'].sum())


teams = sa.get('teams', {'sportIds': 1, 'activeStatus': 'Yes', 'fields': 'teams,name'})['teams']
# teams = sa.notes('teams')
# print(teams)

# ---------------------------------------------------
# maybe idk

import statsapi as sa
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.error import HTTPError
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_squared_error

# def addGameStats(opponent, game_stats):
#     runs = game_stats['batting']['runs']
#     hits = game_stats['batting']['hits']
#     doubles = game_stats['batting']['doubles']
#     triples = game_stats['batting']['triples']
#     homeRuns = game_stats['batting']['homeRuns']
#     rbi = game_stats['batting']['rbi']
#     walks = game_stats['batting']['baseOnBalls']
#     Ks = game_stats['batting']['strikeOuts']
#
#     return opponent, runs, hits, doubles, triples, homeRuns, rbi, walks, Ks
#
#
# today = date.today().strftime("%Y-%m-%d")
# allowed_game_types = {'R', 'P', 'F', 'D', 'L', 'W', 'C', 'N'}
# playername = sa.lookup_player('Aaron Judge')
#
# team_schedule = sa.schedule(
#     team=playername[0]['currentTeam']['id'],
#     start_date=sa.latest_season()['regularSeasonStartDate'],
#     end_date=today
# )
#
# prev_games = [
#     game for game in team_schedule
#     if game['status'] == 'Final' and game['game_type'] in allowed_game_types
# ]
#
#
# def fetch_game_stats(game):
#     game_id = game['game_id']
#     game_date = game['game_date']
#     player_stats = sa.boxscore_data(game_id)
#
#     if player_stats['teamInfo']['away']['id'] == playername[0]['currentTeam']['id']:
#         opponent = game['home_name']
#         game_stats = player_stats['away']['players']['ID' + str(playername[0]['id'])]['stats']
#     else:
#         opponent = game['away_name']
#         game_stats = player_stats['home']['players']['ID' + str(playername[0]['id'])]['stats']
#
#     if game_stats['batting']:
#         return addGameStats(opponent, game_stats)
#
#
# with ThreadPoolExecutor() as executor:
#     try:
#         rows = list(executor.map(fetch_game_stats, prev_games))
#     except HTTPError:
#         print("Error fetching")
#
#
# rows = [row for row in rows if row is not None]
#
# columns = ['opponent', 'Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Ks']
# stats_df = pd.DataFrame(rows, columns=columns)
#
# X = stats_df['opponent']
# y = stats_df[['Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Ks']]
#
#
# encoder = OneHotEncoder(drop='first')
# X_encoded = encoder.fit_transform(X.values.reshape(-1, 1)).toarray()
#
# # Train Ridge regression models for each target variable
# predictions = {}
# alpha_value = 1.0
#
# for stat in y.columns:
#     rr = Ridge(alpha=alpha_value)
#     rr.fit(X_encoded, y[stat])
#
#     # Predict on training data to evaluate performance
#     y_pred = rr.predict(X_encoded)
#     mse = mean_squared_error(y[stat], y_pred)
#     print(f"Mean Squared Error for {stat}: {mse:.2f}")
#
#     predictions[stat] = rr
#
# # Predicting stats for an upcoming game
# new_opponent = pd.DataFrame({'opponent': ['Pittsburgh Pirates']})
# new_X_encoded = encoder.transform(new_opponent['opponent'].values.reshape(-1, 1)).toarray()
#
# # Store predictions for the new opponent
# new_predictions = {}
#
# for stat in y.columns:
#     new_pred = predictions[stat].predict(new_X_encoded)
#     new_predictions[stat] = new_pred
#
# print("Predicted stats against the opponent:")
# for stat in y.columns:
#     print(f"{stat}: {new_predictions[stat]}")
