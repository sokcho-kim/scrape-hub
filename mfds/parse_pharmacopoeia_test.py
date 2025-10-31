#!/usr/bin/env python3
"""
대한민국 약전 샘플 파싱 테스트

작은 파일로 Upstage API 품질 테스트
- 한글 hwpx: 통칙 (56K)
- 영문 docx: General Notices (52K)
"""
import sys
from pathlib import Path

# shared 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.parsers import create_parser
import json
from datetime import datetime


def test_sample_files():
    """샘플 파일 파싱 테스트"""

    # 테스트 파일
    test_files = [
        {
            'path': 'data/mfds/raw/THE KOREAN PHARMACOPOEIA/ko/[별표 1] 통칙 (제2023-40호).hwpx',
            'lang': 'ko',
            'format': 'hwpx',
            'name': '통칙'
        },
        {
            'path': 'data/mfds/raw/THE KOREAN PHARMACOPOEIA/en/02_[Appendix 1] General Notices.docx',
            'lang': 'en',
            'format': 'docx',
            'name': 'General Notices'
        }
    ]

    # 파서 생성
    parser = create_parser("upstage")

    results = []

    for file_info in test_files:
        file_path = Path(file_info['path'])

        if not file_path.exists():
            print(f"[SKIP] File not found: {file_path}")
            continue

        print("=" * 80)
        print(f"Testing: {file_info['name']} ({file_info['format']}, {file_info['lang']})")
        print(f"Path: {file_path}")
        print(f"Size: {file_path.stat().st_size / 1024:.1f} KB")
        print("=" * 80)

        try:
            # 파싱
            result = parser.parse(file_path)

            # 결과 출력
            print(f"\n[SUCCESS] Parsed successfully!")
            print(f"  Pages: {result.get('pages', 'N/A')}")
            print(f"  Model: {result.get('model', 'N/A')}")
            print(f"  Markdown length: {len(result.get('content', ''))} chars")
            print(f"  HTML length: {len(result.get('html', ''))} chars")

            # 미리보기
            content = result.get('content', '')
            preview_lines = content.split('\n')[:20]
            print(f"\n[PREVIEW] First 20 lines:")
            for i, line in enumerate(preview_lines, 1):
                print(f"  {i:2d} | {line[:100]}")

            # 저장
            output_dir = Path('data/mfds/parsed_test')
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / f"{file_info['name']}_{file_info['lang']}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"\n[SAVED] {output_file}")

            results.append({
                'file': file_info['name'],
                'lang': file_info['lang'],
                'format': file_info['format'],
                'pages': result.get('pages', 0),
                'markdown_chars': len(result.get('content', '')),
                'html_chars': len(result.get('html', '')),
                'status': 'success'
            })

        except Exception as e:
            print(f"\n[ERROR] {type(e).__name__}: {e}")
            results.append({
                'file': file_info['name'],
                'lang': file_info['lang'],
                'format': file_info['format'],
                'status': 'error',
                'error': str(e)
            })

    # 요약
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for r in results:
        if r['status'] == 'success':
            print(f"✓ {r['file']} ({r['format']}): {r['pages']} pages, "
                  f"{r['markdown_chars']} chars")
        else:
            print(f"✗ {r['file']} ({r['format']}): {r.get('error', 'Unknown error')}")

    # 결과 저장
    summary_file = Path('data/mfds/parsed_test/test_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\nSummary saved: {summary_file}")


if __name__ == '__main__':
    test_sample_files()
