"""
공고예고 board 상세 분석

href가 # 로 되어 있는 경우, 실제 상세 페이지 접근 방법 확인
"""
import asyncio
from playwright.async_api import async_playwright


async def analyze_pre_announcement():
    """공고예고 board의 상세 페이지 접근 방법 분석"""
    url = "https://www.hira.or.kr/rc/drug/anticancer/antiCncrAnnceList.do?pgmid=HIRAA030023020000"

    print(f"{'='*80}")
    print("공고예고 board 상세 분석")
    print(f"{'='*80}")
    print(f"URL: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle')

        # 첫 번째 게시글 행 찾기
        rows = await page.locator('tbody tr').all()
        if not rows:
            print("행 없음")
            await browser.close()
            return

        first_row = rows[0]
        cells = await first_row.locator('td').all()

        print(f"첫 번째 행 분석:")
        print(f"컬럼 수: {len(cells)}\n")

        for i, cell in enumerate(cells):
            text = await cell.text_content()
            print(f"[{i}] {text.strip()[:80]}")

            # 링크 확인
            links = await cell.locator('a').all()
            for j, link in enumerate(links):
                href = await link.get_attribute('href')
                onclick = await link.get_attribute('onclick')
                link_text = await link.text_content()
                print(f"    Link[{j}]:")
                print(f"      text: {link_text.strip()}")
                print(f"      href: {href}")
                print(f"      onclick: {onclick}")

        # 제목 링크 클릭 시도
        print(f"\n{'='*80}")
        print("제목 클릭 테스트")
        print(f"{'='*80}\n")

        title_link = cells[1].locator('a').first

        if await title_link.count() > 0:
            onclick = await title_link.get_attribute('onclick')
            print(f"onclick 속성: {onclick}")

            if onclick:
                print("\nonclick 함수 실행...")
                print("클릭 전 URL:", page.url)

                # 페이지 탐색 이벤트 대기 (새 URL로 이동할 수 있음)
                try:
                    await title_link.click()
                    await page.wait_for_load_state('networkidle', timeout=5000)
                except Exception as e:
                    print(f"wait_for_load_state 타임아웃 (정상일 수 있음): {e}")
                    await asyncio.sleep(2)

                print("클릭 후 URL:", page.url)

                # 페이지의 본문 확인
                print("\n본문 셀렉터 테스트:")
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
                    '.cont',
                    'div.viewConts',
                    '.viewConts'
                ]

                for selector in selectors:
                    try:
                        elem = page.locator(selector).first
                        if await elem.count() > 0:
                            text = await elem.text_content()
                            print(f"   O {selector:<20} : {len(text)} chars")
                        else:
                            print(f"   X {selector:<20} : None")
                    except:
                        print(f"   X {selector:<20} : Error")

                # 첨부파일 확인
                print("\n첨부파일 링크:")
                file_links = await page.locator('a[onclick*="downLoad"]').all()
                print(f"   downLoad 링크: {len(file_links)}개")

                if file_links:
                    for i, link in enumerate(file_links[:3]):
                        filename = await link.text_content()
                        onclick_attr = await link.get_attribute('onclick')
                        print(f"   [{i+1}] {filename.strip()}")
                        print(f"       onclick: {onclick_attr}")
            else:
                print("\nonclick 속성 없음, 직접 클릭 시도...")
                await title_link.click()
                await asyncio.sleep(2)

                # 페이지가 변경되었는지 확인
                print(f"현재 URL: {page.url}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(analyze_pre_announcement())
