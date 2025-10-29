"""
전체암 보기 페이지 분석

https://www.cancer.go.kr/lay1/program/S1T211C223/cancer/list.do
페이지에서 모든 암종 목록 추출
"""
import asyncio
from playwright.async_api import async_playwright

async def analyze_all_cancer_page():
    """전체암 보기 페이지 분석"""
    url = "https://www.cancer.go.kr/lay1/program/S1T211C223/cancer/list.do"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"페이지 로드 중: {url}")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        print("\n=== 페이지 제목 ===")
        title = await page.title()
        print(title)

        # 암 종류 링크 찾기 (cancer/list.do 패턴)
        print("\n=== 암종 목록 추출 ===")
        all_links = await page.query_selector_all('a')

        cancer_links = []
        for link in all_links:
            href = await link.get_attribute('href')
            text = await link.inner_text()

            if href and 'cancer/list.do' in href and '/S1T211C' in href:
                # 코드 추출 (C223, C224 등)
                code_match = href.split('/S1T211C')[1].split('/')[0] if '/S1T211C' in href else None
                if code_match and text.strip():
                    cancer_links.append({
                        'name': text.strip(),
                        'code': 'C' + code_match,
                        'url': href
                    })

        # 중복 제거
        seen = set()
        unique_cancers = []
        for cancer in cancer_links:
            key = cancer['code']
            if key not in seen:
                seen.add(key)
                unique_cancers.append(cancer)

        print(f"총 발견된 암종: {len(unique_cancers)}개\n")

        for i, cancer in enumerate(unique_cancers, 1):
            print(f"{i:2d}. {cancer['name']:15s} (코드: {cancer['code']}) - {cancer['url']}")

        # Python config 형식으로 출력
        print("\n\n=== config.py용 데이터 ===\n")
        print("CANCER_TYPES = [")
        for cancer in unique_cancers:
            print(f'''    {{
        "name": "{cancer['name']}",
        "code": "{cancer['code']}",
        "list_url": "{cancer['url']}",
        "category": "암의 종류"
    }},''')
        print("]")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_all_cancer_page())
