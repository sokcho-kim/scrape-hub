"""Dostarlimab 주변 내용을 JSON으로 저장"""
import json

# HIRA JSON 로드
with open("data/hira_cancer/raw/hira_cancer_20251023_184848.json", 'r', encoding='utf-8') as f:
    hira_data = json.load(f)

hira_first = hira_data['data']['announcement'][0]
hira_content = hira_first.get('content', '')

# Dostarlimab 위치
key_phrase = "Dostarlimab"
idx = hira_content.index(key_phrase)

# 주변 200자 추출
start = max(0, idx-100)
end = min(len(hira_content), idx+100)
surrounding = hira_content[start:end]

# 유니코드 정보
char_info = []
for i, char in enumerate(surrounding):
    char_info.append({
        'position': start + i,
        'char': char,
        'unicode': f"U+{ord(char):04X}",
        'is_quote': char in ["'", "'", "'", '"', '"', '"']
    })

# 저장
output = {
    'found_at_position': idx,
    'surrounding_text': surrounding,
    'character_details': char_info
}

with open("hira_cancer/parsers/surrounding_dostarlimab.json", 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"저장 완료: surrounding_dostarlimab.json")
print(f"Dostarlimab 위치: {idx}")
print(f"주변 텍스트 길이: {len(surrounding)}")

# 따옴표 찾기
quotes_found = [c for c in char_info if c['is_quote']]
print(f"따옴표 발견: {len(quotes_found)}개")
for q in quotes_found[:5]:
    print(f"  위치 {q['position']}: '{q['char']}' {q['unicode']}")
