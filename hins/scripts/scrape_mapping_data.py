"""
HINS SNOMED CT 매핑 데이터 상세 수집

KCD-SNOMED CT, EDI-SNOMED CT, 기타-SNOMED CT 각각의
실제 매핑 테이블 데이터를 수집합니다.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


# 프로젝트 루트 및 데이터 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "hins"
RAW_DIR = DATA_DIR / "raw"
PARSED_DIR = DATA_DIR / "parsed"

# 각 매핑 타입별 디렉토리
(RAW_DIR / "kcd").mkdir(parents=True, exist_ok=True)
(RAW_DIR / "edi").mkdir(parents=True, exist_ok=True)
(RAW_DIR / "etc").mkdir(parents=True, exist_ok=True)


class MappingDataScraper:
    """SNOMED CT 매핑 데이터 수집기"""

    def __init__(self, headless=False):
        self.headless = headless
        self.base_url = "https://hins.or.kr"
        self.browser = None
        self.page = None

    async def init_browser(self):
        """브라우저 초기화"""
        print("[INFO] 브라우저 시작...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--start-maximized']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await context.new_page()
        print("[OK] 브라우저 시작 완료")

    async def close_browser(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("[INFO] 브라우저 종료")

    async def navigate_and_click(self, menu_code, mapping_type):
        """메뉴 클릭 및 페이지 이동"""
        print(f"\n[INFO] {mapping_type} 페이지로 이동 중...")

        # 메인 페이지 접속
        await self.page.goto(f"{self.base_url}/main/viewMain.do",
                           wait_until="domcontentloaded",
                           timeout=60000)
        await asyncio.sleep(3)

        # 매핑 테이블 페이지로 이동
        await self.page.evaluate("fn_go_page('3070000', '')")
        await self.page.wait_for_load_state("domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        # 해당 매핑 타입 버튼 클릭
        print(f"[INFO] {mapping_type} 버튼 클릭...")
        await self.page.evaluate(f"fn_go_page('{menu_code}', '')")
        await self.page.wait_for_load_state("domcontentloaded", timeout=60000)
        await asyncio.sleep(5)

        current_url = self.page.url
        print(f"[OK] {mapping_type} 페이지 접근: {current_url}")

        return current_url

    async def extract_all_tables(self, html_content, mapping_type):
        """페이지의 모든 테이블 추출"""
        soup = BeautifulSoup(html_content, 'lxml')
        tables = soup.find_all('table')

        print(f"[INFO] {mapping_type}: 테이블 {len(tables)}개 발견")

        all_data = []

        for idx, table in enumerate(tables, 1):
            print(f"[INFO] 테이블 {idx} 파싱 중...")

            # 헤더 추출
            headers = []
            thead = table.find('thead')
            if thead:
                for th in thead.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
            else:
                first_row = table.find('tr')
                if first_row:
                    headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]

            # 본문 추출
            rows = []
            tbody = table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if row and any(row):  # 빈 행 제외
                        rows.append(row)
            else:
                for tr in table.find_all('tr')[1:]:
                    row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if row and any(row):
                        rows.append(row)

            if rows:
                print(f"[INFO] 테이블 {idx}: {len(rows)}행 추출")

                # DataFrame 생성
                if headers and len(headers) == len(rows[0]):
                    df = pd.DataFrame(rows, columns=headers)
                else:
                    df = pd.DataFrame(rows)

                all_data.append({
                    "table_index": idx,
                    "headers": headers,
                    "row_count": len(rows),
                    "dataframe": df
                })

        return all_data

    async def save_data(self, tables_data, mapping_type, html_content):
        """데이터 저장"""
        type_dir = RAW_DIR / mapping_type.lower().replace("-", "_").replace(" ", "_")
        type_dir.mkdir(parents=True, exist_ok=True)

        # HTML 저장
        html_path = type_dir / f"{mapping_type}_page.html"
        html_path.write_text(html_content, encoding='utf-8')
        print(f"[SAVED] HTML: {html_path}")

        # 각 테이블을 CSV로 저장
        for table_data in tables_data:
            idx = table_data['table_index']
            df = table_data['dataframe']

            csv_path = type_dir / f"table_{idx}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"[SAVED] CSV: {csv_path} ({table_data['row_count']} 행)")

            # JSON으로도 저장
            json_path = type_dir / f"table_{idx}.json"
            json_data = {
                "mapping_type": mapping_type,
                "table_index": idx,
                "headers": table_data['headers'],
                "row_count": table_data['row_count'],
                "data": df.to_dict('records'),
                "scraped_at": datetime.now().isoformat()
            }
            json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"[SAVED] JSON: {json_path}")

        # 스크린샷
        screenshot_path = type_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[SAVED] 스크린샷: {screenshot_path}")

        # 요약 정보
        summary = {
            "mapping_type": mapping_type,
            "tables_count": len(tables_data),
            "total_rows": sum(t['row_count'] for t in tables_data),
            "scraped_at": datetime.now().isoformat(),
            "tables": [
                {
                    "index": t['table_index'],
                    "headers": t['headers'],
                    "row_count": t['row_count']
                }
                for t in tables_data
            ]
        }
        summary_path = type_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"[SAVED] 요약: {summary_path}")

        return summary

    async def scrape_mapping_type(self, menu_code, mapping_type):
        """특정 매핑 타입 스크래핑"""
        print("\n" + "=" * 60)
        print(f"{mapping_type} 데이터 수집 시작")
        print("=" * 60)

        try:
            # 페이지 이동
            await self.navigate_and_click(menu_code, mapping_type)

            # HTML 가져오기
            html_content = await self.page.content()

            # 테이블 추출
            tables_data = await self.extract_all_tables(html_content, mapping_type)

            if not tables_data:
                print(f"[WARNING] {mapping_type}: 테이블이 없습니다")
                # HTML과 스크린샷만 저장
                type_dir = RAW_DIR / mapping_type.lower().replace("-", "_").replace(" ", "_")
                type_dir.mkdir(parents=True, exist_ok=True)
                html_path = type_dir / f"{mapping_type}_page.html"
                html_path.write_text(html_content, encoding='utf-8')
                screenshot_path = type_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await self.page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"[SAVED] HTML과 스크린샷만 저장됨")
                return {"success": False, "reason": "no tables"}

            # 데이터 저장
            summary = await self.save_data(tables_data, mapping_type, html_content)

            print(f"\n[SUCCESS] {mapping_type} 수집 완료!")
            print(f"  - 테이블: {summary['tables_count']}개")
            print(f"  - 총 행: {summary['total_rows']}행")

            return {"success": True, "summary": summary}

        except Exception as e:
            print(f"[ERROR] {mapping_type} 수집 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def scrape_all(self):
        """모든 매핑 데이터 수집"""
        try:
            await self.init_browser()

            results = {}

            # 1. KCD-SNOMED CT
            results["kcd"] = await self.scrape_mapping_type("3070100", "KCD-SNOMED CT")
            await asyncio.sleep(3)

            # 2. EDI-SNOMED CT
            results["edi"] = await self.scrape_mapping_type("3070200", "EDI-SNOMED CT")
            await asyncio.sleep(3)

            # 3. 기타-SNOMED CT (메뉴 코드 확인 필요)
            # results["etc"] = await self.scrape_mapping_type("3070300", "기타-SNOMED CT")

            return results

        finally:
            await self.close_browser()


async def main():
    """메인 실행"""
    print("=" * 60)
    print("HINS SNOMED CT 매핑 데이터 상세 수집")
    print("=" * 60)

    scraper = MappingDataScraper(headless=False)
    results = await scraper.scrape_all()

    print("\n" + "=" * 60)
    print("전체 수집 결과")
    print("=" * 60)

    for mapping_type, result in results.items():
        status = "[OK]" if result.get("success") else "[FAIL]"
        print(f"{status} {mapping_type.upper()}")
        if result.get("success") and result.get("summary"):
            summary = result["summary"]
            print(f"     - 테이블: {summary['tables_count']}개")
            print(f"     - 총 행: {summary['total_rows']}행")
        elif not result.get("success"):
            print(f"     - 이유: {result.get('reason') or result.get('error')}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
