"""
공고 board만 217건 전체 수집
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from scraper import HIRACancerScraper


async def main():
    """공고 board만 수집"""
    output_dir = Path("data/hira_cancer/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with HIRACancerScraper(output_dir, download_attachments=False) as scraper:
        # 공고 board만 수집
        print("="*80)
        print("공고 board 전체 수집 시작 (217건 예상)")
        print("="*80)

        posts = await scraper.scrape_board('announcement', max_pages=None)

        print(f"\n수집 완료: {len(posts)}개 게시글")

        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"announcement_only_{timestamp}.json"

        result = {
            'metadata': {
                'collected_at': datetime.now().isoformat(),
                'total_posts': len(posts),
                'board': '공고'
            },
            'data': posts
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n저장 완료: {output_file}")
        print(f"파일 크기: {output_file.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    asyncio.run(main())
