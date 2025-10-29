"""
NCC (국립암센터) 암정보 스크래퍼

Phase 1: 항암화학요법 관련 페이지 수집
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

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from ncc.config import (
    BASE_URL,
    CHEMOTHERAPY_PAGES,
    CANCER_TYPES,
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
    """국립암센터 암정보 스크래퍼"""

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

    async def scrape_page(self, page_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        단일 페이지 스크래핑

        Args:
            page_info: 페이지 정보 (url, category, title, filename)

        Returns:
            파싱된 데이터 또는 None (실패 시)
        """
        url = BASE_URL + page_info["url"]
        logger.info(f"스크래핑 시작: {page_info['title']} ({url})")

        try:
            # 페이지 로드
            await self.page.goto(url, timeout=SCRAPING_CONFIG["timeout"])
            await self.page.wait_for_load_state("networkidle")

            # 콘텐츠 영역 추출
            content_data = await self.extract_content()

            if not content_data:
                logger.warning(f"콘텐츠 추출 실패: {page_info['title']}")
                return None

            # 데이터 구조화
            result = {
                "url": url,
                "category": page_info["category"],
                "title": page_info["title"],
                "filename": page_info["filename"],
                "content": content_data,
                "metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "1.0"
                }
            }

            # 저장
            await self.save_data(result, page_info["filename"])

            self.scraped_count += 1
            logger.info(f"✅ 스크래핑 완료: {page_info['title']}")

            return result

        except Exception as e:
            logger.error(f"❌ 스크래핑 실패: {page_info['title']} - {str(e)}")
            self.failed_count += 1
            return None

    async def extract_content(self) -> Optional[Dict[str, Any]]:
        """
        페이지 콘텐츠 추출 (노이즈 제거 버전)

        Returns:
            {
                "sections": [...],
                "tables": [...],
                "images": [...],
                "raw_text": "..."
            }
        """
        try:
            # 먼저 노이즈 요소 제거 (navigation, menu, breadcrumb, social media 등)
            await self.remove_noise_elements()

            # 메인 콘텐츠 영역 찾기
            # NCC 사이트는 보통 .cont_box, .contents_box, .detail_cont 등의 클래스 사용
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
                # body 전체를 대상으로
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
            'header',  # 헤더 전체
            'footer',  # 푸터
            '.sub-nav',  # 상단 네비게이션
            '.video_menu',  # 비디오 메뉴
            '.lnb',  # 좌측 네비게이션
            '.gnb',  # 글로벌 네비게이션
            '.sns__link',  # SNS 링크
            '.link__box',  # 링크 박스
            '.sub_site',  # 서브 사이트 링크
            '.language_book',  # 언어 선택
            '#evaluation',  # 평가/만족도 영역
            '.cancer_menu',  # 암 종류 메뉴
            '.cancer_list',  # 암 목록
            'nav',  # 모든 nav 태그
        ]

        for selector in noise_selectors:
            try:
                await self.page.evaluate(f'''
                    document.querySelectorAll("{selector}").forEach(el => el.remove());
                ''')
            except:
                pass  # 없으면 무시

    async def extract_sections(self, element) -> List[Dict[str, Any]]:
        """섹션별 제목 + 내용 추출"""
        sections = []

        try:
            # h2, h3, h4 등의 제목 요소 찾기
            headings = await element.query_selector_all('h2, h3, h4, .tit, .subtitle')

            for heading in headings:
                heading_text = await heading.inner_text()
                heading_tag = await heading.evaluate('el => el.tagName.toLowerCase()')

                # 제목 다음의 콘텐츠 추출 (다음 제목 전까지)
                section_content = ""

                # 제목 바로 다음 요소들 수집
                next_elements = await heading.evaluate_handle('''
                    el => {
                        const result = [];
                        let current = el.nextElementSibling;
                        while (current && !['H2', 'H3', 'H4'].includes(current.tagName)) {
                            if (current.tagName !== 'TABLE') {  // 표는 별도 처리
                                result.push(current.innerText);
                            }
                            current = current.nextElementSibling;
                        }
                        return result.join('\\n');
                    }
                ''')

                section_content = await next_elements.json_value()

                if heading_text.strip():
                    sections.append({
                        "heading": heading_text.strip(),
                        "level": heading_tag,
                        "content": section_content.strip() if section_content else ""
                    })

        except Exception as e:
            logger.error(f"섹션 추출 중 오류: {str(e)}")

        return sections

    async def extract_tables(self, element) -> List[Dict[str, Any]]:
        """표 데이터 추출"""
        tables = []

        try:
            table_elements = await element.query_selector_all('table')

            for idx, table in enumerate(table_elements):
                # 표 제목 (caption 또는 이전 제목)
                caption = await table.query_selector('caption')
                table_title = await caption.inner_text() if caption else f"표 {idx + 1}"

                # 헤더 추출
                headers = []
                header_rows = await table.query_selector_all('thead tr, tr:first-child')
                if header_rows:
                    header_cells = await header_rows[0].query_selector_all('th, td')
                    for cell in header_cells:
                        headers.append(await cell.inner_text())

                # 데이터 행 추출
                rows = []
                body_rows = await table.query_selector_all('tbody tr')
                if not body_rows:
                    # tbody가 없으면 전체 tr 중 첫 행 제외
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

    async def extract_images(self, element) -> List[Dict[str, str]]:
        """이미지 정보 추출"""
        images = []

        try:
            img_elements = await element.query_selector_all('img')

            for img in img_elements:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt') or ""

                # 상대 경로를 절대 경로로 변환
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
            logger.error(f"이미지 추출 중 오류: {str(e)}")

        return images

    async def extract_sections_filtered(self, element) -> List[Dict[str, Any]]:
        """
        섹션별 제목 + 내용 추출 (필터링된 버전)
        h4, h5, h6 태그만 추출하여 네비게이션 메뉴 제외
        """
        sections = []

        try:
            # h4, h5, h6만 추출 (h2, h3는 네비게이션에서 사용됨)
            headings = await element.query_selector_all('h4, h5, h6')

            for heading in headings:
                heading_text = await heading.inner_text()
                heading_tag = await heading.evaluate('el => el.tagName.toLowerCase()')

                # 제목이 "요약설명", "갑상선암이란" 등 실제 콘텐츠인지 확인
                # 네비게이션 텍스트 제외
                nav_keywords = ['하위메뉴', '바로가기', '공유하기', '인쇄', '만족도', '평가']
                if any(keyword in heading_text for keyword in nav_keywords):
                    continue

                # 제목 다음의 콘텐츠 추출
                section_content = ""
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

    async def extract_content_images(self, element) -> List[Dict[str, str]]:
        """
        콘텐츠 이미지만 추출 (아이콘, SNS 이미지 제외)
        """
        images = []

        try:
            img_elements = await element.query_selector_all('img')

            # 제외할 이미지 키워드
            exclude_keywords = [
                'icon', 'ico', 'sns', 'facebook', 'twitter', 'instagram',
                'youtube', 'blog', 'star', 'btn', 'button', 'close', 'arrow'
            ]

            for img in img_elements:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt') or ""

                # 아이콘이나 UI 요소 제외
                if any(keyword in src.lower() for keyword in exclude_keywords):
                    continue

                if any(keyword in alt.lower() for keyword in exclude_keywords):
                    continue

                # 상대 경로를 절대 경로로 변환
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
            # Parsed JSON 저장
            parsed_file = Path(OUTPUT_DIRS["parsed"]) / f"{filename}.json"
            with open(parsed_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"저장 완료: {parsed_file}")

        except Exception as e:
            logger.error(f"데이터 저장 실패: {str(e)}")

    async def run_phase1(self):
        """Phase 1: 항암화학요법 페이지 스크래핑"""
        logger.info("=" * 100)
        logger.info("Phase 1: 항암화학요법 정보 스크래핑 시작")
        logger.info("=" * 100)

        results = []

        for page_info in CHEMOTHERAPY_PAGES:
            result = await self.scrape_page(page_info)
            if result:
                results.append(result)

            # 요청 간격 대기
            await asyncio.sleep(SCRAPING_CONFIG["delay_between_requests"])

        # 최종 요약
        logger.info("=" * 100)
        logger.info("Phase 1 완료")
        logger.info(f"성공: {self.scraped_count}개 / 실패: {self.failed_count}개")
        logger.info("=" * 100)

        return results

    async def extract_cancer_content_links(self, cancer_info: Dict[str, str]) -> List[Dict[str, str]]:
        """
        암종별 list 페이지에서 실제 콘텐츠 링크 추출

        Args:
            cancer_info: 암종 정보 (name, code, list_url)

        Returns:
            추출된 페이지 정보 리스트 [{"url": "...", "title": "...", "is_main": bool}]
        """
        url = BASE_URL + cancer_info["list_url"]
        logger.info(f"링크 추출 시작: {cancer_info['name']} ({url})")

        try:
            await self.page.goto(url, timeout=SCRAPING_CONFIG["timeout"], wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)  # 2초 대기 (동적 콘텐츠 로드)

            links = []

            # 패턴 1: 메인 list.do 페이지 자체 (가장 중요)
            links.append({
                "url": cancer_info["list_url"],
                "title": f"{cancer_info['name']} 개요",
                "cancer_name": cancer_info["name"],
                "is_main": True
            })

            # 패턴 2: cancer/view.do 링크 (상세 페이지)
            all_links = await self.page.query_selector_all('a')
            for link in all_links:
                href = await link.get_attribute('href')
                if not href:
                    continue

                # cancer/view.do 또는 contents.do 링크 찾기
                if 'cancer/view.do' in href or (f'S1T211{cancer_info["code"]}' in href and 'contents.do' in href):
                    try:
                        title = await link.inner_text()
                        title = title.strip()

                        if not title or len(title) > 100:  # 너무 긴 제목은 제외
                            continue

                        # 상대 경로 처리
                        if not href.startswith('http'):
                            if not href.startswith('/'):
                                href = '/' + href

                        # 중복 제거
                        if not any(l['url'] == href for l in links):
                            links.append({
                                "url": href,
                                "title": title,
                                "cancer_name": cancer_info["name"],
                                "is_main": False
                            })
                    except Exception:
                        continue

            logger.info(f"링크 추출 완료: {cancer_info['name']} - {len(links)}개")
            return links

        except Exception as e:
            logger.error(f"링크 추출 실패: {cancer_info['name']} - {str(e)}")
            # 실패해도 최소한 메인 페이지는 반환
            return [{
                "url": cancer_info["list_url"],
                "title": f"{cancer_info['name']} 개요",
                "cancer_name": cancer_info["name"],
                "is_main": True
            }]

    async def run_phase2(self, max_cancers: Optional[int] = None):
        """
        Phase 2: 암종별 치료 정보 스크래핑

        Args:
            max_cancers: 최대 암종 수 (테스트용, None이면 전체)
        """
        logger.info("=" * 100)
        logger.info("Phase 2: 암종별 치료 정보 스크래핑 시작")
        logger.info("=" * 100)

        all_results = []
        cancer_types = CANCER_TYPES[:max_cancers] if max_cancers else CANCER_TYPES

        for cancer_info in cancer_types:
            logger.info(f"\n[{cancer_info['name']}] 처리 시작")

            # 1. 링크 추출
            content_links = await self.extract_cancer_content_links(cancer_info)

            if not content_links:
                logger.warning(f"{cancer_info['name']}: 추출된 링크 없음")
                continue

            # 2. 각 콘텐츠 페이지 스크래핑
            for link_info in content_links:
                # filename 생성: 암종명_제목
                safe_cancer = cancer_info['name'].replace('·', '_')
                safe_title = re.sub(r'[^\w\s-]', '', link_info['title']).strip().replace(' ', '_')
                filename = f"{safe_cancer}_{safe_title}"

                page_info = {
                    "url": link_info["url"],
                    "category": f"암의 종류 > {cancer_info['name']}",
                    "title": link_info["title"],
                    "filename": filename
                }

                result = await self.scrape_page(page_info)
                if result:
                    all_results.append(result)

                # 요청 간격 대기
                await asyncio.sleep(SCRAPING_CONFIG["delay_between_requests"])

            logger.info(f"[{cancer_info['name']}] 완료\n")

        # 최종 요약
        logger.info("=" * 100)
        logger.info("Phase 2 완료")
        logger.info(f"성공: {self.scraped_count}개 / 실패: {self.failed_count}개")
        logger.info("=" * 100)

        return all_results


