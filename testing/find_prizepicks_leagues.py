import sys, requests, json
sys.path.insert(0, 'C:/github/SportsPropAnalyzer')

HEADERS = {
    "Host": "api.prizepicks.com",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 Chrome/109.0.0.0 Mobile Safari/537.36",
    "Origin": "https://app.prizepicks.com",
    "Referer": "https://app.prizepicks.com/",
}

results = {}
for lid in range(1, 20):
    try:
        r = requests.get(
            f"https://api.prizepicks.com/projections?league_id={lid}&per_page=10&single_stat=true",
            headers=HEADERS, timeout=10
        )
        data = r.json().get("data", [])
        included = r.json().get("included", [])
        if data:
            # Get league name from included
            league_name = next((x["attributes"].get("name","?") for x in included if x.get("type")=="league"), "?")
            stat_types = list({x["attributes"]["stat_type"] for x in data if "stat_type" in x.get("attributes",{})})
            results[lid] = {"league": league_name, "stats": sorted(stat_types), "count": len(data)}
            print(f"league_id={lid}: {league_name} — {len(data)} props — stats: {sorted(stat_types)[:5]}...")
        else:
            print(f"league_id={lid}: empty")
    except Exception as e:
        print(f"league_id={lid}: error — {e}")

print("\n=== SUMMARY ===")
for lid, info in results.items():
    print(f"\nleague_id={lid} ({info['league']}):")
    for s in info['stats']:
        print(f"  {s}")
