"""
암종 이름 → KCD 코드 자동 매핑 파일 생성

NCC 암종 이름과 KCD-9 질병 코드를 매칭합니다.
- 코드 기반: KCD 데이터에서 암 코드만 추출
- 키워드 검색: 암종 이름 키워드로 KCD 검색
- 수동 검증: 매핑 결과 CSV 출력 → 사람이 검증 후 사용
"""

import json
from pathlib import Path
import pandas as pd
import re


PROJECT_ROOT = Path(__file__).parent
KCD_FILE = PROJECT_ROOT / "data" / "kssc" / "kcd-9th" / "normalized" / "kcd9_full.json"
NCC_DIR = PROJECT_ROOT / "data" / "ncc" / "cancer_info" / "parsed"
OUTPUT_FILE = PROJECT_ROOT / "bridges" / "cancer_kcd_mapping.json"
OUTPUT_CSV = PROJECT_ROOT / "bridges" / "cancer_kcd_mapping.csv"


def is_cancer_code(code):
    """암 코드 여부 (C00-D48)"""
    if not code:
        return False

    # 범위 코드 제외
    if '-' in code:
        return False

    # C로 시작
    if code.startswith('C'):
        return True

    # D00-D48
    if code.startswith('D'):
        match = re.match(r'D(\d+)', code)
        if match:
            num = int(match.group(1))
            return 0 <= num <= 48

    return False


def extract_cancer_keywords(cancer_name):
    """
    암종 이름에서 검색 키워드 추출
    예: "유방암" → ["유방"]
        "급성 골수성백혈병" → ["급성", "골수성", "백혈병"]
    """
    # 조사/접미사 제거
    name = cancer_name.replace("암", "").replace("종양", "").replace("종", "")
    name = name.replace("악성", "").strip()

    # 특수 케이스
    special_cases = {
        "유방": ["유방"],
        "폐": ["폐"],
        "위": ["위"],
        "간": ["간"],
        "대장": ["대장", "결장", "직장"],
        "췌장": ["췌장"],
        "담낭": ["담낭"],
        "담도": ["담도"],
        "갑상선": ["갑상선"],
        "전립선": ["전립선"],
        "자궁경부": ["자궁경부", "자궁목"],
        "자궁내막": ["자궁내막", "자궁체부"],
        "난소": ["난소"],
        "방광": ["방광"],
        "신장": ["신장", "콩팥"],
        "직장": ["직장"],
        "결장": ["결장"],
        "간내 담도": ["간내", "담도"],
        "고환": ["고환", "정소"],
        "후두": ["후두"],
        "설": ["혀"],
        "구강": ["구강", "입"],
        "침샘": ["침샘", "타액선"],
        "항문": ["항문"],
        "피부": ["피부"],
        "흑색종": ["흑색종", "멜라닌세포"],
        "기저세포": ["기저세포"],
        "편평상피세포": ["편평상피세포"],
        "음경": ["음경"],
        "외음부": ["외음부"],
        "질": ["질"],
        "뇌": ["뇌", "두개내"],
        "교모세포종": ["교모세포종", "glioblastoma"],
        "성상세포종": ["성상세포종", "astrocytoma"],
        "수막종": ["수막종", "meningioma"],
        "뇌하수체": ["뇌하수체", "뇌하수체"],
        "척수": ["척수", "척수"],
        "흉선": ["흉선"],
        "중피종": ["중피종", "흉막"],
        "골": ["뼈", "골"],
        "연부조직": ["연부조직", "연조직"],
        "육종": ["육종", "sarcoma"],
        "위장관 기질": ["위장관", "간질", "GIST"],
        "횡문근육종": ["횡문근육종", "rhabdomyosarcoma"],
        "림프종": ["림프종", "림프"],
        "비호지킨": ["비호지킨", "non-Hodgkin"],
        "거대B세포": ["거대B세포", "large B-cell"],
        "다발골수종": ["다발골수종", "형질세포", "myeloma"],
        "급성 골수성백혈병": ["급성", "골수성", "백혈병", "AML"],
        "급성 림프구성백혈병": ["급성", "림프구성", "백혈병", "ALL"],
        "만성 골수성백혈병": ["만성", "골수성", "백혈병", "CML"],
        "만성 림프구성백혈병": ["만성", "림프구성", "백혈병", "CLL"],
        "골수이형성증후군": ["골수이형성", "MDS"],
    }

    # 특수 케이스 먼저 확인
    for key, keywords in special_cases.items():
        if key in cancer_name:
            return keywords

    # 공백/특수문자로 분할
    keywords = re.split(r'[\s\-·]+', name)
    keywords = [k for k in keywords if len(k) > 1]  # 1글자는 제외

    return keywords if keywords else [name]


