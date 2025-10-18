"""
대법원 포털 직접 URL 접근

주어진 URL에서 시작해서 관련 법령 링크를 찾습니다.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json
from datetime import datetime
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.logger import setup_logger

# 사용자 제공 URL
LAW_URL = "https://portal.scourt.go.kr/pgp/main.on?w2xPath=PGP1021M04&jisCntntsSrno=2025000009651&srchwd=%EC%9D%98%EB%A3%8C%EA%B8%89%EC%97%AC%EB%B2%95&c=900"
OUTPUT_DIR = Path("data/likms/laws")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logger("scourt_direct", project="likms")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page()

    try:
        # 의료급여법 페이지 접속
        logger.info("의료급여법 페이지 접속...")
        page.goto(LAW_URL, wait_until="networkidle")
        time.sleep(5)

        # 1. 의료급여법 텍스트 저장
        logger.info("\n[1/3] 의료급여법 텍스트 추출")
        body_text = page.locator("body").inner_text()
        logger.info(f"  텍스트 길이: {len(body_text):,} 글자")

        # 저장
        txt_path = OUTPUT_DIR / "의료급여법.txt"
        txt_path.write_text(body_text, encoding='utf-8')
        logger.info(f"  ✅ 저장: {txt_path}")

        json_path = OUTPUT_DIR / "의료급여법.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "title": "의료급여법",
                "content": body_text,
                "scraped_at": datetime.now().isoformat(),
                "source": "대법원 사법정보공개포털",
                "url": page.url
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"  ✅ 저장: {json_path}")

        # 2. 시행령 링크 찾기
        logger.info("\n[2/3] 시행령 링크 찾기...")

        # "시행령" 텍스트가 있는 링크 찾기
        enforcement_links = page.locator("a:has-text('시행령')").all()
        logger.info(f"  '시행령' 링크 {len(enforcement_links)}개 발견")

        for idx, link in enumerate(enforcement_links[:5]):
            try:
                link_text = link.inner_text().strip()
                logger.info(f"    링크 {idx+1}: {link_text}")
            except:
                pass

        if enforcement_links:
            logger.info("\n  첫 번째 시행령 링크 클릭...")
            enforcement_links[0].click()
            time.sleep(5)

            # 시행령 텍스트 추출
            body_text = page.locator("body").inner_text()
            logger.info(f"  텍스트 길이: {len(body_text):,} 글자")

            # 저장
            txt_path = OUTPUT_DIR / "의료급여법_시행령.txt"
            txt_path.write_text(body_text, encoding='utf-8')
            logger.info(f"  ✅ 저장: {txt_path}")

            json_path = OUTPUT_DIR / "의료급여법_시행령.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "title": "의료급여법 시행령",
                    "content": body_text,
                    "scraped_at": datetime.now().isoformat(),
                    "source": "대법원 사법정보공개포털",
                    "url": page.url
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"  ✅ 저장: {json_path}")

            # 원래 페이지로 돌아가기
            page.go_back()
            time.sleep(3)
        else:
            logger.warning("  시행령 링크를 찾을 수 없습니다")

        # 3. 시행규칙 링크 찾기
        logger.info("\n[3/3] 시행규칙 링크 찾기...")

        # "시행규칙" 텍스트가 있는 링크 찾기
        regulation_links = page.locator("a:has-text('시행규칙')").all()
        logger.info(f"  '시행규칙' 링크 {len(regulation_links)}개 발견")

        for idx, link in enumerate(regulation_links[:5]):
            try:
                link_text = link.inner_text().strip()
                logger.info(f"    링크 {idx+1}: {link_text}")
            except:
                pass

        if regulation_links:
            logger.info("\n  첫 번째 시행규칙 링크 클릭...")
            regulation_links[0].click()
            time.sleep(5)

            # 시행규칙 텍스트 추출
            body_text = page.locator("body").inner_text()
            logger.info(f"  텍스트 길이: {len(body_text):,} 글자")

            # 저장
            txt_path = OUTPUT_DIR / "의료급여법_시행규칙.txt"
            txt_path.write_text(body_text, encoding='utf-8')
            logger.info(f"  ✅ 저장: {txt_path}")

            json_path = OUTPUT_DIR / "의료급여법_시행규칙.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "title": "의료급여법 시행규칙",
                    "content": body_text,
                    "scraped_at": datetime.now().isoformat(),
                    "source": "대법원 사법정보공개포털",
                    "url": page.url
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"  ✅ 저장: {json_path}")
        else:
            logger.warning("  시행규칙 링크를 찾을 수 없습니다")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 법령 수집 완료!")
        logger.info("=" * 60)

        # 10초 대기
        logger.info("\n브라우저를 10초간 유지합니다...")
        time.sleep(10)

    except Exception as e:
        logger.error(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

logger.info("\n작업 완료!")
