"""엔티티 추출 테스트"""
import json
import re
from pathlib import Path

# 첫 번째 공고 로드
with open("hira_cancer/parsers/debug_announcements.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

first_ann = data['samples'][0]
content = first_ann['content']

print("="*80)
print("첫 번째 공고 테스트")
print("="*80)
print(f"제목: {first_ann['title']}")
print(f"내용 길이: {len(content)} 자")

# 약제 패턴 테스트 (한글 작은따옴표 지원)
drug_pattern = re.compile(r"['']([A-Z][a-zA-Z0-9\-]+(?:\s*\+\s*[A-Z][a-zA-Z0-9\-]+)*)['']")
drugs = drug_pattern.findall(content)

print(f"\n[약제 추출] {len(drugs)}개 발견:")
for drug in drugs[:10]:
    print(f"  - {drug}")

# 암종 테스트
cancer_types = [
    "갑상선암", "위암", "대장암", "폐암", "간암", "유방암", "전립선암",
    "췌장암", "담낭암", "담도암", "신장암", "방광암", "자궁암", "난소암",
    "비호지킨림프종"
]

found_cancers = []
for cancer in cancer_types:
    if cancer in content:
        found_cancers.append(cancer)

print(f"\n[암종 추출] {len(found_cancers)}개 발견:")
for cancer in found_cancers:
    print(f"  - {cancer}")

# 요법 정보 테스트
regimen_patterns = {
    'type': re.compile(r'(병용요법|단독요법|복합요법)'),
    'line': re.compile(r'(\d+차|차\s*이상)'),
    'purpose': re.compile(r'(고식적요법|보조요법|adjuvant|neoadjuvant)'),
}

print(f"\n[요법 정보]")
for key, pattern in regimen_patterns.items():
    matches = pattern.findall(content)
    print(f"  {key}: {matches[:5]}")

# 변경 유형 테스트
action_pattern = re.compile(r'(신설|변경|삭제|추가|개정)')
actions = action_pattern.findall(content)
print(f"\n[변경 유형] {len(actions)}개 발견:")
print(f"  {set(actions)}")

# 섹션 분리 테스트
print(f"\n[섹션 분리 테스트]")
lines = content.split('\n')
sections = []
current_section = []

for line in lines:
    line = line.strip()
    if line.startswith('- ') or line.startswith('ㆍ'):
        if current_section:
            sections.append('\n'.join(current_section))
        current_section = [line]
    elif current_section:
        current_section.append(line)

if current_section:
    sections.append('\n'.join(current_section))

print(f"총 {len(sections)}개 섹션 발견")
print(f"\n처음 3개 섹션:")
for i, section in enumerate(sections[:3], 1):
    print(f"\n[섹션 {i}]")
    print(section[:200] + "..." if len(section) > 200 else section)

    # 각 섹션에서 추출 테스트
    section_drugs = drug_pattern.findall(section)
    section_cancers = [c for c in cancer_types if c in section]

    print(f"  약제: {section_drugs[:3]}")
    print(f"  암종: {section_cancers}")
