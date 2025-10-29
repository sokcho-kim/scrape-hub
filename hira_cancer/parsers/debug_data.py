"""HIRA 데이터 구조 디버깅"""
import json
from pathlib import Path

# HIRA 데이터 로드
hira_file = Path("data/hira_cancer/raw/hira_cancer_20251023_184848.json")
with open(hira_file, 'r', encoding='utf-8') as f:
    hira_data = json.load(f)

announcements = hira_data['data']['announcement']

print(f"총 공고 수: {len(announcements)}")
print(f"\n" + "="*80)
print("첫 번째 공고 샘플")
print("="*80)

# 첫 번째 공고
first = announcements[0]
print(f"\n제목: {first.get('title', 'N/A')}")
print(f"번호: {first.get('announcement_no', 'N/A')}")
print(f"날짜: {first.get('created_date', 'N/A')}")

content = first.get('content', '')
print(f"\n내용 길이: {len(content)} 자")
print(f"내용 있음: {'예' if content else '아니오'}")

if content:
    print(f"\n내용 샘플 (처음 500자):")
    print("-" * 80)
    print(content[:500])
    print("-" * 80)

    # 약제명 패턴 확인
    import re
    drug_pattern = re.compile(r"'([A-Z][a-zA-Z0-9\-]+(?:\s*\+\s*[A-Z][a-zA-Z0-9\-]+)*)'")
    drugs_found = drug_pattern.findall(content)
    print(f"\n발견된 약제 패턴: {len(drugs_found)}개")
    if drugs_found:
        print(f"  예시: {drugs_found[:5]}")

    # 암종 확인
    cancer_types = ["폐암", "유방암", "위암", "대장암", "간암"]
    found_cancers = [c for c in cancer_types if c in content]
    print(f"\n발견된 암종: {found_cancers}")

    # 요법 키워드
    regimen_keywords = ["병용요법", "단독요법", "1차", "2차", "고식적"]
    found_keywords = [k for k in regimen_keywords if k in content]
    print(f"발견된 요법 키워드: {found_keywords}")

# 내용 없는 공고 체크
no_content = [a for a in announcements if not a.get('content')]
print(f"\n\n내용 없는 공고: {len(no_content)}개 / {len(announcements)}개")

# 내용 있는 공고 샘플 찾기
with_content = [a for a in announcements if a.get('content')]
print(f"내용 있는 공고: {len(with_content)}개")

if with_content:
    print(f"\n" + "="*80)
    print("내용 있는 공고 샘플")
    print("="*80)
    sample = with_content[0]
    print(f"제목: {sample.get('title', 'N/A')}")
    content = sample.get('content', '')
    print(f"내용 길이: {len(content)} 자")
    print(f"\n내용 샘플:")
    print("-" * 80)
    print(content[:1000])
