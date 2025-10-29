"""
NCC 스크래퍼 개선된 추출 테스트

갑상선암 페이지 하나만 스크래핑하여 결과 확인
"""
import asyncio
import sys
sys.path.append('.')

from ncc.scraper import NCCScraper

async def test_single_page():
    """단일 페이지 테스트"""
    # 갑상선암 메인 페이지 테스트
    test_page = {
        "url": "/lay1/program/S1T211C212/cancer/list.do",
        "category": "암의 종류 > 갑상선암",
        "title": "갑상선암 개요 (테스트)",
        "filename": "test_갑상선암_filtered"
    }

    async with NCCScraper() as scraper:
        result = await scraper.scrape_page(test_page)

        if result:
            print("\n=== 테스트 성공 ===")
            print(f"섹션 수: {len(result['content']['sections'])}")
            print(f"이미지 수: {len(result['content']['images'])}")
            print(f"표 수: {len(result['content']['tables'])}")

            print("\n=== 추출된 섹션 ===")
            for i, section in enumerate(result['content']['sections'][:5], 1):
                print(f"\n{i}. [{section['level']}] {section['heading']}")
                print(f"   내용 길이: {len(section['content'])} 문자")
                print(f"   내용 미리보기: {section['content'][:100]}...")

            print("\n=== 추출된 이미지 ===")
            for i, img in enumerate(result['content']['images'][:5], 1):
                print(f"{i}. {img['alt']} - {img['url'][:60]}...")

            print(f"\n파일 저장됨: data/ncc/parsed/test_갑상선암_filtered.json")
        else:
            print("스크래핑 실패")

if __name__ == "__main__":
    asyncio.run(test_single_page())
