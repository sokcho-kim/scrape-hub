"""
HIRA 고시 문서 파싱 스크립트

Upstage Document Parse API를 사용하여
HWP/PDF 문서를 Markdown으로 변환하고 메타데이터 연결
"""
from pathlib import Path
import json
import sys
import codecs
from datetime import datetime

# UTF-8 출력 설정 (Windows)
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 상위 디렉토리 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from shared.parsers import ParserFactory


def load_document_tree():
    """document_tree.json 로드"""
    tree_path = Path(__file__).parent / "config" / "document_tree.json"
    with open(tree_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_metadata(filename: str, doc_tree: dict) -> dict:
    """
    파일명으로 document_tree.json에서 메타데이터 찾기

    Args:
        filename: 파일명
        doc_tree: document_tree.json 데이터

    Returns:
        메타데이터 (seq, name, path)
    """
    for doc in doc_tree['documents']:
        # 파일명과 문서명 매칭
        if doc['name'] in filename:
            return {
                "seq": doc['seq'],
                "name": doc['name'],
                "path": doc['path'],
                "category": _categorize(doc['path'])
            }

    return {}


def _categorize(path: list) -> str:
    """
    폴더 경로로 카테고리 분류

    Args:
        path: 폴더 계층 경로

    Returns:
        카테고리 ("법령", "고시", "행정해석")
    """
    if not path:
        return "기타"

    # 행정해석 판단
    if "행정해석" in path:
        return "행정해석"

    # 고시기준 판단
    if "고시기준" in path or any("고시" in p for p in path):
        return "고시"

    # 법령 판단
    if any("법" in p for p in path):
        return "법령"

    return "기타"


def parse_sample(sample_count: int = 3):
    """
    샘플 파일 파싱 테스트

    Args:
        sample_count: 테스트할 파일 개수
    """
    print("=" * 80)
    print("샘플 파싱 테스트")
    print("=" * 80)

    docs_dir = Path("data/hira_rulesvc/documents")
    output_dir = Path("data/hira_rulesvc/parsed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 파서 생성
    parser = ParserFactory.create("upstage")
    doc_tree = load_document_tree()

    # 샘플 파일 선택 (크기 작은 순)
    files = sorted(
        list(docs_dir.glob("*.hwp")) + list(docs_dir.glob("*.pdf")),
        key=lambda f: f.stat().st_size
    )[:sample_count]

    print(f"\n{len(files)}개 파일 샘플 테스트\n")

    total_pages = 0
    total_cost = 0.0

    for i, file_path in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] {file_path.name[:60]}")
            print(f"  크기: {file_path.stat().st_size/1024:.1f} KB", end=" ")

            # 파싱
            result = parser.parse(file_path)

            # 메타데이터 추가
            metadata = get_metadata(file_path.name, doc_tree)
            result['metadata'].update(metadata)
            result['filename'] = file_path.name
            result['parsed_at'] = datetime.now().isoformat()

            # 저장
            output_file = output_dir / f"{file_path.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            pages = result.get('pages', 0)
            total_pages += pages
            cost = pages * 0.01

            print(f"→ {pages} 페이지 (${cost:.2f}) ✓")
            print(f"  저장: {output_file.name}\n")

        except Exception as e:
            print(f"  ✗ Error: {e}\n")

    print("-" * 80)
    print(f"완료: {len(files)}개 파일")
    print(f"총 페이지: {total_pages}")
    print(f"비용: ${total_pages * 0.01:.2f} (약 ₩{int(total_pages * 0.01 * 1300):,})")
    print("=" * 80)


def parse_all():
    """전체 문서 파싱"""
    print("=" * 80)
    print("HIRA 문서 전체 파싱")
    print("=" * 80)

    # 설정
    docs_dir = Path("data/hira_rulesvc/documents")
    output_dir = Path("data/hira_rulesvc/parsed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 파서 생성
    parser = ParserFactory.create("upstage")
    doc_tree = load_document_tree()

    # 파일 목록
    files = sorted(list(docs_dir.glob("*.hwp")) + list(docs_dir.glob("*.pdf")))

    print(f"\n총 {len(files)}개 파일 파싱 시작...\n")

    results = []
    total_pages = 0
    success_count = 0
    fail_count = 0

    for i, file_path in enumerate(files, 1):
        try:
            # 파일명 표시 (50자 제한)
            display_name = file_path.name
            if len(display_name) > 50:
                display_name = display_name[:47] + "..."

            print(f"[{i:2d}/{len(files)}] {display_name:<50}", end=" ")

            # 파싱
            result = parser.parse(file_path)

            # 메타데이터 추가
            metadata = get_metadata(file_path.name, doc_tree)
            result['metadata'].update(metadata)
            result['filename'] = file_path.name
            result['parsed_at'] = datetime.now().isoformat()

            # 저장
            output_file = output_dir / f"{file_path.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            pages = result.get('pages', 0)
            total_pages += pages
            success_count += 1

            print(f"✓ ({pages:2d}p)")

            results.append(result)

        except Exception as e:
            fail_count += 1
            print(f"✗ {str(e)[:30]}")

    # 요약 통계
    print("\n" + "=" * 80)
    print("파싱 완료")
    print("-" * 80)
    print(f"성공: {success_count}/{len(files)} 파일")
    print(f"실패: {fail_count} 파일")
    print(f"총 페이지: {total_pages} 페이지")
    print(f"비용: ${total_pages * 0.01:.2f} (약 ₩{int(total_pages * 0.01 * 1300):,}원)")
    print("=" * 80)

    # 결과 저장
    summary_file = output_dir / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_files": len(files),
            "success": success_count,
            "fail": fail_count,
            "total_pages": total_pages,
            "cost_usd": total_pages * 0.01,
            "cost_krw": int(total_pages * 0.01 * 1300),
            "parsed_at": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

    print(f"\n요약 저장: {summary_file}")


def retry_failed(use_ocr: bool = False):
    """
    실패한 파일만 재시도

    Args:
        use_ocr: True면 Digitization API (강제 OCR) 사용
    """
    print("=" * 80)
    if use_ocr:
        print("HIRA 문서 실패 파일 재파싱 (OCR 강제 모드)")
    else:
        print("HIRA 문서 실패 파일 재파싱")
    print("=" * 80)

    # 설정
    docs_dir = Path("data/hira_rulesvc/documents")
    output_dir = Path("data/hira_rulesvc/parsed")

    # 파서 생성
    parser = ParserFactory.create("upstage")
    doc_tree = load_document_tree()

    # 전체 파일 목록
    all_files = sorted(list(docs_dir.glob("*.hwp")) + list(docs_dir.glob("*.pdf")))

    # 이미 파싱된 파일 확인
    parsed_files = {f.stem for f in output_dir.glob("*.json") if f.name != "_summary.json"}

    # 실패한 파일 추출
    failed_files = [f for f in all_files if f.stem not in parsed_files]

    if not failed_files:
        print("\n실패한 파일이 없습니다. 모든 파일이 파싱되었습니다.")
        return

    print(f"\n총 {len(failed_files)}개 실패 파일 재시도...")
    if use_ocr:
        print("⚡ Digitization API (강제 OCR) 모드 사용\n")
    else:
        print()

    results = []
    total_pages = 0
    success_count = 0
    fail_count = 0

    for i, file_path in enumerate(failed_files, 1):
        try:
            # 파일명 표시
            display_name = file_path.name
            if len(display_name) > 50:
                display_name = display_name[:47] + "..."

            print(f"[{i:2d}/{len(failed_files)}] {display_name:<50}", end=" ")

            # 파싱 (OCR 모드 선택)
            if use_ocr:
                result = parser.parse_with_ocr(file_path)
            else:
                result = parser.parse(file_path)

            # 메타데이터 추가
            metadata = get_metadata(file_path.name, doc_tree)
            result['metadata'].update(metadata)
            result['filename'] = file_path.name
            result['parsed_at'] = datetime.now().isoformat()

            # 저장
            output_file = output_dir / f"{file_path.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            pages = result.get('pages', 0)
            total_pages += pages
            success_count += 1

            print(f"✓ ({pages:2d}p)")

            results.append(result)

        except Exception as e:
            fail_count += 1
            error_msg = str(e)[:40]
            print(f"✗ {error_msg}")

    # 요약 통계
    print("\n" + "=" * 80)
    print("재파싱 완료")
    print("-" * 80)
    print(f"성공: {success_count}/{len(failed_files)} 파일")
    print(f"실패: {fail_count} 파일")
    print(f"추가 페이지: {total_pages} 페이지")
    print(f"추가 비용: ${total_pages * 0.01:.2f} (약 ₩{int(total_pages * 0.01 * 1300):,}원)")

    # 전체 통계 업데이트
    summary_file = output_dir / "_summary.json"
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            old_summary = json.load(f)

        new_summary = {
            "total_files": old_summary["total_files"],
            "success": old_summary["success"] + success_count,
            "fail": old_summary["fail"] - success_count + fail_count,
            "total_pages": old_summary["total_pages"] + total_pages,
            "cost_usd": (old_summary["total_pages"] + total_pages) * 0.01,
            "cost_krw": int((old_summary["total_pages"] + total_pages) * 0.01 * 1300),
            "parsed_at": datetime.now().isoformat()
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(new_summary, f, ensure_ascii=False, indent=2)

        print("-" * 80)
        print(f"전체 성공률: {new_summary['success']}/{new_summary['total_files']} 파일")
        print(f"전체 페이지: {new_summary['total_pages']} 페이지")
        print(f"전체 비용: ${new_summary['cost_usd']:.2f} (약 ₩{new_summary['cost_krw']:,}원)")

    print("=" * 80)


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='HIRA 문서 파싱')
    parser.add_argument(
        '--sample',
        type=int,
        metavar='N',
        help='샘플 N개 파일만 테스트'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='전체 파일 파싱'
    )
    parser.add_argument(
        '--retry',
        action='store_true',
        help='실패한 파일만 재시도'
    )
    parser.add_argument(
        '--ocr',
        action='store_true',
        help='강제 OCR 모드 사용 (Digitization API)'
    )

    args = parser.parse_args()

    if args.sample:
        parse_sample(args.sample)
    elif args.all:
        parse_all()
    elif args.retry:
        retry_failed(use_ocr=args.ocr)
    else:
        # 기본: 3개 샘플 테스트
        print("사용법:")
        print("  python hira_rulesvc/parse_documents.py --sample 5     # 샘플 5개 테스트")
        print("  python hira_rulesvc/parse_documents.py --all           # 전체 파싱")
        print("  python hira_rulesvc/parse_documents.py --retry         # 실패 파일 재시도")
        print("  python hira_rulesvc/parse_documents.py --retry --ocr   # OCR 강제 모드로 재시도")
        print()
        print("기본: 샘플 3개 테스트")
        print()
        parse_sample(3)


if __name__ == "__main__":
    main()
