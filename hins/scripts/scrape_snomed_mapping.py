"""
HINS SNOMED CT 매핑 테이블 스크래퍼

Playwright를 사용하여 HINS 웹사이트에서
KCD-SNOMED CT, EDI-SNOMED CT, 기타-SNOMED CT 매핑 데이터 수집
"""

import asyncio
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "hins"
RAW_DIR = DATA_DIR / "raw"
PARSED_DIR = DATA_DIR / "parsed"

# 디렉토리 생성
(RAW_DIR / "kcd").mkdir(parents=True, exist_ok=True)
(RAW_DIR / "edi").mkdir(parents=True, exist_ok=True)
(RAW_DIR / "etc").mkdir(parents=True, exist_ok=True)
PARSED_DIR.mkdir(parents=True, exist_ok=True)


class HINSScraper:
    """HINS SNOMED CT 매핑 테이블 스크래퍼"""

    def __init__(self, headless=False):
        self.headless = headless
        self.base_url = "https://hins.or.kr"
        self.browser: Browser = None
        self.page: Page = None

    async def init_browser(self):
        """브라우저 초기화"""
        print("[INFO] Playwright 브라우저 시작...")
        playwright = await async_playwright().start()

        # Chromium 브라우저 실행 (헤드리스 모드 선택 가능)
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--start-maximized']  # 최대화 모드
        )

        # 새 페이지 생성
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await context.new_page()

        print("[OK] 브라우저 시작 완료")

    async def close_browser(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("[INFO] 브라우저 종료")

    async def navigate_to_mapping_table(self):
        """SNOMED CT 매핑 테이블 페이지로 이동"""
        print(f"[INFO] 메인 페이지 접속: {self.base_url}")

        # 메인 페이지 접속 (타임아웃 증가, 조건 완화)
        await self.page.goto(f"{self.base_url}/main/viewMain.do",
                           wait_until="domcontentloaded",
                           timeout=60000)
        await asyncio.sleep(5)  # 페이지 로딩 대기

        print("[INFO] SNOMED CT 메뉴 클릭...")

        # JavaScript 함수 직접 호출 (fn_go_page('3070000',''))
        await self.page.evaluate("""
            fn_go_page('3070000', '');
        """)

        # 페이지 전환 대기
        await self.page.wait_for_load_state("domcontentloaded", timeout=60000)
        await asyncio.sleep(5)

        current_url = self.page.url
        print(f"[OK] 매핑 테이블 페이지 접근: {current_url}")

        # 페이지 HTML 저장
        html_content = await self.page.content()
        save_path = RAW_DIR / "mapping_table_playwright.html"
        save_path.write_text(html_content, encoding='utf-8')
        print(f"[SAVED] 페이지 HTML 저장: {save_path}")

        return html_content

    async def extract_page_description(self, html_content):
        """페이지 설명 및 안내문 추출"""
        soup = BeautifulSoup(html_content, 'lxml')

        # 페이지 제목
        title = soup.find('h1') or soup.find('h2', class_='page_title')

        # 본문 설명
        descriptions = []
        for p in soup.find_all('p', class_=['description', 'intro', 'guide']):
            descriptions.append(p.get_text(strip=True))

        # 안내 사항
        notices = []
        for div in soup.find_all('div', class_=['notice', 'info', 'alert']):
            notices.append(div.get_text(strip=True))

        result = {
            "title": title.get_text(strip=True) if title else "용어표준 매핑 테이블",
            "descriptions": descriptions,
            "notices": notices,
            "scraped_at": datetime.now().isoformat()
        }

        # JSON 저장
        save_path = PARSED_DIR / "page_description.json"
        save_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"[SAVED] 페이지 설명 저장: {save_path}")

        return result

    async def find_download_links(self, html_content):
        """다운로드 링크 찾기"""
        soup = BeautifulSoup(html_content, 'lxml')

        # 다운로드 링크 패턴 찾기
        download_links = []

        # <a> 태그에서 다운로드 관련 링크 찾기
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)

            # KCD, EDI, SNOMED 관련 링크
            if any(keyword in text.upper() or keyword in href.upper()
                   for keyword in ['KCD', 'EDI', 'SNOMED', '다운로드', 'DOWNLOAD', '엑셀', 'EXCEL', 'XLS']):
                download_links.append({
                    "text": text,
                    "href": href,
                    "onclick": link.get('onclick', '')
                })

        # 버튼 찾기
        for button in soup.find_all('button'):
            text = button.get_text(strip=True)
            onclick = button.get('onclick', '')

            if any(keyword in text for keyword in ['다운로드', '엑셀', 'Excel', 'KCD', 'EDI']):
                download_links.append({
                    "text": text,
                    "onclick": onclick,
                    "type": "button"
                })

        print(f"[INFO] 발견된 다운로드 링크: {len(download_links)}개")
        for i, link in enumerate(download_links, 1):
            print(f"  {i}. {link['text']}")

        # JSON 저장
        save_path = PARSED_DIR / "download_links.json"
        save_path.write_text(json.dumps(download_links, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"[SAVED] 다운로드 링크 정보 저장: {save_path}")

        return download_links

    async def extract_table_data(self, html_content):
        """테이블 데이터 추출"""
        soup = BeautifulSoup(html_content, 'lxml')

        tables_data = []

        # 모든 테이블 찾기
        tables = soup.find_all('table')
        print(f"[INFO] 발견된 테이블: {len(tables)}개")

        for idx, table in enumerate(tables, 1):
            print(f"[INFO] 테이블 {idx} 파싱 중...")

            # 테이블 헤더
            headers = []
            thead = table.find('thead')
            if thead:
                for th in thead.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
            else:
                # thead 없으면 첫 번째 tr을 헤더로
                first_row = table.find('tr')
                if first_row:
                    headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]

            # 테이블 본문
            rows = []
            tbody = table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if row:  # 빈 행 제외
                        rows.append(row)
            else:
                # tbody 없으면 모든 tr 처리 (첫 번째 제외)
                for tr in table.find_all('tr')[1:]:
                    row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if row:
                        rows.append(row)

            if headers and rows:
                table_info = {
                    "table_index": idx,
                    "headers": headers,
                    "row_count": len(rows),
                    "rows": rows[:10]  # 샘플 10개만 저장 (전체는 CSV로)
                }
                tables_data.append(table_info)

                # CSV로 전체 데이터 저장
                if rows:
                    df = pd.DataFrame(rows, columns=headers if len(headers) == len(rows[0]) else None)
                    csv_path = PARSED_DIR / f"table_{idx}.csv"
                    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                    print(f"[SAVED] 테이블 {idx} CSV 저장: {csv_path} ({len(rows)} 행)")

        # JSON 요약 저장
        save_path = PARSED_DIR / "tables_summary.json"
        save_path.write_text(json.dumps(tables_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"[SAVED] 테이블 요약 저장: {save_path}")

        return tables_data

    async def click_and_download(self, selector, download_dir, wait_time=5):
        """버튼 클릭 및 다운로드 대기"""
        try:
            print(f"[INFO] 클릭 시도: {selector}")

            # 다운로드 이벤트 리스너 설정
            async with self.page.expect_download() as download_info:
                await self.page.click(selector)
                download = await download_info.value

                # 파일 저장
                filename = download.suggested_filename
                save_path = download_dir / filename
                await download.save_as(save_path)
                print(f"[SAVED] 파일 다운로드: {save_path}")

                return str(save_path)

        except Exception as e:
            print(f"[ERROR] 다운로드 실패: {e}")
            await asyncio.sleep(wait_time)
            return None

    async def scrape_all(self):
        """전체 스크래핑 프로세스"""
        try:
            # 브라우저 초기화
            await self.init_browser()

            # 매핑 테이블 페이지 이동
            html_content = await self.navigate_to_mapping_table()

            # 페이지 설명 추출
            await self.extract_page_description(html_content)

            # 다운로드 링크 찾기
            download_links = await self.find_download_links(html_content)

            # 테이블 데이터 추출
            tables = await self.extract_table_data(html_content)

            # 스크린샷 저장
            screenshot_path = RAW_DIR / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[SAVED] 전체 페이지 스크린샷: {screenshot_path}")

            return {
                "download_links": download_links,
                "tables_count": len(tables),
                "success": True
            }

        except Exception as e:
            print(f"[ERROR] 스크래핑 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

        finally:
            # 브라우저 종료
            await self.close_browser()


async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("HINS SNOMED CT 매핑 테이블 스크래퍼")
    print("=" * 60)
    print()

    # 스크래퍼 실행 (headless=False로 브라우저 표시)
    scraper = HINSScraper(headless=False)
    result = await scraper.scrape_all()

    print()
    print("=" * 60)
    if result["success"]:
        print("[SUCCESS] 스크래핑 완료!")
        print(f"  - 다운로드 링크: {len(result['download_links'])}개")
        print(f"  - 테이블: {result['tables_count']}개")
    else:
        print(f"[FAILED] 스크래핑 실패: {result.get('error')}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
