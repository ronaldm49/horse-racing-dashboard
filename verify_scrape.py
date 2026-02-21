
import asyncio
import sys
import os
from pprint import pprint

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper import ZeturfScraper
from datetime import datetime

async def main():
    print("Starting verification of jockey data...")
    scraper = ZeturfScraper()
    await scraper.start()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Finding races for {date_str} to test...")
    
    urls = await scraper.scrape_daily_program(date_str)
    
    if not urls:
        print("No races found to test.")
        await scraper.stop()
        return

    # Test the first race found
    test_url = urls[0]
    print(f"Testing race: {test_url}")
    
    data = await scraper.scrape_race(test_url)
    
    if data:
        print(f"Race: {data['title']}")
        print(f"Time Str: {data.get('time_str')}")
        print(f"Timestamp: {data.get('timestamp')}")
        print(f"Runners found: {len(data['runners'])}")
        for r in data['runners']:
            print(f"  #{r['number']} {r['name']} - Jockey: {r['jockey']}")
    else:
        print("Failed to scrape race data.")
        
    await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())
