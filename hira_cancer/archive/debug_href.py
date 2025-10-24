"""
Check actual href values in list page
"""
import asyncio
from playwright.async_api import async_playwright


async def check_hrefs():
    """Check href values"""
    url = "https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023010000"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle')

        # Get first row
        rows = await page.locator('tbody tr').all()

        if rows:
            first_row = rows[0]

            # Get title cell (3rd cell, index 2)
            cells = await first_row.locator('td').all()
            if len(cells) > 2:
                title_link = cells[2].locator('a').first

                if await title_link.count() > 0:
                    href = await title_link.get_attribute('href')
                    text = await title_link.text_content()

                    print(f"Title: {text.strip()}")
                    print(f"Raw href: {href}")
                    print(f"Starts with /: {href.startswith('/') if href else False}")
                    print(f"Starts with http: {href.startswith('http') if href else False}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_hrefs())
