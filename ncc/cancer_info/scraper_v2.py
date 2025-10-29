"""
NCC (국립암센터) 암정보 스크래퍼 v2

전체 100개 암종 수집 (태그 시스템 적용)
- 주요암, 성인, 소아청소년 태그
- 개선된 노이즈 필터링
"""
import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import logging
import sys

sys.path.append(str(Path(__file__).parent.parent))

from ncc.config import (
    BASE_URL,
    CHEMOTHERAPY_PAGES,
    CANCER_TYPES_ALL,
    SCRAPING_CONFIG,
    OUTPUT_DIRS
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'{OUTPUT_DIRS["logs"]}/scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class NCCScraper:
    """국립암센터 암정보 스크래퍼 v2"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.scraped_count = 0
        self.failed_count = 0

        # 출력 디렉토리 생성
        for dir_path in OUTPUT_DIRS.values():
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=SCRAPING_CONFIG["headless"]
        )
        self.page = await self.browser.new_page()
        await self.page.set_extra_http_headers({
            'User-Agent': SCRAPING_CONFIG["user_agent"]
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()

    async def scrape_cancer(self, cancer_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        단일 암종 스크래핑 (cancer_seq 기반)

        Args:
            cancer_info: 암종 정보 {"name": "갑상선암", "cancer_seq": "3341", "tags": [...]}

        Returns:
            파싱된 데이터 또는 None
        """
        # URL 생성 (전체암 보기 페이지의 view.do)
        url = f"{BASE_URL}/lay1/program/S1T211C223/cancer/view.do?cancer_seq={cancer_info['cancer_seq']}"
        logger.info(f"스크래핑 시작: {cancer_info['name']} (seq: {cancer_info['cancer_seq']})")

        try:
            # 페이지 로드
            await self.page.goto(url, timeout=SCRAPING_CONFIG["timeout"])
            await self.page.wait_for_load_state("networkidle")

            # 콘텐츠 영역 추출
            content_data = await self.extract_content()

            if not content_data:
                logger.warning(f"콘텐츠 추출 실패: {cancer_info['name']}")
                return None

            # 데이터 구조화 (태그 포함)
            result = {
                "name": cancer_info["name"],
                "cancer_seq": cancer_info["cancer_seq"],
                "tags": cancer_info["tags"],  # 태그 추가
                "url": url,
                "category": " > ".join(cancer_info["tags"]),
                "content": content_data,
                "metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "2.0"
                }
            }

            # 저장 (파일명: {암종이름}_{cancer_seq}.json)
            filename = f"{cancer_info['name']}_{cancer_info['cancer_seq']}"
            await self.save_data(result, filename)

            self.scraped_count += 1
            logger.info(f"스크래핑 완료: {cancer_info['name']}")

            return result

        except Exception as e:
            logger.error(f"스크래핑 실패: {cancer_info['name']} - {str(e)}")
            self.failed_count += 1
            return None

    async def extract_content(self) -> Optional[Dict[str, Any]]:
        """
        페이지 콘텐츠 추출 (노이즈 제거 버전)
        """
        try:
            # 먼저 노이즈 요소 제거
            await self.remove_noise_elements()

            # 메인 콘텐츠 영역 찾기
            content_selectors = [
                '.cont_box',
                '.contents_box',
                '.detail_cont',
                '#contents',
                'article',
                '.content'
            ]

            content_element = None
            for selector in content_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    content_element = element
                    break

            if not content_element:
                logger.warning("콘텐츠 영역을 찾을 수 없음")
                content_element = await self.page.query_selector('body')

            # 섹션 추출 (제목 + 본문) - h4#go 이후부터만
            sections = await self.extract_sections_filtered(content_element)

            # 표 추출
            tables = await self.extract_tables(content_element)

            # 이미지 추출 (콘텐츠 이미지만)
            images = await self.extract_content_images(content_element)

            # 전체 텍스트 (정제된 버전)
            raw_text = await content_element.inner_text()

            return {
                "sections": sections,
                "tables": tables,
                "images": images,
                "raw_text": raw_text.strip()
            }

        except Exception as e:
            logger.error(f"콘텐츠 추출 중 오류: {str(e)}")
            return None

    async def remove_noise_elements(self):
        """페이지에서 노이즈 요소 제거"""
        noise_selectors = [
            'header', 'footer',
            '.sub-nav', '.video_menu',
            '.lnb', '.gnb',
            '.sns__link', '.link__box',
            '.sub_site', '.language_book',
            '#evaluation',
            '.cancer_menu', '.cancer_list',
            'nav',
        ]

        for selector in noise_selectors:
            try:
                await self.page.evaluate(f'''
                    document.querySelectorAll("{selector}").forEach(el => el.remove());
                ''')
            except:
                pass

    async def extract_sections_filtered(self, element) -> List[Dict[str, Any]]:
        """섹션별 제목 + 내용 추출 (필터링된 버전)"""
        sections = []

        try:
            headings = await element.query_selector_all('h4, h5, h6')

            for heading in headings:
                heading_text = await heading.inner_text()
                heading_tag = await heading.evaluate('el => el.tagName.toLowerCase()')

                # 네비게이션 텍스트 제외
                nav_keywords = ['하위메뉴', '바로가기', '공유하기', '인쇄', '만족도', '평가']
                if any(keyword in heading_text for keyword in nav_keywords):
                    continue

                # 제목 다음의 콘텐츠 추출
                next_elements = await heading.evaluate_handle('''
                    el => {
                        const result = [];
                        let current = el.nextElementSibling;
                        while (current && !['H4', 'H5', 'H6'].includes(current.tagName)) {
                            if (current.tagName !== 'TABLE' && current.tagName !== 'SCRIPT') {
                                const text = current.innerText;
                                if (text && text.trim()) {
                                    result.push(text.trim());
                                }
                            }
                            current = current.nextElementSibling;
                        }
                        return result.join('\\n');
                    }
                ''')

                section_content = await next_elements.json_value()

                if heading_text.strip() and section_content.strip():
                    sections.append({
                        "heading": heading_text.strip(),
                        "level": heading_tag,
                        "content": section_content.strip()
                    })

        except Exception as e:
            logger.error(f"필터링된 섹션 추출 중 오류: {str(e)}")

        return sections

    async def extract_tables(self, element) -> List[Dict[str, Any]]:
        """표 데이터 추출"""
        tables = []

        try:
            table_elements = await element.query_selector_all('table')

            for idx, table in enumerate(table_elements):
                caption = await table.query_selector('caption')
                table_title = await caption.inner_text() if caption else f"표 {idx + 1}"

                headers = []
                header_rows = await table.query_selector_all('thead tr, tr:first-child')
                if header_rows:
                    header_cells = await header_rows[0].query_selector_all('th, td')
                    for cell in header_cells:
                        headers.append(await cell.inner_text())

                rows = []
                body_rows = await table.query_selector_all('tbody tr')
                if not body_rows:
                    all_rows = await table.query_selector_all('tr')
                    body_rows = all_rows[1:] if len(all_rows) > 1 else []

                for row in body_rows:
                    cells = await row.query_selector_all('td, th')
                    row_data = []
                    for cell in cells:
                        row_data.append(await cell.inner_text())
                    if row_data:
                        rows.append(row_data)

                tables.append({
                    "title": table_title.strip(),
                    "headers": [h.strip() for h in headers],
                    "rows": [[cell.strip() for cell in row] for row in rows]
                })

        except Exception as e:
            logger.error(f"표 추출 중 오류: {str(e)}")

        return tables

    async def extract_content_images(self, element) -> List[Dict[str, str]]:
        """콘텐츠 이미지만 추출 (아이콘, SNS 이미지 제외)"""
        images = []

        try:
            img_elements = await element.query_selector_all('img')

            exclude_keywords = [
                'icon', 'ico', 'sns', 'facebook', 'twitter', 'instagram',
                'youtube', 'blog', 'star', 'btn', 'button', 'close', 'arrow'
            ]

            for img in img_elements:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt') or ""

                if any(keyword in src.lower() for keyword in exclude_keywords):
                    continue
                if any(keyword in alt.lower() for keyword in exclude_keywords):
                    continue

                if src and not src.startswith('http'):
                    if src.startswith('/'):
                        src = BASE_URL + src
                    else:
                        src = BASE_URL + '/' + src

                if src:
                    images.append({
                        "url": src,
                        "alt": alt.strip()
                    })

        except Exception as e:
            logger.error(f"콘텐츠 이미지 추출 중 오류: {str(e)}")

        return images

    async def save_data(self, data: Dict[str, Any], filename: str):
        """데이터 저장 (JSON)"""
        try:
            parsed_file = Path(OUTPUT_DIRS["parsed"]) / f"{filename}.json"
            with open(parsed_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"저장 완료: {parsed_file}")

        except Exception as e:
            logger.error(f"데이터 저장 실패: {str(e)}")

    async def run_phase2_all(self):
        """Phase 2: 전체 100개 암종 스크래핑"""
        logger.info("=" * 100)
        logger.info("Phase 2: 전체 100개 암종 스크래핑 시작")
        logger.info(f"총 암종 수: {len(CANCER_TYPES_ALL)}개")
        logger.info("=" * 100)

        results = []

        for cancer_info in CANCER_TYPES_ALL:
            result = await self.scrape_cancer(cancer_info)
            if result:
                results.append(result)

            # 요청 간격 대기
            await asyncio.sleep(SCRAPING_CONFIG["delay_between_requests"])

        # 최종 요약
        logger.info("=" * 100)
        logger.info("Phase 2 완료")
        logger.info(f"성공: {self.scraped_count}개 / 실패: {self.failed_count}개")
        logger.info(f"성공률: {self.scraped_count / len(CANCER_TYPES_ALL) * 100:.1f}%")
        logger.info("=" * 100)

        # 요약 JSON 저장
        summary = {
            "phase": "phase2_all",
            "total_cancers": len(CANCER_TYPES_ALL),
            "scraped_count": self.scraped_count,
            "failed_count": self.failed_count,
            "success_rate": f"{self.scraped_count / len(CANCER_TYPES_ALL) * 100:.1f}%",
            "timestamp": datetime.now().isoformat()
        }

        summary_file = Path(OUTPUT_DIRS["parsed"]) / "phase2_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return results


async def main(mode: str = "phase2_all"):
    """메인 실행 함수"""
    async with NCCScraper() as scraper:
        if mode == "phase2_all":
            await scraper.run_phase2_all()
        else:
            print(f"알 수 없는 모드: {mode}")
            print("사용 가능한 모드: phase2_all")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "phase2_all"
    asyncio.run(main(mode))
