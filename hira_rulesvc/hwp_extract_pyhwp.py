#!/usr/bin/env python3
"""
pyhwp를 사용한 HWP 텍스트 추출
"""
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


def extract_text_with_pyhwp(hwp_path: Path, output_txt: Path) -> bool:
    """
    pyhwp의 hwp5txt 명령으로 텍스트 추출

    Args:
        hwp_path: HWP 파일 경로
        output_txt: 출력 텍스트 파일 경로

    Returns:
        성공 여부
    """
    try:
        print(f"[EXTRACT] {hwp_path.name}")

        # hwp5txt 실행 파일 경로
        base_dir = Path(__file__).parent.parent
        hwp5txt_exe = base_dir / 'scraphub' / 'Scripts' / 'hwp5txt.exe'

        # hwp5txt 명령 실행
        result = subprocess.run(
            [str(hwp5txt_exe), str(hwp_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )

        if result.returncode != 0:
            print(f"  [ERROR] hwp5txt failed: {result.stderr[:200]}")
            return False

        # 텍스트 저장
        output_txt.parent.mkdir(parents=True, exist_ok=True)
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(result.stdout)

        lines = len(result.stdout.splitlines())
        chars = len(result.stdout)
        print(f"  [SUCCESS] {lines} lines, {chars} chars")

        return True

    except subprocess.TimeoutExpired:
        print(f"  [ERROR] Timeout (60s)")
        return False
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False


def extract_html_with_pyhwp(hwp_path: Path, output_html: Path) -> bool:
    """
    pyhwp의 hwp5html 명령으로 HTML 변환

    Args:
        hwp_path: HWP 파일 경로
        output_html: 출력 HTML 파일 경로

    Returns:
        성공 여부
    """
    try:
        print(f"[HTML] {hwp_path.name}")

        # hwp5html 실행 파일 경로
        base_dir = Path(__file__).parent.parent
        hwp5html_exe = base_dir / 'scraphub' / 'Scripts' / 'hwp5html.exe'

        # hwp5html 명령 실행
        result = subprocess.run(
            [str(hwp5html_exe), str(hwp_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )

        if result.returncode != 0:
            print(f"  [ERROR] hwp5html failed: {result.stderr[:200]}")
            return False

        # HTML 저장
        output_html.parent.mkdir(parents=True, exist_ok=True)
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(result.stdout)

        print(f"  [SUCCESS] HTML created")

        return True

    except subprocess.TimeoutExpired:
        print(f"  [ERROR] Timeout (60s)")
        return False
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False


def extract_failed_files(
    failed_json: Path,
    output_dir: Path,
    format: str = 'txt'
) -> Dict:
    """실패한 HWP 파일들에서 텍스트/HTML 추출"""

    # 실패 파일 목록 로드
    with open(failed_json, 'r', encoding='utf-8') as f:
        summary = json.load(f)

    failed_files = summary.get('failed_files', [])

    if not failed_files:
        print("[INFO] No failed files to process")
        return {'total': 0, 'success': 0, 'failed': 0}

    print("=" * 80)
    print(f"pyhwp로 텍스트 추출 ({len(failed_files)}개)")
    print("=" * 80)

    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    still_failed = []

    for i, failed_item in enumerate(failed_files, 1):
        hwp_path = Path(failed_item['path'])

        print(f"\n[{i}/{len(failed_files)}] {hwp_path.name}")

        if format == 'txt':
            output_file = output_dir / f"{hwp_path.stem}.txt"
            success = extract_text_with_pyhwp(hwp_path, output_file)
        elif format == 'html':
            output_file = output_dir / f"{hwp_path.stem}.html"
            success = extract_html_with_pyhwp(hwp_path, output_file)
        else:
            # 둘 다 시도
            txt_file = output_dir / f"{hwp_path.stem}.txt"
            html_file = output_dir / f"{hwp_path.stem}.html"
            success_txt = extract_text_with_pyhwp(hwp_path, txt_file)
            success_html = extract_html_with_pyhwp(hwp_path, html_file)
            success = success_txt or success_html

        if success:
            success_count += 1
        else:
            still_failed.append({
                'path': str(hwp_path),
                'error': 'pyhwp extraction failed'
            })

    # 결과 요약
    print("\n" + "=" * 80)
    print("추출 완료")
    print("=" * 80)
    print(f"총 시도: {len(failed_files)}개")
    print(f"성공: {success_count}개")
    print(f"여전히 실패: {len(still_failed)}개")

    if still_failed:
        print("\n[여전히 실패한 파일]")
        for item in still_failed:
            print(f"  - {Path(item['path']).name}")

    return {
        'total': len(failed_files),
        'success': success_count,
        'failed': len(still_failed),
        'failed_files': still_failed
    }


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='pyhwp로 HWP 텍스트 추출')
    parser.add_argument('--input', '-i', help='HWP 파일 경로')
    parser.add_argument('--output', '-o', help='출력 파일 경로')
    parser.add_argument('--format', choices=['txt', 'html', 'both'],
                        default='txt', help='출력 형식')
    parser.add_argument('--batch', action='store_true',
                        help='실패 파일 일괄 처리')
    parser.add_argument('--failed-json',
                        default='data/hira_rulesvc/parsed/retry_summary.json',
                        help='실패 파일 JSON')
    parser.add_argument('--output-dir',
                        default='data/hira_rulesvc/pyhwp_extracted',
                        help='출력 디렉토리')

    args = parser.parse_args()

    if args.batch:
        # 일괄 처리 모드
        base_dir = Path(__file__).parent.parent
        failed_json = base_dir / args.failed_json
        output_dir = base_dir / args.output_dir

        results = extract_failed_files(failed_json, output_dir, args.format)

        # 결과 저장
        result_file = output_dir / 'extraction_summary.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n추출 요약: {result_file}")

        return 0 if results['failed'] == 0 else 1

    elif args.input and args.output:
        # 단일 파일 처리
        hwp_path = Path(args.input)
        output_path = Path(args.output)

        if args.format == 'html':
            success = extract_html_with_pyhwp(hwp_path, output_path)
        else:
            success = extract_text_with_pyhwp(hwp_path, output_path)

        return 0 if success else 1

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
