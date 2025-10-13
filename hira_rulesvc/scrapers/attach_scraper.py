"""
HIRA 서식 첨부파일 스크래퍼

서식 정보(attach) 목록에서 다운로드 버튼을 통해 첨부파일을 수집합니다.
"""
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
import time
import random
from typing import List, Dict
from pathlib import Path
import json
import re
import os

from shared.utils.logger import setup_logger
from shared.utils.csv_handler import save_to_csv
from hira_rulesvc.config import get_seq_by_name, get_seq_by_partial_match

logger = setup_logger('attach_scraper', project='hira_rulesvc')

# 설정
BASE_URL = 'http://rulesvc.hira.or.kr/lmxsrv/main/main.srv'
PAGE_TIMEOUT = 30000
DOWNLOAD_TIMEOUT = 60000

class AttachScraper:
    def __init__(self, target_seq: str = None, target_name: str = None, headless: bool = True):
        """
        Args:
            target_seq: SEQ 값 직접 지정 (예: "2")
            target_name: 고시명으로 지정 (예: "요양급여비용 청구방법(보건복지부 고시)")
            headless: 헤드리스 모드 여부
        """
        self.headless = headless
        self.meta_records = []

        # SEQ 결정
        if target_seq:
            self.target_seq = target_seq
            logger.info(f"SEQ 직접 지정: {target_seq}")
        elif target_name:
            try:
                self.target_seq = get_seq_by_name(target_name)
                logger.info(f"고시명 '{target_name}' → SEQ {self.target_seq}")
            except ValueError:
                # 정확 매칭 실패 시 부분 매칭 시도
                self.target_seq = get_seq_by_partial_match(target_name)
                logger.info(f"부분 매칭 '{target_name}' → SEQ {self.target_seq}")
        else:
            # 기본값: 요양급여비용 청구방법(보건복지부 고시)
            self.target_seq = "2"
            logger.info(f"기본 SEQ 사용: {self.target_seq}")

        # 출력 디렉토리
        self.out_dir = Path('data/hira_rulesvc') / f'seq_{self.target_seq}'
        self.files_dir = self.out_dir / 'files'
        self.files_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"출력 디렉토리: {self.out_dir}")

    def run(self):
        """크롤러 실행"""
        logger.info("=" * 60)
        logger.info("HIRA 서식 첨부파일 스크래퍼 시작")
        logger.info(f"대상 SEQ: {self.target_seq}")
        logger.info("=" * 60)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.set_default_timeout(PAGE_TIMEOUT)

            try:
                # 1. 메인 페이지 접속
                logger.info(f"메인 페이지 접속: {BASE_URL}")
                page.goto(BASE_URL)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                # 2. 서식정보 탭 클릭 (menu_go('2'))
                logger.info("서식정보 탭 클릭")
                page.evaluate("menu_go('2')")
                time.sleep(2)

                # 3. 폼 제출로 목록 페이지 진입
                content_frame = self.navigate_to_list(page)

                # 4. 목록 화면 검증
                self.verify_list_page(content_frame)

                # 5. 페이지네이션 처리
                self.handle_pagination(content_frame, page)

                # 6. 메타데이터 저장
                self.save_metadata()

                logger.info("=" * 60)
                logger.info(f"크롤링 완료! 총 {len(self.meta_records)}개 레코드 수집")
                logger.info(f"출력 위치: {self.out_dir}")
                logger.info("=" * 60)

            except Exception as e:
                logger.error(f"크롤러 실행 중 오류: {e}", exc_info=True)
                # 에러 발생 시에도 수집된 데이터 저장
                if self.meta_records:
                    self.save_metadata()
                raise
            finally:
                browser.close()

    def navigate_to_list(self, page: Page):
        """폼 제출로 목록 페이지 진입"""
        logger.info(f"SEQ={self.target_seq}로 목록 페이지 이동")

        # 폼 값 설정 및 제출
        page.evaluate(f"""() => {{
            document.getElementById('SEQ').value = '{self.target_seq}';
            document.getElementById('SEQ_ATTACH_TYPE').value = '0';  // 전체
            document.getElementById('SEARCH_TYPE').value = 'all';
            document.getElementById('seachForm').action = '/lmxsrv/attach/attachList.srv';
            document.getElementById('seachForm').submit();
        }}""")

        # contentbody iframe 로딩 대기
        logger.info("목록 페이지 로딩 대기...")
        page.wait_for_load_state("networkidle")
        time.sleep(random.uniform(1.0, 2.0))

        # contentbody iframe 참조
        content_frame = page.frame(name="contentbody")
        if not content_frame:
            raise Exception("contentbody iframe을 찾을 수 없습니다")

        logger.info("contentbody iframe 접근 성공")
        return content_frame

    def verify_list_page(self, frame):
        """목록 화면 검증 (상세 진입 방지 가드)"""
        logger.info("목록 화면 검증 중...")

        try:
            # 방법 1: body 텍스트 확인
            body_text = frame.inner_text('body')

            # 방법 2: 테이블 존재 확인
            tables = frame.query_selector_all('table')

            if len(tables) > 0:
                logger.info(f"✓ 목록 화면 확인 ({len(tables)}개 테이블 발견)")
                return True

            logger.warning("⚠ 목록 화면이 아닐 수 있습니다")
            logger.warning(f"페이지 내용 미리보기: {body_text[:200]}")

        except Exception as e:
            logger.error(f"목록 화면 검증 실패: {e}")
            raise

    def handle_pagination(self, frame, page: Page):
        """페이지네이션 처리"""
        page_no = 1

        while True:
            logger.info(f"[페이지 {page_no}] 처리 시작")

            # 현재 페이지 파싱
            self.parse_list_page(frame, page_no)

            # 다음 페이지 버튼 찾기
            next_btn = self.find_next_button(frame)

            if not next_btn:
                logger.info("마지막 페이지 도달")
                break

            # 다음 페이지 클릭
            logger.info(f"다음 페이지로 이동...")
            next_btn.click()
            frame.wait_for_load_state("networkidle")
            time.sleep(random.uniform(0.5, 1.0))

            page_no += 1

    def find_next_button(self, frame):
        """다음 페이지 버튼 찾기"""
        try:
            # 1순위: "다음" 텍스트
            next_links = frame.query_selector_all('a')
            for link in next_links:
                text = link.inner_text().strip()
                if "다음" in text or "▶" in text or ">" in text:
                    # disabled 체크
                    disabled = link.get_attribute('disabled')
                    class_name = link.get_attribute('class')
                    if not disabled and 'disabled' not in (class_name or ''):
                        logger.info(f"다음 버튼 찾음: '{text}'")
                        return link

            logger.info("다음 버튼 없음 (마지막 페이지)")
            return None

        except Exception as e:
            logger.error(f"다음 버튼 탐색 실패: {e}")
            return None

    def parse_list_page(self, frame, page_no: int):
        """목록 페이지 파싱"""
        try:
            # 디버깅: HTML 전체 구조 덤프
            html_content = frame.content()
            debug_file = self.out_dir / f'debug_page{page_no}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"디버그 HTML 저장: {debug_file}")

            # 테이블에서 tbody tr 찾기
            rows = frame.query_selector_all('table tbody tr')
            logger.info(f"[페이지 {page_no}] {len(rows)}개 행 발견")

            if len(rows) == 0:
                logger.warning(f"[페이지 {page_no}] 행이 없습니다. HTML 구조 확인 필요")
                # 테이블 없이 tr만 찾아보기
                rows = frame.query_selector_all('tr')
                logger.info(f"[페이지 {page_no}] 전체 tr: {len(rows)}개")
                return

            for idx, row in enumerate(rows):
                try:
                    self.parse_row(row, page_no, idx, frame)
                except Exception as e:
                    logger.error(f"[{page_no}-{idx}] 행 파싱 실패: {e}")

        except Exception as e:
            logger.error(f"[페이지 {page_no}] 목록 파싱 실패: {e}", exc_info=True)

    def parse_row(self, row, page_no: int, row_idx: int, frame):
        """개별 행 파싱"""
        cells = row.query_selector_all('td')

        if len(cells) == 0:
            logger.warning(f"[{page_no}-{row_idx}] td가 없음 (헤더 행일 수 있음)")
            return

        # 기본 데이터 추출 (셀 개수에 따라 유연하게 처리)
        record = {
            'page_no': page_no,
            'row_index': row_idx,
            'no': cells[0].inner_text().strip() if len(cells) > 0 else "",
            'title': cells[1].inner_text().strip() if len(cells) > 1 else "",
            'attach_type': cells[2].inner_text().strip() if len(cells) > 2 else "",
            'filename': cells[3].inner_text().strip() if len(cells) > 3 else "",
            'downloaded_files': [],
            'errors': []
        }

        logger.info(f"[{page_no}-{row_idx}] {record['title'][:30]}...")

        # 다운로드 버튼 찾기 (보통 마지막 셀)
        download_cell = cells[-1] if len(cells) > 0 else None
        if download_cell:
            self.download_file(download_cell, record, page_no, row_idx, frame)
        else:
            record['errors'].append("다운로드 셀 없음")

        self.meta_records.append(record)

    def download_file(self, cell, record: dict, page_no: int, row_idx: int, frame):
        """파일 다운로드"""
        try:
            # 다운로드 버튼 찾기
            download_btn = self.find_download_button(cell)

            if not download_btn:
                record['errors'].append("다운로드 버튼 없음")
                logger.warning(f"[{page_no}-{row_idx}] 다운로드 버튼을 찾을 수 없음")
                return

            # 다운로드 실행
            logger.info(f"[{page_no}-{row_idx}] 다운로드 시작...")

            page = frame.page
            with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
                download_btn.click()

            download = download_info.value
            filename = download.suggested_filename

            # 파일명 sanitize 및 저장
            safe_filename = self.sanitize_filename(filename)
            unique_filename = self.generate_unique_filename(f"{page_no}_{row_idx}_{safe_filename}")

            file_path = self.files_dir / unique_filename
            download.save_as(str(file_path))

            record['downloaded_files'].append(str(file_path))
            logger.info(f"[{page_no}-{row_idx}] ✓ 다운로드 완료: {unique_filename}")

        except Exception as e:
            error_msg = f"다운로드 실패: {str(e)}"
            record['errors'].append(error_msg)
            logger.error(f"[{page_no}-{row_idx}] {error_msg}")

    def find_download_button(self, cell):
        """다운로드 버튼 탐지 (다층 폴백)"""
        # 1순위: 텍스트 "다운로드"
        btn = cell.query_selector('text="다운로드"')
        if btn:
            return btn

        # 2순위: title/alt 속성
        btn = cell.query_selector('[title*="다운로드"], [alt*="다운로드"]')
        if btn:
            return btn

        # 3순위: 이미지 src에 "download"
        btn = cell.query_selector('img[src*="download"]')
        if btn:
            return btn

        # 4순위: a 태그 (첫 번째)
        btn = cell.query_selector('a')
        if btn:
            return btn

        return None

    def sanitize_filename(self, filename: str) -> str:
        """OS 금지 문자 제거"""
        return re.sub(r'[\\/:*?"<>|]', '_', filename)

    def generate_unique_filename(self, filename: str) -> str:
        """중복 파일명 처리"""
        path = self.files_dir / filename
        if not path.exists():
            return filename

        # 확장자 분리
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
        else:
            name, ext = filename, ''

        dup_count = 1
        while True:
            new_name = f"{name}_dup{dup_count}.{ext}" if ext else f"{name}_dup{dup_count}"
            if not (self.files_dir / new_name).exists():
                return new_name
            dup_count += 1

    def save_metadata(self):
        """메타데이터 저장"""
        if not self.meta_records:
            logger.warning("저장할 메타데이터가 없습니다")
            return

        # JSON Lines
        jsonl_path = self.out_dir / 'meta.jsonl'
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for record in self.meta_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        logger.info(f"메타데이터 저장: {jsonl_path}")

        # CSV
        csv_path = self.out_dir / 'meta.csv'
        # downloaded_files와 errors 리스트를 문자열로 변환
        csv_records = []
        for record in self.meta_records:
            csv_record = record.copy()
            csv_record['downloaded_files'] = '; '.join(record['downloaded_files'])
            csv_record['errors'] = '; '.join(record['errors'])
            csv_records.append(csv_record)

        save_to_csv(csv_records, 'meta.csv', project='hira_rulesvc')
        logger.info(f"메타데이터 저장: {csv_path}")

        logger.info(f"총 {len(self.meta_records)}개 레코드 저장 완료")


if __name__ == '__main__':
    # 테스트: 요양급여비용 청구방법(보건복지부 고시)
    scraper = AttachScraper(
        target_name="요양급여비용 청구방법(보건복지부 고시)",
        headless=False  # 브라우저 보면서 테스트
    )
    scraper.run()
