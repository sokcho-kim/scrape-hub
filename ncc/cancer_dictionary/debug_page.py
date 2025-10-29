"""
페이지 구조 디버깅
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = "https://www.cancer.go.kr/lay1/program/S1T523C837/dictionaryworks/list.do?rows=30&cpage=1"
        print(f"페이지 로딩: {url}\n")

        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # HTML 저장
        html = await page.content()
        with open('data/ncc/cancer_dictionary/logs/page_structure.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML 저장됨: data/ncc/cancer_dictionary/logs/page_structure.html\n")

        # 전체 항목 수 찾기
        print("=== 전체 항목 수 찾기 ===")
        candidates = await page.query_selector_all('strong, .total_num, .result_count, span')
        for i, elem in enumerate(candidates[:20]):
            text = await elem.inner_text()
            if '건' in text or ',' in text or text.isdigit():
                print(f"{i}: {text}")

        print("\n=== 목록 항목 찾기 ===")
        # 다양한 셀렉터 시도
        selectors = [
            'table tbody tr',
            '.board_list tbody tr',
            '.list_wrap li',
            'ul.list li',
            '.item',
            'tbody tr',
            'tr'
        ]

        for selector in selectors:
            items = await page.query_selector_all(selector)
            print(f"{selector}: {len(items)}개")

        # 테이블 구조 확인
        print("\n=== 테이블 구조 ===")
        tables = await page.query_selector_all('table')
        print(f"테이블 수: {len(tables)}")

        if tables:
            rows = await tables[0].query_selector_all('tbody tr')
            print(f"첫 번째 테이블 행 수: {len(rows)}")

            if rows:
                for i, row in enumerate(rows[:3]):
                    cells = await row.query_selector_all('td, th')
                    cell_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_texts.append(text.strip()[:50])
                    print(f"행 {i}: {cell_texts}")

        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())
