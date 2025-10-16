"""
다운로드된 파일과 document_tree.json 비교 검증 스크립트
"""
import json
from pathlib import Path

def verify_downloads():
    """다운로드된 파일 검증"""

    # document_tree.json 로드
    tree_file = Path("hira_rulesvc/config/document_tree.json")
    with open(tree_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    expected_docs = data['documents']

    # 다운로드된 파일 목록
    download_dir = Path("data/hira_rulesvc/documents")
    downloaded_files = [f.name for f in download_dir.glob("*.hwp")]

    print(f"\n{'='*80}")
    print(f"다운로드 검증 리포트")
    print(f"{'='*80}")
    print(f"\n예상 문서 수: {len(expected_docs)}개")
    print(f"다운로드된 파일 수: {len(downloaded_files)}개")
    print(f"성공률: {len(downloaded_files)/len(expected_docs)*100:.1f}%")

    # 미수집 문서 찾기
    missing_docs = []

    for doc in expected_docs:
        name = doc['name']
        seq = doc['seq']
        path = ' > '.join(doc['path'])

        # 파일명 매칭 (부분 일치)
        found = False
        for filename in downloaded_files:
            if name in filename:
                found = True
                break

        if not found:
            missing_docs.append({
                'seq': seq,
                'name': name,
                'path': path
            })

    # 결과 출력
    if missing_docs:
        print(f"\n{'='*80}")
        print(f"미수집 문서 목록 ({len(missing_docs)}개)")
        print(f"{'='*80}")
        for idx, doc in enumerate(missing_docs, 1):
            print(f"\n{idx}. [{doc['seq']}] {doc['name']}")
            print(f"   경로: {doc['path']}")
    else:
        print(f"\n✓ 모든 문서 수집 완료!")

    # 다운로드된 파일 목록 (파일로 저장)
    output_file = Path("hira_rulesvc/debug/downloaded_list.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"다운로드된 파일 목록 ({len(downloaded_files)}개)\n")
        f.write(f"{'='*80}\n")
        for idx, filename in enumerate(sorted(downloaded_files), 1):
            f.write(f"{idx:2d}. {filename}\n")

    print(f"\n다운로드된 파일 목록은 {output_file}에 저장되었습니다.")

    # 중복 파일 찾기
    print(f"\n{'='*80}")
    print(f"중복 파일 검사")
    print(f"{'='*80}")

    # 괄호 제거한 이름으로 중복 체크
    from collections import Counter
    clean_names = []
    for filename in downloaded_files:
        # 괄호 안 내용 제거
        clean = filename.split('(')[0].strip() if '(' in filename else filename
        clean = clean.replace('[2]', '').strip()
        clean_names.append(clean)

    duplicates = {name: count for name, count in Counter(clean_names).items() if count > 1}

    if duplicates:
        print(f"중복 파일 발견: {len(duplicates)}개")
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"중복 파일 발견: {len(duplicates)}개\n")
            f.write(f"{'='*80}\n")
            for name, count in duplicates.items():
                print(f"  - {name}: {count}개")
                f.write(f"  - {name}: {count}개\n")
                matching = [fname for fname in downloaded_files if name in fname]
                for m in matching:
                    print(f"    → {m}")
                    f.write(f"    → {m}\n")
    else:
        print("중복 파일 없음")

if __name__ == '__main__':
    verify_downloads()
