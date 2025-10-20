"""
HIRA EBOOK PDF 파싱 및 분석
"""
import pdfplumber
from pathlib import Path
import json

def parse_pdfs():
    ebook_dir = Path('data/hira/ebook')
    pdf_files = sorted([f for f in ebook_dir.glob('*.pdf')])

    print('=== HIRA EBOOK 파싱 시작 ===')
    print(f'총 {len(pdf_files)}개 파일 처리 중...\n')

    results = []

    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f'[{idx}/{len(pdf_files)}] Processing...')

        try:
            with pdfplumber.open(pdf_file) as pdf:
                num_pages = len(pdf.pages)

                # 첫 페이지 텍스트 추출
                first_page_text = pdf.pages[0].extract_text() if num_pages > 0 else ''

                # 전체 텍스트 길이 추정 (처음 5페이지만 샘플링)
                sample_text = ''
                sample_pages = min(5, num_pages)
                for i in range(sample_pages):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        sample_text += page_text

                avg_chars_per_page = len(sample_text) // sample_pages if sample_pages > 0 else 0
                estimated_total = avg_chars_per_page * num_pages

                file_info = {
                    'filename': pdf_file.name,
                    'size_mb': round(pdf_file.stat().st_size / 1024 / 1024, 1),
                    'pages': num_pages,
                    'avg_chars_per_page': avg_chars_per_page,
                    'estimated_total_chars': estimated_total,
                    'first_page_preview': first_page_text[:500] if first_page_text else ''
                }

                results.append(file_info)
                print(f'  OK: {num_pages} pages, ~{estimated_total:,} chars')

        except Exception as e:
            print(f'  ERROR: {e}')
            results.append({
                'filename': pdf_file.name,
                'error': str(e)
            })

    # 통계
    print('\n' + '=' * 80)
    print('=== 파싱 완료 ===')
    total_files = len(results)
    success_files = len([r for r in results if 'error' not in r])
    total_size = sum(r.get('size_mb', 0) for r in results)
    total_pages = sum(r.get('pages', 0) for r in results)
    total_chars = sum(r.get('estimated_total_chars', 0) for r in results)

    print(f'성공: {success_files}/{total_files} 파일')
    print(f'총 용량: {total_size:.1f} MB')
    print(f'총 페이지: {total_pages:,} 페이지')
    print(f'예상 글자 수: {total_chars:,} 글자 (약 {total_chars / 1000000:.1f}M 글자)')

    # JSON 저장
    output_file = ebook_dir / 'parsing_summary.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_files': total_files,
                'success_files': success_files,
                'total_size_mb': total_size,
                'total_pages': total_pages,
                'estimated_total_chars': total_chars
            },
            'files': results
        }, f, ensure_ascii=False, indent=2)

    print(f'\n메타데이터 저장: {output_file}')

    return results

if __name__ == '__main__':
    parse_pdfs()
