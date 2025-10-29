"""
전체암 보기 페이지에서 모든 암종의 cancer_seq ID 추출

총 100개 암종 (성인 92 + 소아청소년 8)
"""
import asyncio
import re
from playwright.async_api import async_playwright

async def extract_all_cancer_ids():
    """모든 암종 ID 추출"""
    url = "https://www.cancer.go.kr/lay1/program/S1T211C223/cancer/list.do"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"페이지 로드 중: {url}")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # 모든 링크에서 cancer_seq 추출
        all_links = await page.query_selector_all('a')

        cancer_data = []
        seen_seqs = set()

        for link in all_links:
            href = await link.get_attribute('href')
            text = await link.inner_text()

            if href and 'cancer_seq=' in href:
                # cancer_seq 추출
                match = re.search(r'cancer_seq=(\d+)', href)
                if match:
                    cancer_seq = match.group(1)
                    name = text.strip()

                    # 중복 제거 및 유효한 이름만
                    if cancer_seq not in seen_seqs and name and len(name) > 1 and '>' not in name:
                        seen_seqs.add(cancer_seq)

                        # 소아청소년 암 구분
                        is_pediatric = '소아청소년' in name

                        cancer_data.append({
                            'name': name,
                            'cancer_seq': cancer_seq,
                            'url': f"/lay1/program/S1T211C223/cancer/view.do?cancer_seq={cancer_seq}",
                            'category': '소아청소년 암' if is_pediatric else '성인 암'
                        })

        # 정렬
        cancer_data.sort(key=lambda x: (x['category'], x['name']))

        print(f"\n총 발견된 암종: {len(cancer_data)}개")
        print(f"  - 성인 암: {sum(1 for c in cancer_data if c['category'] == '성인 암')}개")
        print(f"  - 소아청소년 암: {sum(1 for c in cancer_data if c['category'] == '소아청소년 암')}개")

        # 목록 출력
        print("\n=== 암종 목록 ===\n")
        for i, cancer in enumerate(cancer_data, 1):
            category_mark = '[소아]' if cancer['category'] == '소아청소년 암' else '      '
            print(f"{i:3d}. {category_mark} {cancer['name']:20s} (seq: {cancer['cancer_seq']})")

        # Python config 형식으로 출력
        print("\n\n=== config.py용 CANCER_TYPES_ALL ===\n")
        print("# 전체 암종 목록 (100개)")
        print("CANCER_TYPES_ALL = [")
        for cancer in cancer_data:
            print(f'''    {{
        "name": "{cancer['name']}",
        "cancer_seq": "{cancer['cancer_seq']}",
        "view_url": "{cancer['url']}",
        "category": "{cancer['category']}"
    }},''')
        print("]")

        await browser.close()

        return cancer_data

if __name__ == "__main__":
    result = asyncio.run(extract_all_cancer_ids())
