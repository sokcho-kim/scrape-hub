"""
다운로드 수정 테스트
공고 게시판 1개 게시글만 테스트
"""
import asyncio
import logging
from pathlib import Path
from scraper import HIRACancerScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def main():
    """다운로드 수정 테스트"""
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / 'data' / 'hira_cancer' / 'raw'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("다운로드 수정 테스트 (공고 게시판 1페이지)")
    print("="*80)

    async with HIRACancerScraper(output_dir, download_attachments=True) as scraper:
        # 공고 게시판 1페이지만 테스트
        posts = await scraper.scrape_board('announcement', max_pages=1)

        print(f"\n수집 완료: {len(posts)}개 게시글")

        # 첨부파일 통계
        total_attachments = sum(len(p.get('attachments', [])) for p in posts)
        downloaded = sum(
            sum(1 for att in p.get('attachments', []) if att.get('downloaded'))
            for p in posts
        )

        print(f"총 첨부파일: {total_attachments}개")
        print(f"다운로드 성공: {downloaded}개")
        print(f"다운로드 실패: {total_attachments - downloaded}개")

        # 샘플 확인
        if posts and posts[0].get('attachments'):
            sample = posts[0]['attachments'][0]
            print(f"\n샘플 첨부파일:")
            print(f"  파일명: {sample['filename']}")
            print(f"  다운로드: {sample.get('downloaded', False)}")
            print(f"  경로: {sample.get('local_path', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
