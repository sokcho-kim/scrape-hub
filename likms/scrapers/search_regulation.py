"""
대법원 포털에서 의료급여법 시행규칙 검색

검색 결과에서 URL을 찾아냅니다.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import sys
import urllib.parse

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

BASE_URL = "https://portal.scourt.go.kr/pgp/main.on"

logger = setup_logger("search_regulation", project="likms")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()

    try:
        # 검색어
        search_keyword = "의료급여법 시행규칙"
        encoded_keyword = urllib.parse.quote(search_keyword)

        # 검색 URL
        search_url = f"{BASE_URL}?w2xPath=PGP1021M04&c=900&srchwd={encoded_keyword}"

        logger.info(f"검색어: {search_keyword}")
        logger.info(f"검색 URL: {search_url}")

        page.goto(search_url, wait_until="networkidle")
        time.sleep(5)

        # 페이지 제목 확인
        title = page.title()
        logger.info(f"\n페이지 제목: {title}")

        # 모든 링크 찾기
        links = page.locator("a").all()
        logger.info(f"\n전체 링크 개수: {len(links)}")

        # "시행규칙" 포함 링크 찾기
        logger.info("\n'시행규칙' 포함 링크:")
        found_links = []

        for idx, link in enumerate(links):
            try:
                href = link.get_attribute("href")
                text = link.inner_text().strip()

                if "시행규칙" in text or "의료급여법" in text:
                    logger.info(f"\n  링크 {len(found_links)+1}:")
                    logger.info(f"    텍스트: {text[:100]}")
                    logger.info(f"    href: {href}")

                    found_links.append({
                        "text": text,
                        "href": href
                    })
            except:
                continue

        # 첫 번째 시행규칙 링크 클릭 시도
        if found_links:
            logger.info(f"\n총 {len(found_links)}개 관련 링크 발견")

            # "의료급여법 시행규칙" 정확히 일치하는 링크 찾기
            for link_info in found_links:
                if "의료급여법 시행규칙" in link_info["text"]:
                    logger.info(f"\n★ 정확한 링크 발견: {link_info['text']}")

                    # 링크 클릭
                    matching_link = page.locator(f"a:has-text('{link_info['text'][:30]}')").first
                    if matching_link.count() > 0:
                        logger.info("링크 클릭 중...")
                        matching_link.click()
                        time.sleep(5)

                        # URL 확인
                        current_url = page.url()
                        logger.info(f"\n✅ 시행규칙 페이지 URL:")
                        logger.info(f"{current_url}")

                        # jisCntntsSrno 추출
                        if "jisCntntsSrno=" in current_url:
                            import re
                            match = re.search(r'jisCntntsSrno=(\d+)', current_url)
                            if match:
                                srno = match.group(1)
                                logger.info(f"\n✅ jisCntntsSrno: {srno}")
                                logger.info(f"\n이 값을 scourt_collect_all.py에 추가하세요!")

                        # 텍스트 확인
                        body_text = page.locator("body").inner_text()
                        logger.info(f"\n텍스트 길이: {len(body_text):,} 글자")

                        break
        else:
            logger.warning("\n시행규칙 링크를 찾을 수 없습니다")

        # 스크린샷 저장
        output_dir = Path("data/likms/exploration")
        output_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output_dir / "regulation_search.png"), full_page=True)
        logger.info(f"\n스크린샷 저장: regulation_search.png")

        # 15초 대기
        logger.info("\n브라우저를 15초간 유지합니다...")
        time.sleep(15)

    except Exception as e:
        logger.error(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

logger.info("\n검색 완료!")
