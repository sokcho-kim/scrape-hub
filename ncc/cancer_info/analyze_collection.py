"""
NCC 수집 데이터 분석 스크립트
"""
import json
from pathlib import Path
from collections import Counter

def analyze_collection():
    """수집된 데이터 분석"""
    parsed_dir = Path("data/ncc/parsed")

    # 모든 암종 JSON 파일 찾기 (summary 파일 제외)
    cancer_files = [f for f in parsed_dir.glob("*_*.json") if "summary" not in f.name]
    chemotherapy_files = [f for f in parsed_dir.glob("*.json") if "_" not in f.name and "summary" not in f.name]

    print("=" * 80)
    print("NCC 암정보 수집 결과 분석")
    print("=" * 80)

    # 전체 통계
    print(f"\n전체 수집 파일: {len(cancer_files) + len(chemotherapy_files)}개")
    print(f"  - 암종 데이터: {len(cancer_files)}개")
    print(f"  - 항암화학요법 데이터: {len(chemotherapy_files)}개")

    # 태그별 분류
    tag_counter = Counter()
    major_cancers = []
    adult_cancers = []
    pediatric_cancers = []

    for file in cancer_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tags = data.get('tags', [])

                # 태그 카운트
                for tag in tags:
                    tag_counter[tag] += 1

                # 분류
                if "주요암" in tags:
                    major_cancers.append(data['name'])
                if "성인" in tags:
                    adult_cancers.append(data['name'])
                if "소아청소년" in tags:
                    pediatric_cancers.append(data['name'])

        except Exception as e:
            print(f"파일 읽기 오류: {file.name} - {e}")

    print(f"\n태그별 분류:")
    print(f"  - 주요암: {tag_counter.get('주요암', 0)}개")
    print(f"  - 성인: {tag_counter.get('성인', 0)}개")
    print(f"  - 소아청소년: {tag_counter.get('소아청소년', 0)}개")

    print(f"\n12대 주요암 목록 ({len(major_cancers)}개):")
    for cancer in sorted(major_cancers):
        print(f"  - {cancer}")

    print(f"\n소아청소년 암 목록 ({len(pediatric_cancers)}개):")
    for cancer in sorted(pediatric_cancers):
        print(f"  - {cancer}")

    # 콘텐츠 통계
    print(f"\n콘텐츠 통계:")
    total_sections = 0
    total_tables = 0
    total_images = 0

    for file in cancer_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                content = data.get('content', {})
                total_sections += len(content.get('sections', []))
                total_tables += len(content.get('tables', []))
                total_images += len(content.get('images', []))
        except:
            pass

    print(f"  - 총 섹션 수: {total_sections}개")
    print(f"  - 총 표 수: {total_tables}개")
    print(f"  - 총 이미지 수: {total_images}개")
    print(f"  - 평균 섹션/암종: {total_sections/len(cancer_files):.1f}개")

    print("\n" + "=" * 80)
    print("수집 완료!")
    print("=" * 80)

if __name__ == "__main__":
    analyze_collection()
