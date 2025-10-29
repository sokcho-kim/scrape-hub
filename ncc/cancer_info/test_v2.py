"""
Scraper V2 테스트

갑상선암 1개만 테스트
"""
import asyncio
import sys
sys.path.append('.')

from ncc.scraper_v2 import NCCScraper

async def test_single_cancer():
    """단일 암종 테스트 (갑상선암)"""

    # 갑상선암 정보
    test_cancer = {
        "name": "갑상선암",
        "cancer_seq": "3341",
        "tags": ["주요암", "성인"]
    }

    async with NCCScraper() as scraper:
        print("\n=== 갑상선암 테스트 시작 ===\n")

        result = await scraper.scrape_cancer(test_cancer)

        if result:
            print("\n=== 테스트 성공 ===")
            print(f"암종명: {result['name']}")
            print(f"태그: {result['tags']}")
            print(f"섹션 수: {len(result['content']['sections'])}")
            print(f"이미지 수: {len(result['content']['images'])}")
            print(f"표 수: {len(result['content']['tables'])}")

            print("\n=== 추출된 섹션 ===")
            for i, section in enumerate(result['content']['sections'][:5], 1):
                print(f"\n{i}. [{section['level']}] {section['heading']}")
                print(f"   내용 길이: {len(section['content'])} 문자")
                print(f"   내용 미리보기: {section['content'][:100]}...")

            print(f"\n파일 저장됨: data/ncc/parsed/갑상선암_3341.json")
            print(f"\n태그가 포함된 데이터 구조:")
            print(f"  - name: {result['name']}")
            print(f"  - cancer_seq: {result['cancer_seq']}")
            print(f"  - tags: {result['tags']}")  # ← 중요!

        else:
            print("스크래핑 실패")

if __name__ == "__main__":
    asyncio.run(test_single_cancer())
