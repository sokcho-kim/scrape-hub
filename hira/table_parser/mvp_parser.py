"""
MVP: 텍스트 앵커 감지 + Camelot Lattice 파싱
Phase: Option C - Step 1 (2시간)

목표:
- 텍스트 앵커 (표 N, 도표 N, 그림 N) 감지
- Camelot lattice로 격자형 표 파싱
- 행 단위 JSONL 출력
- source_anchor 포함
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber
import camelot

# 상수
TABLE_ANCHOR_PATTERN = r'표\s*\d+(-\d+)?|도표\s*\d+|그림\s*\d+'
CODE_REF_PATTERN = r'고시\s*제?\d{4}-\d+|수가\s*[가-힣A-Z\d]+|\d{4}\.\d+\.\d+\.\s*개정|법률\s*제\d+호'
TABLE_SCORE_TH = 0.5


def detect_table_anchors(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    PDF에서 텍스트 앵커 기반 표 후보 감지

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        [{"page": 10, "anchor": "표 3-2", "bbox": [x0, y0, x1, y1], "score": 0.9}, ...]
    """
    candidates = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if not text:
                continue

            # 텍스트 앵커 찾기
            matches = re.finditer(TABLE_ANCHOR_PATTERN, text)
            for match in matches:
                anchor = match.group()

                # 앵커 근처에 표가 있을 가능성 높음
                # 간단한 점수: 앵커가 있으면 0.8 기본 점수
                score = 0.8

                # 페이지 내 표 구조 힌트 (선/사각형)
                # Camelot이 자동으로 감지할 것이므로 일단 스킵

                candidates.append({
                    "page": page_num,
                    "anchor": anchor,
                    "bbox": None,  # Camelot이 실제 bbox 제공
                    "score": score,
                    "has_anchor": True
                })

    return candidates


def parse_with_camelot(pdf_path: Path, page_num: int) -> List[Any]:
    """
    Camelot lattice로 페이지의 표 파싱

    Args:
        pdf_path: PDF 파일 경로
        page_num: 페이지 번호 (1-based)

    Returns:
        Camelot Table 객체 리스트
    """
    try:
        # lattice: 격자형 표 (선이 명확한 경우)
        tables = camelot.read_pdf(
            str(pdf_path),
            pages=str(page_num),
            flavor='lattice',
            line_scale=40  # 선 감지 임계값
        )
        return tables
    except Exception as e:
        print(f"  Camelot error on page {page_num}: {str(e)}")
        return []


def normalize_table_row(row: List[str], headers: List[str]) -> Dict[str, Any]:
    """
    표 행을 정규화하여 KV 형식으로 변환

    Args:
        row: 행 데이터
        headers: 헤더 리스트

    Returns:
        {"구분": "...", "코드": "...", ...}
    """
    table_kv = {}
    for i, header in enumerate(headers):
        if i < len(row):
            value = row[i].strip()
            # 숫자 변환 시도
            try:
                if value and value.replace(',', '').replace('.', '').isdigit():
                    value = float(value.replace(',', ''))
            except:
                pass
            table_kv[header] = value
        else:
            table_kv[header] = ""

    return table_kv


def row_to_text(table_kv: Dict[str, Any]) -> str:
    """
    행 KV를 문장으로 변환

    Args:
        table_kv: {"구분": "...", "코드": "..."}

    Returns:
        "구분=..., 코드=..."
    """
    parts = []
    for key, value in table_kv.items():
        if isinstance(value, (int, float)):
            parts.append(f"{key}={value}")
        else:
            parts.append(f"{key}={value}")

    return ", ".join(parts)


def extract_code_refs(text: str) -> List[str]:
    """
    텍스트에서 수가/고시/법령 번호 추출

    Args:
        text: 텍스트

    Returns:
        ["고시 제2025-10", "수가 AA001", ...]
    """
    matches = re.findall(CODE_REF_PATTERN, text)
    return list(set(matches))  # 중복 제거


