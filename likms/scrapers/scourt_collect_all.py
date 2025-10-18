"""
대법원 포털에서 의료급여법 3종 일괄 수집

직접 URL로 접근하여 법률, 시행령, 시행규칙을 수집합니다.
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

BASE_URL = "https://portal.scourt.go.kr/pgp/main.on"
OUTPUT_DIR = Path("data/likms/laws")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logger("scourt_collect_all", project="likms")

# 의료급여법 3종 URL 정보
LAWS = [
    {
        "name": "의료급여법",
        "type": "법률",
        "jisCntntsSrno": "2025000009651"
    },
    {
        "name": "의료급여법 시행령",
        "type": "대통령령",
        "jisCntntsSrno": "3331773"
    },
    {
        "name": "의료급여법 시행규칙",
        "type": "보건복지부령",
        "jisCntntsSrno": "2025000018495"
    }
]

def scrape_law(page, law_info):
    """단일 법령 수집"""
    name = law_info["name"]
    jisCntntsSrno = law_info["jisCntntsSrno"]

    logger.info("=" * 60)
    logger.info(f"법령 수집: {name}")
    logger.info("=" * 60)

    # URL 생성
    url = f"{BASE_URL}?w2xPath=PGP1021M04&jisCntntsSrno={jisCntntsSrno}&srchwd=%EC%9D%98%EB%A3%8C%EA%B8%89%EC%97%AC%EB%B2%95&c=900"

    logger.info(f"접속 URL: {url}")
    page.goto(url, wait_until="networkidle")
    time.sleep(5)

    # 텍스트 추출
    body_text = page.locator("body").inner_text()
    logger.info(f"텍스트 길이: {len(body_text):,} 글자")

    # 저장
    safe_name = name.replace(" ", "_")

    # TXT 저장
    txt_path = OUTPUT_DIR / f"{safe_name}.txt"
    txt_path.write_text(body_text, encoding='utf-8')
    logger.info(f"✅ TXT 저장: {txt_path}")

    # JSON 저장
    data = {
        "title": name,
        "type": law_info["type"],
        "content": body_text,
        "scraped_at": datetime.now().isoformat(),
        "source": "대법원 사법정보공개포털",
        "url": url,
        "jisCntntsSrno": jisCntntsSrno
    }

    json_path = OUTPUT_DIR / f"{safe_name}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ JSON 저장: {json_path}")

    logger.info("=" * 60)

    return data

def find_regulation_link(page):
    """페이지에서 시행규칙 링크 찾기"""
    logger.info("\n시행규칙 링크 찾기...")

    # "시행규칙" 텍스트가 있는 링크 찾기
    regulation_links = page.locator("a:has-text('시행규칙')").all()

    if regulation_links:
        logger.info(f"시행규칙 링크 {len(regulation_links)}개 발견")

        for idx, link in enumerate(regulation_links[:5]):
            try:
                href = link.get_attribute("href")
                text = link.inner_text().strip()
                logger.info(f"  링크 {idx+1}: {text} → {href}")
            except:
                pass

        return regulation_links[0] if regulation_links else None
    else:
        logger.warning("시행규칙 링크를 찾을 수 없습니다")
        return None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page()

    try:
        collected = []

        # 1. 의료급여법 (법률)
        logger.info("\n[1/3] 의료급여법 (법률)")
        result1 = scrape_law(page, LAWS[0])
        collected.append(result1)
        time.sleep(2)

        # 2. 의료급여법 시행령
        logger.info("\n[2/3] 의료급여법 시행령")
        result2 = scrape_law(page, LAWS[1])
        collected.append(result2)
        time.sleep(2)

        # 3. 의료급여법 시행규칙
        logger.info("\n[3/3] 의료급여법 시행규칙")
        result3 = scrape_law(page, LAWS[2])
        collected.append(result3)
        time.sleep(2)

        # 요약
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ 수집 완료: {len(collected)}/3개 법령")
        logger.info("=" * 60)

        for item in collected:
            logger.info(f"  - {item['title']}: {len(item['content']):,} 글자")

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
