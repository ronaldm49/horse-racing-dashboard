import asyncio
import time
from backend.scraper import ZeturfScraper

async def benchmark():
    scraper = ZeturfScraper()
    await scraper.start()
    
    # Use a known URL or find one. For now I'll use a sample or try to discover one.
    print("Finding a race to test...")
    today = "2026-02-11" # User's current date
    races = await scraper.scrape_daily_program(today)
    
    if not races:
        print("No races found to benchmark.")
        await scraper.stop()
        return

    # Pick up to 5 races
    test_urls = races[:5]
    if len(test_urls) < 5:
        # duplicate if not enough
        test_urls = (test_urls * 5)[:5]
        
    print(f"Testing concurrency with {len(test_urls)} races...")
    
    async def scrape(url):
         start = time.time()
         await scraper.scrape_race(url)
         return time.time() - start

    for i in range(3):
        start_batch = time.time()
        tasks = [scrape(url) for url in test_urls]
        results = await asyncio.gather(*tasks)
        batch_dur = time.time() - start_batch
        
        print(f"Batch {i+1} total time: {batch_dur:.2f}s")
        print(f"  Individual times: {[f'{t:.2f}s' for t in results]}")
        
    await scraper.stop()

if __name__ == "__main__":
    asyncio.run(benchmark())
