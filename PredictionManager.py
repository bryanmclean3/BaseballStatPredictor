import statsapi as sa
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.error import HTTPError
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder
# from BaseballStatPredictor.views import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.error import HTTPError
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder
import json
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from urllib.parse import quote_plus, urlencode
import requests


today = '2024-08-21'


def addBattingGameStats(opponent, game_stats):
    runs = game_stats['batting']['runs']
    hits = game_stats['batting']['hits']
    doubles = game_stats['batting']['doubles']
    triples = game_stats['batting']['triples']
    homeRuns = game_stats['batting']['homeRuns']
    rbi = game_stats['batting']['rbi']
    walks = game_stats['batting']['baseOnBalls']
    Ks = game_stats['batting']['strikeOuts']

    return opponent, runs, hits, doubles, triples, homeRuns, rbi, walks, Ks


# get necessary player pitching stats from each game stats
def addPitchingGameStats(opponent, game_stats):
    inningsPitched = game_stats['pitching']['inningsPitched']
    hits = game_stats['pitching']['hits']
    runs = game_stats['pitching']['runs']
    earnedRuns = game_stats['pitching']['earnedRuns']
    homeRuns = game_stats['pitching']['homeRuns']
    walks = game_stats['pitching']['baseOnBalls']
    Ks = game_stats['pitching']['strikeOuts']
    Ps = game_stats['pitching']['numberOfPitches']

    return opponent, inningsPitched, hits, runs, earnedRuns, homeRuns, walks, Ks, Ps


# get desired player's stats from the boxscore for a game
def fetch_batter_game_stats(game, player_id, playername):
    game_id = game['game_id']
    player_stats = sa.boxscore_data(game_id)

    if player_stats['teamInfo']['away']['id'] == playername[0]['currentTeam']['id']:
        opponent = game['home_name']
        players = player_stats['away']['players']
    else:
        opponent = game['away_name']
        players = player_stats['home']['players']

    player_key = 'ID' + str(player_id)
    if player_key in players:
        game_stats = players[player_key]['stats']
        if game_stats['batting']:
            return addBattingGameStats(opponent, game_stats)
    else:
        return None


# get desired player's stats from the boxscore for a game
def fetch_pitcher_game_stats(game, player_id, playername):
    game_id = game['game_id']
    player_stats = sa.boxscore_data(game_id)

    if player_stats['teamInfo']['away']['id'] == playername[0]['currentTeam']['id']:
        opponent = game['home_name']
        players = player_stats['away']['players']
    else:
        opponent = game['away_name']
        players = player_stats['home']['players']

    player_key = 'ID' + str(player_id)
    if player_key in players:
        game_stats = players[player_key]['stats']
        if game_stats['pitching']:
            return addPitchingGameStats(opponent, game_stats)
    else:
        return None

