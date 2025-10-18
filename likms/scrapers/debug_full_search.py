"""
현행법률 탭에서 법령 검색 테스트
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

BASE_URL = 'https://likms.assembly.go.kr/law'

logger = setup_logger("likms_full_search", project="likms")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()

    # 메인 페이지 접속
    logger.info("메인 페이지 접속")
    page.goto(BASE_URL, wait_until="networkidle")
    time.sleep(2)

    # 현행법률 탭 클릭
    logger.info("\n'현행법률' 탭 클릭 시도...")

    # 여러 방법으로 현행법률 탭 찾기
    try:
        law_tab = page.locator("a:has-text('현행법률')").first
        if law_tab.count() > 0:
            logger.info("  '현행법률' 링크 발견")
            law_tab.click()
            time.sleep(3)
        else:
            logger.warning("  '현행법률' 링크를 찾을 수 없음")
    except Exception as e:
        logger.error(f"  오류: {e}")

    # 검색
    logger.info("\n의료급여법 검색")
    search_input = page.locator("input[type='text']").first
    search_input.fill("의료급여법")

    search_button = page.locator("button:has-text('검색')").first
    search_button.click()
    time.sleep(3)

    # 검색 결과 확인
    logger.info("\n검색 결과 확인...")

    tables = page.locator("table").all()
    logger.info(f"테이블 개수: {len(tables)}")

    for table_idx, table in enumerate(tables):
        rows = table.locator("tr").all()
        logger.info(f"\n테이블 {table_idx + 1}: {len(rows)}개 행")

        for row_idx, row in enumerate(rows[:5]):
            links = row.locator("a").all()
            if links:
                link_text = links[0].inner_text().strip()
                if "의료급여" in link_text:
                    logger.info(f"  ★ 발견! 행 {row_idx + 1}: {link_text}")
                else:
                    logger.info(f"  행 {row_idx + 1}: {link_text[:50]}")

    # 스크린샷 저장
    output_dir = Path("data/likms/exploration")
    output_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output_dir / "full_search.png"), full_page=True)
    logger.info(f"\n스크린샷 저장: full_search.png")

    # 15초 대기
    logger.info("\n브라우저를 15초간 유지합니다...")
    time.sleep(15)

    browser.close()

logger.info("\n분석 완료!")
