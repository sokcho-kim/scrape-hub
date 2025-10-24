"""
HIRA 페이지 HTML 구조 디버깅
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_page_structure():
    """페이지 구조 확인"""
    url = "https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023010000"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 브라우저 보이게
        page = await browser.new_page()

        print(f"페이지 로딩: {url}")
        await page.goto(url, wait_until='networkidle')

        # 1. 전체 테이블 찾기
        print("\n" + "="*80)
        print("1. 모든 테이블 찾기")
        print("="*80)

        tables = await page.locator('table').all()
        print(f"발견된 테이블: {len(tables)}개")

        for i, table in enumerate(tables):
            classes = await table.get_attribute('class')
            id_attr = await table.get_attribute('id')
            print(f"\n테이블 {i+1}:")
            print(f"  class: {classes}")
            print(f"  id: {id_attr}")

            # tbody 확인
            tbody = table.locator('tbody')
            if await tbody.count() > 0:
                rows = await tbody.locator('tr').all()
                print(f"  tbody 행 수: {len(rows)}")

                # 첫 몇 행 출력
                for j, row in enumerate(rows[:3]):
                    cells = await row.locator('td').all()
                    print(f"    Row {j+1}: {len(cells)}개 셀")

                    # 각 셀 내용
                    for k, cell in enumerate(cells[:6]):
                        text = await cell.text_content()
                        text = text.strip()[:50]  # 처음 50자만
                        print(f"      Cell {k+1}: {text}")

        # 2. 특정 선택자로 검색
        print("\n" + "="*80)
        print("2. 다양한 선택자 시도")
        print("="*80)

        selectors = [
            'table.table',
            'table.board-list',
            'table.list',
            '.board tbody tr',
            '.table tbody tr',
            'tbody tr',
        ]

        for selector in selectors:
            count = await page.locator(selector).count()
            print(f"{selector:30} → {count}개")

        # 3. 제목 링크 찾기
        print("\n" + "="*80)
        print("3. 제목 링크 찾기")
        print("="*80)

        link_selectors = [
            'td a',
            'a.ellipsis',
            'a[href*="brdBltNo"]',
            'tbody a',
        ]

        for selector in link_selectors:
            links = await page.locator(selector).all()
            print(f"{selector:30} → {len(links)}개 링크")

            if links:
                # 첫 번째 링크 상세 정보
                first_link = links[0]
                text = await first_link.text_content()
                href = await first_link.get_attribute('href')
                print(f"  첫 번째 링크:")
                print(f"    텍스트: {text.strip()}")
                print(f"    href: {href}")

        # 4. 페이지 HTML 전체 저장
        print("\n" + "="*80)
        print("4. HTML 저장")
        print("="*80)

        html = await page.content()
        with open('hira_cancer/debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("저장 완료: hira_cancer/debug_page.html")

        # 사용자가 확인할 시간
        print("\n브라우저에서 페이지를 확인하세요 (10초 대기)...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_page_structure())
