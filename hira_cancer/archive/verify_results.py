"""
수집 결과 검증 스크립트
"""
import json
from pathlib import Path


def verify_results(json_file: Path):
    """수집 결과 검증"""
    print("="*80)
    print("HIRA 암질환 데이터 수집 결과 검증")
    print("="*80)

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    metadata = data['metadata']
    boards_data = data['data']

    print(f"\n[수집 일시] {metadata['timestamp']}")
    print(f"\n[전체 통계]")

    total_posts = sum(b['posts'] for b in metadata['boards'].values())
    total_attachments = sum(b['attachments'] for b in metadata['boards'].values())

    print(f"  총 게시글: {total_posts}개")
    print(f"  총 첨부파일: {total_attachments}개")

    print(f"\n[Board별 상세]")

    for board_key, board_info in metadata['boards'].items():
        print(f"\n  [{board_info['name']}]")
        print(f"    게시글: {board_info['posts']}개")
        print(f"    첨부파일: {board_info['attachments']}개")

        # 실제 데이터 확인
        posts = boards_data[board_key]

        # 본문 통계
        total_content_length = sum(len(p.get('content', '')) for p in posts)
        avg_content_length = total_content_length / len(posts) if posts else 0

        # 본문 없는 게시글
        empty_content = sum(1 for p in posts if not p.get('content', '').strip())

        # 첨부파일 없는 게시글
        no_attachments = sum(1 for p in posts if p.get('attachment_count', 0) == 0)

        print(f"    평균 본문 길이: {avg_content_length:.0f}자")
        print(f"    본문 없음: {empty_content}개")
        print(f"    첨부파일 없음: {no_attachments}개")

        # 샘플 게시글
        if posts:
            sample = posts[0]
            print(f"\n    샘플 게시글:")
            print(f"      번호: {sample.get('number')}")
            print(f"      제목: {sample.get('title')[:50]}...")
            print(f"      본문: {len(sample.get('content', ''))}자")
            print(f"      첨부: {sample.get('attachment_count', 0)}개")

    # 이슈 검출
    print(f"\n\n[이슈 검출]")

    issues = []

    for board_key, posts in boards_data.items():
        board_name = metadata['boards'][board_key]['name']

        # 본문 누락 체크 (항암화학요법 제외)
        if board_key != 'chemotherapy':
            empty_posts = [p for p in posts if not p.get('content', '').strip()]
            if empty_posts:
                issues.append(f"  [WARNING] [{board_name}] 본문 없는 게시글 {len(empty_posts)}개")

        # 첨부파일 URL 누락 체크
        for post in posts:
            for att in post.get('attachments', []):
                if not att.get('download_url'):
                    issues.append(f"  [WARNING] [{board_name}] 게시글 {post.get('number')}: 첨부파일 URL 없음")
                    break

    if issues:
        for issue in issues:
            print(issue)
    else:
        print("  [OK] 이슈 없음")

    print(f"\n{'='*80}")
    print("검증 완료!")
    print(f"{'='*80}")

    return metadata, boards_data


if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    json_file = base_dir / 'data' / 'hira_cancer' / 'raw' / 'hira_cancer_20251023_163624.json'

    if json_file.exists():
        verify_results(json_file)
    else:
        print(f"파일 없음: {json_file}")
