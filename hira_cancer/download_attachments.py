"""
이미 수집된 JSON에서 첨부파일만 다운로드
"""
import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_attachment(page, attachment: dict, post: dict, output_dir: Path):
    """첨부파일 다운로드"""
    try:
        # 저장 경로 생성
        board_dir = output_dir / 'attachments' / post['board']
        board_dir.mkdir(parents=True, exist_ok=True)

        # 안전한 파일명 생성
        safe_filename = f"{post['number']}_{attachment['filename']}"
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', safe_filename)

        local_path = board_dir / safe_filename

        # 이미 다운로드된 경우 스킵
        if local_path.exists():
            logger.debug(f"  이미 존재: {safe_filename}")
            return True

        # 다운로드
        download_url = attachment.get('download_url')
        if not download_url:
            logger.warning(f"  다운로드 URL 없음: {safe_filename}")
            return False

        logger.info(f"  다운로드: {safe_filename}")

        async with page.expect_download(timeout=30000) as download_info:
            await page.goto(download_url)

        download = await download_info.value
        await download.save_as(local_path)

        logger.info(f"  저장 완료: {local_path.name} ({local_path.stat().st_size / 1024:.1f} KB)")
        return True

    except Exception as e:
        logger.error(f"첨부파일 다운로드 실패 ({attachment.get('filename', 'Unknown')}): {e}")
        return False


async def download_all_attachments(json_file: Path, output_dir: Path):
    """JSON 파일에서 모든 첨부파일 다운로드"""
    logger.info("="*80)
    logger.info("첨부파일 다운로드 시작")
    logger.info("="*80)

    # JSON 로드
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    boards_data = data['data']

    # 전체 첨부파일 수 계산
    total_attachments = 0
    for posts in boards_data.values():
        for post in posts:
            total_attachments += len(post.get('attachments', []))

    logger.info(f"\n총 첨부파일: {total_attachments}개")

    downloaded = 0
    skipped = 0
    failed = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for board_key, posts in boards_data.items():
            board_name = data['metadata']['boards'][board_key]['name']
            logger.info(f"\n{'='*80}")
            logger.info(f"[{board_name}] 첨부파일 다운로드")
            logger.info(f"{'='*80}")

            for post in posts:
                attachments = post.get('attachments', [])
                if not attachments:
                    continue

                logger.info(f"\n[{post.get('number')}] {post.get('title')[:50]}... ({len(attachments)}개)")

                for attachment in attachments:
                    result = await download_attachment(page, attachment, post, output_dir)

                    if result:
                        downloaded += 1
                    else:
                        failed += 1

                    # Rate limiting
                    await asyncio.sleep(0.5)

        await browser.close()

    logger.info(f"\n{'='*80}")
    logger.info("첨부파일 다운로드 완료")
    logger.info(f"{'='*80}")
    logger.info(f"\n성공: {downloaded}개")
    logger.info(f"실패: {failed}개")
    logger.info(f"전체: {total_attachments}개")

    return downloaded, failed


async def main():
    """메인 실행"""
    base_dir = Path(__file__).parent.parent
    json_file = base_dir / 'data' / 'hira_cancer' / 'raw' / 'hira_cancer_20251023_163624.json'
    output_dir = base_dir / 'data' / 'hira_cancer' / 'raw'

    if not json_file.exists():
        logger.error(f"JSON 파일 없음: {json_file}")
        return

    downloaded, failed = await download_all_attachments(json_file, output_dir)

    logger.info(f"\n완료! 다운로드: {downloaded}개, 실패: {failed}개")


if __name__ == "__main__":
    asyncio.run(main())
