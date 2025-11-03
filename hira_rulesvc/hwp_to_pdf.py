#!/usr/bin/env python3
"""
HWP → PDF 변환기
한컴오피스 COM 자동화 사용
"""
import os
import sys
import time
from pathlib import Path
import win32com.client
import pythoncom


class HwpToPdfConverter:
    """한컴오피스를 사용한 HWP → PDF 변환기"""

    def __init__(self):
        self.hwp = None

    def __enter__(self):
        """COM 객체 생성"""
        pythoncom.CoInitialize()
        try:
            self.hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
            # 창 숨김 설정
            self.hwp.XHwpWindows.Item(0).Visible = False
        except Exception as e:
            print(f"[ERROR] Failed to create HWP COM object: {e}")
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """COM 객체 정리"""
        if self.hwp:
            try:
                self.hwp.Quit()
            except:
                pass
        pythoncom.CoUninitialize()

    def convert(self, hwp_path: Path, pdf_path: Path) -> bool:
        """
        HWP 파일을 PDF로 변환

        Args:
            hwp_path: HWP 파일 경로
            pdf_path: 출력 PDF 경로

        Returns:
            성공 여부
        """
        try:
            # 절대 경로로 변환
            hwp_path = hwp_path.resolve()
            pdf_path = pdf_path.resolve()

            print(f"[CONVERT] {hwp_path.name} -> {pdf_path.name}")

            # 출력 디렉토리 생성
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            # HWP 파일 열기
            print(f"  [OPEN] Opening HWP file: {hwp_path}")
            try:
                # Open(filename, format, arg)
                # format: "HWP", "HWPX", "" (자동 감지)
                # arg: "versionwarning:false" 등
                result = self.hwp.Open(str(hwp_path))
                print(f"  [OPEN] Open() returned: {result}")
            except Exception as e:
                print(f"  [ERROR] Open() exception: {e}")
                return False

            print(f"  [OPENED] HWP file loaded")

            # PDF로 저장
            # SaveAs(filename, format, arg)
            # format: "PDF"
            print(f"  [SAVE] Saving as PDF...")
            result = self.hwp.SaveAs(str(pdf_path), "PDF", "")
            if not result:
                print(f"  [ERROR] Failed to save as PDF")
                return False

            print(f"  [SUCCESS] PDF created: {pdf_path}")

            # 문서 닫기
            self.hwp.Clear(1)

            return True

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            return False


def convert_single_file(hwp_path: str, pdf_path: str) -> int:
    """단일 파일 변환"""
    hwp_file = Path(hwp_path)
    pdf_file = Path(pdf_path)

    if not hwp_file.exists():
        print(f"[ERROR] HWP file not found: {hwp_path}")
        return 1

    with HwpToPdfConverter() as converter:
        success = converter.convert(hwp_file, pdf_file)
        return 0 if success else 1


def convert_failed_files(
    failed_json: Path,
    input_dir: Path,
    output_dir: Path
) -> dict:
    """실패한 HWP 파일들을 PDF로 변환"""
    import json

    # 실패 파일 목록 로드
    with open(failed_json, 'r', encoding='utf-8') as f:
        summary = json.load(f)

    failed_files = summary.get('failed_files', [])

    if not failed_files:
        print("[INFO] No failed files to convert")
        return {'total': 0, 'success': 0, 'failed': 0}

    print("=" * 80)
    print(f"HWP → PDF 변환 ({len(failed_files)}개)")
    print("=" * 80)

    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    still_failed = []

    with HwpToPdfConverter() as converter:
        for i, failed_item in enumerate(failed_files, 1):
            hwp_path = Path(failed_item['path'])

            print(f"\n[{i}/{len(failed_files)}] {hwp_path.name}")

            # 출력 PDF 경로
            pdf_path = output_dir / f"{hwp_path.stem}.pdf"

            # 변환 시도
            success = converter.convert(hwp_path, pdf_path)

            if success:
                success_count += 1
            else:
                still_failed.append({
                    'path': str(hwp_path),
                    'error': 'PDF conversion failed'
                })

            # 잠시 대기 (COM 안정화)
            time.sleep(0.5)

    # 결과 요약
    print("\n" + "=" * 80)
    print("변환 완료")
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

    parser = argparse.ArgumentParser(description='HWP → PDF 변환')
    parser.add_argument('--input', '-i', help='HWP 파일 경로')
    parser.add_argument('--output', '-o', help='PDF 출력 경로')
    parser.add_argument('--batch', action='store_true',
                        help='실패 파일 일괄 변환')
    parser.add_argument('--failed-json',
                        default='data/hira_rulesvc/parsed/retry_summary.json',
                        help='실패 파일 JSON')
    parser.add_argument('--output-dir',
                        default='data/hira_rulesvc/converted_pdf',
                        help='PDF 출력 디렉토리')

    args = parser.parse_args()

    if args.batch:
        # 일괄 변환 모드
        base_dir = Path(__file__).parent.parent
        failed_json = base_dir / args.failed_json
        input_dir = base_dir / 'data/hira_rulesvc/documents'
        output_dir = base_dir / args.output_dir

        results = convert_failed_files(failed_json, input_dir, output_dir)

        # 결과 저장
        import json
        from datetime import datetime

        result_file = output_dir / 'conversion_summary.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n변환 요약: {result_file}")

        return 0 if results['failed'] == 0 else 1

    elif args.input and args.output:
        # 단일 파일 변환 모드
        return convert_single_file(args.input, args.output)

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
