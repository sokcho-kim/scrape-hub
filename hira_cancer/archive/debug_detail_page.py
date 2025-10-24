"""
게시글 상세 페이지 HTML 구조 확인
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_detail_page():
    """상세 페이지 구조 확인"""
    # 공고 게시글 하나 선택
    detail_url = "https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023010000&brdScnBltNo=4&brdBltNo=45648&pageIndex=1&pageIndex2=1"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print(f"상세 페이지 로딩: {detail_url}")
        await page.goto(detail_url, wait_until='networkidle')

        # 1. 본문 내용 찾기
        print("\n" + "="*80)
        print("1. 본문 내용 선택자")
        print("="*80)

        content_selectors = [
            '.board-view-content',
            '.view-content',
            '.content',
            '.view_content',
            '.bbs-content',
            'table.view',
            '.detail-content',
            '#content',
        ]

        for selector in content_selectors:
            count = await page.locator(selector).count()
            if count > 0:
                text = await page.locator(selector).first.text_content()
                print(f"{selector:30} → {count}개, 길이: {len(text.strip())}자")
                print(f"  미리보기: {text.strip()[:100]}")

        # 2. 첨부파일 찾기
        print("\n" + "="*80)
        print("2. 첨부파일 링크")
        print("="*80)

        file_selectors = [
            '.file-list a',
            '.attach-file a',
            'a[onclick*="downLoad"]',
            'a[href*="download"]',
            '.download a',
            'table a[href*="download"]',
        ]

        for selector in file_selectors:
            links = await page.locator(selector).all()
            if links:
                print(f"{selector:30} → {len(links)}개 링크")
                if links:
                    first = links[0]
                    text = await first.text_content()
                    href = await first.get_attribute('href')
                    onclick = await first.get_attribute('onclick')
                    print(f"  첫 번째 링크:")
                    print(f"    텍스트: {text.strip()}")
                    print(f"    href: {href}")
                    print(f"    onclick: {onclick}")

        # 3. HTML 저장
        print("\n" + "="*80)
        print("3. HTML 저장")
        print("="*80)

        html = await page.content()
        with open('hira_cancer/debug_detail_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("저장 완료: hira_cancer/debug_detail_page.html")

        # 사용자 확인 시간
        print("\n브라우저에서 페이지를 확인하세요 (10초 대기)...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_detail_page())
