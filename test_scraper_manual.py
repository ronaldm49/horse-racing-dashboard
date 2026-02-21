import asyncio
from backend.scraper import ZeturfScraper
from datetime import datetime

async def test():
    scraper = ZeturfScraper()
    await scraper.start()
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Testing for date: {today}")
    
    # Test finding meetings first
    page = await scraper.context.new_page()
    url = f"https://www.zeturf.com/en/resultats-et-rapports-du-jour/{today}"
    await page.goto(url, wait_until="domcontentloaded")
    
    meetings = await page.locator("a[href*='/reunion-du-jour/']").all()
    print(f"Found {len(meetings)} meetings:")
    for m in meetings:
        href = await m.get_attribute("href")
        print(href)
        
    print("-" * 20)
    
    # Also check race links again
    races = await page.locator("a[href*='/course-du-jour/']").all()
    print(f"Found {len(races)} race links directly:")
    for r in races:
        href = await r.get_attribute("href")
        print(href)
    
    await scraper.stop()

if __name__ == "__main__":
    asyncio.run(test())
