const API_URL = 'https://horse-racing-backend.fly.dev';

export async function fetchRaces() {
    const res = await fetch(`${API_URL}/races`, { cache: 'no-store' });
    if (!res.ok) {
        throw new Error('Failed to fetch data');
    }
    return res.json();
}

export async function monitorRace(url: string) {
    const res = await fetch(`${API_URL}/monitor?url=${encodeURIComponent(url)}`, {
        method: 'POST',
    });
    return res.json();
}

export async function setBaseline(raceId: number) {
    const res = await fetch(`${API_URL}/baseline/${raceId}`, {
        method: 'POST',
    });
    return res.json();
}

export async function refreshRace(raceId: number) {
    const res = await fetch(`${API_URL}/refresh/${raceId}`, {
        method: 'POST',
    });
    return res.json();
}

export async function resetDatabase() {
    const res = await fetch(`${API_URL}/reset`, {
        method: 'POST',
    });
    return res.json();
}
