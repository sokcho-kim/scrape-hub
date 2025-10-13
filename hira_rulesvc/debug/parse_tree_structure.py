"""
tree.md를 파싱하여 계층 구조 데이터 생성
"""
from pathlib import Path
import json

TREE_MD = Path("docs/samples/hira_rulesvc/tree.md")
ALL_DOCS_JSON = Path("hira_rulesvc/config/all_law_documents.json")
OUTPUT_JSON = Path("hira_rulesvc/config/document_tree.json")


def parse_tree_md():
    """
    tree.md를 파싱하여 각 파일의 경로(path) 계산

    Returns:
        list: 각 문서의 seq, name, path 정보
    """
    # all_law_documents.json 로드 (SEQ 조회용)
    with open(ALL_DOCS_JSON, 'r', encoding='utf-8') as f:
        all_docs_data = json.load(f)

    # name -> seq 매핑 딕셔너리 생성
    name_to_seq = {}
    for doc in all_docs_data['documents']:
        name_to_seq[doc['name']] = doc['seq']

    # tree.md 파싱
    current_path = []
    documents = []

    with open(TREE_MD, 'r', encoding='utf-8') as f:
        for line in f:
            line_stripped = line.rstrip()

            if not line_stripped:
                continue

            if line_stripped.startswith('# '):  # Root (무시)
                current_path = []

            elif line_stripped.startswith('#### '):  # Level 3 폴더
                folder_name = line_stripped[5:].strip()
                current_path = current_path[:2] + [folder_name]

            elif line_stripped.startswith('### '):  # Level 2 폴더
                folder_name = line_stripped[4:].strip()
                current_path = current_path[:1] + [folder_name]

            elif line_stripped.startswith('## '):  # Level 1 폴더
                folder_name = line_stripped[3:].strip()
                current_path = [folder_name]

            elif line_stripped.startswith('* '):  # 파일
                file_name = line_stripped[2:].strip()

                # SEQ 찾기
                seq = name_to_seq.get(file_name)
                if seq:
                    documents.append({
                        'seq': seq,
                        'name': file_name,
                        'path': current_path.copy()
                    })

    return documents


def main():
    print("=" * 60)
    print("tree.md 파싱")
    print("=" * 60)

    print("\n1. tree.md 파싱 중...")
    documents = parse_tree_md()
    print(f"   총 {len(documents)}개 문서 파싱 완료")

    print("\n2. 결과 미리보기 (첫 5개):")
    for doc in documents[:5]:
        path_str = " → ".join(doc['path']) if doc['path'] else "(루트)"
        print(f"   SEQ={doc['seq']:3s} | {path_str} → {doc['name']}")

    print("\n3. 결과 저장 중...")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({
            'total_count': len(documents),
            'documents': documents
        }, f, ensure_ascii=False, indent=2)
    print(f"   저장 완료: {OUTPUT_JSON}")

    # 통계
    print("\n4. 통계:")
    path_lengths = [len(doc['path']) for doc in documents]
    print(f"   - 루트 레벨 (path 길이 0): {path_lengths.count(0)}개")
    print(f"   - Level 1 (path 길이 1): {path_lengths.count(1)}개")
    print(f"   - Level 2 (path 길이 2): {path_lengths.count(2)}개")
    print(f"   - Level 3 (path 길이 3): {path_lengths.count(3)}개")

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)


if __name__ == '__main__':
    main()
