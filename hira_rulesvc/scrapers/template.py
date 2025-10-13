"""
HIRA 규칙 서비스 스크래퍼 템플릿

이 파일은 hira_rulesvc 프로젝트의 스크래퍼를 작성할 때 참고할 템플릿입니다.
"""
from playwright.sync_api import sync_playwright, Page
import time
from typing import List, Dict
from shared.utils.logger import setup_logger
from shared.utils.checkpoint import (
    load_checkpoint, save_checkpoint, is_processed,
    add_processed, update_last_page
)
from shared.utils.csv_handler import save_to_csv, remove_duplicates

# 프로젝트명으로 로거 설정
logger = setup_logger('hira_scraper', project='hira_rulesvc')

# 상수 정의
BASE_URL = 'https://example.com'
SAVE_INTERVAL = 10
PAGE_TIMEOUT = 30000

class HiraScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        # 프로젝트별 체크포인트 로드
        self.checkpoint = load_checkpoint(project='hira_rulesvc', cert_types=['scraper_type'])
        self.buffer = []
        self.context = None

    def run(self):
        """크롤러 실행"""
        logger.info("HIRA 스크래퍼 시작")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            self.context = browser.new_context()
            page = self.context.new_page()
            page.set_default_timeout(PAGE_TIMEOUT)

            try:
                # 크롤링 로직 구현
                logger.info("크롤링 완료")

            except Exception as e:
                logger.error(f"크롤러 실행 중 오류: {e}", exc_info=True)
                self._flush_buffer()
            finally:
                browser.close()

    def _flush_buffer(self):
        """버퍼의 데이터를 CSV에 저장"""
        if self.buffer:
            # 프로젝트별 데이터 저장
            save_to_csv(self.buffer, 'data.csv', project='hira_rulesvc')
            logger.info(f"{len(self.buffer)}개 데이터 저장")
            self.buffer = []


if __name__ == '__main__':
    scraper = HiraScraper(headless=True)
    scraper.run()
