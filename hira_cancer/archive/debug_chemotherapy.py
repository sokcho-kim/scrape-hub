"""
항암화학요법 board 상세 분석
"""
import asyncio
from playwright.async_api import async_playwright


async def analyze_chemotherapy():
    """항암화학요법 board 분석"""
    url = "https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030023030000"

    print(f"{'='*80}")
    print("항암화학요법 board 분석")
    print(f"{'='*80}")
    print(f"URL: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle')

        # 테이블 구조 확인
        rows = await page.locator('tbody tr').all()
        print(f"전체 행 수: {len(rows)}\n")

        for row_idx, row in enumerate(rows):
            cells = await row.locator('td').all()
            print(f"행 {row_idx + 1}:")
            print(f"  컬럼 수: {len(cells)}")

            for i, cell in enumerate(cells):
                text = await cell.text_content()
                print(f"  [{i}] {text.strip()[:80]}")

                # 모든 링크 확인
                links = await cell.locator('a').all()
                for j, link in enumerate(links):
                    href = await link.get_attribute('href')
                    onclick = await link.get_attribute('onclick')
                    link_text = await link.text_content()
                    print(f"      Link[{j}]:")
                    print(f"        text: {link_text.strip()}")
                    print(f"        href: {href}")
                    print(f"        onclick: {onclick}")

            print()

        # 첫 번째 행의 다운로드 링크 클릭 테스트
        if rows:
            print(f"{'='*80}")
            print("다운로드 링크 클릭 테스트")
            print(f"{'='*80}\n")

            first_row = rows[0]
            cells = await first_row.locator('td').all()

            # 링크 찾기
            for cell in cells:
                links = await cell.locator('a').all()
                for link in links:
                    href = await link.get_attribute('href')
                    onclick = await link.get_attribute('onclick')

                    if onclick and 'downLoad' in onclick:
                        print(f"다운로드 링크 발견:")
                        print(f"  onclick: {onclick}")

                        # onclick에서 파라미터 추출
                        import re
                        match = re.search(r"downLoad[A-Za-z]*\(([^)]+)\)", onclick)
                        if match:
                            params_str = match.group(1)
                            params = [p.strip().strip("'\"") for p in params_str.split(',')]
                            print(f"  params: {params}")

                            # 다운로드 URL 생성
                            if len(params) >= 4:
                                download_url = f"https://www.hira.or.kr/bbsDownload.do?brdScnBltNo={params[0]}&brdBltNo={params[1]}&type={params[2]}&atchSeq={params[3]}"
                                print(f"  download_url: {download_url}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(analyze_chemotherapy())
