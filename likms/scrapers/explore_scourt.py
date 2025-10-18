"""
대법원 판례정보 시스템 탐색

의료급여법 정보를 확인합니다.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

URL = "https://portal.scourt.go.kr/pgp/main.on?w2xPath=PGP1021M04&jisCntntsSrno=2025000009651&srchwd=%EC%9D%98%EB%A3%8C%EA%B8%89%EC%97%AC%EB%B2%95&c=900"
OUTPUT_DIR = Path("data/likms/exploration")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logger("scourt_explorer", project="likms")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()

    try:
        # 페이지 접속
        logger.info("대법원 포털 접속 중...")
        page.goto(URL, wait_until="networkidle")
        time.sleep(5)

        # 스크린샷 저장
        page.screenshot(path=str(OUTPUT_DIR / "scourt_page.png"), full_page=True)
        logger.info("스크린샷 저장: scourt_page.png")

        # 페이지 제목
        title = page.title()
        logger.info(f"\n페이지 제목: {title}")

        # 주요 텍스트 추출
        body_text = page.locator("body").inner_text()
        logger.info(f"\n페이지 텍스트 길이: {len(body_text)} 글자")

        # 의료급여법 관련 텍스트 확인
        if "의료급여법" in body_text:
            logger.info("✅ '의료급여법' 텍스트 발견!")

            # 미리보기
            idx = body_text.find("의료급여법")
            preview = body_text[max(0, idx-100):idx+500]
            logger.info(f"\n미리보기:\n{preview}")
        else:
            logger.warning("❌ '의료급여법' 텍스트 없음")
            logger.info(f"\n페이지 내용 일부:\n{body_text[:500]}")

        # 법령 제목 찾기
        headings = page.locator("h1, h2, h3, h4").all()
        logger.info(f"\n발견된 제목 ({len(headings)}개):")
        for h in headings[:10]:
            logger.info(f"  - {h.inner_text()[:100]}")

        # 법령 조문 확인
        articles = page.locator("div, p, article").all()
        logger.info(f"\n콘텐츠 블록 개수: {len(articles)}")

        # 텍스트 저장
        if "의료급여법" in body_text:
            text_file = OUTPUT_DIR / "scourt_의료급여법.txt"
            text_file.write_text(body_text, encoding='utf-8')
            logger.info(f"\n텍스트 저장: {text_file}")

        # 15초 대기
        logger.info("\n브라우저를 15초간 유지합니다...")
        time.sleep(15)

    except Exception as e:
        logger.error(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

logger.info("\n탐색 완료!")
