"""
공고 페이지의 페이지네이션 HTML 구조 확인
"""
import asyncio
from playwright.async_api import async_playwright


async def check_pagination():
    """페이지네이션 HTML 확인"""
    url = "https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023010000"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle')

        # 페이지네이션 영역 HTML 추출
        print("=" * 80)
        print("페이지네이션 영역 HTML")
        print("=" * 80)

        # 여러 셀렉터 시도
        selectors = [
            '.paging',
            '.pagination',
            '.page',
            'div[class*="pag"]',
            'ul[class*="pag"]',
            '.paging_area',
            '.page_num'
        ]

        for selector in selectors:
            try:
                elem = page.locator(selector).first
                if await elem.count() > 0:
                    html = await elem.evaluate('el => el.outerHTML')
                    text = await elem.text_content()
                    print(f"\n[{selector}] 발견!")
                    print(f"텍스트: {text[:200]}")
                    print(f"HTML: {html[:500]}")
                    print()
            except Exception as e:
                pass

        # 전체 게시글 수 찾기
        print("=" * 80)
        print("전체 게시글 수 정보")
        print("=" * 80)

        # "전체 217건" 같은 텍스트 찾기
        total_selectors = [
            'text=/전체.*건/',
            'text=/total/i',
            '.total',
            '.board_total',
            'span:has-text("건")'
        ]

        for selector in total_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.count() > 0:
                    text = await elem.text_content()
                    html = await elem.evaluate('el => el.outerHTML')
                    print(f"\n[{selector}] 발견!")
                    print(f"텍스트: {text}")
                    print(f"HTML: {html}")
                    print()
            except Exception as e:
                pass

        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_pagination())
