import asyncio
import re
from playwright.async_api import async_playwright

class ZeturfScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None
        self._lock = None
        self._sem = None

    def _construct_pmu_silk_url(self, date_str, meeting_num, race_num, runner_num):
        # date_str in YYYY-MM-DD from Zeturf URL -> DDMMYYYY for PMU
        try:
            parts = date_str.split("-") # 2026-02-18
            if len(parts) == 3:
                pmu_date = f"{parts[2]}{parts[1]}{parts[0]}"
                return f"https://www.pmu.fr/back-assets/hippique/casaques/{pmu_date}/R{meeting_num}/C{race_num}/P{runner_num}.png"
        except Exception as e:
            print(f"Error constructing silk URL: {e}")
        return None

    async def _ensure_lock(self):
        if not self._lock:
            self._lock = asyncio.Lock()
        if not self._sem:
            self._sem = asyncio.Semaphore(10)

    async def start(self):
        await self._ensure_lock()
        async with self._lock:
            if self.browser:
                return

            self.playwright = await async_playwright().start()
            # Launch browser (headless by default)
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()

    async def stop(self):
        await self._ensure_lock()
        async with self._lock:
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

    async def restart(self):
        await self.stop()
        await self.start()

    async def get_new_page(self):
        if not self.context:
            await self.start()
        try:
            page = await self.context.new_page()
            # Block unnecessary resources
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                else route.continue_())
            return page
        except Exception:
            print("Context failed, restarting browser...")
            await self.restart()
            page = await self.context.new_page()
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                else route.continue_())
            return page

    async def scrape_race(self, url: str, page=None):
        if not self.context:
            await self.start()
        
        should_close = False
        if not page:
            page = await self.context.new_page()
            should_close = True
        try:
            await page.goto(url, wait_until="domcontentloaded")
            # Wait for the table to appear
            await page.wait_for_selector(".table-runners", timeout=20000)

            # Get race title and time
            title_locator = page.locator("h1")
            race_title = "Unknown Race"
            race_time_str = None
            
            if await title_locator.count() > 0:
                full_title = await title_locator.first.text_content()
                full_title = full_title.strip()
                # Title often contains time like "R1C1 - Vincennes - 13h50 - Prix..."
                # Or time is in a separate span.
                race_title = full_title
                
                # Check for discipline in title or race info
                # "Attelé", "Monté" -> Keep
                # "Plat", "Haies", "Steeple" -> Discard
                
                # Check entire body text to be safe/robust
                body_text = await page.inner_text("body")
                body_text_lower = body_text.lower()
                
                is_trotting = "attelé" in body_text_lower or "monté" in body_text_lower or "harness" in body_text_lower or "mounted" in body_text_lower
                
                if not is_trotting:
                    # Double check page content for debug if needed, but logging brief info
                    print(f"Skipping {url} - Not Trotting (Keywords not found in body)")
                    return None
            
            # Use specific selector for time if available
            # We look for [data-timestamp] usually in a container like .heure-course
            
            # Default to None
            race_timestamp = None
            
            # Try to find the time element with data-timestamp
            # Best candidate based on verification: element with data-timestamp whose parent has class 'heure-course'
            # Or just the first data-timestamp in the header area
            
            time_el = page.locator(".heure-course [data-timestamp]").first
            if await time_el.count() > 0:
                race_time_str = await time_el.text_content()
                race_time_str = race_time_str.strip()
                try:
                    ts_val = await time_el.get_attribute("data-timestamp")
                    if ts_val:
                         race_timestamp = int(ts_val)
                except:
                    pass
            else:
                 # Fallback: try any data-timestamp near h1 or in header
                 # This is properly handled by the specific selector above for now.
                 pass
            
            if not race_time_str:
                 # Last resort fallback to text scanning if needed, but the above is robust for Zeturf
                 pass
            
            # Extract race details from URL for PMU silks
            # URL format: .../2026-02-18/R3C1-...
            pmu_details = None
            try:
                match = re.search(r"/(\d{4}-\d{2}-\d{2})/R(\d+)C(\d+)-", url)
                if match:
                    pmu_details = {
                        "date": match.group(1),
                        "meeting": match.group(2),
                        "race": match.group(3)
                    }
            except Exception as e:
                print(f"Error parsing URL for PMU details: {e}")

            # Find Next Race URL
            next_race_url = None
            try:
                # The navigation bar is usually .bloc-choix-course or .navigation-courses
                # But safer is to look for links with matching pattern: /R{meeting}C{race+1}-
                if pmu_details:
                    current_race_num = int(pmu_details["race"])
                    next_race_num = current_race_num + 1
                    meeting_num = pmu_details["meeting"]
                    date_str = pmu_details["date"]
                    # Pattern example: /en/course/2026-02-18/R3C2-
                    pattern = f"/R{meeting_num}C{next_race_num}-"
                    
                    # Look for any link with this pattern
                    # We look in the whole page, but usually navigation is at top
                    next_link = page.locator(f"a[href*='{pattern}']").first
                    if await next_link.count() > 0:
                        href = await next_link.get_attribute("href")
                        if href:
                            # Ensure full URL
                            if href.startswith("/"):
                                next_race_url = f"https://www.zeturf.com{href}"
                            else:
                                next_race_url = href
            except Exception as e:
                print(f"Error finding next race URL: {e}")

            # Get all runner rows
            rows = await page.locator("tr").all()
            
            runners_data = []
            
            for row in rows:
                # Check if this row has a horse name
                name_locator = row.locator("a.horse-name")
                if await name_locator.count() == 0:
                    continue
                
                name = await name_locator.first.text_content()
                name = name.strip() if name else "Unknown"

                # Check for Non-Runner (Non Partant)
                # Text usually appears in the row or status column
                row_text = await row.text_content()
                is_non_runner = "non partant" in row_text.lower()

                # Number
                num_locator = row.locator("td.numero")
                number = 0
                if await num_locator.count() > 0:
                    num_text = await num_locator.first.text_content()
                    num_text = num_text.strip()
                    if num_text.isdigit():
                        number = int(num_text)
                
                # Silk
                silk_url = None
                silk_img = row.locator("img[src*='casaque']") 
                if await silk_img.count() > 0:
                     silk_url = await silk_img.first.get_attribute("src")
                
                # Try to use PMU silk if available and we have a number
                if pmu_details and number > 0:
                    pmu_silk = self._construct_pmu_silk_url(
                        pmu_details["date"], 
                        pmu_details["meeting"], 
                        pmu_details["race"], 
                        number
                    )
                    if pmu_silk:
                        silk_url = pmu_silk

                # Jockey / Driver
                # In Flat/Jump: often under the name or next to it (class="jockey")
                # In Trotting: in its own column (class="jockey" or similar)
                # We'll try to find any element with class jockey in the row
                jockey_locator = row.locator(".jockey, span.jockey, td.jockey")
                jockey = None
                if await jockey_locator.count() > 0:
                    jockey = await jockey_locator.first.text_content()
                    jockey = jockey.strip()


                # Odds (Cote)
                odds_locator = row.locator("td.cote")
                odds_text = ""
                if await odds_locator.count() > 0:
                     odds_text = await odds_locator.first.text_content()
                     odds_text = odds_text.strip().replace(',', '.')
                
                try:
                    odds = float(odds_text)
                except ValueError:
                    odds = 0.0

                # Ferrure (Shoeing) - D4 check
                red_shoes = await row.locator("span.ferrure-rouge").count()
                
                is_d4 = False
                if red_shoes >= 2:
                    is_d4 = True
                
                # Determine status text for UI
                shoeing_status = ""
                if is_d4:
                    shoeing_status = "D4"
                elif red_shoes == 1:
                    shoeing_status = "DA/DP" 
                
                runners_data.append({
                    "name": name,
                    "odds": odds,
                    "is_d4": is_d4,
                    "shoeing_status": shoeing_status,
                    "number": number,
                    "silk_url": silk_url,
                    "jockey": jockey,
                    "is_non_runner": is_non_runner
                })

            return {"title": race_title, "runners": runners_data, "time_str": race_time_str, "next_race_url": next_race_url}
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
        finally:
            if should_close:
                await page.close()




    async def scrape_daily_program(self, date_str: str) -> list[str]:
        """
        Scrapes the daily program using the Results page (since Program page is down).
        Visits each meeting to filter for France + Trotting.
        """
        if not self.context:
            await self.start()
        
        if not self.context:
            await self.start()
        
        page = await self.context.new_page()
        should_close = True # Always close since we created it
        race_urls = []
        try:
            # URL for specific date - Using RESULTS page
            url = f"https://www.zeturf.com/en/resultats-et-rapports-du-jour/{date_str}"
            await page.goto(url, wait_until="domcontentloaded")
            
            # Wait for content - meeting links
            try:
                await page.wait_for_selector("a[href*='/reunion-du-jour/']", timeout=10000)
            except:
                print("Timeout waiting for meeting links.")
                return []

            # Get all meeting links
            meeting_links = await page.locator("a[href*='/reunion-du-jour/']").all()
            meeting_urls = []
            for link in meeting_links:
                href = await link.get_attribute("href")
                if href:
                    full_url = f"https://www.zeturf.com{href}" if href.startswith("/") else href
                    if full_url not in meeting_urls:
                        meeting_urls.append(full_url)
            
            print(f"Found {len(meeting_urls)} meetings. Filtering for France Trotting...")
            
            # Visit each meeting to check details
            for m_url in meeting_urls:
                try:
                    await page.goto(m_url, wait_until="domcontentloaded")
                    
                    # 1. Check for Country: "France"
                    # Look for the flag icon or text "France" in specific headers to be sure
                    # The flag class is usually "fi fi-fr"
                    content_content = await page.content()
                    is_france = "fi-fr" in content_content or "FRANCE" in await page.locator(".numero-reunion-wrapper").text_content() if await page.locator(".numero-reunion-wrapper").count() > 0 else False
                    
                    if not is_france:
                        # Double check with another selector if unsure, but strict is better for now
                        # Attempt to find "France" in the main header
                        header_text = await page.locator("h1.nom-reunion").text_content() if await page.locator("h1.nom-reunion").count() > 0 else ""
                        if "FRANCE" not in header_text.upper() and "fi-fr" not in content_content:
                            # print(f"Skipping non-French meeting: {m_url}")
                            continue

                    # 2. Iterate over race rows to filtering Mixed Meetings
                    # Select only rows that have the Trotting or Monte icon
                    # Rows are tr.item
                    race_rows = await page.locator("tr.item").all()
                    
                    for row in race_rows:
                        # Check discipline icon within this row
                        # .zt-trot (Harness) or .zt-monte (Mounted)
                        # Avoid .zt-run (Flat) or others
                        is_trot = await row.locator(".zt-trot").count() > 0
                        is_monte = await row.locator(".zt-monte").count() > 0
                        
                        if is_trot or is_monte:
                            # Get the link
                            link_element = row.locator("td.nom a").first
                            if await link_element.count() > 0:
                                href = await link_element.get_attribute("href")
                                if href:
                                    full_r_url = f"https://www.zeturf.com{href}" if href.startswith("/") else href
                                    if full_r_url not in race_urls:
                                        print(f"Found French Trotting Race: {full_r_url}")
                                        race_urls.append(full_r_url)
                        # else:
                        #     print(f"Skipping non-trotting race row in {m_url}")

                except Exception as e:
                    print(f"Error checking meeting {m_url}: {e}")
                    continue

            return race_urls

        except Exception as e:
            print(f"Error scraping program: {e}")
            return []
        finally:
            if should_close:
                await page.close()

    async def scrape_race_result(self, url: str, page=None):
        if not self.context:
            await self.start()
            
        should_close = False
        if not page:
            page = await self.context.new_page()
            should_close = True

        try:
            await page.goto(url, wait_until="domcontentloaded")
            
            result_table = page.locator("table.resultats-table")
            if await result_table.count() == 0:
                return None, 0.0 # No results yet
            
            first_row = result_table.locator("tr").first
            name_el = first_row.locator("td.nom-cheval, a.horse-name, td.horse-name").first
            if await name_el.count() == 0:
                return None, 0.0
                
            winner_name = await name_el.text_content()
            winner_name = winner_name.strip()
            
            return winner_name, 0.0

        except Exception as e:
            print(f"Error scraping result {url}: {e}")
            return None, 0.0
        finally:
            if should_close:
                await page.close()
