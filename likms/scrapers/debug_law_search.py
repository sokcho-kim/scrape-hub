"""
법령 드롭다운을 선택해서 검색 테스트
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

BASE_URL = 'https://likms.assembly.go.kr/law'

logger = setup_logger("likms_law_search", project="likms")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()

    # 메인 페이지 접속
    logger.info("메인 페이지 접속")
    page.goto(BASE_URL, wait_until="networkidle")
    time.sleep(2)

    # 현행법률 탭 클릭
    logger.info("\n'현행법률' 탭 클릭")
    law_tab = page.locator("a:has-text('현행법률')").first
    law_tab.click()
    time.sleep(2)

    # 검색 드롭다운 확인
    logger.info("\n검색 드롭다운 분석...")
    dropdowns = page.locator("select").all()
    logger.info(f"드롭다운 개수: {len(dropdowns)}")

    for idx, dropdown in enumerate(dropdowns):
        try:
            options = dropdown.locator("option").all()
            logger.info(f"\n드롭다운 {idx + 1}: {len(options)}개 옵션")
            for opt in options[:5]:
                logger.info(f"  - {opt.inner_text()}")
        except:
            pass

    # 드롭다운에서 "법령" 선택
    logger.info("\n드롭다운에서 '법령' 선택 시도...")
    try:
        # select 태그 찾기
        search_type_select = page.locator("select").first
        search_type_select.select_option(label="법령")
        logger.info("  '법령' 옵션 선택 완료")
        time.sleep(1)
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

    found_medical_aid = False
    for table_idx, table in enumerate(tables):
        rows = table.locator("tr").all()
        logger.info(f"\n테이블 {table_idx + 1}: {len(rows)}개 행")

        for row_idx, row in enumerate(rows[:15]):
            links = row.locator("a").all()
            if links:
                link_text = links[0].inner_text().strip()
                if "의료급여" in link_text:
                    logger.info(f"  ★★★ 발견! 행 {row_idx + 1}: {link_text}")
                    found_medical_aid = True
                else:
                    logger.info(f"  행 {row_idx + 1}: {link_text[:60]}")

    if found_medical_aid:
        logger.info("\n✅ 의료급여법 검색 성공!")
    else:
        logger.warning("\n❌ 의료급여법을 찾지 못했습니다")

    # 스크린샷 저장
    output_dir = Path("data/likms/exploration")
    output_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output_dir / "law_search.png"), full_page=True)
    logger.info(f"\n스크린샷 저장: law_search.png")

    # 15초 대기
    logger.info("\n브라우저를 15초간 유지합니다...")
    time.sleep(15)

    browser.close()

logger.info("\n분석 완료!")
