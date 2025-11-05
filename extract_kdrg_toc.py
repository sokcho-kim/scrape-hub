"""
KDRG 분류집 목차 추출 및 구조 분석
PyMuPDF(fitz)를 사용하여 목차와 섹션 구조 파악
"""
import sys
import codecs
from pathlib import Path
import json
import fitz  # PyMuPDF

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def extract_toc(pdf_path: Path):
    """PDF에서 목차(TOC) 추출"""

    print('='*80)
    print('📚 KDRG 분류집 목차 추출')
    print('='*80)
    print(f'\n파일: {pdf_path.name}\n')

    # PDF 열기
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    print(f'총 페이지: {total_pages}p\n')

    # 1. 내장된 TOC 추출
    print('[1] 내장 목차(TOC) 추출')
    toc = doc.get_toc()

    if toc:
        print(f'  ✅ {len(toc)}개 항목 발견\n')

        # 목차 구조 출력
        print('[목차 구조 (처음 50개)]')
        for i, item in enumerate(toc[:50], 1):
            level, title, page = item
            indent = '  ' * (level - 1)
            print(f'{i:3d}. {indent}[Lv{level}] {title} (p.{page})')

        if len(toc) > 50:
            print(f'\n... (총 {len(toc)}개 중 50개만 표시)')
    else:
        print('  ❌ 내장 목차 없음')
        print('  💡 텍스트 기반으로 목차 추출 시도...\n')

        # 내장 TOC가 없으면 텍스트에서 추출
        toc = extract_toc_from_text(doc)

    # 2. MDC 구조 분석
    print(f'\n\n[2] MDC 구조 분석')

    mdc_sections = []
    current_mdc = None

    for item in toc:
        level, title, page = item

        # MDC 01, MDC 02 등의 패턴 찾기
        if 'MDC' in title and level <= 2:
            if current_mdc:
                mdc_sections.append(current_mdc)

            current_mdc = {
                'title': title,
                'start_page': page,
                'end_page': None,
                'subsections': []
            }
        elif current_mdc and level <= 3:
            # MDC의 하위 섹션
            current_mdc['subsections'].append({
                'title': title,
                'page': page,
                'level': level
            })

    # 마지막 MDC 추가
    if current_mdc:
        mdc_sections.append(current_mdc)

    # MDC 종료 페이지 계산
    for i, mdc in enumerate(mdc_sections):
        if i < len(mdc_sections) - 1:
            mdc['end_page'] = mdc_sections[i + 1]['start_page'] - 1
        else:
            mdc['end_page'] = total_pages

    # MDC 통계
    print(f'  발견된 MDC: {len(mdc_sections)}개\n')

    for i, mdc in enumerate(mdc_sections[:10], 1):
        pages = mdc['end_page'] - mdc['start_page'] + 1
        subsec_count = len(mdc['subsections'])
        print(f'  {i:2d}. {mdc["title"]:50s} p.{mdc["start_page"]:4d}-{mdc["end_page"]:4d} ({pages:3d}p, {subsec_count:2d}개 하위섹션)')

    if len(mdc_sections) > 10:
        print(f'\n  ... (총 {len(mdc_sections)}개 중 10개만 표시)')

    # 3. 분할 전략 제안
    print(f'\n\n[3] 지능형 분할 전략 제안')

    target_chunk_size = 50  # 목표 청크 크기
    suggested_chunks = []

    for mdc in mdc_sections:
        pages = mdc['end_page'] - mdc['start_page'] + 1

        # MDC가 target_chunk_size보다 작으면 그대로
        if pages <= target_chunk_size:
            suggested_chunks.append({
                'name': mdc['title'],
                'start': mdc['start_page'],
                'end': mdc['end_page'],
                'pages': pages,
                'type': 'mdc'
            })
        else:
            # MDC가 크면 하위섹션으로 분할
            if mdc['subsections']:
                # 하위섹션 기준으로 분할
                for j, subsec in enumerate(mdc['subsections']):
                    if j < len(mdc['subsections']) - 1:
                        end = mdc['subsections'][j + 1]['page'] - 1
                    else:
                        end = mdc['end_page']

                    sub_pages = end - subsec['page'] + 1

                    suggested_chunks.append({
                        'name': f"{mdc['title']} - {subsec['title']}",
                        'start': subsec['page'],
                        'end': end,
                        'pages': sub_pages,
                        'type': 'subsection'
                    })
            else:
                # 하위섹션이 없으면 균등 분할
                num_chunks = (pages + target_chunk_size - 1) // target_chunk_size
                chunk_size = pages // num_chunks

                for j in range(num_chunks):
                    start = mdc['start_page'] + j * chunk_size
                    end = min(start + chunk_size - 1, mdc['end_page'])

                    suggested_chunks.append({
                        'name': f"{mdc['title']} Part {j+1}",
                        'start': start,
                        'end': end,
                        'pages': end - start + 1,
                        'type': 'split'
                    })

    print(f'  제안된 청크 수: {len(suggested_chunks)}개')
    print(f'  평균 페이지: {sum(c["pages"] for c in suggested_chunks) / len(suggested_chunks):.1f}p\n')

    # 청크별 상세 정보
    print('[제안된 분할 (처음 20개)]')
    for i, chunk in enumerate(suggested_chunks[:20], 1):
        chunk_type = {'mdc': '📚', 'subsection': '📖', 'split': '📄'}[chunk['type']]
        print(f'  {i:2d}. {chunk_type} {chunk["name"]:60s} p.{chunk["start"]:4d}-{chunk["end"]:4d} ({chunk["pages"]:3d}p)')

    if len(suggested_chunks) > 20:
        print(f'\n  ... (총 {len(suggested_chunks)}개 중 20개만 표시)')

    # 4. 결과 저장
    output = {
        'source_file': pdf_path.name,
        'total_pages': total_pages,
        'toc_entries': len(toc),
        'mdc_count': len(mdc_sections),
        'suggested_chunks': len(suggested_chunks),
        'toc': [{'level': item[0], 'title': item[1], 'page': item[2]} for item in toc],
        'mdc_sections': mdc_sections,
        'suggested_chunks': suggested_chunks
    }

    output_file = Path('data/hira_master/kdrg_structure.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n\n💾 구조 정보 저장: {output_file}')

    doc.close()

    return output


