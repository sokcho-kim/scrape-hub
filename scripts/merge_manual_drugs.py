#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수동 매핑 약제를 JSON에 병합
"""
import json
from pathlib import Path

# 수동 매핑 로드 (JSON 파일에서)
manual_drugs_path = Path("dictionary/anchor/manual_drugs.json")
with open(manual_drugs_path, 'r', encoding='utf-8') as f:
    manual_data = json.load(f)
    MANUAL_DRUGS = manual_data['manual_drugs']

print(f"Loaded {len(MANUAL_DRUGS)} manual drug mappings from {manual_drugs_path}")

# 기존 JSON 로드
json_path = Path("out/candidates/drug_candidates.json")
with open(json_path, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

existing_pairs = data.get('matched_via_english', [])
print(f"Existing pairs: {len(existing_pairs)}")

# 수동 약제 추가
added = 0
for en, ko_list in MANUAL_DRUGS.items():
    for ko in ko_list:
        # 중복 체크
        if any(p['english'] == en and p['korean'] == ko for p in existing_pairs):
            continue

        existing_pairs.append({
            'english': en,
            'korean': ko,
            'count': 10,  # 높은 count로 우선순위 부여
            'source': 'manual_curated'
        })
        added += 1

print(f"Added manual drugs: {added}")
print(f"Total pairs: {len(existing_pairs)}")

# 저장 (UTF-8-BOM 사용)
with open(json_path, 'w', encoding='utf-8-sig') as f:
    json.dump({'matched_via_english': existing_pairs}, f, ensure_ascii=False, indent=2)

print(f"Saved to {json_path}")
