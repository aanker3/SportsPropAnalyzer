import sys
sys.path.insert(0, 'C:/github/SportsPropAnalyzer')

from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.models import PrizePicksProp
from alphabetter.nba_backend.stat_collector.calculate_and_store_lastx import calculate_hit_rates, store_calculated_stats

db = next(get_db())
props = db.query(PrizePicksProp).filter(PrizePicksProp.stat == 'Double-Double').all()
print(f'Found {len(props)} Double-Double props')
for prop in props:
    stats = calculate_hit_rates(db, prop)
    if stats:
        store_calculated_stats(db, stats)
        print(f'{prop.player_name}: L5={stats["l5_hit_rate"]:.0%}  L10={stats["l10_hit_rate"]:.0%}  best={stats["last_percent_total"]}')
    else:
        print(f'{prop.player_name}: no game data')
db.close()
