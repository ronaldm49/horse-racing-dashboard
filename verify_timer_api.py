
import requests
import json
from datetime import datetime

try:
    response = requests.get("http://127.0.0.1:8000/races")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} races.")
        if data:
            print("Sample Race Data (Top Item):")
            race = data[0]
            print(f"ID: {race.get('id')}")
            print(f"Name: {race.get('name')}")
            print(f"Bumped: {race.get('last_bumped_at')}")
            print(f"Start Time: {race.get('start_time')}")
            
            if race.get('start_time'):
                print("✅ Start time present.")
            else:
                print("❌ Start time missing.")
    else:
        print(f"Failed to fetch races: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
