
import asyncio
from playwright.async_api import async_playwright

async def debug_meeting():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # User mentioned Cagnes-sur-Mer or similar mixed meeting
        # I'll try to find a meeting with mixed races or just inspect the table structure of ANY meeting
        # to see if I can distinguish race types in the list.
        # Let's go to the Results page first to find a link.
        await page.goto("https://www.zeturf.com/en/resultats-et-rapports-du-jour/2026-02-11", wait_until="domcontentloaded")
        
        # Grab first meeting
        meeting_link = await page.locator("a[href*='/reunion-du-jour/']").first.get_attribute("href")
        full_url = f"https://www.zeturf.com{meeting_link}"
        print(f"Inspecting meeting: {full_url}")
        
        await page.goto(full_url, wait_until="domcontentloaded")
        
        # Dump the HTML of the race list table/container
        # Usually it's a table with specific classes
        content = await page.content()
        with open("meeting_debug.html", "w") as f:
            f.write(content)
            
        print("Dumped meeting_debug.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_meeting())
