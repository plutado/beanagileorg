"""Capture README screenshots from a running toolkit filled with placeholder demo data (see demo_data.py).

    uv run --with playwright python scripts/screenshots.py http://127.0.0.1:8801 '<password>' out/ /today /pi/1 ...

Each route is saved as a 1440x900 PNG named after the route. Add "|text" to a route to scroll the first heading
with that text to the top first (for example "/pi/1|Program board"). Section intros are marked as seen and
coaching tips are turned off, so each screen shows its own content.
"""

import asyncio
import sys

from playwright.async_api import async_playwright

BASE, PASSWORD, OUT, ROUTES = sys.argv[1].rstrip("/"), sys.argv[2], sys.argv[3].rstrip("/"), sys.argv[4:]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto(BASE + "/login")
        await page.fill("input[name=password]", PASSWORD)
        await page.press("input[name=password]", "Enter")
        await page.wait_for_load_state("networkidle")
        await page.evaluate("""async () => {
            const help = await (await fetch('/api/help')).json();
            localStorage.setItem('ba-intro-seen', JSON.stringify(Object.keys(help)));
            localStorage.setItem('ba-theme', 'light');
            localStorage.setItem('ba-coach-off', 'true');
        }""")
        for spec in ROUTES:
            route, _, heading = spec.partition("|")
            await page.goto(f"{BASE}/#{route}")
            await page.wait_for_timeout(2000)
            if heading:
                await page.locator(f"h2:has-text('{heading}'), h3:has-text('{heading}')").first.evaluate(
                    "el => { el.scrollIntoView({block: 'start'}); let s = el.parentElement;"
                    " while (s && s.scrollHeight <= s.clientHeight) s = s.parentElement; (s || window).scrollBy(0, -96); }")
                await page.wait_for_timeout(500)
            name = route.strip("/").replace("/", "-") or "root"
            await page.screenshot(path=f"{OUT}/{name}.png")
        await browser.close()


asyncio.run(main())
