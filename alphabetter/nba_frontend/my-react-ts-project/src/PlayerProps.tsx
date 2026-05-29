import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, annotationPlugin);

import API_URL from './api';
const API = API_URL;

interface Prop {
  id: number;
  player_name: string;
  stat: string;
  target: number;
  over_under: string;
  odds_type: string;
  player_id: number;
  sport?: string;
}

interface Stat {
  prop_id: number;
  l5_hit_rate: number;
  l10_hit_rate: number;
  l20_hit_rate: number;
  last_percent_rate: number;
  last_percent_total: string;
}

interface GameLog {
  game_date: string;
  matchup: string;
  game_minutes: number;
  stat_value: number;
}

// Full Tailwind class strings — must be literals so the purger keeps them
const THEME = {
  NBA: {
    accent: 'text-blue-400',
    accentBg: 'bg-blue-600',
    accentBorder: 'border-blue-700/50',
    gradientFrom: 'from-blue-950/40',
    sliderAccent: 'accent-blue-500',
    sliderMax: 82,
    icon: '🏀',
    label: 'NBA',
  },
  MLB: {
    accent: 'text-emerald-400',
    accentBg: 'bg-emerald-600',
    accentBorder: 'border-emerald-700/50',
    gradientFrom: 'from-emerald-950/40',
    sliderAccent: 'accent-emerald-500',
    sliderMax: 162,
    icon: '⚾',
    label: 'MLB',
  },
} as const;

const ODDS_STYLE: Record<string, string> = {
  demon:    'bg-orange-900/50 text-orange-300 border border-orange-700/50',
  goblin:   'bg-purple-900/50 text-purple-300 border border-purple-700/50',
  standard: 'bg-slate-800 text-slate-300 border border-slate-600/50',
};

function RateBar({ rate }: { rate: number }) {
  const pct = Math.round(rate * 100);
  const bar = pct >= 60 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  const txt = pct >= 60 ? 'text-green-400' : pct >= 40 ? 'text-yellow-400' : 'text-red-400';
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="h-1.5 flex-1 rounded-full bg-gray-700">
        <div className={`h-full rounded-full ${bar}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-mono w-8 text-right ${txt}`}>{pct}%</span>
    </div>
  );
}

function PlayerAvatar({ playerId, name, sport }: { playerId: number; name: string; sport: 'NBA' | 'MLB' }) {
  const [failed, setFailed] = useState(false);
  const initials = name.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase();
  const league = sport === 'NBA' ? 'nba' : 'mlb';
  if (failed) {
    return (
      <div className="w-9 h-9 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-300 shrink-0">
        {initials}
      </div>
    );
  }
  return (
    <img
      src={`https://a.espncdn.com/i/headshots/${league}/players/full/${playerId}.png`}
      alt={name}
      className="w-9 h-9 rounded-full object-cover object-top bg-gray-800 shrink-0"
      onError={() => setFailed(true)}
    />
  );
}

type SortKey = 'l5_hit_rate' | 'l10_hit_rate' | 'l20_hit_rate' | 'last_percent_rate';
type TopTab = 'goblin' | 'demon' | 'std-over' | 'std-under';

