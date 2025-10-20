"""
대법원 포털에서 의료법 3종 일괄 수집

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

logger = setup_logger("scourt_medical_law", project="likms")

# 의료법 3종 URL 정보
LAWS = [
    {
        "name": "의료법",
        "type": "법률",
        "jisCntntsSrno": "2025000006833"
    },
    {
        "name": "의료법 시행령",
        "type": "대통령령",
        "jisCntntsSrno": "2025000011809"
    },
    {
        "name": "의료법 시행규칙",
        "type": "보건복지부령",
        "jisCntntsSrno": "2025000011808"
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
    url = f"{BASE_URL}?w2xPath=PGP1021M04&jisCntntsSrno={jisCntntsSrno}&srchwd=%EC%9D%98%EB%A3%8C%EB%B2%95&c=900"

    logger.info(f"접속 URL: {url}")
    page.goto(url, wait_until="networkidle")
    time.sleep(5)

    # 텍스트 추출
    body_text = page.locator("body").inner_text()

    # 줄 수 및 단어 수 계산
    lines = body_text.split('\n')
    words = body_text.split()

    logger.info(f"텍스트 길이: {len(body_text):,} 글자")
    logger.info(f"줄 수: {len(lines):,} 줄")
    logger.info(f"단어 수: {len(words):,} 단어")

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
        "jisCntntsSrno": jisCntntsSrno,
        "stats": {
            "chars": len(body_text),
            "lines": len(lines),
            "words": len(words)
        }
    }

    json_path = OUTPUT_DIR / f"{safe_name}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ JSON 저장: {json_path}")

    logger.info("=" * 60)

    return data

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page()

    try:
        collected = []

        # 3개 법령 순차 수집
        for idx, law_info in enumerate(LAWS, 1):
            logger.info(f"\n[{idx}/{len(LAWS)}] {law_info['name']}")
            result = scrape_law(page, law_info)
            collected.append(result)
            time.sleep(2)

        # 요약
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ 수집 완료: {len(collected)}/{len(LAWS)}개 법령")
        logger.info("=" * 60)

        total_chars = 0
        total_lines = 0
        total_words = 0

        for item in collected:
            stats = item['stats']
            logger.info(f"  - {item['title']}: {stats['chars']:,} 글자, {stats['lines']:,} 줄, {stats['words']:,} 단어")
            total_chars += stats['chars']
            total_lines += stats['lines']
            total_words += stats['words']

        logger.info("\n" + "=" * 60)
        logger.info(f"총계: {total_chars:,} 글자, {total_lines:,} 줄, {total_words:,} 단어")
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
