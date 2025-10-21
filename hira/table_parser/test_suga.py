"""
수가표 PDF 샘플 테스트
- 건강보험요양급여비용.pdf (1,470p)
- 샘플 10페이지 선택 (다양한 위치)
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber
import camelot

# MVP 파서 함수 재사용
TABLE_ANCHOR_PATTERN = r'표\s*\d+(-\d+)?|도표\s*\d+|그림\s*\d+'
CODE_REF_PATTERN = r'고시\s*제?\d{4}-\d+|수가\s*[가-힣A-Z\d]+|\d{4}\.\d+\.\d+\.\s*개정|법률\s*제\d+호'


def detect_table_anchors_page(pdf_path: Path, page_num: int) -> List[Dict[str, Any]]:
    """단일 페이지 앵커 감지"""
    candidates = []

    with pdfplumber.open(pdf_path) as pdf:
        if page_num > len(pdf.pages):
            return candidates

        page = pdf.pages[page_num - 1]
        text = page.extract_text()

        if not text:
            return candidates

        matches = re.finditer(TABLE_ANCHOR_PATTERN, text)
        for match in matches:
            anchor = match.group()
            candidates.append({
                "page": page_num,
                "anchor": anchor,
                "score": 0.8,
                "has_anchor": True
            })

    return candidates


def parse_with_camelot(pdf_path: Path, page_num: int) -> List[Any]:
    """Camelot lattice로 페이지 파싱"""
    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages=str(page_num),
            flavor='lattice',
            line_scale=40
        )
        return tables
    except Exception as e:
        return []


def analyze_page(pdf_path: Path, page_num: int) -> Dict[str, Any]:
    """단일 페이지 분석"""
    result = {
        "page": page_num,
        "anchors": [],
        "tables_found": 0,
        "rows_extracted": 0,
        "camelot_success": False,
        "sample_rows": []
    }

    # 1. 앵커 감지
    anchors = detect_table_anchors_page(pdf_path, page_num)
    result["anchors"] = anchors

    # 2. Camelot 파싱
    tables = parse_with_camelot(pdf_path, page_num)

    if tables:
        result["camelot_success"] = True
        result["tables_found"] = len(tables)

        for table_idx, table in enumerate(tables):
            df = table.df
            if not df.empty:
                result["rows_extracted"] += len(df) - 1  # 헤더 제외

                # 샘플 행 저장 (최대 3행)
                headers = df.iloc[0].tolist()
                for i, row in enumerate(df.iloc[1:4].values):
                    result["sample_rows"].append({
                        "table_id": f"t{page_num}_{table_idx+1}",
                        "headers": headers,
                        "row": row.tolist()
                    })

    return result


def test_suga_sample():
    """수가표 PDF 샘플 테스트"""
    print("="*60)
    print("수가표 PDF 샘플 테스트 (10페이지)")
    print("="*60)

    # PDF 경로
    base_dir = Path(__file__).parent.parent.parent
    pdf_path = base_dir / "data" / "hira" / "ebook" / "2025년 1월판 건강보험요양급여비용-(G000A37-2025-16).pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    # 샘플 페이지 선택 (전략적 분산)
    sample_pages = [
        # 앞부분 (목차, 개요)
        10, 15, 20,
        # 수가표 시작 부분
        100, 105, 110,
        # 중간 복잡한 표
        200, 250, 300,
        # 뒷부분
        500
    ]

    print(f"\nPDF: {pdf_path.name}")
    print(f"샘플 페이지: {sample_pages}")
    print(f"\n{'='*60}\n")

    # 각 페이지 분석
    results = []
    for page_num in sample_pages:
        print(f"Page {page_num}:")
        result = analyze_page(pdf_path, page_num)
        results.append(result)

        print(f"  Anchors: {len(result['anchors'])} ({[a['anchor'] for a in result['anchors']]})")
        print(f"  Camelot: {'OK' if result['camelot_success'] else 'X'}")
        print(f"  Tables: {result['tables_found']}")
        print(f"  Rows: {result['rows_extracted']}")

        if result['sample_rows']:
            print(f"  Sample rows: {len(result['sample_rows'])} rows available")
        print()

    # 전체 요약
    print("="*60)
    print("전체 요약")
    print("="*60)

    total_anchors = sum(len(r['anchors']) for r in results)
    total_tables = sum(r['tables_found'] for r in results)
    total_rows = sum(r['rows_extracted'] for r in results)
    camelot_success_count = sum(1 for r in results if r['camelot_success'])

    print(f"샘플 페이지: {len(sample_pages)}")
    print(f"총 앵커: {total_anchors}")
    print(f"총 테이블: {total_tables}")
    print(f"총 행: {total_rows}")
    print(f"Camelot 성공: {camelot_success_count}/{len(sample_pages)} ({camelot_success_count/len(sample_pages)*100:.1f}%)")

    if total_anchors > 0:
        recall = total_tables / total_anchors if total_anchors > 0 else 0
        print(f"추정 Recall: {recall:.2%} ({total_tables}/{total_anchors})")

    # 결과 저장
    output_dir = base_dir / "data" / "hira" / "table_parser" / "mvp_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "suga_sample_test.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "sample_pages": sample_pages,
            "results": results,
            "summary": {
                "total_anchors": total_anchors,
                "total_tables": total_tables,
                "total_rows": total_rows,
                "camelot_success_rate": camelot_success_count / len(sample_pages)
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {output_path}")

    # 문제점 분석
    print("\n" + "="*60)
    print("발견된 문제점")
    print("="*60)

    no_anchor_pages = [r['page'] for r in results if len(r['anchors']) == 0]
    if no_anchor_pages:
        print(f"1. 앵커 없는 페이지: {no_anchor_pages}")

    anchor_but_no_table = [r['page'] for r in results if len(r['anchors']) > 0 and r['tables_found'] == 0]
    if anchor_but_no_table:
        print(f"2. 앵커는 있지만 표 파싱 실패: {anchor_but_no_table}")
        print(f"   원인: Camelot lattice가 격자선이 약한 표를 감지 못함")
        print(f"   해결책: Camelot stream 추가 필요")

    if total_tables > 0 and total_rows / total_tables < 5:
        print(f"3. 평균 행 수 부족: {total_rows/total_tables:.1f}행/표")
        print(f"   원인: 병합셀 또는 헤더 인식 문제")
        print(f"   해결책: 헤더 정규화 및 병합셀 처리 필요")


if __name__ == "__main__":
    test_suga_sample()
