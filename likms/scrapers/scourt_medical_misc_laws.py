"""
대법원 포털에서 의료 관련 기타 법령 일괄 수집

- 장기등 이식에 관한 법률 3종
- 한의약 육성법 1종
- 보건의료기술 진흥법 2종
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

logger = setup_logger("scourt_medical_misc_laws", project="likms")

# 의료 관련 기타 법령 6종
LAWS = [
    # 장기등 이식에 관한 법률 3종
    {
        "name": "장기등_이식에_관한_법률",
        "type": "법률",
        "jisCntntsSrno": "3313016",
        "search_keyword": "%EC%9E%A5%EA%B8%B0%EB%93%B1%20%EC%9D%B4%EC%8B%9D%EC%97%90%20%EA%B4%80%ED%95%9C%20%EB%B2%95%EB%A5%A0"
    },
    {
        "name": "장기등_이식에_관한_법률_시행령",
        "type": "대통령령",
        "jisCntntsSrno": "2025000010747",
        "search_keyword": "%EC%9E%A5%EA%B8%B0%EB%93%B1%20%EC%9D%B4%EC%8B%9D%EC%97%90%20%EA%B4%80%ED%95%9C%20%EB%B2%95%EB%A5%A0"
    },
    {
        "name": "장기등_이식에_관한_법률_시행규칙",
        "type": "보건복지부령",
        "jisCntntsSrno": "2025000014778",
        "search_keyword": "%EC%9E%A5%EA%B8%B0%EB%93%B1%20%EC%9D%B4%EC%8B%9D%EC%97%90%20%EA%B4%80%ED%95%9C%20%EB%B2%95%EB%A5%A0"
    },
    # 한의약 육성법 1종
    {
        "name": "한의약_육성법",
        "type": "법률",
        "jisCntntsSrno": "3311801",
        "search_keyword": "%ED%95%9C%EC%95%BD%EC%A7%84%ED%9D%A5%EB%B2%95"
    },
    # 보건의료기술 진흥법 2종
    {
        "name": "보건의료기술_진흥법",
        "type": "법률",
        "jisCntntsSrno": "3311110",
        "search_keyword": "%ED%95%9C%EC%95%BD%EC%A7%84%ED%9D%A5%EB%B2%95"
    },
    {
        "name": "보건의료기술_진흥법_시행령",
        "type": "대통령령",
        "jisCntntsSrno": "3335849",
        "search_keyword": "%ED%95%9C%EC%95%BD%EC%A7%84%ED%9D%A5%EB%B2%95"
    }
]

def scrape_law(page, law_info):
    """단일 법령 수집"""
    name = law_info["name"]
    jisCntntsSrno = law_info["jisCntntsSrno"]
    search_keyword = law_info["search_keyword"]

    logger.info("=" * 60)
    logger.info(f"법령 수집: {name}")
    logger.info("=" * 60)

    # URL 생성
    url = f"{BASE_URL}?w2xPath=PGP1021M04&jisCntntsSrno={jisCntntsSrno}&srchwd={search_keyword}&c=900"

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
    safe_name = name

    # TXT 저장
    txt_path = OUTPUT_DIR / f"{safe_name}.txt"
    txt_path.write_text(body_text, encoding='utf-8')
    logger.info(f"✅ TXT 저장: {txt_path}")

    # JSON 저장
    data = {
        "title": name.replace("_", " "),
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

        # 6개 법령 순차 수집
        for idx, law_info in enumerate(LAWS, 1):
            logger.info(f"\n[{idx}/{len(LAWS)}] {law_info['name']}")
            result = scrape_law(page, law_info)
            collected.append(result)
            time.sleep(2)

        # 요약
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ 수집 완료: {len(collected)}/{len(LAWS)}개 법령")
        logger.info("=" * 60)

        # 법령 체계별 구분
        logger.info("\n장기등 이식에 관한 법률:")
        total1 = 0
        for item in collected[:3]:
            stats = item['stats']
            logger.info(f"  - {item['title']}: {stats['chars']:,} 글자")
            total1 += stats['chars']
        logger.info(f"  소계: {total1:,} 글자")

        logger.info("\n한의약 육성법:")
        stats4 = collected[3]['stats']
        logger.info(f"  - {collected[3]['title']}: {stats4['chars']:,} 글자")

        logger.info("\n보건의료기술 진흥법:")
        total2 = 0
        for item in collected[4:]:
            stats = item['stats']
            logger.info(f"  - {item['title']}: {stats['chars']:,} 글자")
            total2 += stats['chars']
        logger.info(f"  소계: {total2:,} 글자")

        total_chars = sum(item['stats']['chars'] for item in collected)
        total_lines = sum(item['stats']['lines'] for item in collected)
        total_words = sum(item['stats']['words'] for item in collected)

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
