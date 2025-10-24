"""
항암화학요법 board만 테스트
"""
import asyncio
import json
from pathlib import Path
from scraper import HIRACancerScraper


async def test_chemotherapy():
    """항암화학요법 board만 테스트"""
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / 'data' / 'hira_cancer' / 'test'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("항암화학요법 board 테스트")
    print("="*80)

    async with HIRACancerScraper(output_dir, download_attachments=False) as scraper:
        posts = await scraper.scrape_board('chemotherapy', max_pages=1)

        print(f"\n결과:")
        print(f"  수집 게시글: {len(posts)}개\n")

        for i, post in enumerate(posts, 1):
            print(f"{i}. 번호: {post.get('number')}")
            print(f"   제목: {post.get('title')}")
            print(f"   본문 길이: {len(post.get('content', ''))}자")
            print(f"   첨부파일: {post.get('attachment_count', 0)}개")

            if post.get('attachments'):
                for j, att in enumerate(post['attachments'], 1):
                    print(f"     [{j}] {att.get('filename')}")
                    print(f"         URL: {att.get('download_url')}")
            print()

        # 결과 저장
        output_file = output_dir / 'chemotherapy_test.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

        print(f"결과 저장: {output_file}")


if __name__ == "__main__":
    asyncio.run(test_chemotherapy())
