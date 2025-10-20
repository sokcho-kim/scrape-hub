"""
HIRA EBOOK PDF 파싱 (Upstage 사용)

기존 shared/parsers.py의 UpstageParser 활용
"""
from pathlib import Path
import json
import sys
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.parsers import create_parser


def parse_ebook():
    """HIRA EBOOK PDF 파일들을 Upstage로 파싱"""

    ebook_dir = Path('data/hira/ebook')
    parsed_dir = Path('data/hira/parsed')
    parsed_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted([f for f in ebook_dir.glob('*.pdf')])

    print(f'=== HIRA EBOOK Upstage 파싱 시작 ===')
    print(f'총 {len(pdf_files)}개 PDF 파일\n')

    # Upstage 파서 생성
    parser = create_parser('upstage')

    results = []
    success_count = 0
    failed_count = 0
    total_pages = 0

    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f'[{idx}/{len(pdf_files)}] {pdf_file.name[:60]}...')

        try:
            # Upstage로 파싱
            result = parser.parse(pdf_file)

            # 메타데이터 추가
            result['filename'] = pdf_file.name
            result['file_size_mb'] = round(pdf_file.stat().st_size / 1024 / 1024, 1)
            result['parsed_at'] = datetime.now().isoformat()

            # 파싱 결과 저장
            output_file = parsed_dir / f'{pdf_file.stem}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            pages = result.get('pages', 0)
            total_pages += pages
            success_count += 1

            print(f'  OK: {pages} pages')
            print(f'  Saved: {output_file.name}')

            results.append({
                'filename': pdf_file.name,
                'status': 'success',
                'pages': pages,
                'output_file': output_file.name
            })

        except Exception as e:
            print(f'  ERROR: {e}')
            failed_count += 1
            results.append({
                'filename': pdf_file.name,
                'status': 'failed',
                'error': str(e)
            })

        print()

    # 요약
    print('=' * 80)
    print('=== 파싱 완료 ===')
    print(f'성공: {success_count}/{len(pdf_files)} 파일')
    print(f'실패: {failed_count}/{len(pdf_files)} 파일')
    print(f'총 페이지: {total_pages} pages')

    # 예상 비용 계산 (페이지당 $0.01)
    estimated_cost = total_pages * 0.01
    print(f'예상 비용: ${estimated_cost:.2f} (약 ₩{int(estimated_cost * 1300):,})')

    # 요약 저장
    summary = {
        'parsed_at': datetime.now().isoformat(),
        'total_files': len(pdf_files),
        'success': success_count,
        'failed': failed_count,
        'total_pages': total_pages,
        'estimated_cost_usd': round(estimated_cost, 2),
        'files': results
    }

    summary_file = ebook_dir / 'upstage_parsing_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f'\n요약 저장: {summary_file}')

    return results


if __name__ == '__main__':
    parse_ebook()
