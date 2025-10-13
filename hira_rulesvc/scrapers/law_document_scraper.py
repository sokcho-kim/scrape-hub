"""
HIRA 고시 문서 크롤러

트리에서 고시 문서(HWP, PDF 등)를 다운로드합니다.
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
from hira_rulesvc.config import TREE_TO_SEQ_MAPPING

BASE_URL = 'http://rulesvc.hira.or.kr/lmxsrv/main/main.srv'


class HIRALawDocumentScraper:
    """
    HIRA 고시 문서 스크래퍼

    트리 구조에서 고시 문서 파일을 다운로드합니다.
    """

    def __init__(self, output_dir: str = "data/hira_rulesvc/documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger("hira_law_document_scraper", project="hira_rulesvc")

    def scrape_all(self):
        """
        전체 고시 문서 수집
        """
        self.logger.info("=" * 60)
        self.logger.info("HIRA 고시 문서 크롤링 시작")
        self.logger.info("=" * 60)

        # tree.md 기반 트리 구조를 순회하면서 문서 다운로드
        total_documents = 0

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            try:
                # 메인 페이지 접속
                self.logger.info(f"메인 페이지 접속: {BASE_URL}")
                page.goto(BASE_URL)
                page.wait_for_load_state("networkidle")
                time.sleep(2)

                # 서식정보 탭 클릭 (최근 고시정보 표시용)
                self.logger.info("서식정보 탭 클릭")
                page.evaluate("menu_go('2')")
                time.sleep(2)

                # contentbody iframe에서 최근 고시정보 추출
                content_frame = page.frame(name="contentbody")
                if not content_frame:
                    self.logger.error("contentbody iframe을 찾을 수 없습니다")
                    return

                # 최근 고시정보 목록 추출
                law_items = self._extract_recent_laws(content_frame)
                self.logger.info(f"최근 고시정보 {len(law_items)}개 발견")

                # 각 고시 문서 다운로드
                for idx, item in enumerate(law_items, 1):
                    self.logger.info(f"\n[{idx}/{len(law_items)}] {item['title']}")
                    self.logger.info(f"  - 날짜: {item['date']}")
                    self.logger.info(f"  - 파일: {item['filename']}")

                    if item['file_type'] == 'hwp':
                        # HWP 파일 - 뷰어 팝업에서 다운로드 버튼 클릭
                        self.logger.info(f"  - HWP 파일 다운로드 (SEQ_REVISION={item['seq_revision']})")
                        success = self._download_hwp_via_popup(page, item)
                    else:
                        # 기타 파일 - fileDown 함수 직접 호출
                        self.logger.info(f"  - 직접 다운로드 (SEQ={item['seq']})")
                        success = self._download_direct(page, item)

                    if success:
                        total_documents += 1
                        self.logger.info(f"  [OK] 다운로드 성공")
                    else:
                        self.logger.warning(f"  [FAIL] 다운로드 실패")

                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"오류 발생: {e}")
                import traceback
                traceback.print_exc()
            finally:
                browser.close()

        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"크롤링 완료! 총 {total_documents}개 문서 다운로드")
        self.logger.info(f"저장 위치: {self.output_dir}")
        self.logger.info("=" * 60)

    def _extract_recent_laws(self, frame) -> list:
        """
        최근 고시정보 목록 추출
        """
        items = []

        # "최근고시정보" 섹션의 li 요소들 가져오기
        law_list_selector = 'ul.list01 li'
        law_elements = frame.query_selector_all(law_list_selector)

        for elem in law_elements:
            try:
                # 제목 추출
                title_elem = elem.query_selector('a')
                if not title_elem:
                    continue

                title = title_elem.get_attribute('title') or title_elem.inner_text().strip()

                # href 속성에서 다운로드 정보 추출
                href = title_elem.get_attribute('href') or ''

                # 날짜 추출
                date_elem = elem.query_selector('span.mdate')
                date = date_elem.inner_text().strip() if date_elem else ''

                # 파일 타입 및 다운로드 정보 파싱
                item = {
                    'title': title,
                    'date': date,
                    'href': href,
                    'filename': '',
                    'file_type': '',
                    'seq_revision': None,
                    'seq': None
                }

                # showPopup('/lmxsrv/print/hwpView.srv?SEQ_REVISION=1366', 'hwpView', 800, 680)
                if 'hwpView.srv' in href:
                    item['file_type'] = 'hwp'
                    # SEQ_REVISION 추출
                    if 'SEQ_REVISION=' in href:
                        seq_rev = href.split('SEQ_REVISION=')[1].split("'")[0]
                        item['seq_revision'] = seq_rev
                    item['filename'] = f"{title}.hwp"

                # fileDown('2284', 'rev')
                elif 'fileDown' in href:
                    item['file_type'] = 'other'
                    # SEQ 추출
                    if "fileDown('" in href:
                        seq = href.split("fileDown('")[1].split("'")[0]
                        item['seq'] = seq
                    item['filename'] = f"{title}.pdf"

                items.append(item)

            except Exception as e:
                self.logger.warning(f"항목 파싱 실패: {e}")
                continue

        return items

    def _download_hwp_via_popup(self, page: Page, item: dict) -> bool:
        """
        HWP 뷰어 팝업에서 다운로드
        """
        try:
            # 새 팝업 대기
            with page.context.expect_page() as popup_info:
                # 팝업 열기
                page.evaluate(f"showPopup('/lmxsrv/print/hwpView.srv?SEQ_REVISION={item['seq_revision']}', 'hwpView', 800, 680)")

            popup = popup_info.value
            popup.wait_for_load_state("networkidle")
            time.sleep(2)

            # 팝업에서 다운로드 버튼 찾기
            # (실제 HTML 구조를 보고 selector 조정 필요)
            download_button = popup.query_selector('a[href*="download"], img[alt*="다운로드"], input[value*="다운로드"]')

            if download_button:
                with page.expect_download() as download_info:
                    download_button.click()

                download: Download = download_info.value
                filename = download.suggested_filename or item['filename']
                file_path = self.output_dir / filename
                download.save_as(file_path)

                popup.close()
                return True
            else:
                self.logger.warning("  다운로드 버튼을 찾을 수 없습니다")
                popup.close()
                return False

        except Exception as e:
            self.logger.error(f"  HWP 다운로드 오류: {e}")
            return False

    def _download_direct(self, page: Page, item: dict) -> bool:
        """
        fileDown 함수 직접 호출하여 다운로드
        """
        try:
            with page.expect_download(timeout=60000) as download_info:
                page.evaluate(f"fileDown('{item['seq']}', 'rev')")

            download: Download = download_info.value
            filename = download.suggested_filename or item['filename']
            file_path = self.output_dir / filename
            download.save_as(file_path)

            return True

        except Exception as e:
            self.logger.error(f"  직접 다운로드 오류: {e}")
            return False


def main():
    scraper = HIRALawDocumentScraper()
    scraper.scrape_all()


if __name__ == '__main__':
    main()
