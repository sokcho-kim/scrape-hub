"""
Phase 1: HIRA EBOOK PDF 품질 분석 (pdfplumber)

목적:
- 전체 PDF 텍스트 추출
- 품질 지표 계산
- 그룹 A/B/C 자동 분류
- Upstage 필요 여부 판단
"""
import pdfplumber
from pathlib import Path
import json
from datetime import datetime


def analyze_pdf_quality(pdf_path: Path) -> dict:
    """
    PDF 파일의 텍스트 추출 품질 분석

    Returns:
        품질 분석 결과
    """
    # 파일명 안전하게 출력 (인코딩 오류 방지)
    try:
        # ASCII 범위 문자만 추출
        safe_name = ''.join(c if ord(c) < 128 else '?' for c in pdf_path.name[:60])
        print(f"  Analyzing: {safe_name}...")
    except:
        print(f"  Analyzing file...")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            total_chars = 0
            total_words = 0
            page_quality = []
            low_quality_pages = []
            table_pages = []

            # 전체 페이지 분석
            for page_num, page in enumerate(pdf.pages, 1):
                # 텍스트 추출
                text = page.extract_text()

                if text:
                    chars = len(text)
                    words = len(text.split())
                    total_chars += chars
                    total_words += words

                    # 페이지별 품질 지표
                    page_quality.append({
                        'page': page_num,
                        'chars': chars,
                        'words': words
                    })

                    # 저품질 페이지 감지 (50자 미만)
                    if chars < 50:
                        low_quality_pages.append(page_num)
                else:
                    page_quality.append({
                        'page': page_num,
                        'chars': 0,
                        'words': 0
                    })
                    low_quality_pages.append(page_num)

                # 표 감지
                tables = page.extract_tables()
                if tables and len(tables) > 0:
                    table_pages.append(page_num)

            # 평균 계산
            avg_chars_per_page = total_chars / num_pages if num_pages > 0 else 0
            avg_words_per_page = total_words / num_pages if num_pages > 0 else 0

            # 품질 점수 (0-100)
            quality_score = min(100, avg_chars_per_page / 5)  # 500자 = 100점

            # 저품질 비율
            low_quality_ratio = len(low_quality_pages) / num_pages if num_pages > 0 else 0

            result = {
                'filename': pdf_path.name,
                'file_size_mb': round(pdf_path.stat().st_size / 1024 / 1024, 1),
                'pages': num_pages,
                'total_chars': total_chars,
                'total_words': total_words,
                'avg_chars_per_page': round(avg_chars_per_page, 1),
                'avg_words_per_page': round(avg_words_per_page, 1),
                'quality_score': round(quality_score, 1),
                'low_quality_pages': low_quality_pages,
                'low_quality_ratio': round(low_quality_ratio * 100, 1),
                'table_pages': table_pages,
                'table_count': len(table_pages),
                'status': 'success'
            }

            print(f"    OK: {num_pages}p, {total_chars:,} chars, avg {avg_chars_per_page:.0f} chars/page")
            print(f"    Quality: {quality_score:.0f}/100, Low-Q pages: {len(low_quality_pages)}, Tables: {len(table_pages)}")

            return result

    except Exception as e:
        print(f"    ERROR: {e}")
        return {
            'filename': pdf_path.name,
            'status': 'failed',
            'error': str(e)
        }


def classify_group(analysis: dict) -> str:
    """
    품질 분석 결과로 그룹 분류

    Returns:
        'A': pdfplumber만으로 충분
        'B': 부분 Upstage 필요
        'C': 전체 Upstage 필요
    """
    if analysis['status'] == 'failed':
        return 'C'

    avg_chars = analysis['avg_chars_per_page']
    low_quality_ratio = analysis['low_quality_ratio']

    # 그룹 C: 전체 Upstage (심각)
    if avg_chars < 50:
        return 'C'

    # 그룹 B: 부분 Upstage (중간)
    if avg_chars < 200 or low_quality_ratio > 10:
        return 'B'

    # 그룹 A: pdfplumber 충분
    return 'A'


def estimate_upstage_cost(analysis: dict, group: str) -> dict:
    """
    Upstage 사용 시 예상 비용 계산

    Returns:
        {
            'pages': 처리할 페이지 수,
            'cost_usd': 예상 비용 (USD),
            'cost_krw': 예상 비용 (KRW)
        }
    """
    if group == 'A':
        # pdfplumber만 사용
        return {'pages': 0, 'cost_usd': 0, 'cost_krw': 0}

    elif group == 'B':
        # 저품질 페이지만 Upstage
        pages = len(analysis.get('low_quality_pages', []))
        cost_usd = pages * 0.01
        cost_krw = int(cost_usd * 1300)
        return {'pages': pages, 'cost_usd': cost_usd, 'cost_krw': cost_krw}

    else:  # group == 'C'
        # 전체 Upstage
        pages = analysis.get('pages', 0)
        cost_usd = pages * 0.01
        cost_krw = int(cost_usd * 1300)
        return {'pages': pages, 'cost_usd': cost_usd, 'cost_krw': cost_krw}


