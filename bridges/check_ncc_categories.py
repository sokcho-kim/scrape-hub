import json
from pathlib import Path
from collections import Counter

print("=" * 100)
print("NCC 카테고리 및 약물 용어 확인")
print("=" * 100)

# LLM 결과 로드
llm_dir = Path('../ncc/cancer_dictionary/llm_dynamic_results')
batch_files = sorted(llm_dir.glob('batch_*.json'))

print(f"\n배치 파일: {len(batch_files)}개")

# 첫 번째 배치만 확인
with open(batch_files[0], encoding='utf-8') as f:
    sample_data = json.load(f)

print(f"샘플 데이터: {len(sample_data)}개")

# 카테고리 확인
categories = Counter([d.get('final_category') for d in sample_data])
print(f"\n카테고리 분포:")
for cat, count in categories.most_common():
    print(f"  {cat}: {count}개")

# 약물 관련 키워드 검색
print(f"\n'치료' 카테고리 샘플:")
treatment = [d for d in sample_data if d.get('final_category') == '치료'][:10]
for t in treatment:
    print(f"  - {t['keyword']}")
    print(f"    {t['content'][:80]}...")

# 항암제 이름으로 검색
anticancer_keywords = [
    '5-FU', '플루오로우라실', '시스플라틴', '독소루비신',
    '파클리탁셀', '이매티닙', '옵디보', '키트루다'
]

print(f"\n항암제 키워드 검색:")
for keyword in anticancer_keywords:
    found = [d for d in sample_data if keyword.lower() in d['keyword'].lower()]
    if found:
        for f in found:
            print(f"  [{f['final_category']}] {f['keyword']}")
            print(f"    {f['content'][:80]}...")
    else:
        print(f"  {keyword}: 없음")

print("\n" + "=" * 100)
