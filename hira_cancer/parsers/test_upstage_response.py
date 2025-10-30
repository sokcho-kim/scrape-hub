#!/usr/bin/env python3
"""Upstage API 응답 구조 테스트"""
import os
import requests
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.getenv('UPSTAGE_API_KEY')
if not api_key:
    print("UPSTAGE_API_KEY not found")
    exit(1)

# 첫 번째 청크로 테스트
chunk_path = Path("data/hira_cancer/raw/attachments/chemotherapy/_temp_공고책자_20251001/공고책자_20251001_chunk_0001-0100.pdf")

if not chunk_path.exists():
    print(f"Chunk not found: {chunk_path}")
    exit(1)

print(f"Testing with: {chunk_path.name}")

with open(chunk_path, 'rb') as f:
    files = {'document': (chunk_path.name, f, 'application/pdf')}
    data = {
        'ocr': 'true',
        'output_formats': '["html"]',
    }

    response = requests.post(
        "https://api.upstage.ai/v1/document-ai/document-parse",
        headers={"Authorization": f"Bearer {api_key}"},
        files=files,
        data=data,
        timeout=60
    )

if response.status_code != 200:
    print(f"Error {response.status_code}: {response.text}")
    exit(1)

result = response.json()

print("\n=== Response Structure ===")
print(f"Type: {type(result)}")
print(f"Keys: {list(result.keys())}")

for key, value in result.items():
    print(f"\n{key}:")
    print(f"  Type: {type(value)}")
    if isinstance(value, (str, list, dict)):
        if isinstance(value, str):
            print(f"  Length: {len(value)}")
            print(f"  Preview: {value[:200]}...")
        elif isinstance(value, list):
            print(f"  Length: {len(value)}")
            if len(value) > 0:
                print(f"  First item type: {type(value[0])}")
        elif isinstance(value, dict):
            print(f"  Keys: {list(value.keys())}")

# JSON 저장
import json
output_path = "test_upstage_response.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\nFull response saved to: {output_path}")
