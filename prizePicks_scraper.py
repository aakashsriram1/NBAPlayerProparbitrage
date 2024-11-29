import requests

# Function to get player stats and odds from PrizePicks API
def get_player_stats_and_odds():
    url = 'https://partner-api.prizepicks.com/projections?league_id=7&per_page=10'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        projections = data['data']
        included = {item['id']: item['attributes']['display_name'] for item in data['included'] if item['type'] == 'new_player'}
        stat_types = {item['id']: item['attributes']['name'] for item in data['included'] if item['type'] == 'stat_type'}

        player_stats_and_odds = []
        for projection in projections:
            player_id = projection['relationships']['new_player']['data']['id']
            stat_type_id = projection['relationships']['stat_type']['data']['id']
            player_name = included[player_id]
            stat_type = stat_types[stat_type_id]
            line_score = projection['attributes']['line_score']
            player_stats_and_odds.append(f"{player_name} ({stat_type}): {line_score}")

        return player_stats_and_odds
    else:
        print("Failed to retrieve data")
        return []

# Example usage
try:
    player_stats_and_odds = get_player_stats_and_odds()
    for stat in player_stats_and_odds:
        print(stat)
except Exception as e:
    print(f"Failed to retrieve player stats and odds: {e}")
