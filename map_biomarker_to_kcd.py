"""
바이오마커 암종명 → KCD 코드 매핑 (코드 기반 + GPT 검수)

1. 바이오마커 파일에서 cancer_types 추출
2. 암종명 → KCD 코드 자동 매핑 (키워드 검색)
3. GPT로 검수 요청용 JSON 생성
4. 검수 완료 후 바이오마커 파일 업데이트
"""

import json
from pathlib import Path
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).parent
BIOMARKER_FILE = PROJECT_ROOT / "bridges" / "biomarkers_extracted_v2.json"
KCD_FILE = PROJECT_ROOT / "data" / "kssc" / "kcd-9th" / "normalized" / "kcd9_full.json"
OUTPUT_MAPPING = PROJECT_ROOT / "bridges" / "biomarker_cancer_kcd_mapping.json"
OUTPUT_CSV = PROJECT_ROOT / "bridges" / "biomarker_cancer_kcd_mapping.csv"

# .env 로드
load_dotenv(PROJECT_ROOT / ".env")


def is_cancer_code(code):
    """암 코드 여부 (C00-D48)"""
    if not code or '-' in code:
        return False
    if code.startswith('C'):
        return True
    if code.startswith('D') and len(code) >= 2:
        try:
            num = int(code[1:3])
            return 0 <= num <= 48
        except:
            return False
    return False


def search_kcd_cancer_codes(kcd_data, cancer_name):
    """암종 이름으로 KCD 코드 검색"""
    codes = kcd_data['codes']
    matches = []

    # 검색 키워드 매핑
    keyword_map = {
        "폐암": ["폐"],
        "유방암": ["유방"],
        "위암": ["위"],
        "대장암": ["대장", "결장", "직장"],
        "간암": ["간세포", "간암"],
        "췌장암": ["췌장"],
        "담낭암": ["담낭"],
        "담도암": ["담도"],
        "신장암": ["신장", "콩팥"],
        "방광암": ["방광"],
        "전립선암": ["전립선"],
        "자궁경부암": ["자궁경부", "자궁목"],
        "자궁내막암": ["자궁내막", "자궁체부"],
        "난소암": ["난소"],
        "갑상선암": ["갑상선"],
        "식도암": ["식도"],
        "두경부암": ["두경부", "머리", "목"],
        "흑색종": ["흑색종", "멜라닌"],
        "백혈병": ["백혈병"],
        "림프종": ["림프종"],
        "골수종": ["골수종", "형질세포"],
    }

    keywords = keyword_map.get(cancer_name, [cancer_name.replace("암", "")])

    for code_obj in codes:
        if not is_cancer_code(code_obj['code']):
            continue
        if not code_obj['is_lowest']:  # 최하위 코드만
            continue

        name_kr = code_obj['name_kr'].lower()
        name_en = code_obj['name_en'].lower()

        match_count = sum(1 for kw in keywords if kw.lower() in name_kr or kw.lower() in name_en)

        if match_count > 0:
            # 3글자 코드만 (C50, C34 등)
            if len(code_obj['code']) == 3 or '.' not in code_obj['code']:
                matches.append({
                    'kcd_code': code_obj['code'],
                    'name_kr': code_obj['name_kr'],
                    'name_en': code_obj['name_en'],
                    'match_score': match_count
                })

    # 점수 높은 순, 코드 순
    matches.sort(key=lambda x: (-x['match_score'], x['kcd_code']))

    # 중복 코드 제거 (예: C50, C50.0, C50.1 → C50만)
    seen = set()
    unique = []
    for m in matches:
        base_code = m['kcd_code'][:3]  # C50.0 → C50
        if base_code not in seen:
            seen.add(base_code)
            unique.append(m)

    return unique[:3]  # 상위 3개


