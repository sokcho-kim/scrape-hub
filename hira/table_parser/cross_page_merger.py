"""
페이지 간 연속 표 병합기

문제:
- 하나의 표가 여러 페이지에 걸쳐 있음
- 페이지별로 파싱하면 데이터 무결성 손실

해결:
- bbox 좌표 유사성으로 동일 표 판단
- 헤더 일치 여부 검사
- 연속 페이지의 행을 하나의 표로 병합
"""
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pdfplumber


class TableSegment:
    """페이지별 표 조각"""
    def __init__(self, page_num: int, table_idx: int, bbox: Tuple, data: List[List], has_header: bool):
        self.page_num = page_num
        self.table_idx = table_idx
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.data = data
        self.has_header = has_header
        self.header = data[0] if has_header and data else None


class MergedTable:
    """병합된 표"""
    def __init__(self, segments: List[TableSegment]):
        self.segments = segments
        self.start_page = segments[0].page_num
        self.end_page = segments[-1].page_num
        self.pages = [s.page_num for s in segments]

        # 데이터 병합
        self.header = segments[0].header if segments[0].has_header else None
        self.rows = self._merge_rows()

    def _merge_rows(self) -> List[List]:
        """모든 세그먼트의 행 병합"""
        all_rows = []

        for i, segment in enumerate(self.segments):
            if i == 0:
                # 첫 세그먼트: 헤더 포함 전체
                all_rows.extend(segment.data)
            else:
                # 나머지: 헤더 제외
                if segment.has_header:
                    all_rows.extend(segment.data[1:])
                else:
                    all_rows.extend(segment.data)

        return all_rows

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'start_page': self.start_page,
            'end_page': self.end_page,
            'pages': self.pages,
            'num_pages': len(self.pages),
            'header': self.header,
            'rows': self.rows,
            'num_rows': len(self.rows) - (1 if self.header else 0),
            'num_cols': len(self.header) if self.header else (len(self.rows[0]) if self.rows else 0)
        }


def extract_table_segments(pdf_path: Path, page_range: Tuple[int, int] = None) -> List[TableSegment]:
    """
    PDF에서 표 조각 추출

    Args:
        pdf_path: PDF 파일 경로
        page_range: (start, end) 페이지 범위 (1-based), None이면 전체

    Returns:
        TableSegment 리스트
    """
    segments = []

    with pdfplumber.open(pdf_path) as pdf:
        if page_range:
            start, end = page_range
            pages = pdf.pages[start-1:end]
            page_nums = range(start, end+1)
        else:
            pages = pdf.pages
            page_nums = range(1, len(pdf.pages)+1)

        for page_num, page in zip(page_nums, pages):
            tables = page.find_tables()

            for table_idx, table in enumerate(tables):
                data = table.extract()

                # 유효한 행만 필터
                valid_data = [row for row in data if any(cell for cell in row)]

                if not valid_data:
                    continue

                # 헤더 감지 (휴리스틱)
                has_header = detect_header(valid_data)

                segment = TableSegment(
                    page_num=page_num,
                    table_idx=table_idx,
                    bbox=table.bbox,
                    data=valid_data,
                    has_header=has_header
                )

                segments.append(segment)

    return segments


def detect_header(data: List[List]) -> bool:
    """
    첫 행이 헤더인지 판단

    휴리스틱:
    - 첫 행의 셀이 모두 비어있지 않음
    - 첫 행과 두 번째 행의 문자열 길이 차이
    - 숫자 비율 (헤더는 주로 텍스트)
    """
    if len(data) < 2:
        return False

    first_row = data[0]
    second_row = data[1] if len(data) > 1 else []

    # 첫 행이 모두 비어있으면 헤더 아님
    if not any(cell for cell in first_row):
        return False

    # 첫 행의 숫자 비율
    num_count = sum(1 for cell in first_row if cell and str(cell).replace('.', '').replace(',', '').isdigit())
    num_ratio = num_count / len(first_row)

    # 헤더는 주로 텍스트 (숫자 비율 < 30%)
    if num_ratio < 0.3:
        return True

    return False


