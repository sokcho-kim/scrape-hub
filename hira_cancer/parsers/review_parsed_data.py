#!/usr/bin/env python3
"""
파싱된 공고책자 데이터 검토 스크립트
"""
import json
from pathlib import Path
from collections import Counter
import re


def analyze_parsed_data(json_path: Path):
    """파싱 데이터 분석"""
    print(f"=== 분석 중: {json_path.name} ===\n")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 메타데이터
    print("[Metadata]")
    metadata = data.get('metadata', {})
    print(f"  - 소스: {Path(metadata.get('source_file', '')).name}")
    print(f"  - 총 페이지: {metadata.get('total_pages', 0)}")
    print(f"  - 총 청크: {metadata.get('total_chunks', 0)}")
    print(f"  - 파싱 시각: {metadata.get('parsed_at', 'N/A')}")
    print(f"  - 출력 형식: {metadata.get('output_format', 'N/A')}")

    # 청크 정보
    if 'chunks' in metadata:
        print(f"\n  청크별 정보:")
        for i, chunk in enumerate(metadata['chunks'], 1):
            print(f"    Chunk {i}: {chunk.get('content_length', 0):,} chars, "
                  f"{chunk.get('elapsed_seconds', 0):.2f}s")

    # 2. Content 분석
    content = data.get('content', '')
    print(f"\n[Content 분석]")
    print(f"  - 총 길이: {len(content):,} characters")
    print(f"  - 단어 수: {len(content.split()):,}")
    print(f"  - 줄 수: {content.count(chr(10)):,}")

    # Content 미리보기
    preview_length = min(500, len(content))
    print(f"\n  [미리보기 ({preview_length} chars)]:")
    print(f"  {content[:preview_length]}...")

    # 3. Elements 분석
    elements = data.get('elements', [])
    print(f"\n[Elements 분석]")
    print(f"  - 총 elements: {len(elements):,}개")

    if elements:
        # Element 타입별 집계
        type_counts = Counter()
        for elem in elements:
            elem_type = elem.get('category', 'unknown')
            type_counts[elem_type] += 1

        print(f"\n  타입별 분포:")
        for elem_type, count in type_counts.most_common():
            print(f"    - {elem_type}: {count:,}개")

        # 첫 5개 element 샘플
        print(f"\n  [샘플 elements (처음 5개)]:")
        for i, elem in enumerate(elements[:5], 1):
            print(f"\n  Element {i}:")
            print(f"    - Category: {elem.get('category', 'N/A')}")
            print(f"    - Type: {elem.get('type', 'N/A')}")

            # Text 내용
            if 'text' in elem:
                text = elem['text'][:100] if elem['text'] else '[empty]'
                print(f"    - Text: {text}...")

            # HTML 내용
            if 'html' in elem:
                html = elem['html'][:100] if elem['html'] else '[empty]'
                print(f"    - HTML: {html}...")

    # 4. 약제명 추출 (간단한 패턴 매칭)
    print(f"\n[약제명 패턴 검색]")

    # 일반적인 약제명 패턴
    drug_patterns = {
        '-mab (단클론항체)': r'\b\w+mab\b',
        '-nib (키나제 억제제)': r'\b\w+nib\b',
        '-platin (백금계)': r'\b\w+platin\b',
        '-taxel (탁산계)': r'\b\w+taxel\b',
    }

    for pattern_name, pattern in drug_patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            unique_matches = set(matches)
            print(f"\n  {pattern_name}: {len(unique_matches)}개 발견")
            sample = list(unique_matches)[:10]
            print(f"    예시: {', '.join(sample)}")

    # 5. 한글 약제명 패턴
    print(f"\n  한글 약제명 샘플:")
    kor_drug_pattern = r'([가-힣]{2,8}(?:정|캡슐|주사|시럽|액|주))'
    kor_matches = re.findall(kor_drug_pattern, content)
    if kor_matches:
        kor_counter = Counter(kor_matches)
        print(f"    발견: {len(kor_counter)}개 유니크")
        for drug, count in kor_counter.most_common(20):
            print(f"      - {drug}: {count}회")

    # 6. 레짐 패턴
    print(f"\n[레짐 패턴 검색]")
    regimen_patterns = ['FOLFOX', 'FOLFIRI', 'XELOX', 'CAPOX', 'R-CHOP', 'ABVD']
    for regimen in regimen_patterns:
        count = len(re.findall(r'\b' + regimen + r'\b', content, re.IGNORECASE))
        if count > 0:
            print(f"  - {regimen}: {count}회")


def main():
    json_path = Path("data/hira_cancer/parsed/chemotherapy/공고책자_20251001.json")

    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return 1

    try:
        analyze_parsed_data(json_path)
        print("\n[OK] 분석 완료!")
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
