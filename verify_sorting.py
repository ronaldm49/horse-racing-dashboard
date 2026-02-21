import requests
import json

BASE_URL = "http://localhost:8000"

def get_races():
    response = requests.get(f"{BASE_URL}/races")
    return response.json()

def monitor_race(url):
    response = requests.post(f"{BASE_URL}/monitor?url={url}")
    return response.json()

print("--- Initial State ---")
races = get_races()
if not races:
    print("No races found.")
    exit()

print(f"Top Race: ID {races[0]['id']} - {races[0]['name']} (Bumped: {races[0].get('last_bumped_at')})")
print(f"Bottom Race: ID {races[-1]['id']} - {races[-1]['name']} (Bumped: {races[-1].get('last_bumped_at')})")

# Pick bottom race to bump
target_race = races[-1]
print(f"\n--- Bumping Race {target_race['id']} ({target_race['url']}) ---")
monitor_race(target_race['url'])

print("\n--- After Bump ---")
races_new = get_races()
print(f"Top Race: ID {races_new[0]['id']} - {races_new[0]['name']} (Bumped: {races_new[0].get('last_bumped_at')})")

if races_new[0]['id'] == target_race['id']:
    print("\n✅ SUCCESS: Target race moved to top.")
else:
    print("\n❌ FAILURE: Target race did not move to top.")
