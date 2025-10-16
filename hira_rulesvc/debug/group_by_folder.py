"""
폴더별로 문서를 그룹핑하는 스크립트

document_tree.json의 path를 기준으로 폴더별 문서 목록 생성
"""
import json
from pathlib import Path
from collections import defaultdict

def group_documents_by_folder():
    """폴더 경로별로 문서 그룹핑"""

    # document_tree.json 로드
    tree_file = Path("hira_rulesvc/config/document_tree.json")
    with open(tree_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 폴더별로 그룹핑
    folders = defaultdict(list)

    for doc in data['documents']:
        # path를 키로 사용 (리스트를 튜플로 변환)
        folder_key = tuple(doc['path'])
        folders[folder_key].append({
            'seq': doc['seq'],
            'name': doc['name']
        })

    # 결과 출력
    print(f"\n총 {len(folders)}개 폴더")
    print("=" * 80)

    for folder_path, docs in sorted(folders.items()):
        folder_str = ' > '.join(folder_path)
        print(f"\n폴더: {folder_str}")
        print(f"문서 수: {len(docs)}개")
        for doc in docs:
            print(f"  - [SEQ={doc['seq']}] {doc['name']}")

    # 결과를 JSON으로 저장
    output = []
    for folder_path, docs in folders.items():
        output.append({
            'folder_path': list(folder_path),
            'document_count': len(docs),
            'documents': docs
        })

    output_file = Path("hira_rulesvc/config/folders_grouped.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_folders': len(folders),
            'folders': output
        }, f, ensure_ascii=False, indent=2)

    print(f"\n\n저장 완료: {output_file}")
    print(f"총 {len(folders)}개 폴더, {sum(len(docs) for docs in folders.values())}개 문서")

if __name__ == '__main__':
    group_documents_by_folder()
