import sys
sys.path.insert(0, 'C:/github/SportsPropAnalyzer')

from alphabetter.nba_backend.stat_collector.calculate_and_store_lastx import (
    _calc_hit_rate, _is_hit, _get_stat_value, last_percent, STAT_MAPPING
)

errors = []

# Test 1: _is_hit — exact match on 'over' and 'under' should both be hits
try:
    assert _is_hit(10.0, 10.0, 'over') == True,  "exact over should be hit"
    assert _is_hit(10.0, 10.0, 'under') == True, "exact under should be hit"
    assert _is_hit(9.9, 10.0, 'over') == False,  "below over should be miss"
    assert _is_hit(10.1, 10.0, 'under') == False, "above under should be miss"
    assert _is_hit(11.0, 10.0, 'over') == True,  "above over should be hit"
    assert _is_hit(9.0, 10.0, 'under') == True,  "below under should be hit"
    print("PASS: _is_hit logic")
except AssertionError as e:
    errors.append(f"FAIL _is_hit: {e}")

# Test 2: STAT_MAPPING is importable and correct
try:
    assert 'Points' in STAT_MAPPING
    assert STAT_MAPPING['Pts+Rebs+Asts'] == ['pts', 'reb', 'ast']
    assert STAT_MAPPING['Blocked Shots'] == 'blk'
    print("PASS: STAT_MAPPING import")
except AssertionError as e:
    errors.append(f"FAIL STAT_MAPPING: {e}")

# Test 3: last_percent returns sensible result
try:
    hits = [True, True, True, False, False, True, True]
    rate, frac = last_percent(hits)
    assert '/' in frac, f"expected fraction string, got {frac}"
    assert 0 <= rate <= 100, f"rate out of range: {rate}"
    print(f"PASS: last_percent -> {rate}% ({frac})")
except AssertionError as e:
    errors.append(f"FAIL last_percent: {e}")

# Test 4: _calc_hit_rate with mock games (use simple objects)
class MockGame:
    def __init__(self, pts, reb, ast, blk, stl, tov, min_played):
        self.pts = pts; self.reb = reb; self.ast = ast
        self.blk = blk; self.stl = stl; self.tov = tov
        self.min = min_played

games = [
    MockGame(25, 5, 3, 1, 1, 2, 32),
    MockGame(10, 8, 7, 0, 2, 3, 28),
    MockGame(30, 3, 2, 2, 0, 1, 35),
    MockGame(15, 10, 5, 1, 1, 0, 30),
    MockGame(20, 6, 8, 0, 3, 2, 31),
    MockGame(0, 0, 0, 0, 0, 0, 0),  # DNP row
]

try:
    rate = _calc_hit_rate(games, 20.0, 'over', 'pts')
    # Games with pts>=20: 25, 30, 20 = 3 hits out of 5 active (DNP excluded)
    assert rate == 3/5, f"expected 0.6, got {rate}"
    print(f"PASS: _calc_hit_rate excludes DNP, got {rate}")
except AssertionError as e:
    errors.append(f"FAIL _calc_hit_rate: {e}")

# Test 5: combined stat
try:
    rate2 = _calc_hit_rate(games, 30.0, 'over', ['pts', 'reb'])
    # pts+reb: 30, 18, 33, 25, 26 — hits (>=30): 30, 33, 25? no 25<30... 30>=30 yes, 33>=30 yes
    # 30+3=33, 18 no, 33 yes, 25 no, 26 no -> 2 hits out of 5
    assert rate2 == 2/5, f"expected 0.4, got {rate2}"
    print(f"PASS: _calc_hit_rate combined stat, got {rate2}")
except AssertionError as e:
    errors.append(f"FAIL combined stat: {e}")

if errors:
    print("\nFAILURES:")
    for e in errors: print(" ", e)
    sys.exit(1)
else:
    print("\nAll bugfix tests passed.")
