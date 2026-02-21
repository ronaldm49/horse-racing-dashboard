
import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # URL of a race for today (using the one from the browser agent check if possible, or discovering one)
        # Using a generic recent results page to find a link
        print("Navigating to daily results to find a race...")
        await page.goto("https://www.zeturf.com/en/resultats-et-rapports-du-jour/2026-02-17", wait_until="domcontentloaded")
        
        # Find a race link
        link = page.locator("a[href*='/course-du-jour/']").first
        if await link.count() == 0:
            print("No race links found.")
            await browser.close()
            return
            
        url = "https://www.zeturf.com" + await link.get_attribute("href")
        print(f"Testing Race URL: {url}")
        
        await page.goto(url, wait_until="domcontentloaded")
        
        # --- TEST EXTRACTION LOGIC ---
        
        # 1. Try Header parsing (Handling multiple h1s)
        header_locator = page.locator("h1")
        count = await header_locator.count()
        print(f"Found {count} h1 elements.")
        for i in range(count):
            try:
                txt = await header_locator.nth(i).text_content()
                print(f"H1 #{i}: {txt}")
            except:
                pass
        
        # 2. Try identifying the red time text often found in headers
        # Selector suggestions: .cta_course span, .course-header span
        
        # Let's dump some potential candidates
        candidates = await page.locator("span").all()
        print("Scanning spans for time format (HHhMM)...")
        found_times = []
        for span in candidates[:50]: # limit to first 50 to avoid spam
            text = await span.text_content()
            if text and "h" in text:
                # Simple check for digit+h+digit
                if re.search(r"\d{1,2}h\d{2}", text):
                    print(f"Match found: '{text}' in {span}")
                    found_times.append(text.strip())

        print(f"Potential times found: {found_times}")

        # 3. Look for data-timestamp
        print("Scanning for data-timestamp...")
        elements_with_timestamp = await page.locator("[data-timestamp]").all()
        for el in elements_with_timestamp:
            ts = await el.get_attribute("data-timestamp")
            txt = await el.text_content()
            # Get parent info
            parent = el.locator("..")
            parent_class = await parent.get_attribute("class")
            print(f"Found timestamp: {ts} (Text: {txt}) | Parent Class: {parent_class}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
