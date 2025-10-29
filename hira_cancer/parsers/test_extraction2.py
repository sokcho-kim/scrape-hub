"""엔티티 추출 테스트 - JSON 저장"""
import json
import re
from pathlib import Path

# 첫 번째 공고 로드
with open("hira_cancer/parsers/debug_announcements.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

first_ann = data['samples'][0]
content = first_ann['content']

# 약제 패턴 테스트 (한글 작은따옴표 지원)
drug_pattern = re.compile(r"['']([A-Z][a-zA-Z0-9\-]+(?:\s*\+\s*[A-Z][a-zA-Z0-9\-]+)*)['']")
drugs = drug_pattern.findall(content)

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

# 요법 정보 테스트
regimen_patterns = {
    'type': re.compile(r'(병용요법|단독요법|복합요법)'),
    'line': re.compile(r'(\d+차|차\s*이상)'),
    'purpose': re.compile(r'(고식적요법|보조요법|adjuvant|neoadjuvant)'),
}

regimen_matches = {}
for key, pattern in regimen_patterns.items():
    matches = pattern.findall(content)
    regimen_matches[key] = matches[:5]

# 변경 유형 테스트
action_pattern = re.compile(r'(신설|변경|삭제|추가|개정)')
actions = action_pattern.findall(content)

# 섹션 분리 테스트
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

section_details = []
for i, section in enumerate(sections[:5], 1):
    section_drugs = drug_pattern.findall(section)
    section_cancers = [c for c in cancer_types if c in section]

    section_details.append({
        'section_num': i,
        'content': section[:300],
        'drugs': section_drugs,
        'cancers': section_cancers
    })

# 결과 저장
result = {
    'title': first_ann['title'],
    'content_length': len(content),
    'total_drugs_found': len(drugs),
    'drugs': drugs,
    'total_cancers_found': len(found_cancers),
    'cancers': found_cancers,
    'regimen_matches': regimen_matches,
    'total_actions_found': len(actions),
    'actions': list(set(actions)),
    'total_sections': len(sections),
    'section_samples': section_details
}

output_file = Path("hira_cancer/parsers/test_results.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"테스트 결과 저장: {output_file}")
print(f"  약제: {len(drugs)}개")
print(f"  암종: {len(found_cancers)}개")
print(f"  섹션: {len(sections)}개")
