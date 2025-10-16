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
DOCUMENT_TREE_JSON = Path("hira_rulesvc/config/document_tree.json")


class HIRALawScraperV2:
    """
    HIRA 고시 문서 스크래퍼 V2

    all_law_documents.json을 기반으로 모든 리프 노드를 다운로드합니다.
    """

    def __init__(self, output_dir: str = "data/hira_rulesvc/documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger("hira_law_scraper_v2", project="hira_rulesvc")

        # 문서 트리 로드 (경로 정보 포함)
        with open(DOCUMENT_TREE_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.documents = data['documents']

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

                # 각 문서 다운로드 (전체)
                for idx, doc in enumerate(self.documents, 1):
                    self.logger.info(f"\n[{idx}/{len(self.documents)}] {doc['name']} (SEQ={doc['seq']})")

                    # 재시도 로직 (최대 2번)
                    success = False
                    for attempt in range(2):
                        try:
                            # 1. 트리 네비게이션으로 문서 페이지 이동
                            nav_success = self._navigate_to_document(page, doc)
                            if not nav_success:
                                if attempt == 0:
                                    self.logger.warning(f"  [RETRY] 네비게이션 실패, 재시도 중...")
                                    time.sleep(2)
                                else:
                                    failed_count += 1
                                    self.logger.warning(f"  [FAIL] 네비게이션 실패")
                                continue

                            # 2. 다운로드 시도
                            success = self._download_document(page, doc)
                            if success:
                                downloaded_count += 1
                                self.logger.info(f"  [OK] 다운로드 성공")
                                break
                            else:
                                if attempt == 0:
                                    self.logger.warning(f"  [RETRY] 1회 실패, 재시도 중...")
                                    time.sleep(2)
                                else:
                                    failed_count += 1
                                    self.logger.warning(f"  [FAIL] 다운로드 실패")
                        except Exception as e:
                            if attempt == 0:
                                self.logger.warning(f"  [RETRY] 오류 발생, 재시도: {str(e)[:100]}")
                                time.sleep(2)
                            else:
                                failed_count += 1
                                self.logger.error(f"  [ERROR] {str(e)[:200]}")

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

    def _navigate_to_document(self, page: Page, doc: dict) -> bool:
        """
        트리 구조를 따라 문서까지 네비게이션

        Args:
            page: Playwright Page 객체
            doc: 문서 정보 (seq, name, path 포함)

        Returns:
            성공 여부
        """
        seq = doc['seq']
        name = doc['name']
        path = doc.get('path', [])

        self.logger.info(f"  - 네비게이션 시작: {' > '.join(path)} > {name}")

        # tree01 iframe 가져오기
        tree_frame = page.frame(name="tree01")
        if not tree_frame:
            self.logger.error("  tree01 iframe을 찾을 수 없습니다")
            return False

        try:
            # 1. 경로상의 폴더들을 순서대로 클릭
            for folder_name in path:
                self.logger.info(f"    → 폴더 클릭: {folder_name}")

                # 폴더 링크 찾기 (정확한 텍스트 매칭)
                folder_link = tree_frame.locator(f'a:text-is("{folder_name}")').first

                # 링크가 있는지 확인
                if not folder_link.count():
                    self.logger.warning(f"    폴더를 찾을 수 없음: {folder_name}")
                    # 부분 매칭 시도
                    folder_link = tree_frame.locator(f'a:has-text("{folder_name}")').first
                    if not folder_link.count():
                        self.logger.error(f"    폴더 링크 없음: {folder_name}")
                        return False

                # 폴더 링크 클릭 - JavaScript 강제 클릭으로 visible 체크 우회
                try:
                    # 먼저 스크롤해서 보이게 시도
                    try:
                        folder_link.scroll_into_view_if_needed(timeout=2000)
                    except:
                        pass

                    # JavaScript로 강제 클릭 (display:none 무시)
                    folder_link.evaluate('el => el.click()')
                    time.sleep(2.5)  # 트리 확장 대기 (더 길게)
                except Exception as e:
                    self.logger.warning(f"    폴더 클릭 실패: {e}, 더블클릭 시도")
                    try:
                        folder_link.dblclick()
                        time.sleep(2.5)
                    except:
                        folder_link.click()
                        time.sleep(2.5)

            # 2. 최종 파일 링크 클릭
            self.logger.info(f"    → 파일 클릭: {name}")
            file_link = tree_frame.locator(f'a:text-is("{name}")').first

            if not file_link.count():
                self.logger.warning(f"    정확한 파일명 매칭 실패, 부분 매칭 시도")
                file_link = tree_frame.locator(f'a:has-text("{name}")').first
                if not file_link.count():
                    self.logger.error(f"    파일 링크 없음: {name}")
                    return False

            # 파일 링크를 실제로 클릭 (JavaScript 실행 대신)
            try:
                # href 로깅 (디버깅용)
                try:
                    href = file_link.get_attribute('href')
                    self.logger.info(f"    파일 링크 href: {href[:80] if href else 'N/A'}...")
                except:
                    pass

                # 링크를 화면에 보이게 스크롤
                try:
                    file_link.scroll_into_view_if_needed(timeout=3000)
                    time.sleep(0.5)
                except:
                    pass

                # JavaScript로 강제 클릭 (display:none 등 무시)
                file_link.evaluate('el => el.click()')
                time.sleep(3)
                self.logger.info(f"    [OK] 파일 링크 클릭 완료")

            except Exception as e:
                self.logger.error(f"    파일 링크 클릭 실패: {e}")
                return False

            self.logger.info(f"  ✓ 네비게이션 완료")
            return True

        except Exception as e:
            self.logger.error(f"  네비게이션 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _download_document(self, page: Page, doc: dict) -> bool:
        """
        단일 문서 다운로드

        네비게이션 후 contentbody에서 다운로드 버튼 찾아서 클릭
        """
        seq = doc['seq']
        name = doc['name']

        # contentbody iframe 가져오기
        content_frame = page.frame(name="contentbody")
        if not content_frame:
            self.logger.error("  contentbody iframe을 찾을 수 없습니다")
            return False

        # 다운로드 버튼 찾기 (여러 가지 셀렉터 시도)
        download_button = None

        # 시도 1: a:has-text("다운로드")
        try:
            download_button = content_frame.locator('a:has-text("다운로드")').first
            if download_button.count() > 0:
                self.logger.info(f"  - 다운로드 버튼 발견: a:has-text(\"다운로드\")")
            else:
                download_button = None
        except:
            pass

        # 시도 2: td.sbt04 > a
        if not download_button:
            try:
                download_button = content_frame.locator('td.sbt04 > a').first
                if download_button.count() > 0:
                    self.logger.info(f"  - 다운로드 버튼 발견: td.sbt04 > a")
                else:
                    download_button = None
            except:
                pass

        if not download_button or download_button.count() == 0:
            self.logger.warning("  다운로드 버튼을 찾을 수 없습니다")
            return False

        # 다운로드 실행
        try:
            # 이미 존재하는 파일인지 미리 체크하기 위해 파일명 패턴 추정
            # (하지만 실제 파일명은 다운로드 후에야 알 수 있음)

            with page.expect_download(timeout=30000) as download_info:
                download_button.click()

            download: Download = download_info.value
            original_filename = download.suggested_filename or f"{name}.hwp"

            # 파일명에 SEQ 추가하여 중복 방지: [SEQ] 원본파일명.hwp
            filename_without_ext = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else 'hwp'
            filename = f"[{seq}] {filename_without_ext}.{ext}"

            # 파일명 정리 (특수문자 제거)
            filename = self._clean_filename(filename)
            file_path = self.output_dir / filename

            # 이미 파일이 존재하면 건너뛰기
            if file_path.exists():
                self.logger.info(f"  ○ 이미 존재: {filename} (건너뜀)")
                return True

            download.save_as(file_path)
            self.logger.info(f"  - 저장: {filename}")
            return True

        except Exception as e:
            self.logger.error(f"  다운로드 오류: {str(e)[:200]}")
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
