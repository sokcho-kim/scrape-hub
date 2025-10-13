"""
HIRA 고시 문서 크롤러 v2

모든 리프 노드 문서를 다운로드합니다.
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
LAW_DOCUMENTS_JSON = Path("hira_rulesvc/config/all_law_documents.json")


class HIRALawScraperV2:
    """
    HIRA 고시 문서 스크래퍼 V2

    all_law_documents.json을 기반으로 모든 리프 노드를 다운로드합니다.
    """

    def __init__(self, output_dir: str = "data/hira_rulesvc/documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger("hira_law_scraper_v2", project="hira_rulesvc")

        # 문서 목록 로드
        with open(LAW_DOCUMENTS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # is_folder가 False인 것만 필터링
            self.documents = [doc for doc in data['documents'] if not doc['is_folder']]

        self.logger.info(f"총 {len(self.documents)}개 문서 대상")

    def scrape_all(self):
        """
        전체 고시 문서 수집
        """
        self.logger.info("=" * 60)
        self.logger.info("HIRA 고시 문서 크롤링 시작 V2")
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

                # 각 문서 다운로드 (테스트: 첫 3개만)
                for idx, doc in enumerate(self.documents[:3], 1):
                    self.logger.info(f"\n[{idx}/{len(self.documents[:3])}] {doc['name']} (SEQ={doc['seq']})")

                    try:
                        success = self._download_document(page, doc)
                        if success:
                            downloaded_count += 1
                            self.logger.info(f"  [OK] 다운로드 성공")
                        else:
                            failed_count += 1
                            self.logger.warning(f"  [FAIL] 다운로드 실패")
                    except Exception as e:
                        failed_count += 1
                        self.logger.error(f"  [ERROR] {e}")

                    time.sleep(0.5)

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

    def _download_document(self, page: Page, doc: dict) -> bool:
        """
        단일 문서 다운로드

        전략:
        1. 트리에서 SEQ 클릭 → contentbody에 목록 표시
        2. 목록에서 다운로드 버튼 클릭
        """
        seq = doc['seq']
        name = doc['name']

        # 1. gotoLawList 함수 호출하여 목록으로 이동
        # tree01 iframe 또는 frame0에서 호출해야 함
        self.logger.info(f"  - 목록 페이지로 이동 중...")

        # tree01 iframe에서 시도
        tree_frame = page.frame(name="tree01")
        if tree_frame:
            try:
                tree_frame.evaluate(f"parent.gotoLawList('{seq}', '0', '{name}', '0', 'null', '1', '9', '1', '0', 'http://', '')")
                time.sleep(2)
            except Exception as e:
                self.logger.warning(f"  tree01에서 호출 실패: {e}")
                # frame0에서 시도
                frame0 = page.frame(name="frame0")
                if frame0:
                    frame0.evaluate(f"gotoLawList('{seq}', '0', '{name}', '0', 'null', '1', '9', '1', '0', 'http://', '')")
                    time.sleep(2)
        else:
            self.logger.error("  tree01 iframe을 찾을 수 없습니다")
            return False

        # 2. contentbody iframe에서 다운로드 버튼 찾기
        content_frame = page.frame(name="contentbody")
        if not content_frame:
            self.logger.error("  contentbody iframe을 찾을 수 없습니다")
            return False

        # 디버그: HTML 저장
        debug_dir = Path("data/hira_rulesvc/debug_download")
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_file = debug_dir / f"seq_{seq}_{name[:20]}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(content_frame.content())
        self.logger.info(f"  - 디버그 HTML 저장: {debug_file.name}")

        # 3. 다운로드 버튼 클릭
        # 스크린샷에서 "다운로드" 버튼이 보임
        # 실제 HTML 구조 확인 필요 - 일단 다양한 selector 시도
        download_selectors = [
            'a:has-text("다운로드")',
            'img[alt="다운로드"]',
            'a[href*="download"]',
            'a[href*="fileDown"]',
        ]

        download_button = None
        for selector in download_selectors:
            try:
                download_button = content_frame.query_selector(selector)
                if download_button:
                    self.logger.info(f"  - 다운로드 버튼 발견: {selector}")
                    break
            except:
                continue

        if not download_button:
            self.logger.warning("  다운로드 버튼을 찾을 수 없습니다")
            return False

        # 4. 다운로드 실행
        try:
            with page.expect_download(timeout=30000) as download_info:
                download_button.click()

            download: Download = download_info.value
            filename = download.suggested_filename or f"{name}.hwp"

            # 파일명 정리 (특수문자 제거)
            filename = self._clean_filename(filename)
            file_path = self.output_dir / filename
            download.save_as(file_path)

            self.logger.info(f"  - 저장: {filename}")
            return True

        except Exception as e:
            self.logger.error(f"  다운로드 오류: {e}")
            return False

    def _clean_filename(self, filename: str) -> str:
        """
        파일명에서 사용 불가능한 문자 제거
        """
        # Windows 파일명 금지 문자: < > : " / \ | ? *
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename


def main():
    scraper = HIRALawScraperV2()
    scraper.scrape_all()


if __name__ == '__main__':
    main()