def process_pdf_mvp(pdf_path: Path, doc_id: str, output_dir: Path) -> Dict[str, Any]:
    """
    MVP: 단일 PDF 처리

    Args:
        pdf_path: PDF 파일 경로
        doc_id: 문서 식별자
        output_dir: 출력 디렉토리

    Returns:
        처리 요약
    """
    print(f"\n{'='*60}")
    print(f"Processing: {doc_id}")
    print(f"PDF: {pdf_path.name}")
    print(f"{'='*60}")

    # 1. 텍스트 앵커 감지
    print("\n[1] Detecting table anchors...")
    candidates = detect_table_anchors(pdf_path)
    print(f"  Found {len(candidates)} anchor candidates")

    # 2. Camelot으로 표 파싱
    print("\n[2] Parsing tables with Camelot lattice...")

    all_records = []
    summary = {
        "doc_id": doc_id,
        "total_candidates": len(candidates),
        "total_tables": 0,
        "total_rows": 0,
        "pages_processed": set()
    }

    # 앵커가 있는 페이지 파싱
    pages_with_anchors = set(c["page"] for c in candidates)

    for page_num in sorted(pages_with_anchors):
        print(f"  Processing page {page_num}...")
        tables = parse_with_camelot(pdf_path, page_num)

        if not tables:
            print(f"    No tables found")
            continue

        print(f"    Found {len(tables)} tables")
        summary["pages_processed"].add(page_num)
        summary["total_tables"] += len(tables)

        for table_idx, table in enumerate(tables):
            table_id = f"t{page_num}_{table_idx+1}"

            # DataFrame으로 변환
            df = table.df

            if df.empty:
                continue

            # 첫 행을 헤더로 사용
            headers = df.iloc[0].tolist()
            headers = [str(h).strip() for h in headers]

            # 데이터 행 처리
            for row_idx, row_data in enumerate(df.iloc[1:].values, 1):
                row_id = f"{table_id}r{row_idx}"

                # 정규화
                table_kv = normalize_table_row(row_data.tolist(), headers)
                text = row_to_text(table_kv)

                # code_refs 추출
                code_refs = extract_code_refs(text)

                # bbox (Camelot 제공)
                bbox = table._bbox if hasattr(table, '_bbox') else None

                # 레코드 생성
                record = {
                    "doc_id": doc_id,
                    "page": page_num,
                    "table_id": table_id,
                    "row_id": row_id,
                    "level": 0,  # MVP에서는 중첩 테이블 미지원
                    "parent_table_id": None,
                    "text": text,
                    "table_kv": table_kv,
                    "bbox": bbox,
                    "code_refs": code_refs,
                    "source_anchor": {
                        "page": page_num,
                        "table_id": table_id,
                        "row_id": row_id
                    }
                }

                all_records.append(record)
                summary["total_rows"] += 1

    # 3. JSONL 출력
    print(f"\n[3] Generating output...")
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / f"{doc_id}_tables.jsonl"
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"  Saved: {jsonl_path}")
    print(f"  Records: {len(all_records)}")

    # 4. 요약 저장
    summary["pages_processed"] = sorted(list(summary["pages_processed"]))
    summary["output_file"] = str(jsonl_path)

    summary_path = output_dir / f"{doc_id}_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"  Summary: {summary_path}")

    # 5. 후보 목록 저장
    candidates_path = output_dir / f"{doc_id}_candidates.json"
    with open(candidates_path, 'w', encoding='utf-8') as f:
        json.dump({"candidates": candidates}, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Candidates: {summary['total_candidates']}")
    print(f"  Tables: {summary['total_tables']}")
    print(f"  Rows: {summary['total_rows']}")
    print(f"  Pages: {len(summary['pages_processed'])}")
    print(f"{'='*60}")

    return summary


def main():
    """
    메인 함수: 1개 샘플 PDF 테스트
    """
    # 경로 설정
    base_dir = Path(__file__).parent.parent.parent
    ebook_dir = base_dir / "data" / "hira" / "ebook"
    output_dir = base_dir / "data" / "hira" / "table_parser" / "mvp_output"

    # 테스트 PDF 선택 (가장 작은 것부터)
    test_pdf = ebook_dir / "2025 알기 쉬운 의료급여제도 - (G000DW1-2025-41).pdf"

    if not test_pdf.exists():
        print(f"Error: Test PDF not found: {test_pdf}")
        return

    # MVP 실행
    doc_id = "hira_ebook_test_001"
    summary = process_pdf_mvp(test_pdf, doc_id, output_dir)

    print("\nMVP Test Complete!")


if __name__ == "__main__":
    main()
