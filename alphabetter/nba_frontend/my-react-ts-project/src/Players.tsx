import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import API_URL from './api';
const API = API_URL;

interface NBAGameLog {
  game_date: string; matchup: string;
  min: number; pts: number; reb: number; ast: number;
  stl: number; blk: number; tov: number;
  fgm: number; fga: number; fg_pct: number;
  fg3m: number; fg3a: number; fg3_pct: number;
  ftm: number; fta: number; ft_pct: number;
}

interface MLBGameLog {
  game_date: string; matchup: string; is_pitcher: boolean;
  ab: number; r: number; h: number; doubles: number; triples: number;
  hr: number; rbi: number; bb: number; hbp: number; so: number;
  sb: number; cs: number;
  ip: number; hits_allowed: number; runs_allowed: number;
  er: number; hr_allowed: number; bb_allowed: number; k: number;
}

interface Prop {
  id: number; player_name: string; stat: string;
  target: number; over_under: string; odds_type: string; sport?: string;
}

interface Stat {
  prop_id: number; l5_hit_rate: number; l10_hit_rate: number;
  l20_hit_rate: number; last_percent_rate: number; last_percent_total: string;
}

const pct = (v: number) => v > 0 ? `${(v * 100).toFixed(1)}%` : '—';
const num = (v: number) => v > 0 ? v : '—';

const ODDS_STYLE: Record<string, string> = {
  demon:    'bg-orange-900/50 text-orange-300 border border-orange-700/50',
  goblin:   'bg-purple-900/50 text-purple-300 border border-purple-700/50',
  standard: 'bg-slate-800 text-slate-300 border border-slate-600/50',
};

function RateBar({ rate }: { rate: number }) {
  const p = Math.round(rate * 100);
  const bar = p >= 60 ? 'bg-green-500' : p >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  const txt = p >= 60 ? 'text-green-400' : p >= 40 ? 'text-yellow-400' : 'text-red-400';
  return (
    <div className="flex items-center gap-2 min-w-[90px]">
      <div className="h-1.5 flex-1 rounded-full bg-gray-700">
        <div className={`h-full rounded-full ${bar}`} style={{ width: `${p}%` }} />
      </div>
      <span className={`text-xs font-mono w-8 text-right ${txt}`}>{p}%</span>
    </div>
  );
}

type SortKey = 'l5_hit_rate' | 'l10_hit_rate' | 'l20_hit_rate' | 'last_percent_rate';