def is_continuation(seg_a: TableSegment, seg_b: TableSegment, threshold: float = 0.05) -> bool:
    """
    seg_b가 seg_a의 연속인지 판단

    조건:
    1. 연속 페이지 (page_b = page_a + 1)
    2. bbox x좌표 유사 (좌우 정렬)
    3. 헤더 일치 (seg_b도 헤더가 있으면 seg_a와 동일)
    4. 열 개수 일치
    """
    # 조건 1: 연속 페이지
    if seg_b.page_num != seg_a.page_num + 1:
        return False

    # 조건 2: bbox x좌표 유사성
    x0_a, _, x1_a, _ = seg_a.bbox
    x0_b, _, x1_b, _ = seg_b.bbox

    # 페이지 너비 대비 오차
    width_a = x1_a - x0_a
    x_diff = abs(x0_b - x0_a)

    if x_diff / width_a > threshold:
        return False

    # 조건 3: 헤더 일치
    if seg_a.has_header and seg_b.has_header:
        # 둘 다 헤더가 있으면 내용이 동일해야 함
        if seg_a.header != seg_b.header:
            return False

    # 조건 4: 열 개수 일치
    cols_a = len(seg_a.data[0]) if seg_a.data else 0
    cols_b = len(seg_b.data[0]) if seg_b.data else 0

    if cols_a != cols_b:
        return False

    return True


def merge_cross_page_tables(segments: List[TableSegment]) -> List[MergedTable]:
    """
    페이지 간 표 병합

    알고리즘:
    - 순차적으로 스캔
    - 연속 조건 만족 시 버퍼에 누적
    - 불일치 시 버퍼 flush 후 새 표 시작
    """
    merged_tables = []
    buffer = []

    for segment in segments:
        if not buffer:
            # 첫 세그먼트
            buffer.append(segment)
        elif is_continuation(buffer[-1], segment):
            # 연속 확인
            buffer.append(segment)
        else:
            # 불일치 → 버퍼 flush
            if buffer:
                merged_tables.append(MergedTable(buffer))
            buffer = [segment]

    # 마지막 버퍼 처리
    if buffer:
        merged_tables.append(MergedTable(buffer))

    return merged_tables


def analyze_cross_page_tables(pdf_path: Path, page_range: Tuple[int, int] = None) -> Dict[str, Any]:
    """
    페이지 간 표 분석

    Returns:
        통계 및 병합 결과
    """
    print(f"Extracting table segments from {pdf_path.name}...")
    segments = extract_table_segments(pdf_path, page_range)

    print(f"  Found {len(segments)} table segments")

    print("\nMerging cross-page tables...")
    merged_tables = merge_cross_page_tables(segments)

    print(f"  Result: {len(merged_tables)} merged tables")

    # 통계
    single_page = sum(1 for t in merged_tables if t.num_pages == 1)
    multi_page = sum(1 for t in merged_tables if t.num_pages > 1)
    max_pages = max((t.num_pages for t in merged_tables), default=0)

    total_rows_before = sum(len(s.data) for s in segments)
    total_rows_after = sum(len(t.rows) for t in merged_tables)

    stats = {
        'segments': len(segments),
        'merged_tables': len(merged_tables),
        'single_page_tables': single_page,
        'multi_page_tables': multi_page,
        'max_pages_in_table': max_pages,
        'total_rows_before': total_rows_before,
        'total_rows_after': total_rows_after,
        'tables': [t.to_dict() for t in merged_tables]
    }

    return stats


def main():
    """테스트"""
    base_dir = Path(__file__).parent.parent.parent
    pdf_path = base_dir / "data" / "hira" / "ebook" / "요양급여의 적용기준 및 방법에 관한 세부사항(약제) - 2025년 7월판(G000DB5-2025-94).pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    print("="*80)
    print("페이지 간 표 병합 테스트")
    print("="*80)

    # 샘플 범위 테스트 (p100-110)
    stats = analyze_cross_page_tables(pdf_path, page_range=(100, 110))

    print("\n" + "="*80)
    print("통계")
    print("="*80)
    print(f"원본 세그먼트: {stats['segments']}개")
    print(f"병합 후 표: {stats['merged_tables']}개")
    print(f"  - 단일 페이지: {stats['single_page_tables']}개")
    print(f"  - 다중 페이지: {stats['multi_page_tables']}개")
    print(f"  - 최대 연속 페이지: {stats['max_pages_in_table']}개")
    print(f"\n총 행 수:")
    print(f"  - 병합 전: {stats['total_rows_before']}행")
    print(f"  - 병합 후: {stats['total_rows_after']}행")

    # 다중 페이지 표 상세 출력
    print("\n" + "="*80)
    print("다중 페이지 표 상세")
    print("="*80)

    multi_page_tables = [t for t in stats['tables'] if t['num_pages'] > 1]

    for i, table in enumerate(multi_page_tables[:5]):  # 최대 5개
        print(f"\n표 {i+1}:")
        print(f"  페이지: {table['start_page']}-{table['end_page']} ({table['pages']})")
        print(f"  크기: {table['num_rows']}x{table['num_cols']}")
        print(f"  헤더: {table['header']}")
        if table['rows']:
            print(f"  첫 행: {table['rows'][1][:3] if len(table['rows']) > 1 else table['rows'][0][:3]}")


if __name__ == "__main__":
    main()
