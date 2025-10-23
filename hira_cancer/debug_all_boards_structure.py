"""
모든 board의 HTML 구조 확인 디버그 스크립트

각 board의 목록 페이지와 상세 페이지 HTML 구조를 확인
"""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path


async def analyze_board(url: str, board_name: str):
    """board의 HTML 구조 분석"""
    print(f"\n{'='*80}")
    print(f"[{board_name}] 분석 시작: {url}")
    print(f"{'='*80}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 목록 페이지
        print(f"\n[목록 페이지 분석]")
        await page.goto(url, wait_until='networkidle')

        # 1. 페이징 정보
        print("\n1. 페이징 정보:")
        try:
            total_txt = await page.locator('.total-txt').text_content()
            print(f"   .total-txt: {total_txt}")
        except:
            print("   .total-txt: 없음")

        # 2. 테이블 구조
        print("\n2. 테이블 구조:")
        rows = await page.locator('tbody tr').all()
        print(f"   전체 행 수: {len(rows)}")

        if rows:
            first_row = rows[0]
            cells = await first_row.locator('td').all()
            print(f"   첫 번째 행 컬럼 수: {len(cells)}")

            for i, cell in enumerate(cells):
                text = await cell.text_content()
                has_link = await cell.locator('a').count() > 0
                print(f"   [{i}] {text[:50].strip():<50} | 링크: {has_link}")

            # 첫 번째 게시글 링크
            title_link = None
            for i, cell in enumerate(cells):
                link = cell.locator('a').first
                if await link.count() > 0:
                    href = await link.get_attribute('href')
                    title = await link.text_content()
                    if href and title.strip():
                        print(f"\n   제목 링크 발견 (컬럼 {i}):")
                        print(f"   - 제목: {title.strip()}")
                        print(f"   - href: {href}")
                        title_link = href
                        break

        # 3. 상세 페이지 분석
        if title_link:
            print(f"\n[상세 페이지 분석]")

            # URL 완성
            if title_link.startswith('http'):
                detail_url = title_link
            elif title_link.startswith('/'):
                detail_url = f"https://www.hira.or.kr{title_link}"
            elif title_link.startswith('?'):
                current_path = url.split('?')[0]
                detail_url = current_path + title_link
            else:
                detail_url = f"https://www.hira.or.kr/{title_link}"

            print(f"   상세 URL: {detail_url}")

            await page.goto(detail_url, wait_until='networkidle')

            # 본문 셀렉터 테스트
            print("\n   본문 셀렉터 테스트:")
            selectors = [
                'div.view',
                '.view',
                '.viewCont',
                '.viewContent',
                '.board-view',
                '.content',
                '#content',
                '.detail-content',
                'div.cont',
                '.cont'
            ]

            for selector in selectors:
                try:
                    elem = page.locator(selector).first
                    if await elem.count() > 0:
                        text = await elem.text_content()
                        print(f"   O {selector:<20} : {len(text)}chars")
                    else:
                        print(f"   X {selector:<20} : None")
                except:
                    print(f"   X {selector:<20} : Error")

            # 첨부파일 링크
            print("\n   첨부파일 링크:")
            file_links = await page.locator('a[onclick*="downLoad"]').all()
            print(f"   downLoad 링크: {len(file_links)}개")

            if file_links:
                for i, link in enumerate(file_links[:3]):  # 최대 3개
                    filename = await link.text_content()
                    onclick = await link.get_attribute('onclick')
                    print(f"   [{i+1}] {filename.strip()}")
                    print(f"       onclick: {onclick}")

        await browser.close()


async def main():
    """메인 실행"""
    boards = [
        ("https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023010000", "공고"),
        ("https://www.hira.or.kr/rc/drug/anticancer/antiCncrAnnceList.do?pgmid=HIRAA030023020000", "공고예고"),
        ("https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023030000", "항암화학요법"),
        ("https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023080000", "FAQ"),
    ]

    for url, name in boards:
        await analyze_board(url, name)
        await asyncio.sleep(2)  # board 간 대기

    print(f"\n{'='*80}")
    print("전체 분석 완료")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
