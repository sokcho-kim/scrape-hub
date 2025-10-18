"""
검색 결과 구조 디버깅 스크립트

검색 결과 테이블의 상세한 구조를 파악합니다.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

BASE_URL = 'https://likms.assembly.go.kr/law'

logger = setup_logger("likms_debug", project="likms")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()

    # 메인 페이지 접속
    logger.info("메인 페이지 접속")
    page.goto(BASE_URL, wait_until="networkidle")
    time.sleep(2)

    # 검색
    logger.info("의료급여법 검색")
    search_input = page.locator("input[type='text']").first
    search_input.fill("의료급여법")

    search_button = page.locator("button:has-text('검색')").first
    search_button.click()
    time.sleep(3)

    # 검색 결과 분석
    logger.info("\n" + "=" * 60)
    logger.info("검색 결과 상세 분석")
    logger.info("=" * 60)

    # 테이블 확인
    tables = page.locator("table").all()
    logger.info(f"\n테이블 개수: {len(tables)}")

    for table_idx, table in enumerate(tables):
        logger.info(f"\n--- 테이블 {table_idx + 1} ---")

        rows = table.locator("tr").all()
        logger.info(f"행 개수: {len(rows)}")

        # 처음 5개 행만 상세 분석
        for row_idx, row in enumerate(rows[:10]):
            logger.info(f"\n  행 {row_idx + 1}:")

            # 행 전체 텍스트
            row_text = row.inner_text()
            logger.info(f"    전체 텍스트: {row_text[:100]}")

            # td 개수
            tds = row.locator("td").all()
            logger.info(f"    td 개수: {len(tds)}")

            # 각 td의 내용
            for td_idx, td in enumerate(tds):
                td_text = td.inner_text().strip()
                if td_text:
                    logger.info(f"      td[{td_idx}]: {td_text[:50]}")

            # 링크 확인
            links = row.locator("a").all()
            logger.info(f"    링크 개수: {len(links)}")

            for link_idx, link in enumerate(links):
                link_text = link.inner_text().strip()
                logger.info(f"      link[{link_idx}]: {link_text}")

    # 10초간 대기
    logger.info("\n브라우저를 15초간 유지합니다...")
    time.sleep(15)

    browser.close()

logger.info("\n분석 완료!")
