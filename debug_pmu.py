import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Ensure we block tracking/ads to speed up
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["media", "font"] else route.continue_())
        
        # Trying a slightly different URL format just in case, or stick to the one I was using
        # 18022026 -> 18.02.2026
        # Official format usually: https://www.pmu.fr/turf/18022026/R3/C1
        url = "https://www.pmu.fr/turf/18022026/R3/C1"
        print(f"Loading {url}...")
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            print(f"Loaded {page.url}")
            
            # Wait a bit for JS
            await asyncio.sleep(5)
            
            # Save HTML for inspection
            html = await page.content()
            with open("pmu_debug.html", "w") as f:
                f.write(html)
            print("Saved pmu_debug.html")

            # Try to find images
            imgs = await page.locator("img[src*='casaques']").all()
            print(f"Found {len(imgs)} casaque images.")
            
            if len(imgs) > 0:
                src = await imgs[0].get_attribute("src")
                print(f"Sample src: {src}")
                
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
