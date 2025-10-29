"""HIRA 데이터 상세 분석"""
import json
from pathlib import Path

# HIRA 데이터 로드
hira_file = Path("data/hira_cancer/raw/hira_cancer_20251023_184848.json")
with open(hira_file, 'r', encoding='utf-8') as f:
    hira_data = json.load(f)

announcements = hira_data['data']['announcement']

print(f"총 공고 수: {len(announcements)}")

# 모든 공고의 content 길이 분석
content_lengths = [len(a.get('content', '')) for a in announcements]
print(f"\nContent 길이 통계:")
print(f"  평균: {sum(content_lengths) / len(content_lengths):.0f} 자")
print(f"  최소: {min(content_lengths)} 자")
print(f"  최대: {max(content_lengths)} 자")

# 가장 긴 content 찾기
longest_idx = content_lengths.index(max(content_lengths))
longest = announcements[longest_idx]

print(f"\n" + "="*80)
print(f"가장 긴 content (공고 #{longest_idx + 1})")
print("="*80)
print(f"제목: {longest.get('title', 'N/A')}")
print(f"길이: {len(longest.get('content', ''))} 자")
print(f"\n전체 내용:")
print("-" * 80)
print(longest.get('content', ''))
print("-" * 80)

# 약제 패턴 확인
import re
drug_pattern = re.compile(r"'([A-Z][a-zA-Z0-9\-]+(?:\s*\+\s*[A-Z][a-zA-Z0-9\-]+)*)'")
drugs_found = drug_pattern.findall(longest.get('content', ''))
print(f"\n발견된 약제: {drugs_found[:10]}")

# 첨부파일 분석
print(f"\n" + "="*80)
print("첨부파일 분석")
print("="*80)

attachments = hira_data['data']['attachment']
print(f"총 첨부파일 수: {len(attachments)}")

# 첨부파일 타입별 분류
from collections import Counter
file_types = Counter()
for att in attachments:
    file_name = att.get('file_name', '')
    if '.' in file_name:
        ext = file_name.split('.')[-1].lower()
        file_types[ext] += 1

print(f"\n파일 타입별:")
for ext, count in file_types.most_common():
    print(f"  .{ext}: {count}개")

# 샘플 첨부파일
print(f"\n첨부파일 샘플 (처음 5개):")
for i, att in enumerate(attachments[:5], 1):
    print(f"  [{i}] {att.get('file_name', 'N/A')} ({att.get('file_size', 'N/A')})")
    print(f"      공고번호: {att.get('announcement_no', 'N/A')}")
