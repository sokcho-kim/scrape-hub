"""
tree.md와 tree HTML을 비교하여 모든 리프 노드의 SEQ를 추출
"""
from pathlib import Path
import re
import json

TREE_MD = Path("docs/samples/hira_rulesvc/tree.md")
TREE_HTML = Path("data/hira_rulesvc/debug/step1_main_tree01.html")
OUTPUT_JSON = Path("hira_rulesvc/config/all_law_documents.json")

def extract_leaf_nodes_from_md():
    """
    tree.md에서 모든 리프 노드 추출 (* 로 시작하는 항목)
    """
    leaf_nodes = []

    with open(TREE_MD, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('* '):
                # '* ' 제거
                name = line[2:].strip()
                leaf_nodes.append(name)

    return leaf_nodes

def find_seq_in_html(name, html_content):
    """
    HTML에서 특정 이름의 SEQ 찾기
    """
    # gotoLawList 패턴 찾기
    # gotoLawList('2', '0', '요양급여비용 청구방법(보건복지부 고시)', '0', 'null', '1', '9', '1', '2284', 'http://', '')
    pattern = rf"gotoLawList\('(\d+)',\s*'(\d+)',\s*'{re.escape(name)}'"
    matches = re.findall(pattern, html_content)

    if matches:
        seq, is_folder = matches[0]
        return {
            'seq': seq,
            'is_folder': is_folder == '1',
            'name': name
        }

    return None

def main():
    print("=" * 60)
    print("HIRA 리프 노드 추출")
    print("=" * 60)

    # 1. tree.md에서 리프 노드 추출
    print("\n1. tree.md에서 리프 노드 추출 중...")
    leaf_nodes = extract_leaf_nodes_from_md()
    print(f"   총 {len(leaf_nodes)}개 리프 노드 발견")

    # 2. tree HTML 로드
    print("\n2. tree HTML 로드 중...")
    with open(TREE_HTML, 'r', encoding='utf-8') as f:
        html_content = f.read()
    print(f"   HTML 크기: {len(html_content)} bytes")

    # 3. 각 리프 노드의 SEQ 찾기
    print("\n3. 각 리프 노드의 SEQ 매핑 중...")
    results = []
    not_found = []

    for idx, name in enumerate(leaf_nodes, 1):
        info = find_seq_in_html(name, html_content)
        if info:
            results.append(info)
            print(f"   [{idx}/{len(leaf_nodes)}] {name} → SEQ={info['seq']} (폴더={info['is_folder']})")
        else:
            not_found.append(name)
            print(f"   [{idx}/{len(leaf_nodes)}] {name} → [NOT FOUND]")

    # 4. 결과 저장
    print(f"\n4. 결과 저장 중: {OUTPUT_JSON}")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({
            'total_count': len(results),
            'documents': results,
            'not_found': not_found
        }, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"완료! 총 {len(results)}개 문서 매핑")
    print(f"찾지 못한 항목: {len(not_found)}개")
    if not_found:
        print("\n찾지 못한 항목:")
        for name in not_found:
            print(f"  - {name}")
    print("=" * 60)

if __name__ == '__main__':
    main()