def main():
    """Phase 1 실행: 전체 PDF 분석"""

    ebook_dir = Path('data/hira/ebook')
    pdf_files = sorted([f for f in ebook_dir.glob('*.pdf')])

    print('=' * 80)
    print('PHASE 1: HIRA EBOOK 품질 분석 (pdfplumber)')
    print('=' * 80)
    print(f'\n총 {len(pdf_files)}개 PDF 파일 분석 시작...\n')

    results = []

    # 각 PDF 분석
    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f'[{idx}/{len(pdf_files)}]')
        analysis = analyze_pdf_quality(pdf_file)

        # 그룹 분류
        if analysis['status'] == 'success':
            group = classify_group(analysis)
            cost_estimate = estimate_upstage_cost(analysis, group)

            analysis['group'] = group
            analysis['upstage_cost'] = cost_estimate

            print(f"    Group: {group}, Upstage cost: ${cost_estimate['cost_usd']:.2f}\n")
        else:
            analysis['group'] = 'C'
            analysis['upstage_cost'] = {'pages': 0, 'cost_usd': 0, 'cost_krw': 0}
            print()

        results.append(analysis)

    # 통계 계산
    print('=' * 80)
    print('분석 완료 - 요약')
    print('=' * 80)

    group_a = [r for r in results if r.get('group') == 'A']
    group_b = [r for r in results if r.get('group') == 'B']
    group_c = [r for r in results if r.get('group') == 'C']

    print(f'\n그룹 A (pdfplumber 충분): {len(group_a)}개')
    for r in group_a:
        try:
            safe_name = ''.join(c if ord(c) < 128 else '?' for c in r["filename"][:50])
            print(f'  - {safe_name}... ({r["pages"]}p)')
        except:
            print(f'  - [File] ({r["pages"]}p)')

    print(f'\n그룹 B (부분 Upstage): {len(group_b)}개')
    for r in group_b:
        cost = r['upstage_cost']
        try:
            safe_name = ''.join(c if ord(c) < 128 else '?' for c in r["filename"][:50])
            print(f'  - {safe_name}... ({cost["pages"]}p → ${cost["cost_usd"]:.2f})')
        except:
            print(f'  - [File] ({cost["pages"]}p → ${cost["cost_usd"]:.2f})')

    print(f'\n그룹 C (전체 Upstage): {len(group_c)}개')
    for r in group_c:
        cost = r['upstage_cost']
        try:
            safe_name = ''.join(c if ord(c) < 128 else '?' for c in r["filename"][:50])
            print(f'  - {safe_name}... ({cost["pages"]}p → ${cost["cost_usd"]:.2f})')
        except:
            print(f'  - [File] ({cost["pages"]}p → ${cost["cost_usd"]:.2f})')

    # 총 비용 계산
    total_cost_usd = sum(r['upstage_cost']['cost_usd'] for r in results)
    total_cost_krw = sum(r['upstage_cost']['cost_krw'] for r in results)
    total_pages = sum(r.get('pages', 0) for r in results if r['status'] == 'success')
    upstage_pages = sum(r['upstage_cost']['pages'] for r in results)

    print(f'\n' + '=' * 80)
    print('비용 예상')
    print('=' * 80)
    print(f'총 페이지: {total_pages:,}p')
    print(f'Upstage 처리: {upstage_pages:,}p ({upstage_pages/total_pages*100:.1f}%)')
    print(f'예상 비용: ${total_cost_usd:.2f} (약 {total_cost_krw:,}원)')

    # 결과 저장
    output = {
        'analyzed_at': datetime.now().isoformat(),
        'total_files': len(pdf_files),
        'total_pages': total_pages,
        'summary': {
            'group_a': len(group_a),
            'group_b': len(group_b),
            'group_c': len(group_c),
            'upstage_pages': upstage_pages,
            'total_cost_usd': round(total_cost_usd, 2),
            'total_cost_krw': total_cost_krw
        },
        'files': results
    }

    output_file = ebook_dir / 'analysis_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n분석 결과 저장: {output_file}')
    print('\nPhase 1 완료! 다음 단계로 진행하세요.')


if __name__ == '__main__':
    main()
