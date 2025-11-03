#!/usr/bin/env python3
"""
변환된 PDF 파일과 실패 목록 매칭 검증
"""
import json
from pathlib import Path


def verify_pdf_files():
    """PDF 파일과 실패 목록 비교"""

    base_dir = Path(__file__).parent.parent

    # 실패 목록 로드
    retry_summary = base_dir / 'data/hira_rulesvc/parsed/retry_summary.json'
    with open(retry_summary, 'r', encoding='utf-8') as f:
        summary = json.load(f)

    failed_files = summary.get('failed_files', [])

    # 실패한 HWP 파일명 (확장자 제외)
    failed_stems = set()
    for item in failed_files:
        hwp_path = Path(item['path'])
        failed_stems.add(hwp_path.stem)

    print("=" * 80)
    print("실패 목록 vs 변환된 PDF 검증")
    print("=" * 80)
    print(f"\n[실패 목록] {len(failed_stems)}개:")
    for stem in sorted(failed_stems):
        print(f"  - {stem}")

    # PDF 파일 목록
    pdf_dir = base_dir / 'data/hira_rulesvc/documents'
    pdf_files = sorted(pdf_dir.glob('*.pdf'))

    pdf_stems = set()
    for pdf_file in pdf_files:
        pdf_stems.add(pdf_file.stem)

    print(f"\n[변환된 PDF] {len(pdf_files)}개:")
    for stem in sorted(pdf_stems):
        print(f"  - {stem}")

    # 매칭 검증
    matched = failed_stems & pdf_stems
    missing = failed_stems - pdf_stems
    extra = pdf_stems - failed_stems

    print("\n" + "=" * 80)
    print("매칭 결과")
    print("=" * 80)
    print(f"✓ 매칭됨: {len(matched)}개")
    print(f"✗ 누락됨: {len(missing)}개")
    print(f"+ 추가됨: {len(extra)}개")

    if missing:
        print("\n[누락된 파일]")
        for stem in sorted(missing):
            print(f"  - {stem}.hwp → PDF 변환 필요")

    if extra:
        print("\n[추가 파일 (실패 목록에 없음)]")
        for stem in sorted(extra):
            print(f"  + {stem}.pdf")

    print("\n" + "=" * 80)

    if len(matched) == len(failed_stems):
        print("✓ 모든 파일이 PDF로 변환되었습니다!")
        if extra:
            print(f"  (추가로 {len(extra)}개 파일도 발견되었습니다)")
        return True
    else:
        print(f"✗ {len(missing)}개 파일이 아직 변환되지 않았습니다.")
        return False


if __name__ == '__main__':
    import sys
    success = verify_pdf_files()
    sys.exit(0 if success else 1)