async def main():
    """메인 실행 함수"""
    import sys

    # 인자로 phase 선택 (기본값: phase2)
    phase = sys.argv[1] if len(sys.argv) > 1 else "phase2"

    async with NCCScraper() as scraper:
        if phase == "phase1":
            results = await scraper.run_phase1()
            summary_file = Path(OUTPUT_DIRS["parsed"]) / "phase1_summary.json"
            total_pages = len(CHEMOTHERAPY_PAGES)

        elif phase == "phase2":
            # 테스트: 1개 암종만
            results = await scraper.run_phase2(max_cancers=1)
            summary_file = Path(OUTPUT_DIRS["parsed"]) / "phase2_summary.json"
            total_pages = "1개 암종"

        elif phase == "phase2_all":
            # 전체 암종
            results = await scraper.run_phase2(max_cancers=None)
            summary_file = Path(OUTPUT_DIRS["parsed"]) / "phase2_summary.json"
            total_pages = f"{len(CANCER_TYPES)}개 암종"
        else:
            print(f"알 수 없는 phase: {phase}")
            print("사용법: python ncc/scraper.py [phase1|phase2|phase2_all]")
            return

        # 결과 요약 저장
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "phase": phase,
                "total_pages": total_pages,
                "scraped_count": scraper.scraped_count,
                "failed_count": scraper.failed_count,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        print(f"\n최종 결과:")
        print(f"  - Phase: {phase}")
        print(f"  - 성공: {scraper.scraped_count}개")
        print(f"  - 실패: {scraper.failed_count}개")
        print(f"  - 저장 위치: {OUTPUT_DIRS['parsed']}/")


if __name__ == "__main__":
    asyncio.run(main())
