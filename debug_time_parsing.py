
from datetime import datetime, timedelta

def parse_time(race_time_str):
    print(f"Parsing '{race_time_str}'")
    try:
        parts = race_time_str.split(":")  # 13:50 format?
        if "h" in race_time_str: # 13h50 format
            parts = race_time_str.split("h")
        
        print(f"Parts: {parts}")
        
        if len(parts) >= 2:
            hour = int(parts[0])
            minute = int(parts[1])
            print(f"Hour: {hour}, Minute: {minute}")
            
            now = datetime.utcnow()
            race_dt_cet = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            race_dt_utc = race_dt_cet - timedelta(hours=1) 
            print(f"Result (UTC): {race_dt_utc}")
            return race_dt_utc
        else:
            print("Not enough parts")
    except Exception as e:
        print(f"Error parsing time {race_time_str}: {e}")

parse_time("14h05")
parse_time("14:05")
