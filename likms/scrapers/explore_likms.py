"""
국회 법률정보시스템 (LIKMS) 탐색 스크립트

사이트 구조를 파악하고 법령 검색 및 텍스트 추출 방법을 탐색합니다.
"""
from playwright.sync_api import sync_playwright, Page
from pathlib import Path
import time
import json
from datetime import datetime
import sys

# 상위 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

BASE_URL = 'https://likms.assembly.go.kr/law'
OUTPUT_DIR = Path("data/likms/exploration")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class LIKMSExplorer:
    """
    국회 법률정보시스템 탐색기

    법령 검색 메커니즘과 텍스트 추출 방법을 파악합니다.
    """

    def __init__(self):
        self.logger = setup_logger("likms_explorer", project="likms")
        self.screenshots_dir = OUTPUT_DIR / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def explore(self):
        """
        사이트 탐색 실행
        """
        self.logger.info("=" * 60)
        self.logger.info("국회 법률정보시스템 탐색 시작")
        self.logger.info("=" * 60)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)
            context = browser.new_context()
            page = context.new_page()

            try:
                # 1. 메인 페이지 접속
                self.logger.info(f"메인 페이지 접속: {BASE_URL}")
                page.goto(BASE_URL, wait_until="networkidle")
                time.sleep(3)

                # 스크린샷 저장
                self._save_screenshot(page, "01_main_page")

                # 2. 페이지 구조 분석
                self._analyze_page_structure(page)

                # 3. 의료급여법 검색 시도
                self._search_law(page, "의료급여법")

                # 4. 검색 결과 분석
                time.sleep(3)
                self._save_screenshot(page, "02_search_results")
                self._analyze_search_results(page)

                # 5. 첫 번째 결과 클릭 및 상세 페이지 분석
                self._open_first_result(page)

                # 6. 법령 상세 페이지 분석
                time.sleep(3)
                self._save_screenshot(page, "03_law_detail")
                self._analyze_law_detail(page)

                # 7. 법령 텍스트 추출 시도
                law_text = self._extract_law_text(page)
                if law_text:
                    self._save_text(law_text, "의료급여법_샘플")

                self.logger.info("\n탐색 완료! 브라우저를 10초간 유지합니다...")
                time.sleep(10)

            except Exception as e:
                self.logger.error(f"오류 발생: {e}")
                import traceback
                traceback.print_exc()
                self._save_screenshot(page, "99_error")
            finally:
                browser.close()

        self.logger.info("=" * 60)
        self.logger.info("탐색 종료")
        self.logger.info(f"결과 저장 위치: {OUTPUT_DIR}")
        self.logger.info("=" * 60)

    def _analyze_page_structure(self, page: Page):
        """페이지 구조 분석"""
        self.logger.info("\n[페이지 구조 분석]")

        # iframe 확인
        frames = page.frames
        self.logger.info(f"Frame 개수: {len(frames)}")
        for i, frame in enumerate(frames):
            self.logger.info(f"  Frame {i}: {frame.name or frame.url}")

        # 주요 요소 확인
        elements_to_check = [
            "input[type='text']",
            "input[type='search']",
            "button:has-text('검색')",
            "a:has-text('검색')",
            "#search",
            ".search-box",
            "form"
        ]

        for selector in elements_to_check:
            count = page.locator(selector).count()
            if count > 0:
                self.logger.info(f"  발견: {selector} ({count}개)")

    def _search_law(self, page: Page, keyword: str):
        """법령 검색"""
        self.logger.info(f"\n[법령 검색: {keyword}]")

        try:
            # 검색창 찾기 (여러 방법 시도)
            search_input = None
            search_selectors = [
                "input[type='text']",
                "input[type='search']",
                "input[name*='search']",
                "input[placeholder*='검색']",
                "#searchKeyword",
                "#keyword"
            ]

            for selector in search_selectors:
                if page.locator(selector).count() > 0:
                    search_input = page.locator(selector).first
                    self.logger.info(f"  검색창 발견: {selector}")
                    break

            if not search_input:
                self.logger.warning("  검색창을 찾을 수 없습니다. 수동으로 확인 필요")
                return

            # 검색어 입력
            search_input.fill(keyword)
            self.logger.info(f"  검색어 입력: {keyword}")
            time.sleep(1)

            # 검색 버튼 찾기 및 클릭
            search_button = None
            button_selectors = [
                "button:has-text('검색')",
                "a:has-text('검색')",
                "input[type='submit']",
                "button[type='submit']"
            ]

            for selector in button_selectors:
                if page.locator(selector).count() > 0:
                    search_button = page.locator(selector).first
                    self.logger.info(f"  검색 버튼 발견: {selector}")
                    break

            if search_button:
                search_button.click()
                self.logger.info("  검색 실행")
            else:
                # Enter 키로 검색 시도
                search_input.press("Enter")
                self.logger.info("  Enter 키로 검색 실행")

        except Exception as e:
            self.logger.error(f"  검색 실패: {e}")

    def _analyze_search_results(self, page: Page):
        """검색 결과 분석"""
        self.logger.info("\n[검색 결과 분석]")

        # 결과 목록 찾기
        result_selectors = [
            ".search-result",
            ".result-list",
            "table tr",
            "ul.list li",
            "div.list-item"
        ]

        for selector in result_selectors:
            count = page.locator(selector).count()
            if count > 0:
                self.logger.info(f"  결과 항목 발견: {selector} ({count}개)")

                # 첫 번째 항목의 텍스트 확인
                first_item = page.locator(selector).first
                text = first_item.inner_text()[:100]
                self.logger.info(f"  첫 번째 항목: {text}...")

    def _open_first_result(self, page: Page):
        """첫 번째 검색 결과 클릭"""
        self.logger.info("\n[첫 번째 결과 열기]")

        try:
            # 링크 찾기
            link_selectors = [
                "a:has-text('의료급여법')",
                ".law-title a",
                "table a",
                "ul.list a"
            ]

            for selector in link_selectors:
                if page.locator(selector).count() > 0:
                    link = page.locator(selector).first
                    link_text = link.inner_text()
                    self.logger.info(f"  링크 발견: {link_text}")
                    link.click()
                    self.logger.info("  클릭 완료")
                    return

            self.logger.warning("  클릭할 링크를 찾을 수 없습니다")

        except Exception as e:
            self.logger.error(f"  링크 클릭 실패: {e}")

    def _analyze_law_detail(self, page: Page):
        """법령 상세 페이지 분석"""
        self.logger.info("\n[법령 상세 페이지 분석]")

        # 주요 영역 확인
        content_selectors = [
            ".law-content",
            ".law-text",
            "#lawContent",
            "article",
            ".article-content",
            "div.content"
        ]

        for selector in content_selectors:
            count = page.locator(selector).count()
            if count > 0:
                self.logger.info(f"  콘텐츠 영역 발견: {selector}")

    def _extract_law_text(self, page: Page) -> str:
        """법령 텍스트 추출"""
        self.logger.info("\n[법령 텍스트 추출]")

        # 콘텐츠 영역 찾기
        content_selectors = [
            ".law-content",
            ".law-text",
            "#lawContent",
            "article",
            ".article-content",
            "div.content",
            "body"
        ]

        for selector in content_selectors:
            if page.locator(selector).count() > 0:
                content = page.locator(selector).first
                text = content.inner_text()

                if len(text) > 100:  # 충분한 텍스트가 있는 경우
                    self.logger.info(f"  텍스트 추출 성공: {selector}")
                    self.logger.info(f"  텍스트 길이: {len(text)} 글자")
                    self.logger.info(f"  미리보기: {text[:200]}...")
                    return text

        self.logger.warning("  텍스트 추출 실패")
        return None

    def _save_screenshot(self, page: Page, name: str):
        """스크린샷 저장"""
        filepath = self.screenshots_dir / f"{name}.png"
        page.screenshot(path=str(filepath), full_page=True)
        self.logger.info(f"  스크린샷 저장: {filepath.name}")

    def _save_text(self, text: str, name: str):
        """텍스트 파일 저장"""
        filepath = OUTPUT_DIR / f"{name}.txt"
        filepath.write_text(text, encoding='utf-8')
        self.logger.info(f"  텍스트 저장: {filepath}")


def main():
    explorer = LIKMSExplorer()
    explorer.explore()


if __name__ == '__main__':
    main()