def extract_toc_from_text(doc):
    """텍스트에서 목차 추출 (내장 TOC가 없을 경우)"""

    print('  [텍스트 기반 목차 추출]')

    toc = []

    # 목차 페이지 추정 (보통 처음 20페이지 내)
    for page_num in range(min(30, len(doc))):
        page = doc[page_num]
        text = page.get_text()

        lines = text.split('\n')

        for line in lines:
            line = line.strip()

            # MDC 패턴 찾기
            if line.startswith('MDC') or 'ADRG' in line or 'PreMDC' in line:
                # 페이지 번호 추출 시도
                parts = line.split('···')
                if len(parts) >= 2:
                    try:
                        page_no = int(parts[-1].strip())
                        title = parts[0].strip()
                        toc.append([1, title, page_no])
                    except:
                        pass

    print(f'    ✅ {len(toc)}개 항목 추출')

    return toc


def main():
    pdf_path = Path('data/hira_master/KDRG 분류집(신포괄지불제도용 ver1.4).pdf')

    if not pdf_path.exists():
        print(f'❌ 파일 없음: {pdf_path}')
        return

    result = extract_toc(pdf_path)

    print('\n\n' + '='*80)
    print('✅ 완료')
    print('='*80)

    print(f'\n📊 요약:')
    print(f'  - 총 페이지: {result["total_pages"]:,}p')
    print(f'  - 목차 항목: {result["toc_entries"]:,}개')
    print(f'  - MDC 섹션: {result["mdc_count"]}개')
    print(f'  - 제안 청크: {result["suggested_chunks"]}개')
    print(f'  - 평균 청크 크기: {sum(c["pages"] for c in result["suggested_chunks"]) / len(result["suggested_chunks"]):.1f}p')


if __name__ == '__main__':
    main()
