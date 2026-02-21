
import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper import ZeturfScraper

async def main():
    print("Starting verification of race filtering...")
    scraper = ZeturfScraper()
    await scraper.start()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Scraping for {date_str}...")
    
    urls = await scraper.scrape_daily_program(date_str)
    
    print(f"\n--- Results for {date_str} ---")
    print(f"Total filtered races found: {len(urls)}")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
        
    await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())
