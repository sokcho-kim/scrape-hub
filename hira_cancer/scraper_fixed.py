"""
HIRA 암질환 사용약제 및 요법 스크래퍼 (수정 버전)

수정 사항:
1. 공고예고 첨부파일 제대로 파싱
2. 본문을 HTML로 저장 (innerHTML)
"""
import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HIRACancerScraperFixed:
    """HIRA 암질환 게시판 스크래퍼 (수정 버전)"""

    BASE_URL = "https://www.hira.or.kr"

    # 게시판 정보
    BOARDS = {
        'announcement': {
            'name': '공고',
            'url': '/bbsDummy.do?pgmid=HIRAA030023010000',
            'list_selector': 'tbody tr',
            'title_cell_index': 2,
            'cells_count': 6
        },
        'pre_announcement': {
            'name': '공고예고',
            'url': '/rc/drug/anticancer/antiCncrAnnceList.do?pgmid=HIRAA030023020000',
            'list_selector': 'tbody tr',
            'title_cell_index': 1,
            'cells_count': 7
        },
        'chemotherapy': {
            'name': '항암화학요법',
            'url': '/bbsDummy.do?pgmid=HIRAA030023030000',
            'list_selector': 'tbody tr',
            'title_cell_index': 1,
            'cells_count': 3,
            'is_download_list': True
        },
        'faq': {
            'name': 'FAQ',
            'url': '/bbsDummy.do?pgmid=HIRAA030023080000',
            'list_selector': 'tbody tr',
            'title_cell_index': 2,
            'cells_count': 7
        }
    }

    def __init__(self, output_dir: Path, download_attachments: bool = True):
        self.output_dir = output_dir
        self.download_attachments = download_attachments
        self.browser: Browser = None
        self.page: Page = None

    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()

    async def extract_attachments_from_page(self) -> List[Dict[str, Any]]:
        """현재 페이지에서 첨부파일 정보 추출 (개선 버전)"""
        attachments = []

        try:
            # 방법 1: onclick*="downLoad" 링크
            file_links = await self.page.locator('a[onclick*="downLoad"]').all()

            for link in file_links:
                try:
                    # 실제 파일명 추출 시도 (링크 근처 텍스트)
                    filename_elem = link.locator('xpath=preceding-sibling::text()[1] | preceding-sibling::*[1]')
                    if await filename_elem.count() > 0:
                        filename = await filename_elem.first.text_content()
                        filename = filename.strip()
                    else:
                        filename = await link.text_content()
                        filename = filename.strip()

                    onclick = await link.get_attribute('onclick')

                    if not onclick:
                        continue

                    # onclick에서 파라미터 추출
                    match = re.search(r"downLoad[A-Za-z]*\(([^)]+)\)", onclick)
                    if match:
                        params_str = match.group(1)
                        params = [p.strip().strip("'\"") for p in params_str.split(',')]

                        if len(params) >= 4:
                            download_url = f"{self.BASE_URL}/bbsDownload.do?brdScnBltNo={params[0]}&brdBltNo={params[1]}&type={params[2]}&atchSeq={params[3]}"
                        else:
                            download_url = None

                        ext = ''
                        if '.' in filename:
                            ext = '.' + filename.split('.')[-1].lower()

                        attachments.append({
                            'filename': filename,
                            'extension': ext,
                            'download_url': download_url,
                            'onclick_params': params,
                            'downloaded': False,
                            'local_path': None
                        })

                except Exception as e:
                    logger.warning(f"첨부파일 정보 추출 실패: {e}")
                    continue

            # 방법 2: 파일 아이콘 또는 특정 클래스로 추가 검색
            # (공고예고 전용)
            if len(attachments) == 0:
                # .file 클래스나 특정 패턴으로 추가 탐색
                file_items = await self.page.locator('.file, .attach, [class*="attach"], [class*="file"]').all()
                for item in file_items:
                    text = await item.text_content()
                    if '.hwp' in text.lower() or '.pdf' in text.lower() or '.xlsx' in text.lower():
                        # 파일명 추출 및 다운로드 링크 찾기
                        logger.debug(f"추가 파일 발견: {text.strip()}")

        except Exception as e:
            logger.warning(f"첨부파일 목록 조회 실패: {e}")

        return attachments

    async def scrape_post_detail_fixed(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """게시글 상세 내용 스크래핑 (HTML 저장 버전)"""
        logger.info(f"[{post['board_name']}] 상세 조회: {post['title']}")

        await self.page.goto(post['detail_url'], wait_until='networkidle')

        # 상세 내용 추출 (HTML로 저장)
        try:
            content_elem = self.page.locator('div.view, .view, .viewCont')

            if await content_elem.count() > 0:
                # HTML 저장
                content_html = await content_elem.first.inner_html()
                post['content_html'] = content_html.strip()

                # 텍스트도 함께 저장 (검색용)
                content_text = await content_elem.first.text_content()
                post['content'] = content_text.strip()
            else:
                post['content_html'] = ''
                post['content'] = ''

            logger.debug(f"  본문 길이: HTML {len(post.get('content_html', ''))}자, Text {len(post.get('content', ''))}자")

        except Exception as e:
            logger.warning(f"본문 추출 실패: {e}")
            post['content_html'] = ''
            post['content'] = ''

        # 첨부파일 정보 추출 (개선된 함수 사용)
        attachments = await self.extract_attachments_from_page()
        post['attachments'] = attachments
        post['attachment_count'] = len(attachments)

        logger.info(f"  내용: {len(post['content'])}자, 첨부: {len(attachments)}개")

        return post

    def save_results(self, results: Dict[str, List[Dict[str, Any]]]) -> Path:
        """결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f'hira_cancer_fixed_{timestamp}.json'

        # 통계
        stats = {
            'timestamp': timestamp,
            'boards': {}
        }

        for board_key, posts in results.items():
            board_name = self.BOARDS[board_key]['name']
            total_attachments = sum(len(p.get('attachments', [])) for p in posts)

            stats['boards'][board_key] = {
                'name': board_name,
                'posts': len(posts),
                'attachments': total_attachments,
                'downloaded': 0
            }

        # 전체 데이터 저장
        output_data = {
            'metadata': stats,
            'data': results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n결과 저장: {output_file}")
        logger.info(f"총 {sum(s['posts'] for s in stats['boards'].values())}개 게시글")
        logger.info(f"총 {sum(s['attachments'] for s in stats['boards'].values())}개 첨부파일")

        return output_file


async def main():
    """공고예고만 다시 수집"""
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / 'data' / 'hira_cancer' / 'raw'
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("="*80)
    logger.info("HIRA 암질환 - 공고예고 재수집 (첨부파일 포함)")
    logger.info("="*80)

    async with HIRACancerScraperFixed(output_dir, download_attachments=False) as scraper:
        # 공고예고만 1페이지 테스트
        posts = await scraper.scrape_board('pre_announcement', max_pages=1)

        results = {'pre_announcement': posts}
        output_file = scraper.save_results(results)

    logger.info(f"\n완료! 결과: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
