"""
HIRA 암질환 사용약제 및 요법 스크래퍼

수집 대상:
1. 공고
2. 공고예고
3. 항암화학요법
4. FAQ

수집 항목:
- 게시글 번호, 공고번호, 제목, 제·개정일, 작성일
- 게시글 상세 내용
- 첨부파일 (파일명, 확장자, 다운로드)
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


class HIRACancerScraper:
    """HIRA 암질환 게시판 스크래퍼"""

    BASE_URL = "https://www.hira.or.kr"

    # 게시판 정보
    BOARDS = {
        'announcement': {
            'name': '공고',
            'url': '/bbsDummy.do?pgmid=HIRAA030023010000',
            'list_selector': 'tbody tr',
            'title_cell_index': 2,  # 제목이 3번째 셀 (0-based: 2)
            'cells_count': 6
        },
        'pre_announcement': {
            'name': '공고예고',
            'url': '/rc/drug/anticancer/antiCncrAnnceList.do?pgmid=HIRAA030023020000',
            'list_selector': 'tbody tr',
            'title_cell_index': 1,  # 제목이 2번째 셀 (0-based: 1)
            'cells_count': 7
        },
        'chemotherapy': {
            'name': '항암화학요법',
            'url': '/bbsDummy.do?pgmid=HIRAA030023030000',
            'list_selector': 'tbody tr',
            'title_cell_index': 1,  # 파일명이 2번째 셀
            'cells_count': 3,
            'is_download_list': True  # 게시판이 아니라 다운로드 목록
        },
        'faq': {
            'name': 'FAQ',
            'url': '/bbsDummy.do?pgmid=HIRAA030023080000',
            'list_selector': 'tbody tr',
            'title_cell_index': 2,  # 제목이 3번째 셀
            'cells_count': 7
        }
    }

    def __init__(self, output_dir: Path, download_attachments: bool = True):
        """
        Args:
            output_dir: 출력 디렉토리
            download_attachments: 첨부파일 다운로드 여부
        """
        self.output_dir = output_dir
        self.download_attachments = download_attachments
        self.browser: Browser = None
        self.page: Page = None

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()

    async def get_total_pages(self, board_key: str) -> int:
        """
        게시판의 총 페이지 수 조회

        Args:
            board_key: 게시판 키

        Returns:
            총 페이지 수
        """
        board = self.BOARDS[board_key]
        url = self.BASE_URL + board['url']

        logger.info(f"[{board['name']}] 총 페이지 수 조회: {url}")
        await self.page.goto(url, wait_until='networkidle')

        # 페이징 정보 추출
        try:
            # .total-txt에서 "[1/22페이지]" 형태 추출
            total_text = await self.page.locator('.total-txt').text_content()
            # "[1/22페이지]" 또는 "[1/22 페이지]" 형태
            match = re.search(r'\[(\d+)/(\d+)\s*페이지\]', total_text)

            if match:
                current, total = match.groups()
                logger.info(f"[{board['name']}] 총 {total}페이지 발견 (전체 게시글: {total_text})")
                return int(total)
        except Exception as e:
            logger.warning(f"페이징 정보 추출 실패: {e}")

        # 페이징 번호로 추출
        try:
            page_links = await self.page.locator('.pagination a').all()
            page_numbers = []

            for link in page_links:
                text = await link.text_content()
                if text and text.strip().isdigit():
                    page_numbers.append(int(text.strip()))

            if page_numbers:
                return max(page_numbers)
        except Exception as e:
            logger.warning(f"페이징 링크 추출 실패: {e}")

        # 기본값
        return 1

    async def scrape_board_list(self, board_key: str, page_num: int = 1) -> List[Dict[str, Any]]:
        """
        게시판 목록 페이지 스크래핑

        Args:
            board_key: 게시판 키
            page_num: 페이지 번호

        Returns:
            게시글 목록
        """
        board = self.BOARDS[board_key]
        url = self.BASE_URL + board['url']

        if page_num > 1:
            # 페이지 파라미터 추가
            separator = '&' if '?' in url else '?'
            url += f"{separator}pageIndex={page_num}"

        logger.info(f"[{board['name']}] 페이지 {page_num} 스크래핑: {url}")
        await self.page.goto(url, wait_until='networkidle')

        posts = []
        rows = await self.page.locator(board['list_selector']).all()

        for row in rows:
            try:
                # 데이터 행인지 확인 (헤더나 빈 행 제외)
                cells = await row.locator('td').all()

                expected_cells = board.get('cells_count', 6)
                if len(cells) < 3:  # 최소 3개 컬럼 필요
                    continue

                # 번호
                num_text = await cells[0].text_content()
                if not num_text or not num_text.strip().isdigit():
                    continue  # 번호가 없으면 스킵

                # 제목 및 링크 추출
                if board.get('is_download_list'):
                    # 항암화학요법: 제목(컬럼1)과 링크(컬럼2)가 분리됨
                    title_cell_idx = board.get('title_cell_index', 1)
                    title = await cells[title_cell_idx].text_content() if len(cells) > title_cell_idx else ''

                    # 다운로드 링크는 마지막 컬럼(컬럼2)
                    link_cell_idx = len(cells) - 1
                    title_link = cells[link_cell_idx].locator('a').first if len(cells) > link_cell_idx else None
                else:
                    # 일반 게시판: 제목 컬럼에 링크가 있음
                    title_cell_idx = board.get('title_cell_index', 2)
                    title_link = cells[title_cell_idx].locator('a').first if len(cells) > title_cell_idx else None

                    if not title_link or await title_link.count() == 0:
                        continue

                    title = await title_link.text_content()

                if not title_link or await title_link.count() == 0:
                    continue

                detail_url = await title_link.get_attribute('href')
                onclick = await title_link.get_attribute('onclick')

                if not detail_url:
                    continue

                # href가 # 이면 click 필요 (공고예고)
                needs_click = (detail_url == '#' or detail_url == '#none')

                # 전체 URL 생성
                if needs_click:
                    # click 방식 (공고예고 등)
                    detail_url = url  # 현재 페이지에서 처리
                elif detail_url.startswith('http'):
                    # 이미 전체 URL
                    pass
                elif detail_url.startswith('/'):
                    # 절대 경로
                    detail_url = self.BASE_URL + detail_url
                elif detail_url.startswith('?'):
                    # 쿼리 스트링 - 현재 페이지의 경로 사용
                    current_path = board['url'].split('?')[0]
                    detail_url = self.BASE_URL + current_path + detail_url
                else:
                    # 상대 경로
                    detail_url = self.BASE_URL + '/' + detail_url

                # 공고번호 (있는 경우)
                announcement_no = await cells[1].text_content() if len(cells) > 1 else ''

                # 제·개정일
                revision_date = await cells[2].text_content() if len(cells) > 2 else ''

                # 작성일
                created_date = await cells[3].text_content() if len(cells) > 3 else ''

                # 첨부파일 여부
                has_attachment = len(await cells[4].locator('img').all()) > 0 if len(cells) > 4 else False

                post = {
                    'board': board_key,
                    'board_name': board['name'],
                    'number': num_text.strip(),
                    'announcement_no': announcement_no.strip(),
                    'title': title.strip(),
                    'revision_date': revision_date.strip(),
                    'created_date': created_date.strip(),
                    'has_attachment': has_attachment,
                    'detail_url': detail_url,
                    'page': page_num,
                    'needs_click': needs_click,
                    'onclick': onclick
                }

                # 공고예고나 항암화학요법(다운로드 전용)은 목록에서 즉시 처리
                if needs_click and board.get('is_download_list'):
                    # 항암화학요법: 다운로드 링크만 추출
                    if onclick and 'downLoad' in onclick:
                        match = re.search(r"downLoad[A-Za-z]*\(([^)]+)\)", onclick)
                        if match:
                            params_str = match.group(1)
                            params = [p.strip().strip("'\"") for p in params_str.split(',')]

                            if len(params) >= 4:
                                download_url = f"{self.BASE_URL}/bbsDownload.do?brdScnBltNo={params[0]}&brdBltNo={params[1]}&type={params[2]}&atchSeq={params[3]}"

                                post['content'] = ''
                                post['attachments'] = [{
                                    'filename': title.strip(),
                                    'extension': '',
                                    'download_url': download_url,
                                    'onclick_params': params,
                                    'downloaded': False,
                                    'local_path': None
                                }]
                                post['attachment_count'] = 1
                                post['detail_fetched'] = True  # 이미 처리됨

                elif needs_click:
                    # 공고예고: 클릭하여 상세 조회
                    try:
                        await title_link.click()
                        await self.page.wait_for_load_state('networkidle', timeout=10000)

                        # 상세 내용 추출 (HTML + 텍스트)
                        content_elem = self.page.locator('div.view, .view, .viewCont')
                        if await content_elem.count() > 0:
                            # HTML 저장
                            content_html = await content_elem.first.inner_html()
                            post['content_html'] = content_html.strip()
                            # 텍스트 저장 (검색용)
                            content_text = await content_elem.first.text_content()
                            post['content'] = content_text.strip()
                        else:
                            post['content_html'] = ''
                            post['content'] = ''

                        # 첨부파일 (두 가지 패턴 모두 검색 및 다운로드)
                        attachments = []

                        # 패턴 1: downLoad
                        file_links_1 = await self.page.locator('a[onclick*="downLoad"]').all()
                        for i, link in enumerate(file_links_1):
                            filename = await link.text_content()
                            onclick_attr = await link.get_attribute('onclick')

                            if onclick_attr:
                                match = re.search(r"downLoad[A-Za-z]*\(([^)]+)\)", onclick_attr)
                                if match:
                                    params_str = match.group(1)
                                    params = [p.strip().strip("'\"") for p in params_str.split(',')]

                                    if len(params) >= 4:
                                        download_url = f"{self.BASE_URL}/bbsDownload.do?brdScnBltNo={params[0]}&brdBltNo={params[1]}&type={params[2]}&atchSeq={params[3]}"
                                    else:
                                        download_url = None

                                    ext = ''
                                    filename_clean = filename.strip()
                                    if '.' in filename_clean:
                                        ext = '.' + filename_clean.split('.')[-1].lower()

                                    attachment = {
                                        'filename': filename_clean,
                                        'extension': ext,
                                        'download_url': download_url,
                                        'onclick_params': params,
                                        'downloaded': False,
                                        'local_path': None
                                    }

                                    # 첨부파일 다운로드
                                    if self.download_attachments:
                                        downloaded = await self.download_attachment_on_page(link, attachment, post, i)
                                        attachment['downloaded'] = downloaded

                                    attachments.append(attachment)

                        # 패턴 2: Header.goDown1 (공고예고 전용)
                        file_links_2 = await self.page.locator('a[onclick*="goDown1"]').all()
                        for i, link in enumerate(file_links_2):
                            onclick_attr = await link.get_attribute('onclick')

                            if onclick_attr:
                                # Header.goDown1('/share/attach/...', 'filename.hwpx')
                                match = re.search(r"goDown1\('([^']+)',\s*'([^']+)'\)", onclick_attr)
                                if match:
                                    file_path = match.group(1)
                                    filename = match.group(2)

                                    # 다운로드 URL 생성
                                    download_url = f"{self.BASE_URL}{file_path}"

                                    ext = ''
                                    if '.' in filename:
                                        ext = '.' + filename.split('.')[-1].lower()

                                    attachment = {
                                        'filename': filename,
                                        'extension': ext,
                                        'download_url': download_url,
                                        'onclick_params': [file_path, filename],
                                        'downloaded': False,
                                        'local_path': None
                                    }

                                    # 첨부파일 다운로드
                                    if self.download_attachments:
                                        downloaded = await self.download_attachment_on_page(link, attachment, post, i)
                                        attachment['downloaded'] = downloaded

                                    attachments.append(attachment)

                        post['attachments'] = attachments
                        post['attachment_count'] = len(attachments)
                        post['detail_fetched'] = True  # 이미 처리됨

                        logger.info(f"  [{post['number']}] {post['title']} - {len(post['content'])}자, {len(attachments)}개 첨부")

                        # 목록으로 돌아가기
                        await self.page.goto(url, wait_until='networkidle')
                        await asyncio.sleep(0.5)

                    except Exception as e:
                        logger.error(f"공고예고 상세 조회 실패 ({post['title']}): {e}")
                        post['detail_fetched'] = False

                posts.append(post)

                if not post.get('detail_fetched'):
                    logger.debug(f"  [{post['number']}] {post['title']}")

            except Exception as e:
                logger.error(f"게시글 파싱 오류: {e}")
                continue

        logger.info(f"[{board['name']}] 페이지 {page_num}: {len(posts)}개 게시글 추출")

        # URL 샘플 출력
        if posts:
            logger.debug(f"  샘플 URL: {posts[0]['detail_url']}")

        return posts

    async def scrape_post_detail(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        게시글 상세 내용 스크래핑

        Note: 공고예고와 항암화학요법은 scrape_board_list에서 이미 처리됨

        Args:
            post: 게시글 기본 정보

        Returns:
            상세 정보가 추가된 게시글
        """
        logger.info(f"[{post['board_name']}] 상세 조회: {post['title']}")

        await self.page.goto(post['detail_url'], wait_until='networkidle')

        # 상세 내용 추출 (HTML + 텍스트)
        try:
            # 본문 내용 (HIRA 구조: div.view가 본문)
            content_elem = self.page.locator('div.view, .view, .viewCont')

            if await content_elem.count() > 0:
                # HTML 저장
                content_html = await content_elem.first.inner_html()
                post['content_html'] = content_html.strip()
                # 텍스트 저장 (검색용)
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

        # 첨부파일 정보 추출 및 다운로드
        attachments = []

        try:
            # 첨부파일 목록 (HIRA 구조: a[onclick*="downLoad"])
            file_links = await self.page.locator('a[onclick*="downLoad"]').all()

            for i, link in enumerate(file_links):
                try:
                    filename = await link.text_content()
                    onclick = await link.get_attribute('onclick')

                    if not onclick:
                        continue

                    # onclick에서 파라미터 추출
                    # downLoadBbs('1','45648','6','49') 형태
                    match = re.search(r"downLoad[A-Za-z]*\(([^)]+)\)", onclick)
                    if match:
                        params_str = match.group(1)
                        # 작은따옴표 제거하고 파라미터 리스트로 변환
                        params = [p.strip().strip("'\"") for p in params_str.split(',')]

                        # HIRA 다운로드 URL 생성 (메타데이터용)
                        if len(params) >= 4:
                            download_url = f"{self.BASE_URL}/bbsDownload.do?brdScnBltNo={params[0]}&brdBltNo={params[1]}&type={params[2]}&atchSeq={params[3]}"
                        else:
                            download_url = None

                        # 파일명에서 확장자 추출
                        ext = ''
                        filename_clean = filename.strip()
                        if '.' in filename_clean:
                            ext = '.' + filename_clean.split('.')[-1].lower()

                        attachment = {
                            'filename': filename_clean,
                            'extension': ext,
                            'download_url': download_url,
                            'onclick_params': params,  # 디버깅용
                            'downloaded': False,
                            'local_path': None
                        }

                        # 첨부파일 다운로드 (상세 페이지에 있을 때)
                        if self.download_attachments:
                            downloaded = await self.download_attachment_on_page(link, attachment, post, i)
                            attachment['downloaded'] = downloaded

                        attachments.append(attachment)

                except Exception as e:
                    logger.warning(f"첨부파일 정보 추출 실패: {e}")
                    continue

        except Exception as e:
            logger.warning(f"첨부파일 목록 조회 실패: {e}")

        post['attachments'] = attachments
        post['attachment_count'] = len(attachments)

        logger.info(f"  내용: {len(post['content'])}자, 첨부: {len(attachments)}개")

        return post

    async def download_attachment_on_page(self, link_element, attachment: Dict[str, Any], post: Dict[str, Any], link_index: int) -> bool:
        """
        상세 페이지에서 첨부파일 링크 클릭하여 다운로드

        Args:
            link_element: 다운로드 링크 Playwright element
            attachment: 첨부파일 정보
            post: 게시글 정보
            link_index: 링크 인덱스 (재탐색용)

        Returns:
            다운로드 성공 여부
        """
        try:
            # 저장 경로 생성
            board_dir = self.output_dir / 'attachments' / post['board']
            board_dir.mkdir(parents=True, exist_ok=True)

            # 안전한 파일명 생성
            safe_filename = f"{post['number']}_{attachment['filename']}"
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', safe_filename)

            local_path = board_dir / safe_filename

            # 이미 다운로드된 경우 스킵
            if local_path.exists():
                logger.debug(f"    이미 존재: {safe_filename}")
                attachment['local_path'] = str(local_path)
                return True

            # 다운로드 (링크 클릭)
            logger.info(f"    다운로드: {attachment['filename']}")

            async with self.page.expect_download(timeout=30000) as download_info:
                await link_element.click()

            download = await download_info.value

            # 실제 파일명 가져오기
            actual_filename = download.suggested_filename
            if actual_filename and actual_filename != safe_filename:
                # 실제 파일명으로 업데이트
                safe_filename = f"{post['number']}_{actual_filename}"
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', safe_filename)
                local_path = board_dir / safe_filename

            await download.save_as(local_path)

            attachment['local_path'] = str(local_path)
            logger.info(f"    저장 완료: {local_path.name} ({local_path.stat().st_size / 1024:.1f} KB)")

            return True

        except Exception as e:
            logger.error(f"    첨부파일 다운로드 실패 ({attachment.get('filename', 'Unknown')}): {e}")
            return False

    async def scrape_board(self, board_key: str, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        게시판 전체 스크래핑

        Args:
            board_key: 게시판 키
            max_pages: 최대 페이지 수 (None이면 전체)

        Returns:
            모든 게시글 목록
        """
        board = self.BOARDS[board_key]
        logger.info(f"\n{'='*80}")
        logger.info(f"[{board['name']}] 스크래핑 시작")
        logger.info(f"{'='*80}")

        # 총 페이지 수 조회
        total_pages = await self.get_total_pages(board_key)

        if max_pages:
            total_pages = min(total_pages, max_pages)

        logger.info(f"[{board['name']}] 총 {total_pages}페이지 스크래핑 예정")

        all_posts = []

        # 각 페이지 스크래핑
        for page_num in range(1, total_pages + 1):
            try:
                # 목록 조회
                posts = await self.scrape_board_list(board_key, page_num)

                # 상세 조회
                for post in posts:
                    try:
                        # 이미 처리된 경우 (공고예고, 항암화학요법) 스킵
                        if not post.get('detail_fetched', False):
                            # 상세 내용 (첨부파일 다운로드 포함)
                            post = await self.scrape_post_detail(post)

                        all_posts.append(post)

                        # Rate limiting
                        if not post.get('detail_fetched', False):
                            await asyncio.sleep(0.5)

                    except Exception as e:
                        logger.error(f"게시글 처리 오류 ({post.get('title', 'Unknown')}): {e}")
                        continue

                # 페이지 간 대기
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"페이지 {page_num} 스크래핑 오류: {e}")
                continue

        logger.info(f"[{board['name']}] 완료: {len(all_posts)}개 게시글 수집")
        return all_posts

    async def scrape_all(self, max_pages_per_board: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        모든 게시판 스크래핑

        Args:
            max_pages_per_board: 게시판당 최대 페이지 수

        Returns:
            게시판별 게시글 딕셔너리
        """
        results = {}

        for board_key in self.BOARDS.keys():
            try:
                posts = await self.scrape_board(board_key, max_pages=max_pages_per_board)
                results[board_key] = posts

            except Exception as e:
                logger.error(f"게시판 '{board_key}' 스크래핑 실패: {e}")
                results[board_key] = []

        return results

    def save_results(self, results: Dict[str, List[Dict[str, Any]]]) -> Path:
        """
        결과 저장

        Args:
            results: 스크래핑 결과

        Returns:
            저장된 파일 경로
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f'hira_cancer_{timestamp}.json'

        # 통계
        stats = {
            'timestamp': timestamp,
            'boards': {}
        }

        for board_key, posts in results.items():
            board_name = self.BOARDS[board_key]['name']
            total_attachments = sum(len(p.get('attachments', [])) for p in posts)
            downloaded_attachments = sum(
                sum(1 for a in p.get('attachments', []) if a.get('downloaded', False))
                for p in posts
            )

            stats['boards'][board_key] = {
                'name': board_name,
                'posts': len(posts),
                'attachments': total_attachments,
                'downloaded': downloaded_attachments
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
    """메인 실행"""
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / 'data' / 'hira_cancer' / 'raw'
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("="*80)
    logger.info("HIRA 암질환 사용약제 및 요법 스크래퍼")
    logger.info("="*80)

    async with HIRACancerScraper(output_dir, download_attachments=True) as scraper:
        # 전체 스크래핑 (모든 페이지)
        results = await scraper.scrape_all(max_pages_per_board=None)

        # 결과 저장
        output_file = scraper.save_results(results)

    logger.info(f"\n완료! 결과: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
