"""원본 HIRA JSON vs 저장된 debug JSON 비교"""
import json

# 1. 원본 HIRA JSON에서 첫 공고
with open("data/hira_cancer/raw/hira_cancer_20251023_184848.json", 'r', encoding='utf-8') as f:
    hira_data = json.load(f)

hira_first = hira_data['data']['announcement'][0]
hira_content = hira_first.get('content', '')

# 2. 저장된 debug JSON에서 첫 공고
with open("hira_cancer/parsers/debug_announcements.json", 'r', encoding='utf-8') as f:
    debug_data = json.load(f)

debug_first = debug_data['samples'][0]
debug_content = debug_first.get('content', '')

# 비교
print(f"원본 HIRA 길이: {len(hira_content)}")
print(f"저장된 debug 길이: {len(debug_content)}")
print(f"동일 여부: {hira_content == debug_content}")
print()

# 차이 찾기
if hira_content != debug_content:
    # 첫 차이점 찾기
    for i, (c1, c2) in enumerate(zip(hira_content, debug_content)):
        if c1 != c2:
            print(f"첫 차이점 위치: {i}")
            print(f"  원본: '{c1}' (U+{ord(c1):04X})")
            print(f"  저장: '{c2}' (U+{ord(c2):04X})")
            print(f"\n주변 내용 (원본):")
            print(hira_content[max(0, i-50):i+50])
            print(f"\n주변 내용 (저장):")
            print(debug_content[max(0, i-50):i+50])
            break
else:
    print("내용이 완전히 동일합니다")
    print()

    # 약제명이 있는 부분 찾기
    key_phrase = "Dostarlimab"
    if key_phrase in hira_content:
        idx = hira_content.index(key_phrase)
        print(f"'{key_phrase}' 발견 위치: {idx}")
        print(f"\n주변 내용:")
        surrounding = hira_content[max(0, idx-100):idx+100]
        print(surrounding)
        print()

        # 주변 따옴표 확인
        for i, char in enumerate(surrounding):
            if char in ["'", "'", "'"]:
                print(f"  위치 {i}: '{char}' = U+{ord(char):04X}")
    else:
        print(f"'{key_phrase}' not found in content")

# 원본 내용 샘플 출력 (마지막 500자)
print("\n" + "="*80)
print("원본 내용 마지막 500자:")
print("="*80)
print(hira_content[-500:])
