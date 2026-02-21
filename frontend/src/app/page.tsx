'use client';
import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { fetchRaces, monitorRace, resetDatabase } from '../lib/api';
import RaceCard from '../components/RaceCard';
import { LayoutList, Map, Clock, AlertCircle, Menu, X, Trash2 } from 'lucide-react';

interface Race {
    id: number;
    url: string;
    name: string;
    meeting: string;
    start_time?: string;
    runners: any[];
    is_active: boolean;
}

export default function Home() {
    const { data: races, error, mutate } = useSWR<Race[]>('/races', fetchRaces, {
        refreshInterval: 2000,
    });

    const [newUrl, setNewUrl] = useState('');
    const [adding, setAdding] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [resetting, setResetting] = useState(false);

    // Filter Races (Order handled by Backend)
    const filteredRaces = races || [];

    const handleAddStart = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newUrl) return;

        setAdding(true);
        try {
            await monitorRace(newUrl);
            setNewUrl('');
            mutate();
        } catch (err) {
            console.error(err);
            alert('Failed to add race URL');
        } finally {
            setAdding(false);
        }
    };

    const handleReset = async () => {
        if (!confirm("Are you sure? This will remove all races EXCEPT the latest one.")) return;
        setResetting(true);
        try {
            await resetDatabase();
            mutate();
        } catch (err) {
            console.error(err);
            alert('Failed to reset database');
        } finally {
            setResetting(false);
        }
    };

    return (
        <div className="flex min-h-screen bg-[#0f172a] text-slate-200 selection:bg-blue-500/30">
            {/* Mobile Menu Button */}
            <div className="lg:hidden fixed top-6 right-6 z-50">
                <button
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    className="p-3 bg-slate-800/80 backdrop-blur-md border border-slate-700/50 rounded-xl shadow-2xl transition-all active:scale-95"
                >
                    {mobileMenuOpen ? <X size={24} className="text-blue-400" /> : <Menu size={24} className="text-blue-400" />}
                </button>
            </div>

            {/* Sidebar Navigation */}
            <aside className={`
                fixed inset-y-0 left-0 z-40 w-72 bg-slate-900/40 backdrop-blur-xl border-r border-slate-800/50 transform transition-all duration-300 ease-out lg:translate-x-0
                ${mobileMenuOpen ? 'translate-x-0 shadow-[20px_0_50px_rgba(0,0,0,0.5)]' : '-translate-x-full'}
            `}>
                <div className="p-8">
                    <div className="flex items-center gap-3 group cursor-default">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-110 transition-transform">
                            <Map size={20} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight text-white">
                                Racing<span className="text-blue-400">Edge</span>
                            </h1>
                            <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-500">Zeturf intelligence</p>
                        </div>
                    </div>
                </div>

                <nav className="px-5 space-y-1.5 overflow-y-auto h-[calc(100vh-140px)] custom-scrollbar">
                    <div className="mb-6">
                        <button
                            className="w-full flex items-center gap-3 px-4 py-3.5 rounded-xl text-sm font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-[0_0_20px_rgba(59,130,246,0.1)] transition-all cursor-default"
                        >
                            <LayoutList size={20} />
                            All Live Races
                        </button>
                    </div>

                    <div className="mt-8 pt-8 border-t border-slate-800/50">
                        <div className="px-4 text-[10px] font-bold text-slate-500 uppercase tracking-[0.15em] mb-3">
                            Management
                        </div>
                        <button
                            onClick={handleReset}
                            disabled={resetting}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group text-slate-400 hover:text-red-400 hover:bg-slate-800/30 border border-transparent ${resetting ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <Trash2 size={18} className="group-hover:text-red-400 transition-colors" />
                            {resetting ? 'Cleaning...' : 'Reset Clean'}
                        </button>
                        <p className="px-4 mt-2 text-[10px] text-slate-600 leading-relaxed">
                            Clears all history except the most recent race.
                        </p>
                    </div>
                </nav>

                <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-slate-800/50 bg-slate-900/50">
                    <div className="flex items-center gap-3 p-3 bg-blue-500/5 rounded-xl border border-blue-500/10">
                        <div className="relative">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-ping absolute inset-0"></div>
                            <div className="w-2 h-2 bg-green-500 rounded-full relative"></div>
                        </div>
                        <span className="text-xs font-bold text-slate-300">Live Scraper Syncing</span>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 lg:ml-72 p-6 lg:p-12 transition-all">
                {/* Top Toolbar */}
                <div className="max-w-6xl mx-auto mb-12">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div>
                            <h2 className="text-3xl font-extrabold text-white tracking-tight">Dashboard</h2>
                            <p className="text-slate-400 mt-1">Real-time market insights & steamer detection</p>
                        </div>
                        <form onSubmit={handleAddStart} className="flex gap-2 bg-slate-800/50 p-1.5 rounded-2xl border border-slate-700/50 backdrop-blur-sm self-start md:self-center w-full md:w-auto">
                            <input
                                suppressHydrationWarning
                                type="url"
                                placeholder="Paste Zeturf race URL..."
                                value={newUrl}
                                onChange={(e) => setNewUrl(e.target.value)}
                                className="flex-1 bg-transparent border-none focus:ring-0 text-sm px-4 text-white placeholder:text-slate-500 w-full min-w-[280px]"
                            />
                            <button
                                type="submit"
                                disabled={adding}
                                className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 px-6 rounded-xl text-sm transition-all shadow-lg shadow-blue-600/20 disabled:opacity-50 active:scale-95"
                            >
                                {adding ? '...' : 'Track Race'}
                            </button>
                        </form>
                    </div>
                </div>

                {/* Status/Error */}
                {error && (
                    <div className="max-w-6xl mx-auto mb-8 p-6 bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl flex items-center gap-4 backdrop-blur-sm">
                        <div className="p-2 bg-red-500/20 rounded-lg">
                            <AlertCircle size={24} />
                        </div>
                        <div>
                            <p className="font-bold">Backend Connection Failed</p>
                            <p className="text-sm opacity-80">Please ensure the backend server is running on port 8000.</p>
                        </div>
                    </div>
                )}

                {/* Race List */}
                <div className="max-w-6xl mx-auto space-y-8">
                    {!races && !error && (
                        <div className="grid grid-cols-1 gap-6">
                            {[1, 2].map(i => (
                                <div key={i} className="h-96 bg-slate-800/30 rounded-3xl animate-pulse border border-slate-800"></div>
                            ))}
                        </div>
                    )}

                    {filteredRaces.length === 0 && races && races.length > 0 && (
                        <div className="text-slate-500 text-center py-24 bg-slate-800/20 rounded-3xl border border-dashed border-slate-800">
                            <LayoutList size={48} className="mx-auto mb-4 opacity-20" />
                            <h3 className="text-xl font-bold text-slate-300">No matches found</h3>
                            <p className="text-sm">Try selecting a different meeting or add a new race.</p>
                        </div>
                    )}

                    {filteredRaces.map((race: any) => (
                        <div key={race.id} className="transform transition-all hover:scale-[1.005]">
                            <RaceCard race={race} onRefresh={() => mutate()} />
                        </div>
                    ))}

                    {races && races.length === 0 && (
                        <div className="text-center py-32 bg-slate-800/20 rounded-[2.5rem] border border-dashed border-slate-700/50 backdrop-blur-sm">
                            <div className="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-6 border border-slate-700/50">
                                <Clock size={32} className="text-slate-500" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-2">Initialize Your Feed</h3>
                            <p className="text-slate-400 max-w-sm mx-auto">Track your first Zeturf race to begin receiving real-time market data and steamers.</p>
                            <button
                                onClick={() => document.querySelector('input')?.focus()}
                                className="mt-8 px-8 py-3 bg-white text-slate-900 font-bold rounded-2xl hover:bg-slate-200 transition-all active:scale-95 shadow-xl"
                            >
                                Get Started
                            </button>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
