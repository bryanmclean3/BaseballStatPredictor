from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import statsapi as sa
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.error import HTTPError
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder


# Create your views here.

today = date.today().strftime("%Y-%m-%d")

# make API call to get players matching search query
def search_mlb_players(query):
    players = sa.lookup_player(query)
    players = get_player_information(players)
    return players


# get necessary information from API response
def get_player_information(player_list):
    players = []
    for player in player_list:
        player_info = dict()
        player_info['fullName'] = player['fullName']
        player_info['primaryPosition'] = player['primaryPosition']['abbreviation']
        player_info['playerId'] = player['id']
        player_info['teamName'] = sa.get('team', {'teamId': player['currentTeam']['id']})['teams'][0]['name']
        players.append(player_info)
    return players


# send player search results to UI
def player_search(request):
    query = request.GET.get('q', '')
    players = []

    if query:
        players = search_mlb_players(query)

    return render(request, 'player_search.html', {'players': players, 'query': query})

@require_GET
def get_player_prediction(request):
    player_name = request.GET.get('fullName')

    stats = player_stat_prediction(player_name)

    return JsonResponse({'stats': stats})


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

    team_schedule = sa.schedule(
        team=playername[0]['currentTeam']['id'],
        start_date=sa.latest_season()['regularSeasonStartDate'],
        end_date=today
    )

    prev_games = [
        game for game in team_schedule
        if game['status'] == 'Final' and game['game_type'] in allowed_game_types
    ]

    batter_predicted_stats_dict = dict()
    pitcher_predicted_stats_dict = dict()

    if playername[0]['primaryPosition']['abbreviation'] == 'P':  # or playername[0]['primaryPosition']['abbreviation'] == 'TWP':
        with ThreadPoolExecutor() as executor:
            try:
                rows = list(executor.map(lambda game: fetch_pitcher_game_stats(game, player_id, playername), prev_games))
            except HTTPError:
                print("Error fetching")
        rows = [row for row in rows if row is not None]

        columns = ['Opponent', 'Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Home Runs Allowed', 'Walks', 'Strike Outs', 'Pitches Thrown']
        stats_df = pd.DataFrame(rows, columns=columns)

        X_train = stats_df['Opponent']
        y_train = stats_df[['Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Home Runs Allowed', 'Walks', 'Strike Outs', 'Pitches Thrown']]

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

            pitcher_predicted_stats_dict = {'Opponent': next_opponent, **dict(zip(columns[1:], predicted_stats_list[0]))}


    elif playername[0]['primaryPosition']['abbreviation'] != 'P':
        with ThreadPoolExecutor() as executor:
            try:
                rows = list(executor.map(lambda game: fetch_batter_game_stats(game, player_id, playername), prev_games))
            except HTTPError:
                print("Error fetching")

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


def player_stat_mode(request):
    return render(request, 'player_stat_mode.html')


def player_stat_mode_search(request):
    query = request.GET.get('q', '')
    players = []

    if query:
        players = search_mlb_players(query)

    return render(request, 'player_stat_mode.html', {'players': players, 'query': query})


def best_player_stat_mode(request):
    return render(request, 'best_player_stat_mode.html')

def best_player_stat_mode_search(request):
    query = request.GET.get('q', '')
    players = []

    if query:
        players = search_mlb_players(query)

    return render(request, 'best_player_stat_mode.html', {'players': players, 'query': query})

def get_games_today():
    games = sa.schedule(start_date=today, end_date=today)
    todays_games = []
    for game in games:
        todays_games.append((game['away_name'], game['home_name']))
    return todays_games


def head_to_head_mode(request):
    todays_games = get_games_today()

    return render(request, 'head_to_head_mode.html', {'todays_games': todays_games})