"""
NCC 페이지 구조 디버깅

갑상선암 list 페이지의 실제 HTML 구조 확인
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_cancer_list_page():
    url = "https://www.cancer.go.kr/lay1/program/S1T211C212/cancer/list.do"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"페이지 로드 중: {url}")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)  # 5초 대기

        print("\n=== 페이지 제목 ===")
        title = await page.title()
        print(title)

        print("\n=== 모든 링크 (처음 20개) ===")
        all_links = await page.query_selector_all('a')
        print(f"총 링크 수: {len(all_links)}")

        for i, link in enumerate(all_links[:20]):
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                # 인코딩 에러 방지
                text_safe = text[:50].encode('utf-8', errors='ignore').decode('utf-8')
                href_safe = str(href) if href else "None"
                print(f"{i+1}. {text_safe} -> {href_safe}")
            except Exception as e:
                print(f"{i+1}. ERROR: {e}")

        print("\n=== 테이블 확인 ===")
        tables = await page.query_selector_all('table')
        print(f"총 테이블 수: {len(tables)}")

        if tables:
            table_links = await page.query_selector_all('table tbody tr a')
            print(f"테이블 내 링크 수: {len(table_links)}")

        print("\n=== 목록 (ul/li) 확인 ===")
        lists = await page.query_selector_all('ul, ol')
        print(f"총 목록 수: {len(lists)}")

        list_links = await page.query_selector_all('.list_box li a, .cancer_list li a, ul li a, ol li a')
        print(f"목록 내 링크 수: {len(list_links)}")

        print("\n=== HTML 일부 저장 ===")
        html = await page.content()
        with open('data/ncc/logs/thyroid_cancer_list_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML 저장 완료: data/ncc/logs/thyroid_cancer_list_page.html")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_cancer_list_page())
