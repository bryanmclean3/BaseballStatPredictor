from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
import statsapi as sa
import pandas as pd
import numpy as np
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
import BaseballStatPredictor.models as models
import requests

# Create your views here.

# can be changed to set current date for app
# today = date.today().strftime("%Y-%m-%d")
today = '2024-08-21'

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

    user_email = request.session.get("user", {}).get("email")

    return render(request, 'player_search.html', {'players': players, 'query': query, 'user_email': user_email})


# send player predictions to frontend to be displayed in popup
@require_GET
def get_player_prediction(request):
    player_name = request.GET.get('fullName')

    stats = player_stat_prediction(player_name)

    return JsonResponse({'stats': stats})


# get necessary player batting stats from each game stats
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


# do ridge regression to predict next game stats for any player
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


# open the player stat mode
def player_stat_mode(request):
    user_email = request.session.get("user", {}).get("email")

    return render(request, 'player_stat_mode.html', {'user_email': user_email})


# make a player search and send results to frontend
def player_stat_mode_search(request):
    user_email = request.session.get("user", {}).get("email")
    query = request.GET.get('q', '')
    players = []

    if query:
        players = search_mlb_players(query)

    return render(request, 'player_stat_mode.html', {'players': players, 'query': query, 'user_email': user_email})


# open manual stat prediction mode
def manual_stat_prediction_mode(request):
    user_email = request.session.get("user", {}).get("email")
    return render(request, 'manual_player_stat_prediction.html', {'user_email': user_email})


# get the list of matchups that are occurring today or fo whatever date the today variable is set to
def get_games_today():
    games = sa.schedule(start_date=today, end_date=today)
    todays_games = []
    for game in games:
        todays_games.append((game['away_name'], game['home_name']))
    return todays_games


# open the head-to-head prediction mode
def head_to_head_mode(request):
    todays_games = get_games_today()
    user_email = request.session.get("user", {}).get("email")

    return render(request, 'head_to_head_mode.html', {'todays_games': todays_games, 'user_email': user_email})


def about_page(request):
    return render(request, 'about_page.html', {'today': today})


