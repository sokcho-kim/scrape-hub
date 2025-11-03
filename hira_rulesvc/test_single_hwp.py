#!/usr/bin/env python3
"""단일 HWP 파일 테스트"""
import os
import json
import requests
from pathlib import Path

# API 키 설정
API_KEY = "up_fHFVGHQd7ZUsvlvYwGNPjfd6TLuLD"
API_URL = "https://api.upstage.ai/v1/document-ai/document-parse"

# 테스트 파일 (가장 작은 파일)
test_file = Path("data/hira_rulesvc/documents/5-(4) 부당이득금.hwp")

print("=" * 80)
print("HWP 파싱 테스트")
print("=" * 80)
print(f"파일: {test_file.name}")
print(f"크기: {test_file.stat().st_size / 1024:.1f} KB")
print()

# API 호출
print("[API] Uploading to Upstage...")
with open(test_file, 'rb') as f:
    files = {'document': f}
    data = {
        'ocr': 'auto',
        'coordinates': 'true'
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    response = requests.post(
        API_URL,
        headers=headers,
        files=files,
        data=data,
        timeout=300
    )

print(f"[STATUS] {response.status_code}")

if response.status_code == 200:
    result = response.json()

    print("[OK] 파싱 성공!")
    print(f"페이지 수: {len(result.get('pages', []))}")
    print(f"텍스트 길이: {len(result.get('content', {}).get('text', ''))} chars")
    print(f"요소 수: {len(result.get('elements', []))} elements")

    # 샘플 텍스트 출력
    content_text = result.get('content', {}).get('text', '')
    if content_text:
        print("\n[SAMPLE] 첫 500자:")
        print(content_text[:500])

    # JSON 저장
    output_file = Path("data/hira_rulesvc/parsed") / f"{test_file.stem}_test.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVE] {output_file}")
    print("\n✅ 테스트 성공!")

else:
    print(f"[ERROR] {response.text}")
    print("\n❌ 테스트 실패")
