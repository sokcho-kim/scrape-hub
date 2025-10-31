#!/usr/bin/env python3
"""
대한민국 약전 PDF 분할 파싱

PDF 파일을 50페이지씩 분할하여 Upstage API로 파싱
표 구조 보존을 위해 파일 단위로 분할
"""
import sys
from pathlib import Path
import json
import time
from datetime import datetime

# hira_cancer 파서 재사용
sys.path.insert(0, str(Path(__file__).parent.parent))
from hira_cancer.parsers.upstage_split_parser import UpstageSplitParser


def get_mfds_pdf_files():
    """MFDS 약전 PDF 파일 목록 반환"""
    base_dir = Path(__file__).parent.parent / "data/mfds/raw/THE KOREAN PHARMACOPOEIA"

    pdf_files = []

    # 영문 PDF
    en_dir = base_dir / "en"
    if en_dir.exists():
        pdf_files.extend(sorted(en_dir.glob("*.pdf")))

    # 한글 PDF
    ko_dir = base_dir / "ko"
    if ko_dir.exists():
        pdf_files.extend(sorted(ko_dir.glob("*.pdf")))

    if not pdf_files:
        print(f"[ERROR] No PDF files found in:")
        print(f"  {en_dir}")
        print(f"  {ko_dir}")
        return []

    return pdf_files


def main():
    """MFDS 약전 PDF 전체 파싱"""
    print("="*80)
    print("대한민국 약전 PDF 분할 파싱")
    print("="*80)

    # 1. PDF 파일 목록 확인
    pdf_files = get_mfds_pdf_files()
    if not pdf_files:
        return 1

    print(f"\n[FILES] Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        size_mb = pdf_file.stat().st_size / 1024 / 1024
        print(f"  - {pdf_file.name} ({size_mb:.1f} MB)")

    # 2. 출력 디렉토리 준비
    output_dir = Path(__file__).parent.parent / "data/mfds/parsed_pdf"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. 파서 초기화 (50페이지 청크)
    print("\n[PARSER] Initializing Upstage parser...")
    try:
        parser = UpstageSplitParser(chunk_size=50)
        print("  [OK] Parser ready (50 pages per chunk)")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return 1

    # 4. 각 PDF 파일 파싱
    total_start = time.time()
    results_summary = []

    for i, pdf_file in enumerate(pdf_files):
        print(f"\n{'='*80}")
        print(f"[{i+1}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print(f"{'='*80}")

        # 출력 파일 경로
        output_json = output_dir / f"{pdf_file.stem}.json"

        # 이미 파싱된 파일 스킵
        if output_json.exists():
            print(f"[SKIP] Already parsed: {output_json.name}")
            try:
                with open(output_json, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                result_summary = {
                    'file': pdf_file.name,
                    'status': 'skipped',
                    'pages': result.get('metadata', {}).get('total_pages', 0),
                    'content_length': len(result.get('content', '')),
                }
                results_summary.append(result_summary)
            except:
                pass
            continue

        try:
            # 파싱 실행
            file_start = time.time()
            parser.parse_large_pdf(
                pdf_path=str(pdf_file),
                output_path=str(output_json),
                output_format="html",
                keep_chunks=False  # 임시 PDF 청크 삭제
            )
            file_elapsed = time.time() - file_start

            # 결과 요약
            with open(output_json, 'r', encoding='utf-8') as f:
                result = json.load(f)

            result_summary = {
                'file': pdf_file.name,
                'status': 'success',
                'pages': result.get('metadata', {}).get('total_pages', 0),
                'chunks': result.get('metadata', {}).get('total_chunks', 1),
                'content_length': len(result.get('content', '')),
                'elapsed_seconds': file_elapsed
            }
            results_summary.append(result_summary)

            print(f"\n[OK] SUCCESS")
            print(f"  Pages: {result_summary['pages']}")
            print(f"  Chunks: {result_summary['chunks']}")
            print(f"  Content: {result_summary['content_length']} chars")
            print(f"  Time: {file_elapsed:.1f}s")

        except Exception as e:
            print(f"\n[ERROR] Failed to parse {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()

            result_summary = {
                'file': pdf_file.name,
                'status': 'error',
                'error': str(e),
                'elapsed_seconds': time.time() - file_start
            }
            results_summary.append(result_summary)

        # 파일 간 대기 (API rate limit)
        if i < len(pdf_files) - 1:
            print("\n[WAIT] 2 seconds before next file...")
            time.sleep(2)

    # 5. 전체 요약 저장
    total_elapsed = time.time() - total_start

    summary = {
        'parsed_at': datetime.now().isoformat(),
        'total_files': len(pdf_files),
        'successful': len([r for r in results_summary if r['status'] == 'success']),
        'failed': len([r for r in results_summary if r['status'] == 'error']),
        'skipped': len([r for r in results_summary if r['status'] == 'skipped']),
        'total_elapsed_seconds': total_elapsed,
        'results': results_summary
    }

    summary_path = output_dir / "parse_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 6. 최종 리포트
    print(f"\n{'='*80}")
    print("PARSING COMPLETE")
    print(f"{'='*80}")
    print(f"Total files: {summary['total_files']}")
    print(f"Success: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"\nOutput directory: {output_dir}")
    print(f"Summary: {summary_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
