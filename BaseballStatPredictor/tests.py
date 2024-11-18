import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseballStatPredictor_project.test_settings')
django.setup()

from django.test import TestCase
from BaseballStatPredictor.views import *


class BaseballStatPredictorTests(TestCase):
    def test_search_mlb_players_TC1(self):
        query = 'Aaron Judge'
        players = search_mlb_players(query)
        player = players[0]

        self.assertEqual(player['fullName'], 'Aaron Judge')
        self.assertEqual(player['primaryPosition'], 'CF')
        self.assertEqual(player['playerId'], 592450)
        self.assertEqual(player['teamName'], 'New York Yankees')

    def test_search_mlb_players_TC2(self):
        query = 'ohtani'
        players = search_mlb_players(query)
        player = players[0]

        self.assertEqual(player['fullName'], 'Shohei Ohtani')
        self.assertEqual(player['primaryPosition'], 'TWP')
        self.assertEqual(player['playerId'], 660271)
        self.assertEqual(player['teamName'], 'Los Angeles Dodgers')

    def test_search_mlb_players_TC3(self):
        query = 'harp'
        players = search_mlb_players(query)
        player = players[0]

        self.assertEqual(player['fullName'], 'Bryce Harper')
        self.assertEqual(player['primaryPosition'], '1B')
        self.assertEqual(player['playerId'], 547180)
        self.assertEqual(player['teamName'], 'Philadelphia Phillies')

    def test_search_mlb_players_TC4(self):
        query = 'byr'
        players = search_mlb_players(query)
        player = players[0]

        self.assertEqual(player['fullName'], 'Byron Buxton')
        self.assertEqual(player['primaryPosition'], 'CF')
        self.assertEqual(player['playerId'], 621439)
        self.assertEqual(player['teamName'], 'Minnesota Twins')

    # will only work while the start date is start of 2024 season and today is set to 2024/08/21
    def test_player_stat_prediction_TC5(self):
        playername = sa.lookup_player('arenado')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Milwaukee Brewers')
        self.assertEqual(predictions['Runs'], 0.2742)
        self.assertEqual(predictions['Hits'], 0.8969)
        self.assertEqual(predictions['Doubles'], 0.4616)
        self.assertEqual(predictions['Triples'], 0.0)
        self.assertEqual(predictions['Home Runs'], 0.1236)
        self.assertEqual(predictions['RBIs'], 0.7197)
        self.assertEqual(predictions['Walks'], 0.5899)
        self.assertEqual(predictions['Strike Outs'], 0.6217)

    def test_player_stat_prediction_TC6(self):
        playername = sa.lookup_player('carpenter')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Chicago Cubs')
        self.assertEqual(predictions['Runs'], 0.4863)
        self.assertEqual(predictions['Hits'], 0.9445)
        self.assertEqual(predictions['Doubles'], 0.0647)
        self.assertEqual(predictions['Triples'], 0.0236)
        self.assertEqual(predictions['Home Runs'], 0.4085)
        self.assertEqual(predictions['RBIs'], 1.2192)
        self.assertEqual(predictions['Walks'], 0.0568)
        self.assertEqual(predictions['Strike Outs'], 0.9476)

    def test_player_stat_prediction_TC7(self):
        playername = sa.lookup_player('sweeney')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Chicago Cubs')
        self.assertEqual(predictions['Runs'], 0.8571)
        self.assertEqual(predictions['Hits'], 0.8571)
        self.assertEqual(predictions['Doubles'], 0.0)
        self.assertEqual(predictions['Triples'], 0.0)
        self.assertEqual(predictions['Home Runs'], 0.7143)
        self.assertEqual(predictions['RBIs'], 1.4286)
        self.assertEqual(predictions['Walks'], 0.0)
        self.assertEqual(predictions['Strike Outs'], 0.5714)

    def test_player_stat_prediction_TC8(self):
        playername = sa.lookup_player('ian happ')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Detroit Tigers')
        self.assertEqual(predictions['Runs'], 0.5286)
        self.assertEqual(predictions['Hits'], 0.6082)
        self.assertEqual(predictions['Doubles'], 0.0731)
        self.assertEqual(predictions['Triples'], 0.0041)
        self.assertEqual(predictions['Home Runs'], 0.0542)
        self.assertEqual(predictions['RBIs'], 0.181)
        self.assertEqual(predictions['Walks'], 0.5168)
        self.assertEqual(predictions['Strike Outs'], 1.0618)

    def test_player_stat_prediction_TC9(self):
        playername = sa.lookup_player('ian happ')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Detroit Tigers')
        self.assertEqual(predictions['Runs'], 0.5286)
        self.assertEqual(predictions['Hits'], 0.6082)
        self.assertEqual(predictions['Doubles'], 0.0731)
        self.assertEqual(predictions['Triples'], 0.0041)
        self.assertEqual(predictions['Home Runs'], 0.0542)
        self.assertEqual(predictions['RBIs'], 0.181)
        self.assertEqual(predictions['Walks'], 0.5168)
        self.assertEqual(predictions['Strike Outs'], 1.0618)

    def test_player_stat_prediction_TC10(self):
        playername = sa.lookup_player('lowe')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions, {})

    def test_player_stat_prediction_TC11(self):
        playername = sa.lookup_player('brandon lowe')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Oakland Athletics')
        self.assertEqual(predictions['Runs'], 0.2243)
        self.assertEqual(predictions['Hits'], 0.4112)
        self.assertEqual(predictions['Doubles'], 0.1709)
        self.assertEqual(predictions['Triples'], 0.1456)
        self.assertEqual(predictions['Home Runs'], 0.0335)
        self.assertEqual(predictions['RBIs'], 0.2355)
        self.assertEqual(predictions['Walks'], 0.3367)
        self.assertEqual(predictions['Strike Outs'], 1.1439)

    def test_player_stat_prediction_TC12(self):
        playername = sa.lookup_player('springer')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Cincinnati Reds')
        self.assertEqual(predictions['Runs'], 1.1275)
        self.assertEqual(predictions['Hits'], 1.2087)
        self.assertEqual(predictions['Doubles'], 0.2818)
        self.assertEqual(predictions['Triples'], 0.0064)
        self.assertEqual(predictions['Home Runs'], 0.7833)
        self.assertEqual(predictions['RBIs'], 1.0986)
        self.assertEqual(predictions['Walks'], 0.3415)
        self.assertEqual(predictions['Strike Outs'], 0.6908)

    def test_player_stat_prediction_TC13(self):
        playername = sa.lookup_player('brock burke')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Kansas City Royals')
        self.assertEqual(predictions['Innings Pitched'], 1.0286)
        self.assertEqual(predictions['Hits Allowed'], 0.0)
        self.assertEqual(predictions['Runs Allowed'], 0.0)
        self.assertEqual(predictions['Earned Runs'], 0.0)
        self.assertEqual(predictions['Home Runs Allowed'], 0.0)
        self.assertEqual(predictions['Walks'], 0.2857)
        self.assertEqual(predictions['Strike Outs'], 1.2857)
        self.assertEqual(predictions['Pitches Thrown'], 15.5714)

    def test_player_stat_prediction_TC14(self):
        playername = sa.lookup_player('logan gilbert')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Los Angeles Dodgers')
        self.assertEqual(predictions['Innings Pitched'], 5.1904)
        self.assertEqual(predictions['Hits Allowed'], 5.8235)
        self.assertEqual(predictions['Runs Allowed'], 5.2794)
        self.assertEqual(predictions['Earned Runs'], 4.1324)
        self.assertEqual(predictions['Home Runs Allowed'], 0.3603)
        self.assertEqual(predictions['Walks'], 1.5882)
        self.assertEqual(predictions['Strike Outs'], 6.6176)
        self.assertEqual(predictions['Pitches Thrown'], 95.8529)

    def test_player_stat_prediction_TC15(self):
        playername = sa.lookup_player('banda')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Seattle Mariners')
        self.assertEqual(predictions['Innings Pitched'], 0.7355)
        self.assertEqual(predictions['Hits Allowed'], 0.2581)
        self.assertEqual(predictions['Runs Allowed'], 0.0983)
        self.assertEqual(predictions['Earned Runs'], 0.0784)
        self.assertEqual(predictions['Home Runs Allowed'], 0.0199)
        self.assertEqual(predictions['Walks'], 0.4723)
        self.assertEqual(predictions['Strike Outs'], 1.7233)
        self.assertEqual(predictions['Pitches Thrown'], 15.0421)

    def test_player_stat_prediction_TC16(self):
        playername = sa.lookup_player('pepiot')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Oakland Athletics')
        self.assertEqual(predictions['Innings Pitched'], 5.4127)
        self.assertEqual(predictions['Hits Allowed'], 3.2727)
        self.assertEqual(predictions['Runs Allowed'], 2.0727)
        self.assertEqual(predictions['Earned Runs'], 2.0364)
        self.assertEqual(predictions['Home Runs Allowed'], 0.5455)
        self.assertEqual(predictions['Walks'], 1.2545)
        self.assertEqual(predictions['Strike Outs'], 5.8182)
        self.assertEqual(predictions['Pitches Thrown'], 87.4)

    def test_player_stat_prediction_TC17(self):
        playername = sa.lookup_player('rasmussen')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Oakland Athletics')
        self.assertEqual(predictions['Innings Pitched'], 1.3)
        self.assertEqual(predictions['Hits Allowed'], 1.2)
        self.assertEqual(predictions['Runs Allowed'], 0.3)
        self.assertEqual(predictions['Earned Runs'], 0.3)
        self.assertEqual(predictions['Home Runs Allowed'], 0.0)
        self.assertEqual(predictions['Walks'], 0.6)
        self.assertEqual(predictions['Strike Outs'], 2.6)
        self.assertEqual(predictions['Pitches Thrown'], 27.1)

    def test_player_stat_prediction_TC18(self):
        playername = sa.lookup_player('roansy')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions, {})

    def test_player_stat_prediction_TC19(self):
        playername = sa.lookup_player('erceg')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Los Angeles Angels')
        self.assertEqual(predictions['Innings Pitched'], 0.9978)
        self.assertEqual(predictions['Hits Allowed'], 0.1957)
        self.assertEqual(predictions['Runs Allowed'], 0.0)
        self.assertEqual(predictions['Earned Runs'], 0.0)
        self.assertEqual(predictions['Home Runs Allowed'], 0.0)
        self.assertEqual(predictions['Walks'], 0.0)
        self.assertEqual(predictions['Strike Outs'], 1.8261)
        self.assertEqual(predictions['Pitches Thrown'], 15.1522)

    def test_player_stat_prediction_TC20(self):
        playername = sa.lookup_player('gerrit cole')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Cleveland Guardians')
        self.assertEqual(predictions['Innings Pitched'], 5.1)
        self.assertEqual(predictions['Hits Allowed'], 5.5417)
        self.assertEqual(predictions['Runs Allowed'], 2.25)
        self.assertEqual(predictions['Earned Runs'], 2.25)
        self.assertEqual(predictions['Home Runs Allowed'], 0.8333)
        self.assertEqual(predictions['Walks'], 1.625)
        self.assertEqual(predictions['Strike Outs'], 6.4167)
        self.assertEqual(predictions['Pitches Thrown'], 90.6667)

    def test_player_stat_prediction_TC21(self):
        playername = sa.lookup_player('luis gil')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Cleveland Guardians')
        self.assertEqual(predictions['Innings Pitched'], 4.0297)
        self.assertEqual(predictions['Hits Allowed'], 3.1622)
        self.assertEqual(predictions['Runs Allowed'], 2.509)
        self.assertEqual(predictions['Earned Runs'], 2.491)
        self.assertEqual(predictions['Home Runs Allowed'], 0.7748)
        self.assertEqual(predictions['Walks'], 4.4144)
        self.assertEqual(predictions['Strike Outs'], 4.4865)
        self.assertEqual(predictions['Pitches Thrown'], 84.9865)

    def test_player_stat_prediction_TC22(self):
        playername = sa.lookup_player('cole sands')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'San Diego Padres')
        self.assertEqual(predictions['Innings Pitched'], 1.0196)
        self.assertEqual(predictions['Hits Allowed'], 1.0227)
        self.assertEqual(predictions['Runs Allowed'], 0.267)
        self.assertEqual(predictions['Earned Runs'], 0.2244)
        self.assertEqual(predictions['Home Runs Allowed'], 0.0597)
        self.assertEqual(predictions['Walks'], 0.0824)
        self.assertEqual(predictions['Strike Outs'], 1.6733)
        self.assertEqual(predictions['Pitches Thrown'], 17.1591)

    def test_player_stat_prediction_TC23(self):
        playername = sa.lookup_player('matt waldron')
        predictions = player_stat_prediction(playername[0]['id'])

        self.assertEqual(predictions['Opponent'], 'Minnesota Twins')
        self.assertEqual(predictions['Innings Pitched'], 4.7372)
        self.assertEqual(predictions['Hits Allowed'], 8.7124)
        self.assertEqual(predictions['Runs Allowed'], 6.5265)
        self.assertEqual(predictions['Earned Runs'], 6.4602)
        self.assertEqual(predictions['Home Runs Allowed'], 0.854)
        self.assertEqual(predictions['Walks'], 1.1991)
        self.assertEqual(predictions['Strike Outs'], 3.9248)
        self.assertEqual(predictions['Pitches Thrown'], 91.5487)

    def test_get_games_today_TC24(self):
        games_today = get_games_today()

        self.assertEqual(len(games_today), 15)
        self.assertIn(('Baltimore Orioles', 'New York Mets'), games_today)
        self.assertIn(('Boston Red Sox', 'Houston Astros'), games_today)
        self.assertIn(('Pittsburgh Pirates', 'Texas Rangers'), games_today)
        self.assertIn(('Chicago White Sox', 'San Francisco Giants'), games_today)
        self.assertIn(('Minnesota Twins', 'San Diego Padres'), games_today)
        self.assertIn(('Arizona Diamondbacks', 'Miami Marlins'), games_today)
        self.assertIn(('Colorado Rockies', 'Washington Nationals'), games_today)
        self.assertIn(('Cleveland Guardians', 'New York Yankees'), games_today)
        self.assertIn(('Cincinnati Reds', 'Toronto Blue Jays'), games_today)
        self.assertIn(('Philadelphia Phillies', 'Atlanta Braves'), games_today)
        self.assertIn(('Milwaukee Brewers', 'St. Louis Cardinals'), games_today)
        self.assertIn(('Detroit Tigers', 'Chicago Cubs'), games_today)
        self.assertIn(('Los Angeles Angels', 'Kansas City Royals'), games_today)
        self.assertIn(('Tampa Bay Rays', 'Oakland Athletics'), games_today)
        self.assertIn(('Seattle Mariners', 'Los Angeles Dodgers'), games_today)

    def test_fetch_batter_game_stats_TC25(self):
        playername = sa.lookup_player('aaron judge')
        game = sa.schedule(
            team=playername[0]['currentTeam']['id'],
            start_date='2024-07-26',
            end_date='2024-07-26'
        )[0]

        stats = fetch_batter_game_stats(game, playername[0]['id'], playername)

        self.assertEqual(stats[0], 'Boston Red Sox')  # opponent
        self.assertEqual(stats[1], 1)  # runs
        self.assertEqual(stats[2], 1)  # hits
        self.assertEqual(stats[3], 0)  # doubles
        self.assertEqual(stats[4], 0)  # triples
        self.assertEqual(stats[5], 1)  # home runs
        self.assertEqual(stats[6], 3)  # rbis
        self.assertEqual(stats[7], 1)  # walks
        self.assertEqual(stats[8], 1)  # strike outs

    def test_fetch_batter_game_stats_TC26(self):
        playername = sa.lookup_player('bobby witt')
        game = sa.schedule(
            team=playername[0]['currentTeam']['id'],
            start_date='2024-07-26',
            end_date='2024-07-26'
        )[0]

        stats = fetch_batter_game_stats(game, playername[0]['id'], playername)

        self.assertEqual(stats[0], 'Chicago Cubs')  # opponent
        self.assertEqual(stats[1], 1)  # runs
        self.assertEqual(stats[2], 1)  # hits
        self.assertEqual(stats[3], 0)  # doubles
        self.assertEqual(stats[4], 0)  # triples
        self.assertEqual(stats[5], 0)  # home runs
        self.assertEqual(stats[6], 0)  # rbis
        self.assertEqual(stats[7], 0)  # walks
        self.assertEqual(stats[8], 0)  # strike outs

    def test_fetch_batter_game_stats_TC26(self):
        playername = sa.lookup_player('massey')
        game = sa.schedule(
            team=playername[0]['currentTeam']['id'],
            start_date='2024-07-26',
            end_date='2024-07-26'
        )[0]

        stats = fetch_batter_game_stats(game, playername[0]['id'], playername)

        self.assertEqual(stats[0], 'Chicago Cubs')  # opponent
        self.assertEqual(stats[1], 0)  # runs
        self.assertEqual(stats[2], 0)  # hits
        self.assertEqual(stats[3], 0)  # doubles
        self.assertEqual(stats[4], 0)  # triples
        self.assertEqual(stats[5], 0)  # home runs
        self.assertEqual(stats[6], 0)  # rbis
        self.assertEqual(stats[7], 0)  # walks
        self.assertEqual(stats[8], 0)  # strike outs

    def test_fetch_batter_game_stats_TC27(self):
        playername = sa.lookup_player('ian happ')
        game = sa.schedule(
            team=playername[0]['currentTeam']['id'],
            start_date='2024-07-26',
            end_date='2024-07-26'
        )[0]

        stats = fetch_batter_game_stats(game, playername[0]['id'], playername)

        self.assertEqual(stats[0], 'Kansas City Royals')  # opponent
        self.assertEqual(stats[1], 0)  # runs
        self.assertEqual(stats[2], 0)  # hits
        self.assertEqual(stats[3], 0)  # doubles
        self.assertEqual(stats[4], 0)  # triples
        self.assertEqual(stats[5], 0)  # home runs
        self.assertEqual(stats[6], 0)  # rbis
        self.assertEqual(stats[7], 1)  # walks
        self.assertEqual(stats[8], 0)  # strike outs












