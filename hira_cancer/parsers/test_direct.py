"""HIRA JSON에서 직접 테스트"""
import json
import re

# HIRA 데이터 직접 로드
with open("data/hira_cancer/raw/hira_cancer_20251023_184848.json", 'r', encoding='utf-8') as f:
    hira_data = json.load(f)

announcements = hira_data['data']['announcement']

# 첫 번째 공고
first = announcements[0]
content = first.get('content', '')

print(f"공고 번호: {first.get('announcement_no')}")
print(f"내용 길이: {len(content)}")
print()

# 내용에서 작은따옴표가 있는 부분 찾기
lines_with_quotes = [line for line in content.split('\n') if "'" in line or "'" in line or "'" in line]

print(f"작은따옴표가 있는 줄: {len(lines_with_quotes)}개")
print()

if lines_with_quotes:
    print("처음 5줄:")
    for i, line in enumerate(lines_with_quotes[:5], 1):
        print(f"\n[{i}] {line.strip()[:150]}")

        # 유니코드 확인
        for char in line:
            if char in ["'", "'", "'"]:
                print(f"    발견된 따옴표: '{char}' = U+{ord(char):04X}")

        # 다양한 패턴 테스트
        patterns = [
            (r"'([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)'", "ASCII '"),
            (r"'([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)'", "Curly '"),
            (r"'([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)'", "Curly '"),
            (r"['']([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)['']", "Both"),
        ]

        for pattern_str, desc in patterns:
            matches = re.findall(pattern_str, line)
            if matches:
                print(f"    {desc}: {matches}")

# 전체 내용에서 패턴 테스트
print("\n" + "="*80)
print("전체 내용 패턴 테스트")
print("="*80)

pattern = re.compile(r"'([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)'")
all_matches = pattern.findall(content)

print(f"\nASCII ' 패턴: {len(all_matches)}개 매치")
if all_matches:
    print(f"예시: {all_matches[:5]}")

# Curly quotes 테스트
pattern2 = re.compile(r"'([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)'")
all_matches2 = pattern2.findall(content)

print(f"\nCurly ' 패턴: {len(all_matches2)}개 매치")
if all_matches2:
    print(f"예시: {all_matches2[:5]}")

# Both 테스트
pattern3 = re.compile(r"['']([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)['']")
all_matches3 = pattern3.findall(content)

print(f"\nBoth 패턴: {len(all_matches3)}개 매치")
if all_matches3:
    print(f"예시: {all_matches3[:5]}")