def search_kcd_by_keywords(kcd_data, keywords):
    """KCD 데이터에서 키워드로 검색"""
    codes = kcd_data['codes']
    matches = []

    for code_obj in codes:
        if not is_cancer_code(code_obj['code']):
            continue

        # 범위 코드 제외
        if code_obj['is_header'] or not code_obj['is_lowest']:
            continue

        name_kr = code_obj['name_kr'].lower()
        name_en = code_obj['name_en'].lower()

        # 모든 키워드가 포함되는지 확인
        match_count = 0
        for keyword in keywords:
            if keyword.lower() in name_kr or keyword.lower() in name_en:
                match_count += 1

        if match_count > 0:
            matches.append({
                'kcd_code': code_obj['code'],
                'name_kr': code_obj['name_kr'],
                'name_en': code_obj['name_en'],
                'match_count': match_count,
                'match_ratio': match_count / len(keywords)
            })

    # 매칭 비율 높은 순으로 정렬
    matches.sort(key=lambda x: (-x['match_ratio'], -x['match_count'], x['kcd_code']))

    return matches


def main():
    """메인 실행"""
    print("=" * 70)
    print("암종 이름 → KCD 코드 자동 매핑")
    print("=" * 70)

    # KCD 데이터 로드
    print("\n[INFO] KCD-9 데이터 로딩...")
    with open(KCD_FILE, 'r', encoding='utf-8') as f:
        kcd_data = json.load(f)
    print(f"[OK] KCD-9 {kcd_data['total_codes']}개 코드 로드")

    # NCC 암종 로드
    print("\n[INFO] NCC 암종 파일 로딩...")
    import glob
    cancer_files = glob.glob(str(NCC_DIR / "*_*.json"))
    exclude = ["summary", "chemotherapy", "cytotoxic", "immune", "targeted"]
    cancer_files = [f for f in cancer_files if not any(e in f for e in exclude)]

    cancers = []
    for file_path in cancer_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cancers.append({
                    'name': data['name'],
                    'seq': data['cancer_seq']
                })
        except:
            pass

    print(f"[OK] {len(cancers)}개 암종 로드")

    # 매핑 생성
    print("\n[INFO] 암종 → KCD 자동 매핑 중...")
    mappings = []
    csv_rows = []

    for cancer in cancers:
        cancer_name = cancer['name']
        keywords = extract_cancer_keywords(cancer_name)

        # KCD 검색
        matches = search_kcd_by_keywords(kcd_data, keywords)

        # 상위 5개만 선택
        top_matches = matches[:5]

        # 매핑 저장
        kcd_codes = [m['kcd_code'] for m in top_matches]
        mappings.append({
            'cancer_name': cancer_name,
            'cancer_seq': cancer['seq'],
            'keywords': keywords,
            'kcd_codes': kcd_codes,
            'top_match': top_matches[0] if top_matches else None,
            'candidates': top_matches
        })

        # CSV 행 생성 (사람이 검증하기 쉽게)
        for i, match in enumerate(top_matches[:3]):  # 상위 3개만
            csv_rows.append({
                'cancer_name': cancer_name,
                'cancer_seq': cancer['seq'],
                'rank': i + 1,
                'kcd_code': match['kcd_code'],
                'kcd_name_kr': match['name_kr'],
                'kcd_name_en': match['name_en'],
                'match_ratio': f"{match['match_ratio']:.2%}",
                'match_count': match['match_count'],
                'keywords': ', '.join(keywords),
                'is_best_match': 'YES' if i == 0 else ''
            })

        print(f"  {cancer_name}: {len(top_matches)}개 후보 발견 (키워드: {keywords})")

    # JSON 저장
    output_json = {
        'metadata': {
            'creation_date': pd.Timestamp.now().isoformat(),
            'source_kcd': str(KCD_FILE),
            'source_ncc': str(NCC_DIR),
            'total_cancers': len(cancers),
            'method': 'keyword_search_code_based',
            'note': '이 파일은 자동 생성되었습니다. 수동 검증이 필요합니다.'
        },
        'mappings': mappings
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] JSON 매핑 파일 저장: {OUTPUT_FILE}")

    # CSV 저장 (사람이 검증용)
    df = pd.DataFrame(csv_rows)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

    print(f"[OK] CSV 검증 파일 저장: {OUTPUT_CSV}")

    # 통계
    print("\n" + "=" * 70)
    print("매핑 통계")
    print("=" * 70)

    no_match = [m for m in mappings if not m['kcd_codes']]
    single_match = [m for m in mappings if len(m['kcd_codes']) == 1]
    multi_match = [m for m in mappings if len(m['kcd_codes']) > 1]

    print(f"총 암종: {len(cancers)}개")
    print(f"  매칭 없음: {len(no_match)}개")
    print(f"  1개 매칭: {len(single_match)}개")
    print(f"  다중 매칭: {len(multi_match)}개")

    if no_match:
        print(f"\n매칭 실패한 암종:")
        for m in no_match:
            print(f"  - {m['cancer_name']} (키워드: {m['keywords']})")

    print("\n" + "=" * 70)
    print("다음 단계:")
    print(f"1. {OUTPUT_CSV} 파일을 Excel에서 열기")
    print(f"2. 각 암종별로 is_best_match 컬럼 검증 및 수정")
    print(f"3. 검증 완료 후 import_cancers.py에서 이 매핑 파일 사용")
    print("=" * 70)


if __name__ == "__main__":
    main()
