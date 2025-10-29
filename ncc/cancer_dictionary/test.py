"""
암정보 사전 스크래퍼 테스트

첫 1-2 페이지만 테스트
"""
import asyncio
import sys
sys.path.append('.')

from ncc.cancer_dictionary.scraper import CancerDictionaryScraper

async def test_scraper():
    """처음 2페이지만 테스트"""
    print("\n=== 암정보 사전 스크래퍼 테스트 ===\n")
    print("첫 2페이지만 수집합니다...\n")

    async with CancerDictionaryScraper() as scraper:
        await scraper.scrape_all(start_page=1, end_page=2, batch_size=1)

    print("\n=== 테스트 완료 ===")
    print(f"수집된 항목: {scraper.scraped_count}개")
    print(f"실패: {scraper.failed_count}개")
    print("\n결과 파일: data/ncc/cancer_dictionary/parsed/batch_0001.json")

if __name__ == "__main__":
    asyncio.run(test_scraper())
