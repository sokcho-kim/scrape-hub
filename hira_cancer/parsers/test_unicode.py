"""유니코드 작은따옴표 테스트"""
import re

# 샘플 텍스트
text = "- 자궁암에 'Dostarlimab + Paclitaxel + Carboplatin' 병용요법(1차, 고식적요법) 신설"

print("원본 텍스트:")
print(text)
print()

# 각 문자의 유니코드 확인
print("작은따옴표 위치의 유니코드:")
for i, char in enumerate(text):
    if char in ["'", "'", "'"]:
        print(f"  위치 {i}: '{char}' = U+{ord(char):04X}")

print()

# 다양한 패턴 테스트
patterns = [
    (r"'([A-Z][a-zA-Z0-9\s\+\-]+)'", "ASCII 작은따옴표 '"),
    (r"'([A-Z][a-zA-Z0-9\s\+\-]+)'", "왼쪽 큰따옴표 ' (U+2018)"),
    (r"'([A-Z][a-zA-Z0-9\s\+\-]+)'", "오른쪽 큰따옴표 ' (U+2019)"),
    (r"['']([A-Z][a-zA-Z0-9\s\+\-]+)['']", "양쪽 큰따옴표 모두"),
    (r"['']([A-Z][a-zA-Z0-9\s\+\-]+)['']", "Unicod양쪽 (복사)"),
]

for pattern_str, desc in patterns:
    pattern = re.compile(pattern_str)
    matches = pattern.findall(text)
    print(f"{desc}:")
    print(f"  패턴: {repr(pattern_str)}")
    print(f"  결과: {matches}")
    print()

# 수동으로 명확한 유니코드 입력
text2 = "자궁암에 'Dostarlimab + Paclitaxel + Carboplatin' 병용요법"
print("수동 입력 텍스트:")
print(text2)

pattern_manual = re.compile(r"'([A-Z][a-zA-Z0-9\s\+\-]+)'")
matches_manual = pattern_manual.findall(text2)
print(f"수동 패턴 결과: {matches_manual}")
