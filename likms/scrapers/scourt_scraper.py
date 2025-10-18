"""
대법원 포털에서 법령 수집 크롤러

의료급여법, 시행령, 시행규칙을 수집합니다.
"""
from playwright.sync_api import sync_playwright, Page
from pathlib import Path
import time
import json
from datetime import datetime
import sys
import urllib.parse

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

BASE_URL = "https://portal.scourt.go.kr/pgp/main.on"
OUTPUT_DIR = Path("data/likms/laws")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class SCourtLawScraper:
    """
    대법원 포털 법령 크롤러
    """

    def __init__(self):
        self.logger = setup_logger("scourt_scraper", project="likms")

    def scrape_law_by_search(self, law_name: str):
        """
        법령명으로 검색해서 수집

        Args:
            law_name: 법령명 (예: "의료급여법", "의료급여법 시행령")
        """
        self.logger.info("=" * 60)
        self.logger.info(f"법령 수집: {law_name}")
        self.logger.info("=" * 60)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=300)
            page = browser.new_page()

            try:
                # 1. 법령 검색
                self.logger.info("법령 검색 중...")
                self._search_law(page, law_name)
                time.sleep(3)

                # 2. 검색 결과에서 정확한 법령 찾아서 클릭
                if not self._click_exact_law(page, law_name):
                    self.logger.error(f"법령을 찾을 수 없습니다: {law_name}")
                    return None

                time.sleep(3)

                # 3. 법령 텍스트 추출
                law_text = self._extract_law_text(page)
                if not law_text:
                    self.logger.error("법령 텍스트 추출 실패")
                    return None

                # 4. 메타데이터 추출
                metadata = self._extract_metadata(page, law_name)

                # 5. 데이터 저장
                result = {
                    "title": law_name,
                    "metadata": metadata,
                    "content": law_text,
                    "scraped_at": datetime.now().isoformat(),
                    "source": "대법원 사법정보공개포털",
                    "url": page.url
                }

                self._save_law(result, law_name)

                self.logger.info("=" * 60)
                self.logger.info(f"✅ 법령 수집 완료: {law_name}")
                self.logger.info(f"텍스트 길이: {len(law_text):,} 글자")
                self.logger.info("=" * 60)

                return result

            except Exception as e:
                self.logger.error(f"오류 발생: {e}")
                import traceback
                traceback.print_exc()
                return None
            finally:
                browser.close()

    def scrape_multiple(self, law_names: list):
        """
        여러 법령 일괄 수집
        """
        self.logger.info("=" * 60)
        self.logger.info(f"일괄 수집 시작: {len(law_names)}개 법령")
        self.logger.info("=" * 60)

        results = []
        for idx, law_name in enumerate(law_names, 1):
            self.logger.info(f"\n[{idx}/{len(law_names)}] {law_name}")
            result = self.scrape_law_by_search(law_name)
            if result:
                results.append(result)
            time.sleep(2)

        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"일괄 수집 완료: {len(results)}/{len(law_names)}개 성공")
        self.logger.info("=" * 60)

        return results

    def _search_law(self, page: Page, law_name: str):
        """법령 검색 페이지 열기"""
        # 검색어 URL 인코딩
        search_keyword = urllib.parse.quote(law_name)

        # 검색 URL 구성
        # 예: w2xPath=PGP1021M04&c=900&srchwd=의료급여법
        search_url = f"{BASE_URL}?w2xPath=PGP1021M04&c=900&srchwd={search_keyword}"

        self.logger.info(f"검색 URL: {search_url}")
        page.goto(search_url, wait_until="networkidle")

    def _click_exact_law(self, page: Page, law_name: str) -> bool:
        """
        검색 결과에서 정확히 일치하는 법령 클릭
        """
        self.logger.info(f"검색 결과에서 '{law_name}' 찾는 중...")

        # 페이지 제목 확인
        title = page.title()
        if law_name in title:
            self.logger.info(f"✓ 이미 법령 페이지에 있음: {title}")
            return True

        # 링크 찾기
        links = page.locator("a").all()
        for link in links:
            try:
                link_text = link.inner_text().strip()
                if law_name == link_text or law_name in link_text:
                    self.logger.info(f"✓ 법령 링크 발견: {link_text}")
                    link.click()
                    return True
            except:
                continue

        self.logger.warning(f"법령 링크를 찾을 수 없음: {law_name}")
        return False

    def _extract_law_text(self, page: Page) -> str:
        """법령 텍스트 추출"""
        self.logger.info("법령 텍스트 추출 중...")

        body_text = page.locator("body").inner_text()

        self.logger.info(f"✓ 텍스트 추출 완료 ({len(body_text):,} 글자)")
        return body_text

    def _extract_metadata(self, page: Page, law_name: str) -> dict:
        """메타데이터 추출"""
        metadata = {
            "title": law_name,
            "page_title": page.title(),
            "url": page.url
        }

        # 페이지에서 법령번호, 시행일 등 추출 시도
        body_text = page.locator("body").inner_text()

        # 법령번호 패턴: [법률 제20926호, ...]
        import re
        law_number_match = re.search(r'\[([^\]]+제\d+호[^\]]*)\]', body_text)
        if law_number_match:
            metadata["law_number"] = law_number_match.group(1)

        return metadata

    def _save_law(self, data: dict, law_name: str):
        """법령 데이터 저장"""
        # 파일명에서 특수문자 제거
        safe_name = law_name.replace(" ", "_").replace("/", "_")

        # JSON 저장
        json_path = OUTPUT_DIR / f"{safe_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"  JSON 저장: {json_path}")

        # 텍스트 파일 저장
        txt_path = OUTPUT_DIR / f"{safe_name}.txt"
        txt_path.write_text(data["content"], encoding='utf-8')
        self.logger.info(f"  TXT 저장: {txt_path}")


def main():
    """
    의료급여법 3종 수집
    """
    scraper = SCourtLawScraper()

    # 의료급여 관련 법령 3종
    laws_to_scrape = [
        "의료급여법",
        "의료급여법 시행령",
        "의료급여법 시행규칙"
    ]

    scraper.scrape_multiple(laws_to_scrape)


if __name__ == '__main__':
    main()
