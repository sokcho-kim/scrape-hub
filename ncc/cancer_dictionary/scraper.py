"""
NCC 암정보 사전 스크래퍼

총 3,543건의 암 정보 사전 데이터 수집
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

sys.path.append(str(Path(__file__).parent.parent.parent))

from ncc.cancer_dictionary.config import (
    BASE_URL,
    DICTIONARY_LIST_URL,
    DICTIONARY_DETAIL_URL,
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


class CancerDictionaryScraper:
    """암정보 사전 스크래퍼"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.scraped_count = 0
        self.failed_count = 0
        self.total_items = 0

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

    async def get_total_pages(self) -> int:
        """전체 페이지 수 가져오기"""
        try:
            # 첫 페이지 로드
            url = f"{DICTIONARY_LIST_URL}?rows={SCRAPING_CONFIG['rows_per_page']}&cpage=1"
            await self.page.goto(url, timeout=SCRAPING_CONFIG["timeout"])
            await self.page.wait_for_load_state("networkidle")

            # 전체 항목 수 추출 (예: "총 3,543건")
            total_text = await self.page.locator('.total_num, .result_count, strong').first.inner_text()
            match = re.search(r'(\d{1,3}(?:,\d{3})*)', total_text)

            if match:
                self.total_items = int(match.group(1).replace(',', ''))
                rows_per_page = SCRAPING_CONFIG['rows_per_page']
                total_pages = (self.total_items + rows_per_page - 1) // rows_per_page
                logger.info(f"총 항목 수: {self.total_items}개, 페이지 수: {total_pages}개")
                return total_pages
            else:
                logger.warning("전체 항목 수를 찾을 수 없음. 기본값 사용")
                return 119  # 기본값

        except Exception as e:
            logger.error(f"페이지 수 확인 중 오류: {str(e)}")
            return 119  # 기본값

    async def scrape_page(self, page_num: int) -> List[Dict[str, Any]]:
        """단일 페이지 스크래핑"""
        items = []

        try:
            url = f"{DICTIONARY_LIST_URL}?rows={SCRAPING_CONFIG['rows_per_page']}&cpage={page_num}"
            logger.info(f"페이지 {page_num} 스크래핑 시작: {url}")

            await self.page.goto(url, timeout=SCRAPING_CONFIG["timeout"])
            await self.page.wait_for_load_state("networkidle")

            # 목록 항목 추출 (.word-box 내 button.word)
            list_items = await self.page.query_selector_all('.word-box button.word')

            if not list_items:
                logger.warning(f"페이지 {page_num}에서 항목을 찾을 수 없음")
                return items

            logger.info(f"페이지 {page_num}에서 {len(list_items)}개 항목 발견")

            for item in list_items:
                try:
                    # 제목 추출
                    title = await item.inner_text()
                    title = title.strip()

                    if not title:
                        continue

                    # onclick 속성에서 키워드 추출 (wordClick 함수)
                    onclick = await item.get_attribute('onclick')
                    keyword = None

                    if onclick:
                        # wordClick('1-메틸-디-트립토판', this) 형식
                        match = re.search(r'wordClick\([\'"](.+?)[\'"]', onclick)
                        if match:
                            keyword = match.group(1)

                    # 상세 내용 가져오기 (Ajax 요청)
                    content = ""
                    if keyword:
                        content = await self.fetch_detail_content(keyword)

                    item_data = {
                        "title": title,
                        "keyword": keyword,
                        "content": content,
                        "page_num": page_num,
                        "scraped_at": datetime.now().isoformat()
                    }

                    items.append(item_data)
                    self.scraped_count += 1

                    if self.scraped_count % 50 == 0:
                        logger.info(f"진행 중: {self.scraped_count}개 수집 완료")

                except Exception as e:
                    logger.error(f"항목 추출 중 오류: {str(e)}")
                    self.failed_count += 1
                    continue

        except Exception as e:
            logger.error(f"페이지 {page_num} 스크래핑 실패: {str(e)}")

        return items

    async def fetch_detail_content(self, keyword: str) -> str:
        """Ajax로 상세 내용 가져오기"""
        try:
            # JavaScript를 사용하지 않고 직접 JSON 응답 받기
            # keyword를 URL 인코딩
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)

            result = await self.page.evaluate(f'''
                async () => {{
                    const response = await fetch('/inc/searchWorks/search.do', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }},
                        body: 'work={encoded_keyword}'
                    }});
                    const data = await response.json();
                    return data;
                }}
            ''')

            # JSON 응답에서 설명 추출
            if result and 'sense' in result:
                return result['sense'].strip()
            else:
                logger.warning(f"설명을 찾을 수 없음 (keyword: {keyword})")
                return ""

        except Exception as e:
            logger.error(f"상세 내용 가져오기 실패 (keyword: {keyword}): {str(e)}")
            return ""

    async def save_items(self, items: List[Dict[str, Any]], batch_num: int):
        """배치 단위로 저장"""
        try:
            filename = Path(OUTPUT_DIRS["parsed"]) / f"batch_{batch_num:04d}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)

            logger.info(f"배치 {batch_num} 저장 완료: {len(items)}개 항목 ({filename})")

        except Exception as e:
            logger.error(f"배치 {batch_num} 저장 실패: {str(e)}")

    async def scrape_all(self, start_page: int = 1, end_page: Optional[int] = None, batch_size: int = 10):
        """전체 사전 스크래핑"""
        logger.info("=" * 100)
        logger.info("암정보 사전 스크래핑 시작")
        logger.info("=" * 100)

        # 전체 페이지 수 확인
        total_pages = await self.get_total_pages()

        if end_page is None:
            end_page = total_pages
        else:
            end_page = min(end_page, total_pages)

        logger.info(f"수집 범위: 페이지 {start_page} ~ {end_page}")

        all_items = []
        batch_num = 1

        for page_num in range(start_page, end_page + 1):
            items = await self.scrape_page(page_num)
            all_items.extend(items)

            # 배치 단위로 저장
            if len(all_items) >= batch_size * SCRAPING_CONFIG['rows_per_page']:
                await self.save_items(all_items, batch_num)
                all_items = []
                batch_num += 1

            # 요청 간격 대기
            await asyncio.sleep(SCRAPING_CONFIG["delay_between_requests"])

            # 진행 상황 로그
            progress = (page_num - start_page + 1) / (end_page - start_page + 1) * 100
            logger.info(f"진행률: {progress:.1f}% ({page_num}/{end_page} 페이지)")

        # 남은 항목 저장
        if all_items:
            await self.save_items(all_items, batch_num)

        # 최종 요약
        logger.info("=" * 100)
        logger.info("암정보 사전 스크래핑 완료")
        logger.info(f"성공: {self.scraped_count}개 / 실패: {self.failed_count}개")
        if self.total_items > 0:
            logger.info(f"예상 총 항목: {self.total_items}개")
            logger.info(f"수집률: {self.scraped_count / self.total_items * 100:.1f}%")
        logger.info("=" * 100)

        # 요약 JSON 저장
        summary = {
            "total_expected": self.total_items,
            "scraped_count": self.scraped_count,
            "failed_count": self.failed_count,
            "success_rate": f"{self.scraped_count / self.total_items * 100:.1f}%" if self.total_items > 0 else "0.0%",
            "start_page": start_page,
            "end_page": end_page,
            "timestamp": datetime.now().isoformat()
        }

        summary_file = Path(OUTPUT_DIRS["parsed"]) / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)


async def main(start_page: int = 1, end_page: Optional[int] = None):
    """메인 실행 함수"""
    async with CancerDictionaryScraper() as scraper:
        await scraper.scrape_all(start_page=start_page, end_page=end_page)


if __name__ == "__main__":
    # 명령줄 인자: python scraper.py [시작페이지] [종료페이지]
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else None

    asyncio.run(main(start_page=start, end_page=end))
