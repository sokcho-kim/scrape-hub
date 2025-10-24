"""
HIRA Cancer 스크래핑 결과 확인
"""
import json
from pathlib import Path


def check_results():
    """최신 결과 파일 확인"""
    data_dir = Path("data/hira_cancer/raw")

    # 최신 JSON 파일 찾기
    json_files = list(data_dir.glob("hira_cancer_*.json"))

    if not json_files:
        print("결과 파일이 없습니다.")
        return

    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"최신 파일: {latest_file.name}")
    print(f"파일 크기: {latest_file.stat().st_size / 1024:.1f} KB")
    print()

    # JSON 로드
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 통계
    print("="*80)
    print("수집 통계")
    print("="*80)

    metadata = data.get('metadata', {})
    boards = metadata.get('boards', {})

    total_posts = 0
    total_attachments = 0
    total_content_chars = 0

    for board_key, board_info in boards.items():
        print(f"\n[{board_info['name']}]")
        print(f"  게시글: {board_info['posts']}개")
        print(f"  첨부파일: {board_info['attachments']}개")

        total_posts += board_info['posts']
        total_attachments += board_info['attachments']

    print(f"\n{'='*80}")
    print(f"총 게시글: {total_posts}개")
    print(f"총 첨부파일: {total_attachments}개")
    print(f"{'='*80}")

    # 샘플 확인
    print(f"\n{'='*80}")
    print("샘플 게시글 확인")
    print('='*80)

    for board_key, posts in data.get('data', {}).items():
        if posts:
            print(f"\n[{board_key}] 첫 게시글:")
            post = posts[0]
            print(f"  제목: {post.get('title', 'N/A')[:50]}")
            print(f"  URL: {post.get('detail_url', 'N/A')[:80]}")
            print(f"  본문 길이: {len(post.get('content', ''))}자")
            print(f"  첨부파일 수: {len(post.get('attachments', []))}개")

            if post.get('attachments'):
                att = post['attachments'][0]
                print(f"  첫 첨부파일: {att.get('filename', 'N/A')}")
                print(f"    확장자: {att.get('extension', 'N/A')}")
                print(f"    다운로드 URL: {att.get('download_url', 'N/A')[:80]}")

    # 문제 확인
    print(f"\n{'='*80}")
    print("데이터 품질 확인")
    print('='*80)

    issues = []

    for board_key, posts in data.get('data', {}).items():
        empty_content = sum(1 for p in posts if not p.get('content', '').strip())
        no_url = sum(1 for p in posts if not p.get('detail_url'))

        if empty_content > 0:
            issues.append(f"[{board_key}] 본문 없음: {empty_content}개")
        if no_url > 0:
            issues.append(f"[{board_key}] URL 없음: {no_url}개")

    if issues:
        print("\n문제 발견:")
        for issue in issues:
            print(f"  ⚠ {issue}")
    else:
        print("\n✓ 모든 데이터 정상")


if __name__ == "__main__":
    check_results()
