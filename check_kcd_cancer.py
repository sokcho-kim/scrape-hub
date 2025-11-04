import json
import re

print("=" * 100)
print("KCD-8 암 관련 코드 확인")
print("=" * 100)

# JSON 로드
with open('data/hira_master/parsed/KCD-8 1권_220630_20220630034856.json', encoding='utf-8') as f:
    data = json.load(f)

content = data['content']

print(f"\n문서 정보:")
print(f"  - 총 페이지: {data['total_pages']}")
print(f"  - 파싱된 청크: {data['chunks_parsed']}")
print(f"  - 내용 크기: {len(content):,} bytes")

# C00-C97 악성신생물(암) 코드 검색
print(f"\n[악성신생물 코드 검색: C00-C97]")
cancer_pattern = r'C\d{2}(?:\.\d+)?\s+[가-힣\s\(\)]+(?=\n|C\d{2}|$)'
cancer_matches = re.findall(cancer_pattern, content)

print(f"  발견된 코드: {len(cancer_matches)}개")
print(f"\n샘플 (처음 30개):")
for match in cancer_matches[:30]:
    print(f"    {match.strip()}")

# 특정 암 검색
print(f"\n[주요 암 검색]")
cancer_keywords = ['유방', '폐', '위', '대장', '간', '췌장', '전립선', '자궁경부']

for keyword in cancer_keywords:
    pattern = f'C\\d{{2}}(?:\\.\\d+)?\\s+.*{keyword}.*'
    matches = re.findall(pattern, content)
    if matches:
        print(f"\n  [{keyword}암]:")
        for m in matches[:5]:
            print(f"    {m.strip()}")

print("\n" + "=" * 100)
