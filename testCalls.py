import statsapi as sa

playername = sa.lookup_player('Aaron Judge')
player = sa.player_stat_data(playername[0]['id'], 'hitting', 'season')

# print(player['stats'][0]['stats']['homeRuns'])

games = sa.schedule(start_date='09/17/2024', end_date='09/17/2024')

# for game in games:
#     print("{} at {}".format(game['away_name'], game['home_name']))




