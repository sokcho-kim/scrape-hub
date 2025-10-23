"""
공고예고 board의 첨부파일 실제 확인
"""
import asyncio
from playwright.async_api import async_playwright


async def check_attachments():
    """공고예고 첫 게시글의 첨부파일 확인"""
    url = "https://www.hira.or.kr/rc/drug/anticancer/antiCncrAnnceList.do?pgmid=HIRAA030023020000"

    print("="*80)
    print("공고예고 첨부파일 확인")
    print("="*80)
    print(f"URL: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 목록 페이지
        await page.goto(url, wait_until='networkidle')

        # 첫 번째 게시글 클릭
        rows = await page.locator('tbody tr').all()
        if rows:
            first_row = rows[0]
            cells = await first_row.locator('td').all()

            # 제목 링크 클릭
            title_link = cells[1].locator('a').first
            await title_link.click()
            await page.wait_for_load_state('networkidle', timeout=10000)

            print("상세 페이지 로드 완료\n")
            print(f"현재 URL: {page.url}\n")

            # 본문 HTML 확인
            print("[본문 HTML 구조]")
            content_elem = page.locator('div.view, .view, .viewCont').first
            if await content_elem.count() > 0:
                html = await content_elem.inner_html()
                print(f"HTML 길이: {len(html)}자")
                print(f"일부: {html[:500]}...\n")

            # 첨부파일 링크 찾기 (모든 방법 시도)
            print("\n[첨부파일 링크 검색]")

            # 방법 1: onclick="downLoad"
            method1 = await page.locator('a[onclick*="downLoad"]').all()
            print(f"1. onclick*=\"downLoad\": {len(method1)}개")
            for link in method1[:3]:
                text = await link.text_content()
                onclick = await link.get_attribute('onclick')
                print(f"   - {text.strip()[:50]} | {onclick}")

            # 방법 2: href 속성이 있는 링크
            method2 = await page.locator('.view a[href], .viewCont a[href]').all()
            print(f"\n2. .view 내 a[href]: {len(method2)}개")
            for link in method2[:3]:
                text = await link.text_content()
                href = await link.get_attribute('href')
                onclick = await link.get_attribute('onclick')
                print(f"   - {text.strip()[:50]} | href={href} | onclick={onclick}")

            # 방법 3: 파일명 패턴 (*.hwp, *.pdf 등)
            print("\n3. 파일명 패턴 검색:")
            all_text = await page.content()
            import re
            filenames = re.findall(r'[\w가-힣\s\(\)]+\.(hwpx?|pdf|xlsx?|docx?)', all_text, re.IGNORECASE)
            print(f"   발견된 파일명: {len(set(filenames))}개")
            for fn in list(set(filenames))[:5]:
                print(f"   - {fn}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_attachments())