export default function Players() {
  const [playerName, setPlayerName] = useState('');
  const [sport, setSport] = useState<'NBA' | 'MLB' | null>(null);
  const [nbaLogs, setNbaLogs] = useState<NBAGameLog[]>([]);
  const [mlbLogs, setMlbLogs] = useState<MLBGameLog[]>([]);
  const [playerProps, setPlayerProps] = useState<Prop[]>([]);
  const [statsMap, setStatsMap] = useState<Record<number, Stat>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetched, setFetched] = useState('');
  const [propSort, setPropSort] = useState<SortKey | null>(null);
  const [propSortDir, setPropSortDir] = useState<'desc' | 'asc'>('desc');
  const [allPlayers, setAllPlayers] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    axios.get(`${API}/api/props`).then(res => {
      const names: string[] = Array.from(
        new Set((res.data.props as Prop[]).map((p: Prop) => p.player_name))
      ).sort();
      setAllPlayers(names);
    });
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setPlayerName(val);
    setActiveSuggestion(-1);
    if (val.trim().length >= 2) {
      const q = val.toLowerCase();
      const matches = allPlayers.filter(n => n.toLowerCase().includes(q)).slice(0, 8);
      setSuggestions(matches);
      setShowSuggestions(matches.length > 0);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveSuggestion(i => Math.min(i + 1, suggestions.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveSuggestion(i => Math.max(i - 1, 0)); }
    else if (e.key === 'Enter' && activeSuggestion >= 0) { e.preventDefault(); selectSuggestion(suggestions[activeSuggestion]); }
    else if (e.key === 'Escape') setShowSuggestions(false);
  };

  const selectSuggestion = (name: string) => {
    setPlayerName(name);
    setSuggestions([]);
    setShowSuggestions(false);
    setActiveSuggestion(-1);
    doFetch(name);
  };

  const doFetch = async (name: string) => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const [logsRes, propsRes, statsRes] = await Promise.all([
        axios.get(`${API}/api/player-gamelogs/${encodeURIComponent(name.trim())}`),
        axios.get(`${API}/api/props`),
        axios.get(`${API}/api/player-stats-calculated`),
      ]);

      const detectedSport: 'NBA' | 'MLB' = logsRes.data.sport ?? 'NBA';
      const logs = logsRes.data.game_logs ?? [];
      const allProps: Prop[] = propsRes.data.props ?? [];
      const allStats: Stat[] = statsRes.data.stats ?? [];

      const filteredProps = allProps.filter(
        p => p.player_name.toLowerCase() === name.trim().toLowerCase()
      );
      const map: Record<number, Stat> = {};
      allStats.forEach((s: Stat) => { map[s.prop_id] = s; });

      setSport(detectedSport);
      if (detectedSport === 'MLB') {
        setMlbLogs(logs);
        setNbaLogs([]);
      } else {
        setNbaLogs(logs);
        setMlbLogs([]);
      }
      setPlayerProps(filteredProps);
      setStatsMap(map);
      setFetched(name.trim());

      if (!logs.length && !filteredProps.length) setError('Player not found.');
    } catch {
      setError('Player not found or server error.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuggestions(false);
    doFetch(playerName);
  };

  const handlePropSort = (key: SortKey) => {
    if (propSort === key) setPropSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setPropSort(key); setPropSortDir('desc'); }
  };

  const sortedProps = propSort
    ? [...playerProps].sort((a, b) => {
        const va = statsMap[a.id]?.[propSort] ?? 0;
        const vb = statsMap[b.id]?.[propSort] ?? 0;
        return propSortDir === 'desc' ? vb - va : va - vb;
      })
    : playerProps;

  // NBA season averages
  const nbaAvg = (key: keyof NBAGameLog) => {
    const active = nbaLogs.filter(g => g.min > 0);
    if (!active.length) return 0;
    return active.reduce((s, g) => s + (g[key] as number), 0) / active.length;
  };

  // MLB season totals / rate stats
  const isPitcher = mlbLogs.length > 0 && mlbLogs[0].is_pitcher;
  const mlbTotal = (key: keyof MLBGameLog) =>
    mlbLogs.reduce((s, g) => s + ((g[key] as number) || 0), 0);

  const totalG   = mlbLogs.length;
  const totalAB  = mlbTotal('ab');
  const totalH   = mlbTotal('h');
  const totalBB  = mlbTotal('bb');
  const totalHBP = mlbTotal('hbp');
  const totalPA  = totalAB + totalBB + totalHBP;
  const total2B  = mlbTotal('doubles');
  const total3B  = mlbTotal('triples');
  const totalHR  = mlbTotal('hr');
  const totalTB  = totalH + total2B + 2 * total3B + 3 * totalHR;
  const ba   = totalAB  > 0 ? totalH / totalAB : 0;
  const obp  = totalPA  > 0 ? (totalH + totalBB + totalHBP) / totalPA : 0;
  const slg  = totalAB  > 0 ? totalTB / totalAB : 0;
  const ops  = obp + slg;

  const totalIP       = mlbTotal('ip');
  const totalER       = mlbTotal('er');
  const totalBBAllowed = mlbTotal('bb_allowed');
  const totalHAllowed  = mlbTotal('hits_allowed');
  const era   = totalIP > 0 ? (totalER / totalIP) * 9 : 0;
  const whip  = totalIP > 0 ? (totalBBAllowed + totalHAllowed) / totalIP : 0;
  const k9    = totalIP > 0 ? (mlbTotal('k') / totalIP) * 9 : 0;
  const bb9   = totalIP > 0 ? (totalBBAllowed / totalIP) * 9 : 0;
  const h9    = totalIP > 0 ? (totalHAllowed / totalIP) * 9 : 0;

  const fmtAvg = (v: number) => v > 0 ? `.${Math.round(v * 1000).toString().padStart(3, '0')}` : '.000';
  const fmtIP  = (ip: number) => {
    const full = Math.floor(ip); const frac = Math.round((ip - full) * 10);
    return frac === 0 ? `${full}.0` : `${full}.${frac}`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Players</h1>
        <p className="text-sm text-gray-500 mt-1">Search any NBA or MLB player with active props</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            value={playerName}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            placeholder="e.g. Aaron Judge, LeBron James…"
            autoComplete="off"
            className="h-10 w-80 rounded-lg border border-gray-700 bg-gray-900 px-4 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
          {showSuggestions && (
            <ul className="absolute left-0 top-full z-50 mt-1 w-full overflow-hidden rounded-lg border border-gray-700 bg-gray-900 shadow-xl">
              {suggestions.map((name, i) => (
                <li
                  key={name}
                  onMouseDown={() => selectSuggestion(name)}
                  className={`cursor-pointer px-4 py-2 text-sm transition-colors ${
                    i === activeSuggestion ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'
                  }`}
                >
                  {name}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="h-10 rounded-lg bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Loading…' : 'Search'}
        </button>
      </form>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {fetched && !loading && (
        <div className="space-y-6">

          {/* ── NBA Season Averages ── */}
          {sport === 'NBA' && nbaLogs.length > 0 && (
            <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
              <p className="text-xs uppercase text-gray-500 mb-3 tracking-wide">
                {fetched} — Season Averages ({nbaLogs.filter(g => g.min > 0).length} games)
              </p>
              <div className="grid grid-cols-4 gap-4 sm:grid-cols-8">
                {([
                  ['PTS', nbaAvg('pts').toFixed(1)],
                  ['REB', nbaAvg('reb').toFixed(1)],
                  ['AST', nbaAvg('ast').toFixed(1)],
                  ['STL', nbaAvg('stl').toFixed(1)],
                  ['BLK', nbaAvg('blk').toFixed(1)],
                  ['TOV', nbaAvg('tov').toFixed(1)],
                  ['FG%', pct(nbaAvg('fg_pct'))],
                  ['3P%', pct(nbaAvg('fg3_pct'))],
                ] as [string, string][]).map(([label, value]) => (
                  <div key={label} className="text-center">
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="text-lg font-bold text-white">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── MLB Season Stats ── */}
          {sport === 'MLB' && mlbLogs.length > 0 && (
            <div className="rounded-xl border border-emerald-900/40 bg-gray-900/60 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-800">
                <span className="text-xs uppercase text-gray-500 tracking-wide font-semibold">
                  {fetched} · {isPitcher ? 'Pitching' : 'Batting'} · 2025 Season
                </span>
              </div>
              <div className="overflow-x-auto">
                {isPitcher ? (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-gray-500 uppercase tracking-wide border-b border-gray-800">
                        {['G','IP','H','R','ER','HR','BB','K','ERA','WHIP','K/9','BB/9','H/9'].map(h => (
                          <th key={h} className="px-4 py-2.5 text-right first:text-left font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="text-sm">
                        {[
                          [totalG,                          false],
                          [fmtIP(totalIP),                  false],
                          [mlbTotal('hits_allowed'),        false],
                          [mlbTotal('runs_allowed'),        false],
                          [mlbTotal('er'),                  false],
                          [mlbTotal('hr_allowed'),          false],
                          [mlbTotal('bb_allowed'),          false],
                          [mlbTotal('k'),                   true ],
                          [era.toFixed(2),                  false],
                          [whip.toFixed(2),                 false],
                          [k9.toFixed(1),                   true ],
                          [bb9.toFixed(1),                  false],
                          [h9.toFixed(1),                   false],
                        ].map(([val, highlight], i) => (
                          <td key={i} className={`px-4 py-3 text-right first:text-left font-mono ${highlight ? 'text-emerald-400 font-bold' : 'text-white'}`}>
                            {String(val)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-gray-500 uppercase tracking-wide border-b border-gray-800">
                        {['G','PA','AB','R','H','2B','3B','HR','RBI','SB','CS','BB','HBP','SO','TB','BA','OBP','SLG','OPS'].map(h => (
                          <th key={h} className="px-4 py-2.5 text-right first:text-left font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="text-sm">
                        {[
                          [totalG,                         false],
                          [totalPA,                        false],
                          [totalAB,                        false],
                          [mlbTotal('r'),                  false],
                          [totalH,                         false],
                          [total2B,                        false],
                          [total3B,                        false],
                          [totalHR,                        true ],
                          [mlbTotal('rbi'),                true ],
                          [mlbTotal('sb'),                 false],
                          [mlbTotal('cs'),                 false],
                          [totalBB,                        false],
                          [totalHBP,                       false],
                          [mlbTotal('so'),                 false],
                          [totalTB,                        false],
                          [fmtAvg(ba),                     true ],
                          [fmtAvg(obp),                    true ],
                          [fmtAvg(slg),                    true ],
                          [ops.toFixed(3),                 true ],
                        ].map(([val, highlight], i) => (
                          <td key={i} className={`px-4 py-3 text-right first:text-left font-mono ${highlight ? 'text-emerald-400 font-bold' : 'text-white'}`}>
                            {String(val)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* ── Active Props ── */}
          {sortedProps.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-3">
                Active Props ({sortedProps.length})
              </h2>
              <div className="overflow-x-auto rounded-xl border border-gray-800">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800 bg-gray-900/80 text-xs uppercase tracking-wide text-gray-500">
                      <th className="px-4 py-3 text-left">Stat</th>
                      <th className="px-4 py-3 text-center">Line</th>
                      <th className="px-4 py-3 text-center">Type</th>
                      {(['l5_hit_rate', 'l10_hit_rate', 'l20_hit_rate', 'last_percent_rate'] as SortKey[]).map((key, i) => (
                        <th key={key} onClick={() => handlePropSort(key)}
                          className="px-4 py-3 text-left min-w-[110px] cursor-pointer select-none hover:text-white transition-colors">
                          <span className="flex items-center gap-1">
                            {['L5','L10','L20','Best %'][i]}
                            <span className="text-gray-600">{propSort === key ? (propSortDir === 'desc' ? '▼' : '▲') : '⇅'}</span>
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/60">
                    {sortedProps.map(prop => {
                      const s = statsMap[prop.id];
                      return (
                        <tr key={prop.id} className="bg-gray-900/30 hover:bg-gray-800/50 transition-colors">
                          <td className="px-4 py-3 font-medium text-white">{prop.stat}</td>
                          <td className="px-4 py-3 text-center">
                            <span className="font-mono text-white">{prop.target}</span>
                            <span className={`ml-1.5 text-xs ${prop.over_under === 'over' ? 'text-green-400' : 'text-red-400'}`}>
                              {prop.over_under === 'over' ? '▲' : '▼'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${ODDS_STYLE[prop.odds_type] ?? ODDS_STYLE.standard}`}>
                              {prop.odds_type}
                            </span>
                          </td>
                          {s ? (
                            <>
                              <td className="px-4 py-3"><RateBar rate={s.l5_hit_rate} /></td>
                              <td className="px-4 py-3"><RateBar rate={s.l10_hit_rate} /></td>
                              <td className="px-4 py-3"><RateBar rate={s.l20_hit_rate} /></td>
                              <td className="px-4 py-3">
                                <span className="font-mono text-xs text-gray-300">{s.last_percent_total}</span>
                                <span className="ml-1 text-xs text-gray-500">({Math.round(s.last_percent_rate * 100)}%)</span>
                              </td>
                            </>
                          ) : (
                            <td colSpan={4} className="px-4 py-3 text-xs text-gray-600 text-center">No data</td>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── NBA Game Log ── */}
          {sport === 'NBA' && nbaLogs.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-3">Game Log</h2>
              <div className="overflow-x-auto rounded-xl border border-gray-800">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-800 bg-gray-900/80 text-gray-500 uppercase tracking-wide">
                      {['Date','Matchup','Min','PTS','REB','AST','STL','BLK','TOV','FGM/A','FG%','3PM/A','3P%','FTM/A','FT%'].map(h => (
                        <th key={h} className="px-3 py-2.5 text-left whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50">
                    {nbaLogs.map((log, i) => (
                      <tr key={i} className={`transition-colors hover:bg-gray-800/40 ${log.min === 0 ? 'opacity-40' : ''}`}>
                        <td className="px-3 py-2 text-gray-400 whitespace-nowrap">{log.game_date}</td>
                        <td className="px-3 py-2 text-gray-300 whitespace-nowrap">{log.matchup}</td>
                        <td className="px-3 py-2 text-gray-400">{log.min}</td>
                        <td className="px-3 py-2 font-medium text-white">{log.pts}</td>
                        <td className="px-3 py-2 text-gray-300">{log.reb}</td>
                        <td className="px-3 py-2 text-gray-300">{log.ast}</td>
                        <td className="px-3 py-2 text-gray-300">{num(log.stl)}</td>
                        <td className="px-3 py-2 text-gray-300">{num(log.blk)}</td>
                        <td className="px-3 py-2 text-gray-300">{num(log.tov)}</td>
                        <td className="px-3 py-2 text-gray-400">{log.fgm}-{log.fga}</td>
                        <td className="px-3 py-2 text-gray-400">{pct(log.fg_pct)}</td>
                        <td className="px-3 py-2 text-gray-400">{log.fg3m}-{log.fg3a}</td>
                        <td className="px-3 py-2 text-gray-400">{pct(log.fg3_pct)}</td>
                        <td className="px-3 py-2 text-gray-400">{log.ftm}-{log.fta}</td>
                        <td className="px-3 py-2 text-gray-400">{pct(log.ft_pct)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── MLB Game Log ── */}
          {sport === 'MLB' && mlbLogs.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-3">
                Game Log {isPitcher ? '(Pitching)' : '(Batting)'}
              </h2>
              <div className="overflow-x-auto rounded-xl border border-gray-800">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-800 bg-gray-900/80 text-gray-500 uppercase tracking-wide">
                      {isPitcher
                        ? ['Date','Matchup','IP','H','R','ER','HR','BB','K'].map(h => (
                            <th key={h} className="px-3 py-2.5 text-left whitespace-nowrap">{h}</th>
                          ))
                        : ['Date','Matchup','AB','R','H','2B','3B','HR','RBI','BB','SO','SB','AVG'].map(h => (
                            <th key={h} className="px-3 py-2.5 text-left whitespace-nowrap">{h}</th>
                          ))
                      }
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50">
                    {mlbLogs.map((log, i) => (
                      <tr key={i} className="transition-colors hover:bg-gray-800/40">
                        <td className="px-3 py-2 text-gray-400 whitespace-nowrap">{log.game_date}</td>
                        <td className="px-3 py-2 text-gray-300 whitespace-nowrap">{log.matchup}</td>
                        {isPitcher ? (
                          <>
                            <td className="px-3 py-2 font-medium text-white">{log.ip}</td>
                            <td className="px-3 py-2 text-gray-300">{log.hits_allowed}</td>
                            <td className="px-3 py-2 text-gray-300">{log.runs_allowed}</td>
                            <td className="px-3 py-2 text-gray-300">{log.er}</td>
                            <td className="px-3 py-2 text-gray-300">{num(log.hr)}</td>
                            <td className="px-3 py-2 text-gray-300">{log.bb_allowed}</td>
                            <td className="px-3 py-2 font-medium text-white">{log.k}</td>
                          </>
                        ) : (
                          <>
                            <td className="px-3 py-2 text-gray-300">{log.ab}</td>
                            <td className="px-3 py-2 text-gray-300">{log.r}</td>
                            <td className="px-3 py-2 font-medium text-white">{log.h}</td>
                            <td className="px-3 py-2 text-gray-300">{num(log.doubles)}</td>
                            <td className="px-3 py-2 text-gray-300">{num(log.triples)}</td>
                            <td className="px-3 py-2 text-gray-300">{num(log.hr)}</td>
                            <td className="px-3 py-2 text-gray-300">{log.rbi}</td>
                            <td className="px-3 py-2 text-gray-300">{num(log.bb)}</td>
                            <td className="px-3 py-2 text-gray-300">{num(log.so)}</td>
                            <td className="px-3 py-2 text-gray-300">{num(log.sb)}</td>
                            <td className="px-3 py-2 text-gray-400">{fmtAvg(log.ab > 0 ? log.h / log.ab : 0)}</td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
