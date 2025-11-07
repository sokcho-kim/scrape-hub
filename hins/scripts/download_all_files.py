"""
HINS SNOMED CT 매핑 파일 전체 다운로드

KCD, EDI, 약제급여 모든 매핑 파일 자동 다운로드
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time


# 프로젝트 루트 및 데이터 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "hins"
DOWNLOAD_DIR = DATA_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 각 타입별 다운로드 디렉토리
(DOWNLOAD_DIR / "kcd").mkdir(parents=True, exist_ok=True)
(DOWNLOAD_DIR / "edi").mkdir(parents=True, exist_ok=True)
(DOWNLOAD_DIR / "medicine").mkdir(parents=True, exist_ok=True)


class FileDownloader:
    """HINS 파일 다운로더"""

    def __init__(self, headless=False):
        self.headless = headless
        self.base_url = "https://hins.or.kr"
        self.browser = None
        self.page = None
        self.download_count = 0
        self.failed_downloads = []

    async def init_browser(self):
        """브라우저 초기화"""
        print("[INFO] 브라우저 시작...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            downloads_path=str(DOWNLOAD_DIR),
            args=['--start-maximized']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        self.page = await context.new_page()
        print("[OK] 브라우저 시작 완료")

    async def close_browser(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print(f"[INFO] 브라우저 종료 (다운로드: {self.download_count}개)")

    async def navigate_to_page(self, menu_code, page_name):
        """특정 페이지로 이동"""
        print(f"\n[INFO] {page_name} 페이지 이동 중...")

        # 메인 페이지
        await self.page.goto(f"{self.base_url}/main/viewMain.do",
                           wait_until="domcontentloaded",
                           timeout=60000)
        await asyncio.sleep(2)

        # 매핑 테이블 페이지
        await self.page.evaluate("fn_go_page('3070000', '')")
        await self.page.wait_for_load_state("domcontentloaded", timeout=60000)
        await asyncio.sleep(2)

        # 해당 타입 페이지
        await self.page.evaluate(f"fn_go_page('{menu_code}', '')")
        await self.page.wait_for_load_state("domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        print(f"[OK] {page_name} 페이지 접근 완료")

    async def click_download_button(self, onclick_code, filename, target_dir):
        """다운로드 버튼 클릭 및 파일 저장"""
        try:
            print(f"  [DOWNLOAD] {filename}...", end=" ", flush=True)

            # 다운로드 이벤트 대기
            async with self.page.expect_download(timeout=60000) as download_info:
                # JavaScript 함수 실행
                await self.page.evaluate(onclick_code)
                download = await download_info.value

                # 파일 저장
                suggested_name = download.suggested_filename
                save_path = target_dir / suggested_name
                await download.save_as(save_path)

                self.download_count += 1
                print(f"OK ({suggested_name})")

                return {
                    "success": True,
                    "filename": suggested_name,
                    "path": str(save_path),
                    "size": save_path.stat().st_size
                }

        except Exception as e:
            print(f"FAIL - {e}")
            self.failed_downloads.append({
                "filename": filename,
                "onclick": onclick_code,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    async def download_kcd_files(self):
        """KCD-SNOMED CT 파일 다운로드"""
        print("\n" + "=" * 60)
        print("KCD-SNOMED CT 파일 다운로드")
        print("=" * 60)

        await self.navigate_to_page("3070100", "KCD-SNOMED CT")

        downloads = []

        # HTML 파싱해서 다운로드 버튼 찾기
        html = await self.page.content()
        soup = BeautifulSoup(html, 'lxml')

        # 다운로드 버튼 찾기
        buttons = soup.find_all('button', class_='btn_go_download')
        print(f"[INFO] 다운로드 버튼 {len(buttons)}개 발견")

        for button in buttons:
            onclick = button.get('onclick', '')
            label = button.get('aria-label', button.get_text(strip=True))

            if 'fn_atch_download' in onclick:
                result = await self.click_download_button(
                    onclick, label, DOWNLOAD_DIR / "kcd"
                )
                downloads.append(result)
                await asyncio.sleep(2)

        return downloads

    async def download_edi_files(self):
        """EDI-SNOMED CT 파일 다운로드"""
        print("\n" + "=" * 60)
        print("EDI-SNOMED CT 파일 다운로드")
        print("=" * 60)

        await self.navigate_to_page("3070200", "EDI-SNOMED CT")

        downloads = []

        # HTML 파싱
        html = await self.page.content()
        soup = BeautifulSoup(html, 'lxml')

        # 테이블에서 다운로드 링크 찾기
        tables = soup.find_all('table')
        print(f"[INFO] 테이블 {len(tables)}개 발견")

        for table_idx, table in enumerate(tables, 1):
            print(f"\n[INFO] 테이블 {table_idx} 처리 중...")

            # 테이블의 각 행 처리
            rows = table.find_all('tr')

            for row_idx, row in enumerate(rows[1:], 1):  # 헤더 제외
                cells = row.find_all(['td', 'th'])

                if len(cells) >= 3:
                    chapter = cells[0].get_text(strip=True)
                    field = cells[1].get_text(strip=True)
                    download_cell = cells[2]

                    # 다운로드 링크/버튼 찾기 (a 태그와 button 태그 모두)
                    links = download_cell.find_all('a', href=True)
                    buttons = download_cell.find_all('button')

                    # a 태그 처리
                    for link in links:
                        onclick = link.get('onclick', '')
                        link_text = link.get_text(strip=True)

                        if 'fn_atch_download' in onclick:
                            filename = f"{chapter}_{field}_{link_text}"
                            result = await self.click_download_button(
                                onclick, filename, DOWNLOAD_DIR / "edi"
                            )
                            downloads.append(result)
                            await asyncio.sleep(1)

                    # button 태그 처리
                    for button in buttons:
                        onclick = button.get('onclick', '')
                        button_text = button.get_text(strip=True)
                        aria_label = button.get('aria-label', button_text)

                        if 'fn_atch_download' in onclick:
                            filename = f"{chapter}_{field}_{aria_label}"
                            result = await self.click_download_button(
                                onclick, filename, DOWNLOAD_DIR / "edi"
                            )
                            downloads.append(result)
                            await asyncio.sleep(1)

        return downloads

    async def download_all(self):
        """전체 파일 다운로드"""
        try:
            await self.init_browser()

            all_downloads = {
                "kcd": [],
                "edi": [],
                "medicine": []
            }

            # 1. KCD 파일 다운로드
            all_downloads["kcd"] = await self.download_kcd_files()

            # 2. EDI 파일 다운로드
            all_downloads["edi"] = await self.download_edi_files()

            # 3. 약제급여 파일 (EDI 테이블 2에 포함되어 있을 수 있음)

            return all_downloads

        finally:
            await self.close_browser()


async def main():
    """메인 실행"""
    print("=" * 60)
    print("HINS SNOMED CT 매핑 파일 전체 다운로드")
    print("=" * 60)
    print()

    downloader = FileDownloader(headless=False)
    results = await downloader.download_all()

    # 결과 요약
    print("\n" + "=" * 60)
    print("다운로드 결과 요약")
    print("=" * 60)

    total_success = 0
    total_size = 0

    for category, downloads in results.items():
        success_count = sum(1 for d in downloads if d.get("success"))
        category_size = sum(d.get("size", 0) for d in downloads if d.get("success"))

        print(f"\n{category.upper()}:")
        print(f"  - 성공: {success_count}개")
        print(f"  - 총 크기: {category_size / 1024 / 1024:.2f} MB")

        total_success += success_count
        total_size += category_size

    print(f"\n총 다운로드: {total_success}개")
    print(f"총 크기: {total_size / 1024 / 1024:.2f} MB")

    # 실패 목록
    if downloader.failed_downloads:
        print(f"\n실패한 다운로드: {len(downloader.failed_downloads)}개")
        for failed in downloader.failed_downloads:
            print(f"  - {failed['filename']}: {failed['error']}")

    # 결과 JSON 저장
    summary = {
        "total_downloads": total_success,
        "total_size_mb": total_size / 1024 / 1024,
        "by_category": {
            category: {
                "count": sum(1 for d in downloads if d.get("success")),
                "files": [
                    {
                        "filename": d.get("filename"),
                        "size_kb": d.get("size", 0) / 1024
                    }
                    for d in downloads if d.get("success")
                ]
            }
            for category, downloads in results.items()
        },
        "failed": downloader.failed_downloads
    }

    summary_path = DOWNLOAD_DIR / "download_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n[SAVED] 요약 파일: {summary_path}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
