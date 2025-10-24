"""
스크래퍼 테스트 - 각 board 1페이지씩
"""
import asyncio
import json
from pathlib import Path
from scraper import HIRACancerScraper


async def test_scraper():
    """각 board 1페이지씩 테스트"""
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / 'data' / 'hira_cancer' / 'test'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("HIRA 암질환 스크래퍼 테스트 (각 board 1페이지)")
    print("="*80)

    async with HIRACancerScraper(output_dir, download_attachments=False) as scraper:
        results = {}

        for board_key in scraper.BOARDS.keys():
            print(f"\n{'='*80}")
            print(f"[{scraper.BOARDS[board_key]['name']}] 테스트")
            print(f"{'='*80}\n")

            try:
                # 1페이지만 수집
                posts = await scraper.scrape_board(board_key, max_pages=1)
                results[board_key] = posts

                print(f"\n[{scraper.BOARDS[board_key]['name']}] 결과:")
                print(f"  수집 게시글: {len(posts)}개")

                if posts:
                    # 첫 번째 게시글 샘플
                    sample = posts[0]
                    print(f"\n  샘플 게시글:")
                    print(f"    번호: {sample.get('number')}")
                    print(f"    제목: {sample.get('title')[:50]}...")
                    print(f"    본문 길이: {len(sample.get('content', ''))}자")
                    print(f"    첨부파일: {sample.get('attachment_count', 0)}개")

                    if sample.get('attachments'):
                        print(f"    첫 번째 첨부파일: {sample['attachments'][0].get('filename', 'N/A')}")

            except Exception as e:
                print(f"[{board_key}] 오류: {e}")
                results[board_key] = []

            await asyncio.sleep(2)

        # 결과 저장
        output_file = output_dir / 'test_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*80}")
        print(f"테스트 완료!")
        print(f"결과: {output_file}")
        print(f"{'='*80}\n")

        # 요약
        for board_key, posts in results.items():
            board_name = scraper.BOARDS[board_key]['name']
            total_content = sum(len(p.get('content', '')) for p in posts)
            total_attachments = sum(p.get('attachment_count', 0) for p in posts)

            print(f"[{board_name:10}] {len(posts):3}개 | "
                  f"본문 {total_content:5}자 | "
                  f"첨부 {total_attachments:3}개")


if __name__ == "__main__":
    asyncio.run(test_scraper())
