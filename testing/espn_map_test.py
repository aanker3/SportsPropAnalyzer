import sys
sys.path.insert(0, 'C:/github/SportsPropAnalyzer')

from alphabetter.nba_backend.fetch_player_stats_espn import build_espn_player_map, fetch_player_stats_espn

player_map = build_espn_player_map()
lines = ['Map size: ' + str(len(player_map))]
for name in ['Shai Gilgeous-Alexander', 'Victor Wembanyama', 'LeBron James', 'Jalen Williams', 'Stephon Castle']:
    lines.append(name + ': ' + str(player_map.get(name)))

shai_id = player_map.get('Shai Gilgeous-Alexander')
if shai_id:
    pname, team, tid, logs = fetch_player_stats_espn(shai_id, 'Shai Gilgeous-Alexander')
    lines.append('Shai games: ' + str(len(logs)))
    if logs:
        lines.append('Sample log[0]: pts=' + str(logs[0]['pts']) + ' reb=' + str(logs[0]['reb']) + ' ast=' + str(logs[0]['ast']) + ' date=' + str(logs[0]['game_date']))
        lines.append('Sample log[-1]: pts=' + str(logs[-1]['pts']) + ' date=' + str(logs[-1]['game_date']))

output = '\n'.join(lines)
print(output)
with open('C:/github/SportsPropAnalyzer/espn_test.txt', 'w') as f:
    f.write(output)
