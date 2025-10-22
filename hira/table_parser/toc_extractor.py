"""
목차 추출기 - 의료 문서 섹션 구조 파악

목적:
- PDF에서 목차 페이지 감지
- 섹션명-페이지 범위 매핑
- 복잡도 추정 (표 밀도, 중첩 여부)
"""
import re
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber


def extract_toc(pdf_path: Path, max_pages: int = 20) -> List[Dict[str, Any]]:
    """
    목차 추출

    Args:
        pdf_path: PDF 파일 경로
        max_pages: 목차 검색 범위 (기본 20페이지)

    Returns:
        섹션 리스트 [{"title": "...", "start_page": N, "end_page": M}]
    """
    sections = []

    with pdfplumber.open(pdf_path) as pdf:
        # 목차 페이지 찾기
        toc_pages = find_toc_pages(pdf, max_pages)

        if not toc_pages:
            print("WARNING: No TOC found. Using heuristic section detection.")
            return detect_sections_heuristic(pdf)

        # 목차에서 섹션 추출
        for page_num in toc_pages:
            page = pdf.pages[page_num]
            text = page.extract_text()

            # 패턴: "제1장 .... 10" 또는 "1. 약제 급여 목록 .... 50"
            patterns = [
                r'제?\s*(\d+)\s*[장절편부]\s+([^\n.]{5,50})\s*\.{2,}\s*(\d+)',  # 제1장 ... 10
                r'(\d+)\.\s+([^\n.]{5,50})\s*\.{2,}\s*(\d+)',  # 1. 제목 ... 10
                r'([가-힣]{2,20})\s*\.{2,}\s*(\d+)',  # 한글 제목 ... 10
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, text, re.MULTILINE)
                for match in matches:
                    if len(match.groups()) == 3:
                        section_num, title, page_num = match.groups()
                        sections.append({
                            'section_num': section_num,
                            'title': title.strip(),
                            'start_page': int(page_num)
                        })
                    elif len(match.groups()) == 2:
                        title, page_num = match.groups()
                        sections.append({
                            'section_num': None,
                            'title': title.strip(),
                            'start_page': int(page_num)
                        })

    # end_page 계산
    for i in range(len(sections) - 1):
        sections[i]['end_page'] = sections[i + 1]['start_page'] - 1

    if sections:
        # 마지막 섹션은 문서 끝까지
        with pdfplumber.open(pdf_path) as pdf:
            sections[-1]['end_page'] = len(pdf.pages)

    return sections


def find_toc_pages(pdf, max_pages: int) -> List[int]:
    """
    목차 페이지 번호 찾기

    패턴: "목차", "Contents", "차례" 등의 제목
    """
    toc_pages = []

    for i in range(min(max_pages, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text()

        if not text:
            continue

        # 첫 100자 내에 목차 키워드
        first_100 = text[:100].upper()

        if any(keyword in first_100 for keyword in ['목차', 'CONTENTS', '차례', 'INDEX']):
            toc_pages.append(i)

    return toc_pages


def detect_sections_heuristic(pdf) -> List[Dict[str, Any]]:
    """
    목차가 없을 경우 휴리스틱으로 섹션 감지

    방법:
    - 큰 폰트 텍스트 (제목)
    - "제N장", "제N절" 패턴
    - 페이지 번호 급변 (새 섹션 시작)
    """
    sections = []

    # 구현 생략 (필요 시 추가)
    print("TODO: Implement heuristic section detection")

    return sections


def estimate_section_complexity(pdf_path: Path, section: Dict) -> Dict[str, Any]:
    """
    섹션 복잡도 추정

    메트릭:
    - 표 밀도 (표 수 / 페이지 수)
    - 중첩 테이블 비율
    - 평균 표 크기 (행 × 열)
    """
    start = section['start_page'] - 1  # 0-based
    end = section['end_page']

    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[start:end]

        total_tables = 0
        nested_tables = 0
        total_rows = 0

        for page in pages:
            tables = page.find_tables()
            total_tables += len(tables)

            # 중첩 테이블 감지 (간단한 휴리스틱)
            for i, table_a in enumerate(tables):
                for j, table_b in enumerate(tables):
                    if i != j and is_nested(table_a.bbox, table_b.bbox):
                        nested_tables += 1
                        break

            # 행 수 추정
            for table in tables:
                data = table.extract()
                total_rows += len([row for row in data if any(cell for cell in row)])

        num_pages = len(pages)

        complexity = {
            'section': section['title'],
            'pages': num_pages,
            'tables': total_tables,
            'table_density': total_tables / num_pages if num_pages > 0 else 0,
            'nested_ratio': nested_tables / total_tables if total_tables > 0 else 0,
            'avg_rows_per_table': total_rows / total_tables if total_tables > 0 else 0,
            'complexity_score': 0.0  # 계산 예정
        }

        # 복잡도 점수 (0-100)
        score = 0
        score += min(complexity['table_density'] * 20, 40)  # 최대 40점
        score += complexity['nested_ratio'] * 30  # 최대 30점
        score += min(complexity['avg_rows_per_table'] / 10 * 30, 30)  # 최대 30점

        complexity['complexity_score'] = score
        complexity['requires_upstage'] = score > 50  # 50점 이상이면 Upstage 권장

        return complexity


def is_nested(bbox_a, bbox_b) -> bool:
    """
    bbox_b가 bbox_a 내부에 있는지 확인

    bbox: (x0, y0, x1, y1)
    """
    x0_a, y0_a, x1_a, y1_a = bbox_a
    x0_b, y0_b, x1_b, y1_b = bbox_b

    # bbox_b가 bbox_a 내부
    return (x0_a < x0_b and y0_a < y0_b and x1_b < x1_a and y1_b < y1_a)


def main():
    """테스트"""
    base_dir = Path(__file__).parent.parent.parent
    pdf_path = base_dir / "data" / "hira" / "ebook" / "요양급여의 적용기준 및 방법에 관한 세부사항(약제) - 2025년 7월판(G000DB5-2025-94).pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    print("="*80)
    print("목차 추출 테스트")
    print("="*80)

    sections = extract_toc(pdf_path)

    print(f"\n발견된 섹션: {len(sections)}개")

    for section in sections[:10]:  # 처음 10개만
        print(f"\n{section.get('section_num', '-')}. {section['title']}")
        print(f"   페이지: {section['start_page']}-{section['end_page']}")

    # 복잡도 추정 (첫 3개 섹션)
    if sections:
        print("\n" + "="*80)
        print("복잡도 분석 (샘플 3개)")
        print("="*80)

        for section in sections[:3]:
            complexity = estimate_section_complexity(pdf_path, section)

            print(f"\n{complexity['section']}")
            print(f"  페이지: {complexity['pages']}")
            print(f"  표: {complexity['tables']}개")
            print(f"  표 밀도: {complexity['table_density']:.2f} (표/페이지)")
            print(f"  중첩 비율: {complexity['nested_ratio']:.1%}")
            print(f"  복잡도: {complexity['complexity_score']:.1f}/100")
            print(f"  Upstage 권장: {'YES' if complexity['requires_upstage'] else 'NO'}")


if __name__ == "__main__":
    main()