# make batting stat predictions based of manually input stats
@csrf_exempt
def batting_stat_prediction(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        matrix = body.get('stats', [])
        nextOpponent = body.get('nextOpponent', '')

        columns = ['Opponent', 'Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Strike Outs']
        stats_df = pd.DataFrame(matrix, columns=columns)

        X_train = stats_df['Opponent']
        y_train = stats_df[['Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Strike Outs']]

        encoder = OneHotEncoder(handle_unknown='ignore')
        X_encoded = encoder.fit_transform(X_train.values.reshape(-1, 1)).toarray()

        ridge = Ridge(alpha=1)

        ridge.fit(X_encoded, y_train)
        new_opponent = pd.DataFrame({'Opponent': [nextOpponent]})
        new_X_encoded = encoder.transform(new_opponent['Opponent'].values.reshape(-1, 1)).toarray()
        predicted_stats = ridge.predict(new_X_encoded)

        predicted_stats_list = predicted_stats.tolist()

        predicted_stats_list = np.around(predicted_stats_list, 4).tolist()

        stats = {'Opponent': nextOpponent, **dict(zip(columns[1:], predicted_stats_list[0]))}

        return JsonResponse({'stats': stats})


# make pitching stat predictions based of manually input stats
@csrf_exempt
def pitching_stat_prediction(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        matrix = body.get('stats', [])
        nextOpponent = body.get('nextOpponent', '')

        columns = ['Opponent', 'Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Home Runs Allowed',
                   'Walks', 'Strike Outs', 'Pitches Thrown']
        stats_df = pd.DataFrame(matrix, columns=columns)

        X_train = stats_df['Opponent']
        y_train = stats_df[
            ['Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Home Runs Allowed', 'Walks',
             'Strike Outs', 'Pitches Thrown']]

        encoder = OneHotEncoder(handle_unknown='ignore')
        X_encoded = encoder.fit_transform(X_train.values.reshape(-1, 1)).toarray()

        ridge = Ridge(alpha=1)

        ridge.fit(X_encoded, y_train)
        new_opponent = pd.DataFrame({'Opponent': [nextOpponent]})
        new_X_encoded = encoder.transform(new_opponent['Opponent'].values.reshape(-1, 1)).toarray()
        predicted_stats = ridge.predict(new_X_encoded)

        predicted_stats_list = predicted_stats.tolist()

        predicted_stats_list = np.around(predicted_stats_list, 4).tolist()

        stats = {'Opponent': nextOpponent,
                 **dict(zip(columns[1:], predicted_stats_list[0]))}

        return JsonResponse({'stats': stats})


@csrf_exempt
def head_to_head_predictions(request):
    if request.method == 'POST':
        user_email = request.session.get("user", {}).get("email")
        body = json.loads(request.body)
        predictions = body.get('predictions')
        game_ids = list(predictions.keys())
        teams = list(predictions.values())

        store_head_to_head_predictions(game_ids, today, user_email, teams)

        return JsonResponse({'status': 'success', 'predictions': predictions})


def store_head_to_head_predictions(game_ids, date, email, teams):
    for idx in range(len(teams)):
        models.HeadToHead.objects.update_or_create(
            game_id=game_ids[idx],
            date=date,
            email=email,
            defaults={
                'team': teams[idx]
            }
        )


@csrf_exempt
def player_stat_predictions(request):
    if request.method == 'POST':
        user_email = request.session.get("user", {}).get("email")
        body = json.loads(request.body)
        predictions = body.get('predictions')

        two_hundred_days_away = (date.today() + timedelta(days=200)).strftime("%Y-%m-%d")
        allowed_game_types = {'R', 'P', 'F', 'D', 'L', 'W', 'C', 'N'}
        playername = sa.lookup_player(predictions['player'])

        schedule = sa.schedule(team=playername[0]['currentTeam']['id'], start_date=today,
                               end_date=two_hundred_days_away)

        filtered_opponents = [game for game in schedule if game['game_type'] in allowed_game_types]

        next_opponent = filtered_opponents[0]

        store_player_predictions(next_opponent['game_date'], user_email, predictions['player'], predictions['Opponent'], predictions)

        return JsonResponse({'status': 'success', 'predictions': predictions})


def store_player_predictions(date, email, name, opponent, predictions):
    models.PlayerStats.objects.update_or_create(
        date=date,
        email=email,
        name=name,
        opponent=opponent,
        defaults={
            'runs': predictions['Runs'] if 'Runs' in predictions else None,
            'hits': predictions['Hits'] if 'Hits' in predictions else None,
            'doubles': predictions['Doubles'] if 'Doubles' in predictions else None,
            'triples': predictions['Triples'] if 'Triples' in predictions else None,
            'home_runs': predictions['Home Runs'] if 'Home Runs' in predictions else None,
            'rbis': predictions['RBIs'] if 'RBIs' in predictions else None,
            'walks': predictions['Walks'] if 'Walks' in predictions else None,
            'strike_outs': predictions['Strike Outs'] if 'Strike Outs' in predictions else None,
            'innings_pitched': predictions['Innings Pitched'] if 'Innings Pitched' in predictions else None,
            'hits_allowed': predictions['Hits Allowed'] if 'Hits Allowed' in predictions else None,
            'runs_allowed': predictions['Runs Allowed'] if 'Runs Allowed' in predictions else None,
            'earned_runs': predictions['Earned Runs'] if 'Earned Runs' in predictions else None,
            'home_runs_allowed': predictions['Home Runs Allowed'] if 'Home Runs Allowed' in predictions else None,
            'pitches_thrown': predictions['Pitches Thrown'] if 'Pitches Thrown' in predictions else None,
        }
    )


def previous_predictions(request):
    user_email = request.session.get("user", {}).get("email")

    return render(request, 'previous_predictions.html', {'user_email': user_email})


@csrf_exempt
def view_predictions(request):
    if request.method == 'POST':
        user_email = request.session.get("user", {}).get("email")
        body = json.loads(request.body)
        selected_date = body.get('selected_date')

        if selected_date <= today:

            HeadToHeadPredictions = list(models.HeadToHead.objects.filter(date=selected_date, email=user_email).values())
            HeadToHeadResults = list()

            if len(HeadToHeadPredictions) > 0:
                team_schedule = sa.schedule(
                    start_date=selected_date,
                    end_date=selected_date
                )

                for idx, game in enumerate(team_schedule):
                    if game['status'] == 'Final':
                        HeadToHeadResults.append({
                            'game_id': idx + 1,
                            'winning_team': game['winning_team'],
                            'losing_team': game['losing_team']
                        })
                    else:
                        HeadToHeadResults.append({'game_id': idx + 1, 'status': 'Game Has Not Finished'})
            else:
                HeadToHeadResults.append({'game_id': 0, 'status': 'No Predictions Available'})

            PlayerStatPredictions = list(models.PlayerStats.objects.filter(date=selected_date, email=user_email).values())

            PlayerNames = models.PlayerStats.objects.filter(date=selected_date, email=user_email).values('name', 'opponent', 'innings_pitched')

            PlayerStatResults = list()
            if len(PlayerNames) > 0:
                for player in PlayerNames:
                    player_lookup = sa.lookup_player(player['name'])[0]
                    player_game = sa.schedule(
                        team=player_lookup['currentTeam']['id'],
                        start_date=selected_date,
                        end_date=selected_date
                    )[0]
                    if player_game['status'] == 'Final':
                        game_id = player_game['game_id']
                        player_stats = sa.boxscore_data(game_id)
                        if player_stats['teamInfo']['away']['id'] == player_lookup['currentTeam']['id']:
                            game_stats = player_stats['away']['players']['ID' + str(player_lookup['id'])]['stats']
                        else:
                            game_stats = player_stats['home']['players']['ID' + str(player_lookup['id'])]['stats']

                        if player['innings_pitched'] is not None:
                            values = list()
                            values.append(game_stats['pitching']['inningsPitched'])
                            values.append(game_stats['pitching']['hits'])
                            values.append(game_stats['pitching']['runs'])
                            values.append(game_stats['pitching']['earnedRuns'])
                            values.append(game_stats['pitching']['homeRuns'])
                            values.append(game_stats['pitching']['baseOnBalls'])
                            values.append(game_stats['pitching']['strikeOuts'])
                            values.append(game_stats['pitching']['numberOfPitches'])

                            keys = ['Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Home Runs Allowed',
                                    'Walks', 'Strike Outs', 'Pitches Thrown']

                            stats_dict = {'name': player['name'], **dict(zip(keys, values))}

                            PlayerStatResults.append(stats_dict)
                        else:
                            values = list()
                            values.append(game_stats['batting']['runs'])
                            values.append(game_stats['batting']['hits'])
                            values.append(game_stats['batting']['doubles'])
                            values.append(game_stats['batting']['triples'])
                            values.append(game_stats['batting']['homeRuns'])
                            values.append(game_stats['batting']['rbi'])
                            values.append(game_stats['batting']['baseOnBalls'])
                            values.append(game_stats['batting']['strikeOuts'])

                            keys = ['Runs', 'Hits', 'Doubles', 'Triples', 'Home Runs', 'RBIs', 'Walks', 'Strike Outs']

                            stats_dict = {'name': player['name'], **dict(zip(keys, values))}

                            PlayerStatResults.append(stats_dict)
                    else:
                        PlayerStatResults.append({'status': 'Game Has Not Finished'})
            else:
                PlayerStatResults.append({'status': 'No Predictions Available'})

            return JsonResponse({'HeadToHeadPredictions': HeadToHeadPredictions, 'HeadToHeadResults': HeadToHeadResults,
                                 'PlayerStatPredictions': PlayerStatPredictions, 'PlayerStatResults': PlayerStatResults})
        else:
            return JsonResponse({'status': 'Fail'})


oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)


# log user in with auth0
def login(request):
    callback_url = request.build_absolute_uri(reverse("callback"))
    return oauth.auth0.authorize_redirect(request, callback_url)


# callback function to get logged-in user's info
def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    user_info_url = f"https://{settings.AUTH0_DOMAIN}/userinfo"

    user_info = oauth.auth0.get(user_info_url, token=token).json()

    request.session["user"] = {
        "sub": token["id_token"],  # Can either be 'sub' or 'id_token'
        "email": user_info.get("email"),
        "name": user_info.get("name"),
    }

    store_user(token["id_token"], user_info.get("name"), user_info.get("email"))

    return redirect(request.build_absolute_uri(reverse("search")))


# log out user from auth0
def logout(request):
    request.session.clear()

    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("search")),
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )


# return teh user to the search page
def search(request):
    user = request.session.get("user")
    user_email = user.get("email") if user else None

    return render(
        request,
        "player_search.html",
        context={
            "session": user,
            "pretty": json.dumps(user, indent=4),
            "user_email": user_email,
        },
    )


# store user in the database
def store_user(sub, name, email):
    user, created = models.User.objects.update_or_create(
        email=email,
        defaults={
            'sub': sub,
            'name': name
        }
    )

    return user