def player_stat_prediction(player_id):
    two_hundred_days_away = (date.today() + timedelta(days=200)).strftime("%Y-%m-%d")
    allowed_game_types = {'R', 'P', 'F', 'D', 'L', 'W', 'C', 'N'}
    playername = sa.lookup_player(player_id)

    url = "https://statsapi.mlb.com/api/v1/seasons?sportId=1&season=2024"

    response = requests.get(url)
    data = response.json()

    regular_season_start_date = data['seasons'][0]['regularSeasonStartDate']

    # regular_season_start_date = sa.latest_season()['regularSeasonStartDate']

    team_schedule = sa.schedule(
        team=playername[0]['currentTeam']['id'],
        start_date=regular_season_start_date,
        end_date=today
    )

    prev_games = [
        game for game in team_schedule
        if game['status'] == 'Final' and game['game_type'] in allowed_game_types
    ]

    batter_predicted_stats_dict = dict()
    pitcher_predicted_stats_dict = dict()

    if playername[0]['primaryPosition'][
        'abbreviation'] == 'P':  # or playername[0]['primaryPosition']['abbreviation'] == 'TWP':
        with ThreadPoolExecutor() as executor:
            try:
                rows = list(
                    executor.map(lambda game: fetch_pitcher_game_stats(game, player_id, playername), prev_games))
            except HTTPError:
                print("Error fetching")
        # rows = []
        # try:
        #     for game in prev_games:
        #         result = fetch_pitcher_game_stats(game, player_id, playername)
        #         rows.append(result)
        # except HTTPError:
        #     print("Error fetching")

        rows = [row for row in rows if row is not None]

        columns = ['Opponent', 'Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Home Runs Allowed',
                   'Walks', 'Strike Outs', 'Pitches Thrown']
        stats_df = pd.DataFrame(rows, columns=columns)

        X_train = stats_df['Opponent']
        y_train = stats_df[
            ['Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Home Runs Allowed', 'Walks',
             'Strike Outs', 'Pitches Thrown']]

        if X_train.values.size != 0:
            encoder = OneHotEncoder(handle_unknown='ignore')
            X_encoded = encoder.fit_transform(X_train.values.reshape(-1, 1)).toarray()

            schedule = sa.schedule(team=playername[0]['currentTeam']['id'], start_date=today,
                                   end_date=two_hundred_days_away)

            filtered_opponents = [game for game in schedule if game['game_type'] in allowed_game_types]

            next_opponent = filtered_opponents[0]

            if playername[0]['currentTeam']['id'] == next_opponent['away_id']:
                next_opponent = next_opponent['home_name']
            else:
                next_opponent = next_opponent['away_name']

            ridge = Ridge(alpha=1)

            ridge.fit(X_encoded, y_train)
            new_opponent = pd.DataFrame({'Opponent': [next_opponent]})
            new_X_encoded = encoder.transform(new_opponent['Opponent'].values.reshape(-1, 1)).toarray()
            predicted_stats = ridge.predict(new_X_encoded)

            predicted_stats_list = predicted_stats.tolist()

            predicted_stats_list = np.around(predicted_stats_list, 4).tolist()

            pitcher_predicted_stats_dict = {'Opponent': next_opponent,
                                            **dict(zip(columns[1:], predicted_stats_list[0]))}

    elif playername[0]['primaryPosition']['abbreviation'] != 'P':
        with ThreadPoolExecutor() as executor:
            try:
                rows = list(executor.map(lambda game: fetch_batter_game_stats(game, player_id, playername), prev_games))
            except HTTPError:
                print("Error fetching")

        # rows = []
        # try:
        #     for game in prev_games:
        #         result = fetch_batter_game_stats(game, player_id, playername)
        #         rows.append(result)
        # except HTTPError:
        #     print("Error fetching")

        rows = [row for row in rows if row is not None]

        columns = ['Opponent', 'Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Strike Outs']
        stats_df = pd.DataFrame(rows, columns=columns)

        X_train = stats_df['Opponent']
        y_train = stats_df[['Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Strike Outs']]

        if X_train.values.size != 0:
            encoder = OneHotEncoder(handle_unknown='ignore')
            X_encoded = encoder.fit_transform(X_train.values.reshape(-1, 1)).toarray()

            schedule = sa.schedule(team=playername[0]['currentTeam']['id'], start_date=today,
                                   end_date=two_hundred_days_away)

            filtered_opponents = [game for game in schedule if game['game_type'] in allowed_game_types]

            next_opponent = filtered_opponents[0]

            if playername[0]['currentTeam']['id'] == next_opponent['away_id']:
                next_opponent = next_opponent['home_name']
            else:
                next_opponent = next_opponent['away_name']

            ridge = Ridge(alpha=1)

            ridge.fit(X_encoded, y_train)
            new_opponent = pd.DataFrame({'Opponent': [next_opponent]})
            new_X_encoded = encoder.transform(new_opponent['Opponent'].values.reshape(-1, 1)).toarray()
            predicted_stats = ridge.predict(new_X_encoded)

            predicted_stats_list = predicted_stats.tolist()

            predicted_stats_list = np.around(predicted_stats_list, 4).tolist()

            batter_predicted_stats_dict = {'Opponent': next_opponent, **dict(zip(columns[1:], predicted_stats_list[0]))}

    predicted_stats_dict = batter_predicted_stats_dict.copy()
    predicted_stats_dict.update(pitcher_predicted_stats_dict)
    return predicted_stats_dict


playername = sa.lookup_player('ian happ')

print(playername)

game = sa.schedule(
    team=playername[0]['currentTeam']['id'],
    start_date='2024-07-26',
    end_date='2024-07-26'
)[0]

stats = fetch_batter_game_stats(game, playername[0]['id'], playername)
print(stats)





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
# playername = sa.lookup_player('Jose Altuve')
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
# X_train = stats_df['opponent']
# y_train = stats_df[['Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Ks']]
#
# encoder = OneHotEncoder(drop='first')
# X_encoded = encoder.fit_transform(X_train.values.reshape(-1, 1)).toarray()
#
# next_opponent = 'Pittsburgh Pirates'
#
# ridge = Ridge(alpha=1)
#
# ridge.fit(X_encoded, y_train)
# new_opponent = pd.DataFrame({'opponent': [next_opponent]})
# new_X_encoded = encoder.transform(new_opponent['opponent'].values.reshape(-1, 1)).toarray()
# predicted_stats = ridge.predict(new_X_encoded)
#
# predicted_stats_df = pd.DataFrame(predicted_stats, columns=['Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Ks'])
# predicted_stats_df.insert(0, 'opponent', next_opponent)
#
# print(predicted_stats_df)



