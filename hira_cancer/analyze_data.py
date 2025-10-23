"""
HIRA 암질환 수집 데이터 분석
"""
import json
from pathlib import Path
from collections import Counter, defaultdict

def analyze_data():
    """수집된 데이터 분석"""

    # 프로젝트 루트로 이동
    base_dir = Path(__file__).parent.parent
    json_file = base_dir / 'data' / 'hira_cancer' / 'raw' / 'hira_cancer_20251023_184848.json'

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('=' * 80)
    print('HIRA 암질환 데이터 수집 분석')
    print('=' * 80)
    print()

    # 메타데이터
    meta = data['metadata']
    print('[전체 통계]')
    print(f"수집 시각: {meta['timestamp']}")
    print()

    total_posts = 0
    total_attachments = 0

    for board_key, board_info in meta['boards'].items():
        print(f"  {board_info['name']:12s}: {board_info['posts']:3d}개 게시글, {board_info['attachments']:3d}개 첨부파일")
        total_posts += board_info['posts']
        total_attachments += board_info['attachments']

    print()
    print(f"  {'총합':12s}: {total_posts:3d}개 게시글, {total_attachments:3d}개 첨부파일")
    print()
    print('=' * 80)
    print()

    # 게시판별 상세 분석
    for board_key, posts in data['data'].items():
        board_name = meta['boards'][board_key]['name']

        print(f"▶ {board_name} ({board_key})")
        print(f"  총 {len(posts)}개 게시글")
        print()

        # 첨부파일 분석
        total_att = sum(len(p.get('attachments', [])) for p in posts)
        downloaded = sum(
            sum(1 for att in p.get('attachments', []) if att.get('downloaded'))
            for p in posts
        )

        print(f"  첨부파일:")
        print(f"    전체: {total_att}개")
        print(f"    다운로드 성공: {downloaded}개")
        print(f"    다운로드 실패: {total_att - downloaded}개")

        if total_att > 0:
            # 확장자 분포
            extensions = []
            for post in posts:
                for att in post.get('attachments', []):
                    ext = att.get('extension', '')
                    if ext:
                        extensions.append(ext.lower())

            if extensions:
                ext_counter = Counter(extensions)
                print(f"    파일 형식:")
                for ext, count in ext_counter.most_common():
                    pct = count / total_att * 100
                    print(f"      {ext:8s}: {count:3d}개 ({pct:5.1f}%)")

        print()

        # 본문 길이 분석
        content_lengths = [len(p.get('content', '')) for p in posts if p.get('content')]
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            max_length = max(content_lengths)
            min_length = min(content_lengths)
            print(f"  본문 길이:")
            print(f"    평균: {avg_length:,.0f}자")
            print(f"    최소: {min_length:,}자")
            print(f"    최대: {max_length:,}자")
            print(f"    본문 있는 게시글: {len(content_lengths)}/{len(posts)}개")
        print()

        # 날짜 분석
        dates = [p.get('date') for p in posts if p.get('date')]
        if dates:
            print(f"  수집 기간:")
            print(f"    최신: {dates[0] if dates else 'N/A'}")
            print(f"    최초: {dates[-1] if len(dates) > 0 else 'N/A'}")
        print()

        # 샘플 게시글 (최신 3개)
        print(f"  최근 게시글 샘플:")
        for i, post in enumerate(posts[:3], 1):
            print(f"    [{i}] #{post.get('number')} - {post.get('title', 'N/A')[:50]}")
            print(f"        날짜: {post.get('date', 'N/A')}")
            print(f"        작성자: {post.get('author', 'N/A')[:40]}")
            print(f"        본문: {len(post.get('content', ''))}자")
            print(f"        첨부파일: {len(post.get('attachments', []))}개")
            if post.get('attachments'):
                for att in post['attachments'][:2]:  # 첫 2개만
                    status = "[OK]" if att.get('downloaded') else "[FAIL]"
                    print(f"          {status} {att.get('filename', 'N/A')}")

        print()
        print('-' * 80)
        print()

    # 파일 크기 분석
    print('[파일 시스템 분석]')
    print()

    json_size = json_file.stat().st_size / 1024 / 1024
    print(f"JSON 메타데이터: {json_size:.2f} MB")
    print()

    # 첨부파일 디렉토리별 파일 수
    attach_dir = base_dir / 'data' / 'hira_cancer' / 'raw' / 'attachments'
    if attach_dir.exists():
        print("첨부파일 디렉토리:")
        for board_dir in sorted(attach_dir.iterdir()):
            if board_dir.is_dir():
                file_count = len(list(board_dir.glob('*')))
                print(f"  {board_dir.name:20s}: {file_count:3d}개 파일")

    print()
    print('=' * 80)

if __name__ == '__main__':
    analyze_data()
