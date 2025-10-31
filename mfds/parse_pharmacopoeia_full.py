#!/usr/bin/env python3
"""
대한민국 약전 전체 파싱 (Upstage API)

한글판 (hwpx) + 영문판 (docx) 모두 파싱
- 한글: 6개 파일 (~22MB)
- 영문: 8개 파일 (~24MB)
- 총: 14개 파일 (~46MB)
"""
import sys
from pathlib import Path
import time
import json
from datetime import datetime

# shared 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.parsers import create_parser


def parse_all_pharmacopoeia_files():
    """약전 전체 파일 파싱"""

    print("=" * 80)
    print("대한민국 약전 전체 파싱 (The Korean Pharmacopoeia)")
    print("=" * 80)

    # 파일 목록 정의
    base_dir = Path('data/mfds/raw/THE KOREAN PHARMACOPOEIA')

    files_to_parse = []

    # 한글판 (ko/)
    ko_dir = base_dir / 'ko'
    if ko_dir.exists():
        for hwpx_file in sorted(ko_dir.glob('*.hwpx')):
            files_to_parse.append({
                'path': hwpx_file,
                'lang': 'ko',
                'format': 'hwpx',
                'name': hwpx_file.stem
            })

    # 영문판 (en/)
    en_dir = base_dir / 'en'
    if en_dir.exists():
        for docx_file in sorted(en_dir.glob('*.docx')):
            files_to_parse.append({
                'path': docx_file,
                'lang': 'en',
                'format': 'docx',
                'name': docx_file.stem
            })

    if not files_to_parse:
        print("[ERROR] No files found!")
        return 1

    # 파일 목록 출력
    print(f"\n[FILES] Found {len(files_to_parse)} files to parse")

    total_size = 0
    for i, file_info in enumerate(files_to_parse, 1):
        file_size = file_info['path'].stat().st_size
        total_size += file_size
        print(f"  {i:2d}. [{file_info['lang']}] {file_info['name'][:60]:60s} "
              f"({file_size/1024/1024:.1f} MB)")

    print(f"\n[TOTAL] {total_size/1024/1024:.1f} MB")

    # 파서 생성
    print("\n[PARSER] Creating Upstage parser...")
    try:
        parser = create_parser("upstage")
    except Exception as e:
        print(f"[ERROR] Failed to create parser: {e}")
        return 1

    # 출력 디렉토리
    output_dir = Path('data/mfds/parsed')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 파싱 시작
    print("\n" + "=" * 80)
    print("PARSING")
    print("=" * 80)

    results = []
    success_count = 0
    error_count = 0
    total_pages = 0

    start_time = time.time()

    for i, file_info in enumerate(files_to_parse, 1):
        file_path = file_info['path']

        print(f"\n[{i}/{len(files_to_parse)}] {file_info['lang'].upper()}: {file_info['name']}")
        print(f"  Path: {file_path}")
        print(f"  Size: {file_path.stat().st_size / 1024:.1f} KB")

        try:
            # 파싱
            parse_start = time.time()
            result = parser.parse(file_path)
            parse_time = time.time() - parse_start

            pages = result.get('pages', 0)
            markdown_len = len(result.get('content', ''))
            html_len = len(result.get('html', ''))

            print(f"  [OK] SUCCESS ({parse_time:.1f}s)")
            print(f"    Pages: {pages}")
            print(f"    Markdown: {markdown_len:,} chars")
            print(f"    HTML: {html_len:,} chars")

            # 저장
            output_file = output_dir / f"{file_info['lang']}_{file_info['name']}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"    Saved: {output_file.name}")

            # 통계
            success_count += 1
            total_pages += pages

            results.append({
                'file': file_info['name'],
                'lang': file_info['lang'],
                'format': file_info['format'],
                'size_kb': file_path.stat().st_size / 1024,
                'pages': pages,
                'markdown_chars': markdown_len,
                'html_chars': html_len,
                'parse_time': parse_time,
                'status': 'success',
                'output_file': str(output_file)
            })

            # API 부하 방지: 짧은 대기
            if i < len(files_to_parse):
                time.sleep(1)

        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            error_count += 1

            results.append({
                'file': file_info['name'],
                'lang': file_info['lang'],
                'format': file_info['format'],
                'size_kb': file_path.stat().st_size / 1024,
                'status': 'error',
                'error': str(e)
            })

    # 완료
    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"\nTotal files: {len(files_to_parse)}")
    print(f"  Success: {success_count}")
    print(f"  Error: {error_count}")
    print(f"  Total pages: {total_pages}")
    print(f"  Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} min)")

    if success_count > 0:
        print(f"  Avg time per file: {elapsed/len(files_to_parse):.1f}s")

    # 언어별 통계
    print("\n[BY LANGUAGE]")
    for lang in ['ko', 'en']:
        lang_results = [r for r in results if r['lang'] == lang and r['status'] == 'success']
        if lang_results:
            total_pages_lang = sum(r['pages'] for r in lang_results)
            total_chars = sum(r['markdown_chars'] for r in lang_results)
            print(f"  {lang.upper()}: {len(lang_results)} files, {total_pages_lang} pages, "
                  f"{total_chars:,} chars")

    # 결과 저장
    summary_file = output_dir / 'parse_summary.json'
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(files_to_parse),
        'success': success_count,
        'error': error_count,
        'total_pages': total_pages,
        'elapsed_seconds': elapsed,
        'results': results
    }

    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nSummary saved: {summary_file}")

    # 에러 목록
    if error_count > 0:
        print("\n[ERRORS]")
        for r in results:
            if r['status'] == 'error':
                print(f"  - {r['file']}: {r.get('error', 'Unknown error')}")

    return 0 if error_count == 0 else 1


if __name__ == '__main__':
    sys.exit(parse_all_pharmacopoeia_files())