def create_gpt_review_prompt(mappings):
    """GPT 검수용 프롬프트 생성"""
    prompt = """다음은 바이오마커의 암종명을 KCD-9 코드로 자동 매핑한 결과입니다.
각 매핑이 정확한지 검토하고, 잘못된 경우 올바른 KCD 코드를 제안해주세요.

매핑 결과:
"""

    for m in mappings:
        biomarker = m['biomarker_name']
        cancer_name = m['cancer_name']
        candidates = m['kcd_candidates']

        prompt += f"\n바이오마커: {biomarker}\n"
        prompt += f"암종명: {cancer_name}\n"
        prompt += "후보 KCD 코드:\n"

        for i, cand in enumerate(candidates, 1):
            prompt += f"  {i}. {cand['kcd_code']} - {cand['name_kr']}\n"

        prompt += "추천 코드: [여기에 선택 또는 수정]\n"
        prompt += "-" * 50 + "\n"

    prompt += """
검토 기준:
1. 암종명과 KCD 코드의 해부학적 위치가 일치하는가?
2. 바이오마커가 해당 암종에 임상적으로 관련이 있는가?
3. 가장 대표적인 상위 코드(예: C50)를 선택했는가?

JSON 형식으로 결과를 반환해주세요:
{
  "reviews": [
    {
      "biomarker_name": "ALK",
      "cancer_name": "폐암",
      "recommended_kcd": "C34",
      "is_correct": true,
      "comment": "폐암의 주요 코드이며 ALK 융합은 폐암의 주요 바이오마커임"
    },
    ...
  ]
}
"""

    return prompt


def main():
    """메인 실행"""
    print("=" * 70)
    print("바이오마커 암종명 → KCD 코드 매핑 (코드 기반)")
    print("=" * 70)

    # 데이터 로드
    print("\n[INFO] 데이터 로딩...")
    with open(BIOMARKER_FILE, 'r', encoding='utf-8') as f:
        biomarker_data = json.load(f)
    with open(KCD_FILE, 'r', encoding='utf-8') as f:
        kcd_data = json.load(f)

    biomarkers = biomarker_data['biomarkers']
    print(f"[OK] 바이오마커 {len(biomarkers)}개 로드")

    # 암종명 추출 및 매핑
    print("\n[INFO] 암종명 → KCD 코드 자동 매핑 중...")
    mappings = []
    csv_rows = []

    for bio in biomarkers:
        biomarker_name = bio['biomarker_name_en']
        cancer_types = bio.get('cancer_types', [])

        for cancer_name in cancer_types:
            # KCD 검색
            candidates = search_kcd_cancer_codes(kcd_data, cancer_name)

            mapping = {
                'biomarker_id': bio['biomarker_id'],
                'biomarker_name': biomarker_name,
                'cancer_name': cancer_name,
                'kcd_candidates': candidates,
                'top_kcd': candidates[0]['kcd_code'] if candidates else None
            }
            mappings.append(mapping)

            # CSV 행
            for i, cand in enumerate(candidates[:3], 1):
                csv_rows.append({
                    'biomarker': biomarker_name,
                    'cancer_name': cancer_name,
                    'rank': i,
                    'kcd_code': cand['kcd_code'],
                    'kcd_name_kr': cand['name_kr'],
                    'is_top': 'YES' if i == 1 else ''
                })

            print(f"  {biomarker_name} - {cancer_name}: {len(candidates)}개 후보")

    # JSON 저장
    output = {
        'metadata': {
            'creation_date': pd.Timestamp.now().isoformat(),
            'source_biomarkers': str(BIOMARKER_FILE),
            'source_kcd': str(KCD_FILE),
            'total_mappings': len(mappings),
            'method': 'keyword_search_code_based'
        },
        'mappings': mappings
    }

    with open(OUTPUT_MAPPING, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 매핑 파일 저장: {OUTPUT_MAPPING}")

    # CSV 저장
    if csv_rows:
        df = pd.DataFrame(csv_rows)
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        print(f"[OK] CSV 파일 저장: {OUTPUT_CSV}")

    # GPT 검수 프롬프트 생성
    gpt_prompt = create_gpt_review_prompt(mappings)
    prompt_file = PROJECT_ROOT / "bridges" / "gpt_review_prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(gpt_prompt)

    print(f"\n[OK] GPT 검수 프롬프트 저장: {prompt_file}")

    # 통계
    print("\n" + "=" * 70)
    print("매핑 통계")
    print("=" * 70)
    print(f"총 매핑: {len(mappings)}개")
    no_match = [m for m in mappings if not m['kcd_candidates']]
    print(f"  매칭 없음: {len(no_match)}개")
    print(f"  매칭 있음: {len(mappings) - len(no_match)}개")

    if no_match:
        print("\n매칭 실패:")
        for m in no_match:
            print(f"  - {m['biomarker_name']} / {m['cancer_name']}")

    print("\n" + "=" * 70)
    print("다음 단계:")
    print(f"1. {prompt_file} 내용을 GPT-4에 전달")
    print(f"2. GPT 검수 결과를 받아 매핑 파일 업데이트")
    print(f"3. 업데이트된 매핑으로 바이오마커 파일에 kcd_codes 추가")
    print("=" * 70)


if __name__ == "__main__":
    main()
