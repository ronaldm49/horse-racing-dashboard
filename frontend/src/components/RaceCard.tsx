'use client';
import { useState, useEffect, useMemo } from 'react';
import { setBaseline, refreshRace } from '../lib/api';
import { Clock, LayoutList } from 'lucide-react';

interface Runner {
    id: number;
    name: string;
    number: number;
    silk_url?: string;
    current_odds: number;
    baseline_odds?: number;
    is_d4: boolean;
    status_text: string;
    steam_percentage: number;
    is_value: boolean;
    is_previous_steamer: boolean; // New
    is_non_runner?: boolean; // New
    jockey?: string; // New
    last_updated: string;
}

interface Race {
    id: number;
    url: string;
    name: string;
    baseline_set_at?: string;
    is_active: boolean;
    winner_name?: string;
    start_time?: string; // New
    runners: Runner[];
}

export default function RaceCard({ race, onRefresh }: { race: Race; onRefresh: () => void }) {
    const [loading, setLoading] = useState(false);
    const [sortConfig, setSortConfig] = useState<{ key: keyof Runner | 'steam_percentage' | 'flags'; direction: 'ascending' | 'descending' } | null>(null);
    const [timeLeft, setTimeLeft] = useState<string>('');

    useEffect(() => {
        if (!race.start_time) {
            setTimeLeft('');
            return;
        }

        const calculateTimeLeft = () => {
            const target = new Date(race.start_time!).getTime();
            const now = new Date().getTime();
            const diff = target - now;

            const absDiff = Math.abs(diff);
            const hours = Math.floor(absDiff / (1000 * 60 * 60));
            const minutes = Math.floor((absDiff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((absDiff % (1000 * 60)) / 1000);

            const sign = diff < 0 ? '+' : '-';
            const formatted = `${sign}${hours > 0 ? hours + ':' : ''}${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            setTimeLeft(formatted);
        };

        calculateTimeLeft();
        const interval = setInterval(calculateTimeLeft, 1000);
        return () => clearInterval(interval);
    }, [race.start_time]);

    const handleSetBaseline = async () => {
        setLoading(true);
        await setBaseline(race.id);
        setLoading(false);
        onRefresh();
    };

    const handleRefresh = async () => {
        setLoading(true);
        try {
            await refreshRace(race.id);
            onRefresh();
        } catch (e) {
            console.error("Refresh failed", e);
        }
        setLoading(false);
    };

    const displayRunners = useMemo(() => {
        return race.runners.filter(r => !r.is_non_runner && r.current_odds > 0);
    }, [race.runners]);

    const timeString = useMemo(() => {
        return race.start_time
            ? new Date(race.start_time).toLocaleTimeString('en-GB', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit' })
            : '';
    }, [race.start_time]);

    useEffect(() => {
        const alertRunners = displayRunners.filter(r => r.is_d4 && r.steam_percentage >= 10);
        if (alertRunners.length > 0 && race.is_active) {
            const audio = new Audio('/alert.mp3');
            audio.play().catch(e => console.log("Audio play failed", e));
        }
    }, [race, displayRunners]);

    const sortedRunners = useMemo(() => {
        return [...displayRunners].sort((a, b) => {
            if (!sortConfig) return 0;
            let aValue: any = a[sortConfig.key as keyof Runner];
            let bValue: any = b[sortConfig.key as keyof Runner];

            if (sortConfig.key === 'flags') {
                const getScore = (r: Runner) => {
                    let score = 0;
                    if (r.is_value) score += 4;
                    if (r.steam_percentage >= 10 && r.is_d4) score += 3;
                    if (r.is_d4) score += 2;
                    if (r.steam_percentage >= 10) score += 1;
                    if (r.is_previous_steamer) score += 0.5;
                    return score;
                };
                aValue = getScore(a);
                bValue = getScore(b);
            }

            if (aValue < bValue) return sortConfig.direction === 'ascending' ? -1 : 1;
            if (aValue > bValue) return sortConfig.direction === 'ascending' ? 1 : -1;
            return 0;
        });
    }, [displayRunners, sortConfig]);

    const requestSort = (key: keyof Runner | 'flags') => {
        let direction: 'ascending' | 'descending' = 'ascending';
        if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    const getSortIndicator = (key: string) => {
        if (!sortConfig || sortConfig.key !== key) return null;
        return <span className="ml-1 text-blue-400">{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>;
    };

    return (
        <div className={`bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-[2rem] overflow-hidden transition-all shadow-2xl ${!race.is_active ? 'opacity-60 saturate-50' : ''}`}>
            {/* Card Header */}
            <div className="p-8 pb-4 border-b border-slate-800/50 flex flex-wrap justify-between items-center gap-6 bg-gradient-to-br from-slate-800/20 to-transparent">
                <div className="space-y-2">
                    <div className="flex items-center gap-3">
                        <h2 className="text-2xl font-black text-white tracking-tight">{race.name}</h2>
                        {timeLeft && (
                            <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${timeLeft.startsWith('-')
                                ? (timeLeft.length < 6 ? 'bg-red-500 text-white animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.4)]' : 'bg-green-500/10 text-green-400 border border-green-500/20')
                                : 'bg-slate-800 text-slate-400 border border-slate-700'
                                }`}>
                                {timeLeft}
                            </div>
                        )}
                        {!race.is_active && (
                            <span className="bg-slate-800 text-slate-500 text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest border border-slate-700">Final</span>
                        )}
                    </div>
                    <div className="flex items-center gap-4 text-xs font-semibold text-slate-500">
                        <div className="flex items-center gap-1.5 uppercase tracking-widest bg-blue-500/5 text-blue-400/80 px-2 py-0.5 rounded-lg border border-blue-500/10">
                            <Clock size={12} />
                            {timeString} GMT
                        </div>
                        <a href={race.url} target="_blank" className="hover:text-blue-400 transition-colors truncate max-w-[240px] opacity-60 hover:opacity-100">
                            {race.url}
                        </a>
                    </div>
                </div>

                <div className="flex items-center gap-3 bg-slate-900/50 p-2 rounded-2xl border border-slate-800">
                    <div className="px-4 py-2 border-r border-slate-800">
                        {race.baseline_set_at ? (
                            <div className="flex flex-col">
                                <span className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Baseline IQ</span>
                                <span className="text-sm text-green-400 font-bold">{new Date(race.baseline_set_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>
                        ) : (
                            <span className="text-[10px] text-red-500 font-black uppercase tracking-widest">Awaiting Baseline</span>
                        )}
                    </div>

                    <div className="flex items-center gap-2 pl-2">
                        <button
                            onClick={handleRefresh}
                            disabled={loading}
                            className={`p-3 rounded-xl transition-all ${loading ? 'bg-slate-800 text-slate-600' : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 active:scale-90'}`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
                            </svg>
                        </button>
                        <button
                            onClick={handleSetBaseline}
                            disabled={loading}
                            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-black rounded-xl transition-all shadow-lg shadow-blue-600/20 active:scale-95 disabled:opacity-50 uppercase tracking-widest"
                        >
                            {loading ? '---' : 'Sync Baseline'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Table Area */}
            <div className="overflow-x-auto p-4 lg:p-6 pt-2">
                <table className="min-w-full text-left">
                    <thead>
                        <tr className="border-b border-slate-800/50">
                            {[
                                { label: 'N°', key: 'number' },
                                { label: 'Colours', key: null },
                                { label: 'Runner / Jockey', key: 'name' },
                                { label: 'Odds', key: 'current_odds' },
                                { label: 'Base', key: 'baseline_odds' },
                                { label: 'Steam %', key: 'steam_percentage' },
                                { label: 'Updated', key: 'last_updated' },
                                { label: 'Signals', key: 'flags' },
                            ].map((col) => (
                                <th
                                    key={col.label}
                                    className={`px-4 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 whitespace-nowrap drop-shadow-sm ${col.key ? 'cursor-pointer hover:text-white group transition-colors' : ''}`}
                                    onClick={() => col.key && requestSort(col.key as any)}
                                >
                                    <div className="flex items-center">
                                        {col.label}
                                        {col.key && getSortIndicator(col.key)}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/30">
                        {sortedRunners.map((runner) => {
                            const isSuperSteamer = runner.steam_percentage >= 15;
                            const isSteamer = runner.steam_percentage >= 10;
                            const isD4 = runner.is_d4;
                            const lastUpdatedTime = new Date(runner.last_updated).toLocaleTimeString();

                            return (
                                <tr key={runner.id} className={`group transition-all hover:bg-white/[0.05] ${isSuperSteamer ? 'bg-orange-500/[0.05]' : ''}`}>
                                    <td className="px-4 py-5">
                                        <span className="text-xl font-black text-white drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)] group-hover:text-blue-200 transition-colors">
                                            {runner.number > 0 ? runner.number : '—'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-5">
                                        <div className="relative group/silk">
                                            {runner.silk_url ? (
                                                <img src={runner.silk_url} alt="Silk" className="w-10 h-10 object-contain drop-shadow-2xl transform group-hover/silk:scale-125 transition-transform" />
                                            ) : (
                                                <div className="w-10 h-10 rounded-full bg-slate-800/50 border border-slate-700 flex items-center justify-center">
                                                    <span className="text-[10px] text-slate-400 font-bold">??</span>
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-4 py-5">
                                        <div className="flex flex-col">
                                            <span className="text-sm font-black text-white drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)] group-hover:text-blue-300 transition-colors uppercase tracking-tight">{runner.name}</span>
                                            {runner.jockey && (
                                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5 mt-0.5">
                                                    <div className="w-1 h-1 bg-slate-500 rounded-full"></div>
                                                    {runner.jockey}
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-4 py-5">
                                        <div className="inline-block px-3 py-1 bg-slate-800/80 border border-slate-600 rounded-lg shadow-lg">
                                            <span className="text-md font-black text-white drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)] tabular-nums">{runner.current_odds.toFixed(1)}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-5">
                                        <span className="text-sm font-bold text-slate-400 tabular-nums drop-shadow-sm">
                                            {runner.baseline_odds ? runner.baseline_odds.toFixed(1) : '—'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-5">
                                        <div className={`flex flex-col ${isSteamer ? 'text-green-400' : 'text-slate-400'}`}>
                                            <span className={`text-md font-black tabular-nums drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)] ${isSteamer ? 'animate-pulse' : ''}`}>
                                                {runner.steam_percentage > 0 ? '+' : ''}{runner.steam_percentage.toFixed(1)}%
                                            </span>
                                            <span className="text-[8px] font-black uppercase opacity-60 tracking-tighter">Velocity Spike</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-5">
                                        <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest tabular-nums drop-shadow-sm">
                                            {lastUpdatedTime}
                                        </span>
                                    </td>
                                    <td className="px-4 py-5">
                                        <div className="flex flex-wrap gap-2">
                                            {runner.is_value && (
                                                <div className="px-2 py-0.5 bg-purple-500/20 text-purple-300 border border-purple-500/40 rounded text-[9px] font-black uppercase tracking-widest flex items-center gap-1 shadow-sm">
                                                    <span className="w-1 h-1 bg-purple-300 rounded-full animate-pulse"></span>
                                                    Value
                                                </div>
                                            )}
                                            {isSteamer && isD4 && (
                                                <div className="px-2 py-0.5 bg-red-600 text-white rounded text-[9px] font-black uppercase tracking-widest flex items-center gap-1 shadow-lg shadow-red-500/20 animate-bounce">
                                                    High Signal
                                                </div>
                                            )}
                                            {runner.is_previous_steamer && (
                                                <div className="px-2 py-0.5 bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded text-[9px] font-black uppercase tracking-widest" title="Historical Steamer">
                                                    Repeat
                                                </div>
                                            )}
                                            {isD4 && (
                                                <div className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded text-[9px] font-black uppercase tracking-widest">
                                                    D4
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
                {race.runners.length === 0 && (
                    <div className="text-center py-20 bg-slate-900/40 rounded-3xl border border-dashed border-slate-800">
                        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4 opacity-40"></div>
                        <p className="text-slate-500 font-black uppercase tracking-widest text-xs">Awaiting Network Feed...</p>
                        <p className="text-[10px] text-slate-600 mt-2">Deep-scraping Zeturf race data...</p>
                    </div>
                )}
            </div>

            {/* Legend / Footer */}
            <div className="px-8 py-3 bg-slate-900/80 border-t border-slate-800 flex justify-between items-center">
                <div className="flex gap-4 opacity-40 hover:opacity-100 transition-opacity">
                    <div className="flex items-center gap-1.5 text-[8px] font-black text-slate-500 uppercase tracking-widest">
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                        Positive Drift
                    </div>
                    <div className="flex items-center gap-1.5 text-[8px] font-black text-slate-500 uppercase tracking-widest">
                        <div className="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
                        E/W Value
                    </div>
                </div>
                <div className="text-[8px] font-black text-slate-600 uppercase tracking-widest">
                    Last Tick Sync: {new Date().toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
}
