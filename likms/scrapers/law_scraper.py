"""
국회 법률정보시스템 (LIKMS) 법령 수집 크롤러

특정 법령을 검색하고 텍스트를 추출하여 저장합니다.
"""
from playwright.sync_api import sync_playwright, Page
from pathlib import Path
import time
import json
from datetime import datetime
import sys
import re

# 상위 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

BASE_URL = 'https://likms.assembly.go.kr/law'
OUTPUT_DIR = Path("data/likms/laws")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class LIKMSLawScraper:
    """
    국회 법률정보시스템 법령 크롤러

    특정 법령을 검색하고 텍스트를 추출합니다.
    """

    def __init__(self):
        self.logger = setup_logger("likms_scraper", project="likms")

    def scrape_law(self, law_name: str, exact_match: bool = True):
        """
        특정 법령 수집

        Args:
            law_name: 법령명 (예: "의료급여법")
            exact_match: 정확히 일치하는 법령만 선택할지 여부
        """
        self.logger.info("=" * 60)
        self.logger.info(f"법령 수집 시작: {law_name}")
        self.logger.info("=" * 60)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)
            context = browser.new_context()
            page = context.new_page()

            try:
                # 1. 메인 페이지 접속
                self.logger.info(f"메인 페이지 접속: {BASE_URL}")
                page.goto(BASE_URL, wait_until="networkidle")
                time.sleep(2)

                # 2. 법령 검색
                self._search_law(page, law_name)
                time.sleep(3)

                # 3. 검색 결과에서 정확한 법령 찾기
                law_info = self._find_exact_law(page, law_name, exact_match)
                if not law_info:
                    self.logger.error(f"법령을 찾을 수 없습니다: {law_name}")
                    return None

                # 4. 법령 상세 페이지 열기
                self._open_law_detail(page, law_info)
                time.sleep(3)

                # 5. 법령 텍스트 추출
                law_text = self._extract_law_text(page)
                if not law_text:
                    self.logger.error("법령 텍스트 추출 실패")
                    return None

                # 6. 메타데이터 수집
                metadata = self._extract_metadata(page, law_name, law_info)

                # 7. 데이터 저장
                result = {
                    "title": law_name,
                    "metadata": metadata,
                    "content": law_text,
                    "scraped_at": datetime.now().isoformat(),
                    "source": BASE_URL
                }

                self._save_law(result, law_name)

                self.logger.info("=" * 60)
                self.logger.info(f"법령 수집 완료: {law_name}")
                self.logger.info(f"텍스트 길이: {len(law_text)} 글자")
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

        Args:
            law_names: 법령명 리스트
        """
        self.logger.info("=" * 60)
        self.logger.info(f"일괄 수집 시작: {len(law_names)}개 법령")
        self.logger.info("=" * 60)

        results = []
        for idx, law_name in enumerate(law_names, 1):
            self.logger.info(f"\n[{idx}/{len(law_names)}] {law_name}")
            result = self.scrape_law(law_name)
            if result:
                results.append(result)
            time.sleep(2)

        self.logger.info("=" * 60)
        self.logger.info(f"일괄 수집 완료: {len(results)}/{len(law_names)}개 성공")
        self.logger.info("=" * 60)

        return results

    def _search_law(self, page: Page, keyword: str):
        """법령 검색"""
        self.logger.info(f"검색어: {keyword}")

        # 검색창 찾기
        search_input = page.locator("input[type='text']").first
        search_input.fill(keyword)
        self.logger.info("  검색어 입력 완료")

        # 검색 버튼 클릭
        search_button = page.locator("button:has-text('검색')").first
        search_button.click()
        self.logger.info("  검색 실행")

    def _find_exact_law(self, page: Page, law_name: str, exact_match: bool) -> dict:
        """
        검색 결과에서 정확한 법령 찾기

        Returns:
            {
                "title": "의료급여법",
                "law_number": "법률 제20309호",
                "enacted_date": "2024.5.17",
                "link": Locator
            }
        """
        self.logger.info("검색 결과 분석 중...")

        # 테이블의 모든 행 가져오기
        rows = page.locator("table tr").all()
        self.logger.info(f"  총 {len(rows)}개 검색 결과")

        for idx, row in enumerate(rows, 1):
            try:
                # 행의 텍스트 추출
                row_text = row.inner_text()

                # 링크 찾기
                links = row.locator("a").all()
                if not links:
                    continue

                # 법령명 추출 (첫 번째 링크)
                first_link = links[0]
                title = first_link.inner_text().strip()

                # 정확한 매칭 또는 포함 여부 확인
                if exact_match:
                    # 정확히 일치하거나, "의료급여법 시행령" 같은 경우 포함
                    if law_name == title or title.startswith(law_name):
                        self.logger.info(f"  ✓ 법령 발견: {title}")

                        # 메타데이터 추출
                        metadata = self._parse_search_result(row_text)
                        metadata["title"] = title
                        metadata["link"] = first_link

                        return metadata
                else:
                    if law_name in title:
                        self.logger.info(f"  ✓ 법령 발견: {title}")

                        metadata = self._parse_search_result(row_text)
                        metadata["title"] = title
                        metadata["link"] = first_link

                        return metadata

            except Exception as e:
                continue

        self.logger.warning(f"  법령을 찾을 수 없습니다: {law_name}")
        return None

    def _parse_search_result(self, row_text: str) -> dict:
        """
        검색 결과 행에서 메타데이터 추출

        예시 텍스트: "의료급여법\t법률\t보건복지부\t2024.5.17"
        """
        parts = row_text.split("\t")

        metadata = {
            "law_type": parts[1] if len(parts) > 1 else "",
            "ministry": parts[2] if len(parts) > 2 else "",
            "date": parts[3] if len(parts) > 3 else ""
        }

        return metadata

    def _open_law_detail(self, page: Page, law_info: dict):
        """법령 상세 페이지 열기"""
        self.logger.info(f"법령 상세 페이지 열기: {law_info['title']}")

        link = law_info["link"]
        link.click()

        self.logger.info("  상세 페이지 로드 완료")

    def _extract_law_text(self, page: Page) -> str:
        """
        법령 텍스트 추출

        본문 영역에서 깨끗한 텍스트만 추출
        """
        self.logger.info("법령 텍스트 추출 중...")

        # 여러 방법으로 콘텐츠 영역 찾기
        content_selectors = [
            ".law-content",
            ".law-text",
            "#lawContent",
            "article",
            ".article-content"
        ]

        for selector in content_selectors:
            if page.locator(selector).count() > 0:
                content = page.locator(selector).first
                text = content.inner_text()

                if len(text) > 1000:  # 충분한 텍스트가 있는 경우
                    self.logger.info(f"  텍스트 추출 성공 ({len(text)} 글자)")
                    return self._clean_text(text)

        # 콘텐츠 영역을 찾지 못한 경우, body 전체에서 추출
        self.logger.warning("  콘텐츠 영역을 찾지 못해 body 전체를 사용합니다")
        text = page.locator("body").inner_text()

        # 네비게이션, 메뉴 등 불필요한 부분 제거
        text = self._clean_text(text)

        self.logger.info(f"  텍스트 추출 완료 ({len(text)} 글자)")
        return text

    def _clean_text(self, text: str) -> str:
        """
        텍스트 정제

        - 네비게이션, 메뉴 등 제거
        - 여러 줄 공백 정리
        """
        # 불필요한 메뉴 텍스트 패턴 제거
        patterns_to_remove = [
            r"주메뉴바로가기",
            r"본문바로가기",
            r"National Assembly Law Information",
            r"상단 검색창",
            r"통합검색",
            r"검색어입력",
            r"상세검색",
            r"자료등록현황 도움말",
            r"왼쪽 트리박스 영역",
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, "", text)

        # 여러 줄 공백을 2줄로 제한
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 앞뒤 공백 제거
        text = text.strip()

        return text

    def _extract_metadata(self, page: Page, law_name: str, law_info: dict) -> dict:
        """메타데이터 추출"""
        metadata = {
            "title": law_info.get("title", law_name),
            "law_type": law_info.get("law_type", ""),
            "ministry": law_info.get("ministry", ""),
            "date": law_info.get("date", ""),
            "url": page.url
        }

        return metadata

    def _save_law(self, data: dict, law_name: str):
        """법령 데이터 저장"""
        # JSON 저장
        json_path = OUTPUT_DIR / f"{law_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"  JSON 저장: {json_path}")

        # 텍스트 파일 저장 (순수 본문만)
        txt_path = OUTPUT_DIR / f"{law_name}.txt"
        txt_path.write_text(data["content"], encoding='utf-8')
        self.logger.info(f"  TXT 저장: {txt_path}")


def main():
    """
    의료급여법 3종 수집
    """
    scraper = LIKMSLawScraper()

    # 의료급여 관련 법령 3종
    laws_to_scrape = [
        "의료급여법",
        "의료급여법 시행령",
        "의료급여법 시행규칙"
    ]

    scraper.scrape_multiple(laws_to_scrape)


if __name__ == '__main__':
    main()
