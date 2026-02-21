import time
from sqlmodel import Session, select, create_engine
from backend.models import Runner, Race

# Connect to DB
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url)

def verify_updates():
    print("Monitoring database for updates...")
    with Session(engine) as session:
        # Find an active race
        active_race = session.exec(select(Race).where(Race.is_active == True)).first()
        if not active_race:
            print("No active races found. Please add a race to the dashboard first.")
            return

        print(f"Monitoring Race: {active_race.name} ({active_race.url})")
        
        # Monitor a runner
        runner = session.exec(select(Runner).where(Runner.race_id == active_race.id)).first()
        if not runner:
            print("No runners found in active race.")
            return

        print(f"Tracking Runner: {runner.name}")
        
        last_ts = runner.last_updated
        print(f"Initial Update Time: {last_ts}")
        
        updates = []
        # Monitor for 20 seconds (40 * 0.5s)
        for i in range(40):
            time.sleep(0.5) 
            session.refresh(runner)
            current_ts = runner.last_updated
            
            # print(f"Check {i}: {current_ts}")
            
            if current_ts != last_ts:
                now = time.time()
                print(f"Update detected! New TS: {current_ts}")
                updates.append(time.time())
                last_ts = current_ts
                
        if len(updates) < 2:
            print(f"Only {len(updates)} updates detected. Is the scraper running?")
            return

        # Calculate intervals
        intervals = []
        for i in range(1, len(updates)):
            diff = updates[i] - updates[i-1]
            intervals.append(diff)
            print(f"Interval: {diff:.2f}s")
            
        avg = sum(intervals) / len(intervals)
        print(f"Average Interval: {avg:.2f}s")
        
        if 1.5 < avg < 2.5:
             print("SUCCESS: Interval is approximately 2 seconds.")
        else:
             print("WARNING: Interval is outside expected range.")

if __name__ == "__main__":
    verify_updates()
