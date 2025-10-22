"""
모든 board의 HTML 구조 확인
"""
import asyncio
from playwright.async_api import async_playwright


BOARDS = {
    '공고': 'https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023010000',
    '공고예고': 'https://www.hira.or.kr/rc/drug/anticancer/antiCncrAnnceList.do?pgmid=HIRAA030023020000',
    '항암화학요법': 'https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023030000',
    'FAQ': 'https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023080000'
}


async def check_board_structure(board_name, url):
    """각 board의 구조 확인"""
    print("=" * 80)
    print(f"[{board_name}] 구조 분석")
    print("=" * 80)
    print(f"URL: {url}")
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle')

        # 1. 총 게시글 수
        try:
            total_elem = await page.locator('.total-txt').first.text_content()
            print(f"총 게시글: {total_elem}")
        except:
            print("총 게시글: 확인 불가")

        # 2. 테이블 행 수
        try:
            rows = await page.locator('tbody tr').all()
            print(f"테이블 행 수: {len(rows)}개")
        except:
            print("테이블 행 수: 확인 불가")

        # 3. 첫 번째 행 구조
        try:
            first_row = await page.locator('tbody tr').first
            cells = await first_row.locator('td').all()
            print(f"셀 개수: {len(cells)}개")

            for i, cell in enumerate(cells):
                text = await cell.text_content()
                has_link = await cell.locator('a').count() > 0
                print(f"  셀 {i}: {text.strip()[:50]} {'(링크 있음)' if has_link else ''}")
        except Exception as e:
            print(f"첫 행 구조: 확인 불가 ({e})")

        # 4. 첫 게시글 링크 구조
        try:
            # 제목 링크 찾기
            title_link = None
            for i in range(10):  # 최대 10개 셀까지 확인
                cell = await page.locator(f'tbody tr').first.locator('td').nth(i)
                link = cell.locator('a').first
                if await link.count() > 0:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    if text and len(text.strip()) > 10:  # 긴 텍스트 = 제목일 가능성
                        print(f"\n제목 링크 (셀 {i}):")
                        print(f"  텍스트: {text.strip()[:50]}")
                        print(f"  href: {href}")
                        title_link = href
                        break
        except Exception as e:
            print(f"링크 구조: 확인 불가 ({e})")

        # 5. 상세 페이지 구조 (제목 링크 있으면)
        if title_link:
            try:
                # URL 생성
                if title_link.startswith('http'):
                    detail_url = title_link
                elif title_link.startswith('/'):
                    detail_url = 'https://www.hira.or.kr' + title_link
                elif title_link.startswith('?'):
                    current_path = url.split('?')[0]
                    detail_url = current_path + title_link
                else:
                    detail_url = 'https://www.hira.or.kr/' + title_link

                print(f"\n상세 페이지 URL: {detail_url}")

                await page.goto(detail_url, wait_until='networkidle')

                # 본문 셀렉터 확인
                selectors = ['.view', '.viewCont', '.content', '.board-view', 'div[class*="view"]']
                for selector in selectors:
                    elem = page.locator(selector).first
                    if await elem.count() > 0:
                        text = await elem.text_content()
                        print(f"  본문 ({selector}): {len(text.strip())}자")

                # 첨부파일 셀렉터 확인
                att_selectors = ['a[onclick*="downLoad"]', 'a[onclick*="download"]', '.file a', '.attach a']
                for selector in att_selectors:
                    elems = await page.locator(selector).all()
                    if len(elems) > 0:
                        print(f"  첨부파일 ({selector}): {len(elems)}개")
                        for i, elem in enumerate(elems[:2]):
                            filename = await elem.text_content()
                            onclick = await elem.get_attribute('onclick')
                            print(f"    [{i+1}] {filename.strip()[:30]} | {onclick[:50] if onclick else 'No onclick'}")

            except Exception as e:
                print(f"상세 페이지: 확인 불가 ({e})")

        await browser.close()
        print()


async def main():
    """모든 board 분석"""
    for board_name, url in BOARDS.items():
        await check_board_structure(board_name, url)


if __name__ == "__main__":
    asyncio.run(main())
