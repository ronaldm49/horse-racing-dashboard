from fastapi import FastAPI, Depends, BackgroundTasks
from sqlmodel import Session, select
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
import time
from datetime import datetime, timedelta

from database import create_db_and_tables, get_session, engine
from models import Race, Runner, OddsHistory, WinnerHistory
from scraper import ZeturfScraper

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = ZeturfScraper()

@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    # Start scraper (Browser)
    await scraper.start()
    
    # Initial Auto-Discovery (Disabled to maintain clean slate)
    # asyncio.create_task(init_todays_races())
    
    # Start background orchestrator
    asyncio.create_task(monitor_orchestrator())

@app.on_event("shutdown")
async def on_shutdown():
    await scraper.stop()

async def init_todays_races():
    """Auto-discover today's French Trotting races."""
    print("Auto-discovering today's races...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    race_urls = await scraper.scrape_daily_program(today_str)
    
    with Session(engine) as session:
        count = 0
        for url in race_urls:
            # Check if exists
            existing = session.exec(select(Race).where(Race.url == url)).first()
            if not existing:
                # Add new race
                # We don't have the name yet, will get it on first scrape
                race = Race(url=url, name="Wait for scrape...", meeting="Unknown")
                session.add(race)
                count += 1
        session.commit()
    print(f"Auto-discovery complete. Added {count} new races.")

monitoring_tasks = {}

async def monitor_orchestrator():
    print("Starting Orchestrator...")
    while True:
        try:
            with Session(engine) as session:
                active_races = session.exec(select(Race).where(Race.is_active == True)).all()
                # Monitor only the latest active race (prioritizing bumped ones)
                active_races = session.exec(select(Race).where(Race.is_active == True).order_by(Race.last_bumped_at.desc(), Race.id.desc()).limit(1)).all()
                active_ids = {r.id for r in active_races}
                
                # Start new tasks
                for race in active_races:
                    if race.id not in monitoring_tasks:
                        print(f"Orchestrator: Starting task for Race {race.id}")
                        task = asyncio.create_task(monitor_race_task(race.id))
                        monitoring_tasks[race.id] = task
                
                # Cancel stopped tasks
                current_task_ids = list(monitoring_tasks.keys())
                for rid in current_task_ids:
                    if rid not in active_ids:
                        print(f"Orchestrator: Stopping task for Race {rid}")
                        monitoring_tasks[rid].cancel()
                        del monitoring_tasks[rid]
            
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Orchestrator error: {e}")
            await asyncio.sleep(5)

async def monitor_race_task(race_id: int):
    page = None
    try:
        while True:
            # Ensure we have a valid page
            if page is None:
                try:
                    page = await scraper.get_new_page()
                    print(f"Task for Race {race_id}: Page created.")
                except Exception as e:
                    print(f"Task {race_id}: Failed to get page ({e}). Retrying...")
                    await asyncio.sleep(2)
                    continue

            start_time = time.time()
            try:
                with Session(engine) as session:
                    race = session.get(Race, race_id)
                    if not race or not race.is_active:
                        print(f"Race {race_id} inactive. Stopping.")
                        break
                    
                    # Scrape
                    scrape_result = await scraper.scrape_race(race.url, page=page)
                    
                    if scrape_result:
                        save_race_data(session, race, scrape_result)
                    else:
                        print(f"Failed to scrape Race {race.id}")
                    
                    session.commit()
                    
                    # Check Result
                    winner_name, final_odds = await scraper.scrape_race_result(race.url, page=page)
                    if winner_name:
                        print(f"Result for {race.name}: {winner_name}")
                        race.winner_name = winner_name
                        race.result_checked = True
                        race.is_active = False
                        session.add(race)
                        
                        # Handle History
                        winner_runner = session.exec(select(Runner).where(Runner.race_id == race.id, Runner.name == winner_name)).first()
                        if winner_runner:
                            steam_pct = winner_runner.steam_percentage
                            is_steamer = steam_pct >= 10.0
                            history = WinnerHistory(
                                horse_name=winner_name,
                                race_date=datetime.utcnow(),
                                final_odds=final_odds,
                                steam_percentage=steam_pct,
                                is_steamer=is_steamer
                            )
                            session.add(history)
                        session.commit()
                        break # End task since inactive

                    # AUTO-SWITCH logic: 10 minutes after start
                    if race.start_time:
                         # 10 minutes past start
                         switch_threshold = race.start_time + timedelta(minutes=10)
                         if datetime.utcnow() > switch_threshold:
                             print(f"Race {race.id} is 10mins past start. Checking for next race...")
                             if race.next_race_url:
                                 # Check if next race already exists
                                 next_exists = session.exec(select(Race).where(Race.url == race.next_race_url)).first()
                                 if not next_exists:
                                     print(f"Auto-switching to next race: {race.next_race_url}")
                                     new_race = Race(url=race.next_race_url, name="Next Race (Loading...)", meeting=race.meeting)
                                     session.add(new_race)
                                     
                                     # Mark current as inactive so orchestrator picks up the new one
                                     race.is_active = False
                                     session.add(race)
                                     session.commit()
                                     break # End current task
                                 else:
                                     # Already exists, just stop this one
                                     race.is_active = False
                                     session.add(race)
                                     session.commit()
                                     break

            except Exception as e:
                print(f"Error in task {race_id}: {e} (Resetting page)")
                # Kill bad page
                try:
                    await page.close()
                except:
                    pass
                page = None
            
            # Sleep logic
            elapsed = time.time() - start_time
            sleep_time = max(0.1, 2.0 - elapsed)
            # print(f"Race {race_id} took {elapsed:.2f}s. Sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

    except asyncio.CancelledError:
        print(f"Task {race_id} cancelled.")
    except Exception as e:
        print(f"Fatal error in task {race_id}: {e}")
    finally:
        if page:
            try:
                await page.close()
            except:
                pass
            print(f"Task {race_id}: Page closed.")

def save_race_data(session, race, scrape_result):
    runners_data = scrape_result["runners"]
    race_title = scrape_result["title"]
    race_time_str = scrape_result.get("time_str")
    race_timestamp = scrape_result.get("timestamp")
    
    # Update race title/time if needed
    if race.name == "Wait for scrape..." and race_title:
        race.name = race_title
    
    # Parse time
    if not race.start_time:
        if race_timestamp:
            try:
                # detailed timestamp is usually in seconds for Zeturf based on verification
                race.start_time = datetime.utcfromtimestamp(race_timestamp)
            except Exception as e:
                print(f"Error parsing timestamp {race_timestamp}: {e}")
        
        elif race_time_str:
            try:
                parts = race_time_str.split(":")  # 13:50 format?
                if "h" in race_time_str: # 13h50 format
                    parts = race_time_str.split("h")
                
                if len(parts) >= 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    now = datetime.utcnow()
                    # Zeturf uses CET/CEST usually.
                    # If we parsed "13h50", that is likely CET.
                    race_dt_cet = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    # User feedback: Zeturf time is likely already accurate for display or strictly UTC in context of issue
                    # Previously we did -1 hour. User said it was 1 hour behind. So we remove the subtraction.
                    race.start_time = race_dt_cet
            except Exception as e:
                print(f"Error parsing time {race_time_str}: {e}")

    session.add(race)
        
    current_runners_count = len(runners_data)
    
    for r_data in runners_data:
            runner = session.exec(select(Runner).where(Runner.race_id == race.id, Runner.name == r_data["name"])).first()
            is_nr = r_data.get("is_non_runner", False)
            
            if not runner:
                history = session.exec(select(WinnerHistory).where(WinnerHistory.horse_name == r_data["name"], WinnerHistory.is_steamer == True)).first()
                is_prev_steamer = True if history else False

                runner = Runner(
                    race_id=race.id,
                    name=r_data["name"],
                    number=r_data.get("number", 0),
                    silk_url=r_data.get("silk_url"),
                    current_odds=r_data["odds"],
                    is_d4=r_data["is_d4"],
                    status_text=r_data["shoeing_status"],
                    is_previous_steamer=is_prev_steamer,
                    is_non_runner=is_nr,
                    jockey=r_data.get("jockey")
                )
                session.add(runner)
            else:
                # Only update last_updated if actual data changes to help frontend caching
                has_changed = False
                if runner.current_odds != r_data["odds"]:
                    runner.current_odds = r_data["odds"]
                    has_changed = True
                if runner.is_d4 != r_data["is_d4"]:
                    runner.is_d4 = r_data["is_d4"] 
                    has_changed = True
                if runner.status_text != r_data["shoeing_status"]:
                    runner.status_text = r_data["shoeing_status"]
                    has_changed = True
                if runner.is_non_runner != is_nr:
                    runner.is_non_runner = is_nr
                    has_changed = True
                if r_data.get("number") and runner.number != r_data["number"]:
                    runner.number = r_data["number"]
                    has_changed = True
                if r_data.get("silk_url") and runner.silk_url != r_data.get("silk_url"):
                    runner.silk_url = r_data.get("silk_url")
                    has_changed = True
                if r_data.get("jockey") and runner.jockey != r_data.get("jockey"):
                    runner.jockey = r_data.get("jockey")
                    has_changed = True
                
                if has_changed:
                    runner.last_updated = datetime.utcnow()
            
            if not is_nr:
                if runner.baseline_odds and runner.baseline_odds > 0:
                     obs_diff = runner.baseline_odds - runner.current_odds
                     runner.steam_percentage = (obs_diff / runner.baseline_odds) * 100
                else:
                     runner.steam_percentage = 0.0
                
                if runner.current_odds > 8.0 and current_runners_count >= 8:
                    runner.is_value = True
                else:
                    runner.is_value = False
            else:
                 runner.steam_percentage = 0.0
                 runner.is_value = False
                
            session.add(runner)

@app.post("/monitor")
async def monitor_race(url: str, session: Session = Depends(get_session)):
    # Check if exists
    existing = session.exec(select(Race).where(Race.url == url)).first()
    if existing:
        # Bump to top
        existing.last_bumped_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        return {"message": "Already monitoring (Bumped to top)", "id": existing.id}
    
    race = Race(url=url, name="Wait for scrape...", meeting="Unknown")
    # last_bumped_at is set by default_factory
    session.add(race)
    session.commit()
    session.refresh(race)
    return {"message": "Added race", "id": race.id}

@app.post("/baseline/{race_id}")
async def set_baseline(race_id: int, session: Session = Depends(get_session)):
    race = session.get(Race, race_id)
    if not race:
        return {"error": "Race not found"}
    
    runners = session.exec(select(Runner).where(Runner.race_id == race_id)).all()
    for runner in runners:
        runner.baseline_odds = runner.current_odds
        runner.steam_percentage = 0.0 # Reset steam on new baseline
        session.add(runner)
    
    race.baseline_set_at = datetime.utcnow()
    session.add(race)
    session.commit()
    return {"message": "Baseline set"}

@app.post("/refresh/{race_id}")
async def refresh_race(race_id: int, session: Session = Depends(get_session)):
    race = session.get(Race, race_id)
    if not race:
        return {"error": "Race not found"}
    
    # Trigger immediate scrape
    print(f"Manual refresh for {race.url}...")
    scrape_result = await scraper.scrape_race(race.url)
    
    if not scrape_result:
        return {"error": "Scrape failed"}
        
    runners_data = scrape_result["runners"]
    
    # Use the shared save function to update DB
    save_race_data(session, race, scrape_result)
    
    session.commit()
    return {"message": "Refreshed"}

@app.get("/races")
async def get_races(session: Session = Depends(get_session)):
    # Return all races, sorted by is_active (True first), then last_bumped_at desc
    races = session.exec(select(Race).order_by(Race.is_active.desc(), Race.last_bumped_at.desc(), Race.id.desc())).all()
    
    # Pre-fetch all runners to avoid N+1 queries
    race_ids = [r.id for r in races]
    all_runners = session.exec(select(Runner).where(Runner.race_id.in_(race_ids))).all() if race_ids else []
    
    runners_by_race = {rid: [] for rid in race_ids}
    for runner in all_runners:
        runners_by_race[runner.race_id].append(runner)
        
    data = []
    for race in races:
        data.append({
            "id": race.id,
            "url": race.url,
            "name": race.name,
            "start_time": race.start_time,
            "baseline_set_at": race.baseline_set_at,
            "last_bumped_at": race.last_bumped_at,
            "is_active": race.is_active,
            "winner_name": race.winner_name,
            "runners": runners_by_race[race.id]
        })
    return data

@app.post("/reset")
async def reset_database(session: Session = Depends(get_session)):
    # Keep the latest race if exists, delete others
    # Get the latest active race
    latest_race = session.exec(select(Race).order_by(Race.id.desc()).limit(1)).first()
    
    if latest_race:
        # Delete all other races and their runners
        # Note: In SQLModel cascading deletes might need explicit handling if not set up in DB
        # But here we can just delete races where id != latest.id
        
        # Delete runners of other races
        statement_runners = select(Runner).where(Runner.race_id != latest_race.id)
        other_runners = session.exec(statement_runners).all()
        for r in other_runners:
            session.delete(r)
            
        # Delete other races
        statement_races = select(Race).where(Race.id != latest_race.id)
        other_races = session.exec(statement_races).all()
        for r in other_races:
            session.delete(r)
            
        session.commit()
        return {"message": "Database reset (kept latest race)"}
    else:
        # No races, just clear everything (safe fallback)
        session.exec(select(Runner)).all() # Just to verify? No, use delete
        # Simpler: Delete all
        runners = session.exec(select(Runner)).all()
        for r in runners: session.delete(r)
        
        races = session.exec(select(Race)).all()
        for r in races: session.delete(r)
        
        session.commit()
        return {"message": "Database cleared (no races found)"}
