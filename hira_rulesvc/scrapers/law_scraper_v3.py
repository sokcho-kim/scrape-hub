"""
HIRA 고시 문서 크롤러 v3

폴더별로 네비게이션한 후, 목록의 모든 문서를 다운로드합니다.
"""
from playwright.sync_api import sync_playwright, Page, Download
from pathlib import Path
import time
import json
from datetime import datetime
import sys

# 상위 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

BASE_URL = 'http://rulesvc.hira.or.kr/lmxsrv/main/main.srv'
FOLDERS_JSON = Path("hira_rulesvc/config/folders_grouped.json")


class HIRALawScraperV3:
    """
    HIRA 고시 문서 스크래퍼 V3

    폴더 단위로 네비게이션하고, 각 폴더의 모든 문서를 다운로드합니다.
    """

    def __init__(self, output_dir: str = "data/hira_rulesvc/documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger("hira_law_scraper_v3", project="hira_rulesvc")

        # 폴더 그룹 로드
        with open(FOLDERS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.folders = data['folders']

        self.logger.info(f"총 {len(self.folders)}개 폴더")

    def scrape_all(self):
        """
        전체 고시 문서 수집
        """
        self.logger.info("=" * 60)
        self.logger.info("HIRA 고시 문서 크롤링 시작 V3 (폴더 기반)")
        self.logger.info("=" * 60)

        downloaded_count = 0
        failed_count = 0

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=300)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            try:
                # 메인 페이지 접속
                self.logger.info(f"메인 페이지 접속: {BASE_URL}")
                page.goto(BASE_URL)
                page.wait_for_load_state("networkidle")
                time.sleep(2)

                # 고시정보 탭 클릭
                self.logger.info("고시정보 탭 클릭")
                page.evaluate("menu_go('1')")
                time.sleep(2)

                # 각 폴더 처리
                for idx, folder_info in enumerate(self.folders, 1):
                    folder_path = folder_info['folder_path']
                    expected_docs = folder_info['documents']

                    folder_str = ' > '.join(folder_path)
                    self.logger.info(f"\n[{idx}/{len(self.folders)}] 폴더: {folder_str}")
                    self.logger.info(f"  예상 문서 수: {len(expected_docs)}개")

                    # 폴더로 네비게이션
                    if not self._navigate_to_folder(page, folder_path):
                        self.logger.warning(f"  폴더 네비게이션 실패")
                        failed_count += len(expected_docs)
                        continue

                    time.sleep(2)

                    # contentbody의 모든 다운로드 버튼 찾기
                    downloaded = self._download_all_in_folder(page, expected_docs)
                    downloaded_count += downloaded
                    failed_count += (len(expected_docs) - downloaded)

                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"오류 발생: {e}")
                import traceback
                traceback.print_exc()
            finally:
                browser.close()

        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"크롤링 완료!")
        self.logger.info(f"  - 성공: {downloaded_count}개")
        self.logger.info(f"  - 실패: {failed_count}개")
        self.logger.info(f"  - 저장 위치: {self.output_dir}")
        self.logger.info("=" * 60)

    def _navigate_to_folder(self, page: Page, folder_path: list) -> bool:
        """
        폴더 경로까지 네비게이션

        트리에서 폴더들을 순서대로 클릭
        """
        tree_frame = page.frame(name="tree01")
        if not tree_frame:
            self.logger.error("  tree01 iframe을 찾을 수 없습니다")
            return False

        try:
            # 각 폴더 클릭
            for folder_name in folder_path:
                self.logger.info(f"    → 폴더 클릭: {folder_name}")

                # 폴더 링크 찾기
                folder_link = tree_frame.locator(f'a:text-is("{folder_name}")').first

                if not folder_link.count():
                    # 부분 매칭 시도
                    folder_link = tree_frame.locator(f'a:has-text("{folder_name}")').first
                    if not folder_link.count():
                        self.logger.error(f"    폴더 링크 없음: {folder_name}")
                        return False

                # 폴더 클릭
                try:
                    folder_link.scroll_into_view_if_needed(timeout=2000)
                except:
                    pass

                folder_link.evaluate('el => el.click()')
                time.sleep(2)

            self.logger.info(f"  ✓ 폴더 네비게이션 완료")
            return True

        except Exception as e:
            self.logger.error(f"  폴더 네비게이션 오류: {e}")
            return False

    def _download_all_in_folder(self, page: Page, expected_docs: list) -> int:
        """
        폴더의 모든 문서 다운로드

        contentbody에 표시된 모든 다운로드 버튼을 클릭
        """
        content_frame = page.frame(name="contentbody")
        if not content_frame:
            self.logger.error("  contentbody iframe을 찾을 수 없습니다")
            return 0

        # SEQ 목록 (검증용)
        expected_seqs = {doc['seq']: doc['name'] for doc in expected_docs}

        # 모든 다운로드 버튼 찾기
        download_buttons = content_frame.locator('a:has-text("다운로드")').all()

        if not download_buttons:
            self.logger.warning(f"  다운로드 버튼을 찾을 수 없습니다")
            return 0

        self.logger.info(f"  발견된 다운로드 버튼: {len(download_buttons)}개")

        downloaded_count = 0

        for idx, button in enumerate(download_buttons, 1):
            try:
                self.logger.info(f"    [{idx}/{len(download_buttons)}] 다운로드 중...")

                with page.expect_download(timeout=30000) as download_info:
                    button.click()

                download: Download = download_info.value
                filename = download.suggested_filename or f"document_{idx}.hwp"

                # 파일명 정리
                filename = self._clean_filename(filename)
                file_path = self.output_dir / filename

                # 파일 저장
                download.save_as(file_path)
                self.logger.info(f"    ✓ 저장: {filename}")
                downloaded_count += 1

                time.sleep(0.5)

            except Exception as e:
                self.logger.error(f"    ✗ 다운로드 실패: {str(e)[:100]}")

        self.logger.info(f"  → 총 {downloaded_count}개 다운로드 완료")
        return downloaded_count

    def _clean_filename(self, filename: str) -> str:
        """
        파일명에서 사용 불가능한 문자 제거
        """
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename


def main():
    scraper = HIRALawScraperV3()
    scraper.scrape_all()


if __name__ == '__main__':
    main()
