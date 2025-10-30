"""NCC 100개 암종 리스트 추출"""
import json
from pathlib import Path

def extract_cancer_list():
    """NCC 암종 파일에서 암종명 추출"""
    cancer_dir = Path("data/ncc/cancer_info/parsed")

    # _숫자.json 형식의 파일만 (100개 암종)
    cancer_files = list(cancer_dir.glob("*_[0-9]*.json"))

    cancer_names = []
    cancer_details = []

    for file in cancer_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cancer_name = data.get('name', '')
        if cancer_name:
            cancer_names.append(cancer_name)
            cancer_details.append({
                'name': cancer_name,
                'cancer_seq': data.get('cancer_seq', ''),
                'tags': data.get('tags', [])
            })

    # 정렬
    cancer_names.sort()
    cancer_details.sort(key=lambda x: x['name'])

    print(f"총 {len(cancer_names)}개 암종 추출\n")

    # 암종명만 출력 (처음 20개)
    print("[처음 20개 암종]")
    for i, name in enumerate(cancer_names[:20], 1):
        print(f"  {i}. {name}")

    print(f"\n... (총 {len(cancer_names)}개)")

    # 파일로 저장
    output = {
        'cancer_names': cancer_names,
        'cancer_details': cancer_details,
        'total': len(cancer_names)
    }

    output_file = Path("ncc/cancer_dictionary/ncc_cancer_list.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[완료] 암종 리스트 저장: {output_file}")

    return cancer_names, cancer_details


if __name__ == '__main__':
    extract_cancer_list()