export default function PlayerProps({ sport }: { sport: 'NBA' | 'MLB' }) {
  const theme = THEME[sport];

  const [props, setProps] = useState<Prop[]>([]);
  const [stats, setStats] = useState<Record<number, Stat>>({});
  const [selectedProp, setSelectedProp] = useState<Prop | null>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [chartOptions, setChartOptions] = useState<any>(null);
  const [chartKey, setChartKey] = useState(0);
  const [seasonAvg, setSeasonAvg] = useState<number | null>(null);
  const [sliderValue, setSliderValue] = useState(10);
  const [sortKey, setSortKey] = useState<SortKey>('l10_hit_rate');
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc');
  const [search, setSearch] = useState('');
  const [oddsFilter, setOddsFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState('');
  const [topPicksOpen, setTopPicksOpen] = useState(false);
  const [topTab, setTopTab] = useState<TopTab>('goblin');
  const [longShotsOpen, setLongShotsOpen] = useState(false);

  const loadData = () => {
    setLoading(true);
    return Promise.all([
      axios.get(`${API}/api/props`),
      axios.get(`${API}/api/player-stats-calculated`),
    ]).then(([propsRes, statsRes]) => {
      setProps(propsRes.data.props);
      const map: Record<number, Stat> = {};
      statsRes.data.stats.forEach((s: Stat) => { map[s.prop_id] = s; });
      setStats(map);
      setLoading(false);
    });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMsg('Fetching latest props and stats…');
    try {
      await axios.post(`${API}/api/fetch_and_calculate_all`);
      setRefreshMsg('Done! Reloading…');
      await loadData();
      setRefreshMsg('');
    } catch {
      setRefreshMsg('Refresh failed — check backend logs.');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  // Reset search/filter when sport changes
  useEffect(() => {
    setSearch('');
    setOddsFilter('all');
  }, [sport]);

  const filtered = useMemo(() => {
    return props
      .filter(p => {
        const q = search.toLowerCase();
        return (p.player_name.toLowerCase().includes(q) || p.stat.toLowerCase().includes(q)) &&
          (oddsFilter === 'all' || p.odds_type === oddsFilter) &&
          (p.sport ?? 'NBA') === sport;
      })
      .sort((a, b) => {
        const sa = stats[a.id]?.[sortKey] ?? 0;
        const sb = stats[b.id]?.[sortKey] ?? 0;
        return sortDir === 'desc' ? sb - sa : sa - sb;
      });
  }, [props, stats, search, oddsFilter, sortKey, sortDir, sport]);

  const topPicks = useMemo(() => {
    const pick = (tab: TopTab) => filtered
      .filter(p => {
        const s = stats[p.id];
        if (!s) return false;
        if (tab === 'goblin') return p.odds_type === 'goblin';
        if (tab === 'demon') return p.odds_type === 'demon';
        if (tab === 'std-over') return p.odds_type === 'standard' && p.over_under === 'over';
        if (tab === 'std-under') return p.odds_type === 'standard' && p.over_under === 'under';
        return false;
      })
      .sort((a, b) => (stats[b.id]?.last_percent_rate ?? 0) - (stats[a.id]?.last_percent_rate ?? 0))
      .slice(0, 8);
    return { goblin: pick('goblin'), demon: pick('demon'), 'std-over': pick('std-over'), 'std-under': pick('std-under') };
  }, [filtered, stats]);

  const longShots = useMemo(() => {
    return filtered
      .filter(p => { const s = stats[p.id]; return s && s.l10_hit_rate < 0.2 && s.l20_hit_rate < 0.25; })
      .sort((a, b) => (stats[a.id]?.l10_hit_rate ?? 1) - (stats[b.id]?.l10_hit_rate ?? 1))
      .slice(0, 20);
  }, [filtered, stats]);

  const topPicksCount = useMemo(() =>
    filtered.filter(p => stats[p.id]?.last_percent_rate >= 0.7).length,
  [filtered, stats]);

  const topPickBest = useMemo(() =>
    filtered.filter(p => stats[p.id]?.last_percent_rate >= 0.7)
      .sort((a, b) => (stats[b.id]?.last_percent_rate ?? 0) - (stats[a.id]?.last_percent_rate ?? 0))[0] ?? null,
  [filtered, stats]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const fetchChart = async (prop: Prop, games: number, isNewProp = false) => {
    const res = await fetch(`${API}/api/last_x/${prop.id}/${games}`);
    const result = await res.json();
    if (!result.game_logs) return;

    if (isNewProp) {
      const allRes = await fetch(`${API}/api/last_x/${prop.id}/${theme.sliderMax}`);
      const allResult = await allRes.json();
      if (allResult.game_logs?.length) {
        const active = allResult.game_logs.filter((l: GameLog) => l.game_minutes > 0);
        const avg = active.length ? active.reduce((s: number, l: GameLog) => s + l.stat_value, 0) / active.length : 0;
        setSeasonAvg(Math.round(avg * 10) / 10);
      }
    }

    const labels = result.game_logs.map((l: GameLog) => `${l.game_date}  ${l.matchup}`);
    const values = result.game_logs.map((l: GameLog) => l.stat_value);
    const target = result.prop.target;
    const isOver = result.prop.over_under === 'over';
    const colors = values.map((v: number) => (isOver ? v >= target : v <= target)
      ? 'rgba(34,197,94,0.8)' : 'rgba(239,68,68,0.7)');

    setChartKey(k => k + 1);
    setChartData({
      labels,
      datasets: [{ label: result.prop.stat, data: values, backgroundColor: colors, borderRadius: 4, borderWidth: 0 }],
    });
    setChartOptions({
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        annotation: {
          annotations: {
            line: {
              type: 'line' as const, yMin: target, yMax: target,
              borderColor: 'rgba(251,191,36,0.9)', borderWidth: 2, borderDash: [6, 4],
              label: { content: `Line: ${target}`, display: true, position: 'end', backgroundColor: 'rgba(251,191,36,0.15)', color: '#fbbf24', font: { size: 11 } },
            },
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx: any) => {
              const log = result.game_logs[ctx.dataIndex];
              return [`${result.prop.stat}: ${ctx.raw}`, `Min: ${log.game_minutes}`];
            },
          },
        },
      },
      scales: {
        x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#1e293b' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
      },
    });
  };

  const closeModal = () => { setSelectedProp(null); setSeasonAvg(null); };
  const closeAll = () => { closeModal(); setTopPicksOpen(false); setLongShotsOpen(false); };

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') closeAll(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const handleRowClick = (prop: Prop) => {
    setSelectedProp(prop);
    setSeasonAvg(null);
    fetchChart(prop, sliderValue, true);
  };

  const TOP_TABS: { key: TopTab; label: string }[] = [
    { key: 'goblin', label: '👺 Goblin' },
    { key: 'demon', label: '😈 Demon' },
    { key: 'std-over', label: 'Standard ↑' },
    { key: 'std-under', label: 'Standard ↓' },
  ];

  const currentTopPicks = topPicks[topTab];

  return (
    <div className="space-y-5">

      {/* Sport header strip */}
      <div className={`-mx-4 px-4 pt-5 pb-4 bg-gradient-to-b ${theme.gradientFrom} to-transparent`}>
        <h1 className="text-2xl font-bold text-white">{theme.icon} {sport} Props</h1>
        <p className="text-sm text-gray-500 mt-0.5">Live PrizePicks lines</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3">

        {/* Total Props */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 px-4 py-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Total Props</p>
          <p className={`mt-1 text-3xl font-bold ${theme.accent}`}>{filtered.length}</p>
          <p className="text-xs text-gray-600 mt-1">active lines</p>
        </div>

        {/* Top Picks */}
        <button
          onClick={() => setTopPicksOpen(true)}
          className="rounded-xl border border-gray-700 bg-gray-900/60 px-4 py-4 text-left hover:border-gray-600 hover:bg-gray-800/60 transition-all group"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Top Picks</p>
            <span className="text-gray-600 group-hover:text-gray-400 text-xs">→</span>
          </div>
          <p className="mt-1 text-3xl font-bold text-green-400">{topPicksCount}</p>
          {topPickBest ? (
            <p className="text-xs text-gray-500 mt-1 truncate">{topPickBest.player_name} · {topPickBest.stat}</p>
          ) : (
            <p className="text-xs text-gray-600 mt-1">high-confidence bets</p>
          )}
        </button>

        {/* Long Shots */}
        <button
          onClick={() => setLongShotsOpen(true)}
          className="rounded-xl border border-gray-700 bg-gray-900/60 px-4 py-4 text-left hover:border-red-900/60 hover:bg-red-950/20 transition-all group"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Long Shots</p>
            <span className="text-gray-600 group-hover:text-red-500 text-xs">→</span>
          </div>
          <p className="mt-1 text-3xl font-bold text-red-500">{longShots.length}</p>
          <p className="text-xs text-gray-600 mt-1">props to avoid</p>
        </button>

      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="h-8 rounded-lg bg-gray-800 px-4 text-xs font-medium text-gray-300 hover:bg-gray-700 hover:text-white disabled:opacity-50 transition-colors"
        >
          {refreshing ? '↻ Refreshing…' : '↻ Refresh'}
        </button>
        {refreshMsg && <span className="text-xs text-gray-400">{refreshMsg}</span>}
        <div className="flex-1" />
        <input
          type="text"
          placeholder="Search player or stat…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="h-9 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm text-white placeholder-gray-500 focus:border-gray-500 focus:outline-none w-52"
        />
        <select
          value={oddsFilter}
          onChange={e => setOddsFilter(e.target.value)}
          className="h-9 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm text-white focus:border-gray-500 focus:outline-none"
        >
          <option value="all">All Types</option>
          <option value="demon">Demon</option>
          <option value="goblin">Goblin</option>
          <option value="standard">Standard</option>
        </select>
      </div>

      <p className="text-xs text-gray-600">{filtered.length} props</p>

      {/* Table */}
      {loading ? (
        <div className="flex h-40 items-center justify-center text-gray-500">Loading…</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/80 text-xs uppercase tracking-wide text-gray-500">
                <th className="px-4 py-3 text-left" colSpan={2}>Player</th>
                <th className="px-4 py-3 text-left">Stat</th>
                <th className="px-4 py-3 text-center">Line</th>
                <th className="px-4 py-3 text-center">Type</th>
                {(['l5_hit_rate', 'l10_hit_rate', 'l20_hit_rate', 'last_percent_rate'] as SortKey[]).map((key, i) => (
                  <th
                    key={key}
                    onClick={() => handleSort(key)}
                    className="px-4 py-3 text-left min-w-[110px] cursor-pointer select-none hover:text-white transition-colors"
                  >
                    <span className="flex items-center gap-1">
                      {['L5', 'L10', 'L20', 'Best %'][i]}
                      <span className="text-gray-600">{sortKey === key ? (sortDir === 'desc' ? '▼' : '▲') : '⇅'}</span>
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filtered.map(prop => {
                const s = stats[prop.id];
                return (
                  <tr
                    key={prop.id}
                    onClick={() => handleRowClick(prop)}
                    className="cursor-pointer bg-gray-900/30 transition-colors hover:bg-gray-800/50"
                  >
                    <td className="pl-4 pr-2 py-2.5">
                      <PlayerAvatar playerId={prop.player_id} name={prop.player_name} sport={sport} />
                    </td>
                    <td className="px-2 py-2.5 font-medium text-white whitespace-nowrap">{prop.player_name}</td>
                    <td className="px-4 py-2.5 text-gray-300">{prop.stat}</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="font-mono text-white">{prop.target}</span>
                      <span className={`ml-1.5 text-xs ${prop.over_under === 'over' ? 'text-green-400' : 'text-red-400'}`}>
                        {prop.over_under === 'over' ? '▲' : '▼'}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${ODDS_STYLE[prop.odds_type] ?? ODDS_STYLE.standard}`}>
                        {prop.odds_type}
                      </span>
                    </td>
                    {s ? (
                      <>
                        <td className="px-4 py-2.5"><RateBar rate={s.l5_hit_rate} /></td>
                        <td className="px-4 py-2.5"><RateBar rate={s.l10_hit_rate} /></td>
                        <td className="px-4 py-2.5"><RateBar rate={s.l20_hit_rate} /></td>
                        <td className="px-4 py-2.5">
                          <span className="font-mono text-xs text-gray-300">{s.last_percent_total}</span>
                          <span className="ml-1 text-xs text-gray-500">({Math.round(s.last_percent_rate * 100)}%)</span>
                        </td>
                      </>
                    ) : (
                      <td colSpan={4} className="px-4 py-2.5 text-gray-700 text-center text-xs">—</td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Top Picks Modal ─────────────────────────────────── */}
      {topPicksOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm" onClick={() => setTopPicksOpen(false)} />
          <div className="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-xl -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-gray-700 bg-gray-900 shadow-2xl overflow-hidden">
            <div className="px-6 pt-5 pb-4 border-b border-gray-800 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">🎯 Top Picks</h2>
                <p className="text-xs text-gray-500 mt-0.5">Best % — most consistent recent form</p>
              </div>
              <button onClick={() => setTopPicksOpen(false)} className="text-gray-500 hover:text-white p-1.5 rounded-lg hover:bg-gray-800">✕</button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 px-4 pt-3 pb-2">
              {TOP_TABS.map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setTopTab(key)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                    topTab === key ? `${theme.accentBg} text-white` : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Picks list */}
            <div className="px-4 pb-4 max-h-96 overflow-y-auto space-y-2">
              {currentTopPicks.length === 0 ? (
                <p className="text-gray-600 text-sm py-6 text-center">No picks in this category right now.</p>
              ) : currentTopPicks.map(prop => {
                const s = stats[prop.id];
                return (
                  <div
                    key={prop.id}
                    onClick={() => { setTopPicksOpen(false); handleRowClick(prop); }}
                    className="flex items-center gap-3 rounded-xl border border-gray-800 bg-gray-800/40 px-4 py-3 cursor-pointer hover:bg-gray-700/50 transition-colors"
                  >
                    <PlayerAvatar playerId={prop.player_id} name={prop.player_name} sport={sport} />
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-white text-sm truncate">{prop.player_name}</p>
                      <p className="text-xs text-gray-400 truncate">
                        {prop.stat} &nbsp;·&nbsp; <span className="font-mono">{prop.target}</span>
                        <span className={`ml-1 ${prop.over_under === 'over' ? 'text-green-400' : 'text-red-400'}`}>
                          {prop.over_under === 'over' ? '▲' : '▼'}
                        </span>
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-bold text-green-400">{s?.last_percent_total}</p>
                      <p className="text-xs text-gray-500">L10: {Math.round((s?.l10_hit_rate ?? 0) * 100)}%</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* ── Long Shots Modal ────────────────────────────────── */}
      {longShotsOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm" onClick={() => setLongShotsOpen(false)} />
          <div className="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-xl -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-red-900/50 bg-gray-900 shadow-2xl overflow-hidden">
            <div className="px-6 pt-5 pb-4 border-b border-red-900/40 bg-red-950/20 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-red-400">🚫 Long Shots</h2>
                <p className="text-xs text-gray-500 mt-0.5">These hit less than 20% in the last 10 games. You've been warned.</p>
              </div>
              <button onClick={() => setLongShotsOpen(false)} className="text-gray-500 hover:text-white p-1.5 rounded-lg hover:bg-gray-800">✕</button>
            </div>

            <div className="px-4 py-4 max-h-96 overflow-y-auto space-y-2">
              {longShots.length === 0 ? (
                <p className="text-gray-600 text-sm py-6 text-center">No catastrophically bad bets right now.</p>
              ) : longShots.map(prop => {
                const s = stats[prop.id];
                return (
                  <div
                    key={prop.id}
                    onClick={() => { setLongShotsOpen(false); handleRowClick(prop); }}
                    className="flex items-center gap-3 rounded-xl border border-red-900/30 bg-red-950/10 px-4 py-3 cursor-pointer hover:bg-red-950/20 transition-colors"
                  >
                    <PlayerAvatar playerId={prop.player_id} name={prop.player_name} sport={sport} />
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-300 text-sm truncate">{prop.player_name}</p>
                      <p className="text-xs text-gray-500 truncate">
                        {prop.stat} &nbsp;·&nbsp; <span className="font-mono">{prop.target}</span>
                        <span className={`ml-1 ${prop.over_under === 'over' ? 'text-green-600' : 'text-red-600'}`}>
                          {prop.over_under === 'over' ? '▲' : '▼'}
                        </span>
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-bold text-red-500">L10: {Math.round((s?.l10_hit_rate ?? 0) * 100)}%</p>
                      <p className="text-xs text-red-700">L20: {Math.round((s?.l20_hit_rate ?? 0) * 100)}%</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* ── Chart Modal ─────────────────────────────────────── */}
      {selectedProp && (
        <>
          <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm" onClick={closeModal} />
          <div className="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-2xl -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-gray-700 bg-gray-900 p-6 shadow-2xl">
            <div className="mb-4 flex items-start justify-between">
              <div className="flex items-center gap-3">
                <PlayerAvatar playerId={selectedProp.player_id} name={selectedProp.player_name} sport={sport} />
                <div>
                  <h2 className="text-lg font-bold text-white">{selectedProp.player_name}</h2>
                  <p className="text-sm text-gray-400">
                    {selectedProp.stat} &mdash; Line: <span className="font-mono text-white">{selectedProp.target}</span>
                    <span className={`ml-2 text-xs ${selectedProp.over_under === 'over' ? 'text-green-400' : 'text-red-400'}`}>
                      {selectedProp.over_under.toUpperCase()}
                    </span>
                    {seasonAvg !== null && (
                      <span className="ml-3 text-xs text-gray-500">
                        Season avg: <span className={`font-mono ${seasonAvg >= selectedProp.target ? 'text-green-400' : 'text-red-400'}`}>{seasonAvg}</span>
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <button onClick={closeModal} className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-800 hover:text-white">✕</button>
            </div>

            {stats[selectedProp.id] && (
              <div className="mb-4 flex gap-3">
                {(['l5', 'l10', 'l20'] as const).map(k => {
                  const rate = stats[selectedProp.id][`${k}_hit_rate` as SortKey];
                  const pct = Math.round(rate * 100);
                  const color = pct >= 60 ? 'text-green-400 bg-green-900/30 border-green-800' : pct >= 40 ? 'text-yellow-400 bg-yellow-900/30 border-yellow-800' : 'text-red-400 bg-red-900/30 border-red-800';
                  return (
                    <div key={k} className={`rounded-lg border px-3 py-1.5 text-center ${color}`}>
                      <p className="text-xs text-gray-500 uppercase">{k.toUpperCase()}</p>
                      <p className="text-lg font-bold">{pct}%</p>
                    </div>
                  );
                })}
                <div className={`rounded-lg border ${theme.accentBorder} bg-gray-800/40 px-3 py-1.5 text-center`}>
                  <p className="text-xs text-gray-500 uppercase">Best %</p>
                  <p className={`text-lg font-bold ${theme.accent}`}>{stats[selectedProp.id].last_percent_total}</p>
                </div>
              </div>
            )}

            <div className="h-56">
              {chartData && chartOptions && <Bar key={chartKey} data={chartData} options={chartOptions} />}
            </div>

            <div className="mt-4">
              <label className="mb-1 flex justify-between text-xs text-gray-400">
                <span>Games shown</span>
                <span className="font-mono text-white">{sliderValue}</span>
              </label>
              <input
                type="range" min={5} max={theme.sliderMax} value={sliderValue}
                onChange={e => { const v = Number(e.target.value); setSliderValue(v); if (selectedProp) fetchChart(selectedProp, v); }}
                className={`w-full ${theme.sliderAccent}`}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
