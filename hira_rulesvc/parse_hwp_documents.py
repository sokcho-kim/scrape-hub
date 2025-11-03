#!/usr/bin/env python3
"""
HIRA 급여기준 HWP 문서 파싱 (Upstage API 사용)

목적: 건강보험 급여기준 HWP 문서를 구조화된 JSON으로 변환
"""
import os
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class UpstageHWPParser:
    """Upstage API를 사용한 HWP 파서"""

    # Upstage API 제한
    MAX_FILE_SIZE_MB = 50
    MAX_PAGES_SYNC = 100

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.upstage.ai/v1/document-ai/document-parse"
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
        self.failed_files = []
        self.oversized_files = []

    def check_file_size(self, file_path: Path) -> bool:
        """파일 크기 체크 (50MB 제한)"""
        size_mb = file_path.stat().st_size / 1024 / 1024
        if size_mb > self.MAX_FILE_SIZE_MB:
            self.oversized_files.append({
                'path': str(file_path),
                'size_mb': round(size_mb, 2),
                'reason': f'파일 크기 초과 ({size_mb:.2f}MB > {self.MAX_FILE_SIZE_MB}MB)'
            })
            return False
        return True

    def parse_hwp(self, hwp_path: Path) -> Optional[Dict]:
        """
        HWP 파일을 Upstage API로 파싱

        Returns:
            {
                'file_name': '...',
                'file_size_mb': ...,
                'page_count': ...,
                'content': '...',  # 전체 텍스트
                'elements': [...],  # 구조화된 요소
                'metadata': {...}
            }
        """
        print(f"\n[PARSE] {hwp_path.name}")

        # 파일 크기 체크
        if not self.check_file_size(hwp_path):
            print(f"  [SKIP] 파일 크기 초과")
            return None

        # API 호출
        try:
            with open(hwp_path, 'rb') as f:
                files = {'document': f}
                data = {
                    'ocr': 'auto',  # OCR 자동 적용
                    'coordinates': 'true'  # 좌표 정보 포함
                }

                print(f"  [API] Uploading to Upstage...")
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    files=files,
                    data=data,
                    timeout=300  # 5분 타임아웃
                )

            if response.status_code != 200:
                error_msg = f"API 오류: {response.status_code}"
                print(f"  [ERROR] {error_msg}")
                print(f"  Response: {response.text[:200]}")
                self.failed_files.append({
                    'path': str(hwp_path),
                    'error': error_msg,
                    'response': response.text[:500]
                })
                return None

            # 응답 파싱
            result = response.json()

            # 데이터 구조화
            parsed_data = {
                'file_name': hwp_path.name,
                'file_size_mb': round(hwp_path.stat().st_size / 1024 / 1024, 2),
                'page_count': len(result.get('pages', [])),
                'content': result.get('content', {}).get('text', ''),
                'elements': result.get('elements', []),
                'metadata': {
                    'parsed_at': datetime.now().isoformat(),
                    'api': 'upstage-document-parse',
                    'model': result.get('model', 'unknown')
                }
            }

            print(f"  [OK] {parsed_data['page_count']} pages, {len(parsed_data['content'])} chars")
            return parsed_data

        except requests.exceptions.Timeout:
            error_msg = "API 타임아웃 (5분 초과)"
            print(f"  [ERROR] {error_msg}")
            self.failed_files.append({
                'path': str(hwp_path),
                'error': error_msg
            })
            return None

        except Exception as e:
            error_msg = f"파싱 실패: {str(e)}"
            print(f"  [ERROR] {error_msg}")
            self.failed_files.append({
                'path': str(hwp_path),
                'error': error_msg
            })
            return None

    def parse_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        skip_existing: bool = True
    ) -> Dict:
        """
        디렉토리 내 모든 HWP 파일 파싱

        Returns:
            {
                'total': ...,
                'success': ...,
                'failed': ...,
                'skipped': ...,
                'oversized': ...
            }
        """
        # HWP 파일 목록
        hwp_files = sorted(input_dir.glob('*.hwp'))
        hwp_files.extend(sorted(input_dir.glob('*.hwpx')))

        print("=" * 80)
        print("HIRA 급여기준 HWP 파싱")
        print("=" * 80)
        print(f"입력 디렉토리: {input_dir}")
        print(f"출력 디렉토리: {output_dir}")
        print(f"HWP 파일 수: {len(hwp_files)}개")
        print("=" * 80)

        # 출력 디렉토리 생성
        output_dir.mkdir(parents=True, exist_ok=True)

        # 파싱 진행
        success_count = 0
        skipped_count = 0

        for i, hwp_file in enumerate(hwp_files, 1):
            # 파일명 안전하게 출력 (유니코드 에러 방지)
            try:
                file_name = hwp_file.name
            except:
                file_name = hwp_file.stem

            print(f"\n[{i}/{len(hwp_files)}]", end=" ")
            try:
                print(file_name)
            except UnicodeEncodeError:
                print(f"[File {i}]")

            # 출력 파일명 생성
            output_file = output_dir / f"{hwp_file.stem}.json"

            # 이미 파싱된 파일 건너뛰기
            if skip_existing and output_file.exists():
                print(f"  [SKIP] 이미 파싱됨")
                skipped_count += 1
                continue

            # 파싱 실행
            parsed = self.parse_hwp(hwp_file)

            if parsed:
                # JSON 저장
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                print(f"  [SAVE] {output_file.name}")
                success_count += 1

            # API Rate Limit 고려 (초당 1개 정도)
            if i < len(hwp_files):
                time.sleep(1)

        # 결과 요약
        print("\n" + "=" * 80)
        print("파싱 완료")
        print("=" * 80)
        print(f"총 파일: {len(hwp_files)}개")
        print(f"성공: {success_count}개")
        print(f"실패: {len(self.failed_files)}개")
        print(f"건너뜀: {skipped_count}개")
        print(f"크기 초과: {len(self.oversized_files)}개")

        # 실패/초과 파일 리스트
        if self.failed_files:
            print("\n[실패 파일]")
            for item in self.failed_files:
                print(f"  - {Path(item['path']).name}: {item['error']}")

        if self.oversized_files:
            print("\n[크기 초과 파일 - 분할 필요]")
            for item in self.oversized_files:
                print(f"  - {Path(item['path']).name}: {item['size_mb']}MB")

        return {
            'total': len(hwp_files),
            'success': success_count,
            'failed': len(self.failed_files),
            'skipped': skipped_count,
            'oversized': len(self.oversized_files),
            'failed_files': self.failed_files,
            'oversized_files': self.oversized_files
        }


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='HIRA HWP 문서 파싱')
    parser.add_argument('--input', '-i',
                        default='data/hira_rulesvc/documents',
                        help='HWP 파일 디렉토리')
    parser.add_argument('--output', '-o',
                        default='data/hira_rulesvc/parsed',
                        help='출력 디렉토리')
    parser.add_argument('--skip-existing', action='store_true', default=True,
                        help='이미 파싱된 파일 건너뛰기')
    parser.add_argument('--force', action='store_true',
                        help='기존 파일 덮어쓰기')

    args = parser.parse_args()

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / args.input
    output_dir = base_dir / args.output

    # API 키 확인
    api_key = os.getenv('UPSTAGE_API_KEY')
    if not api_key:
        print("[ERROR] UPSTAGE_API_KEY 환경변수가 설정되지 않았습니다.")
        print("설정 방법:")
        print('  Windows: $env:UPSTAGE_API_KEY="your-api-key"')
        print('  Linux/Mac: export UPSTAGE_API_KEY="your-api-key"')
        return 1

    # 파서 초기화 및 실행
    parser = UpstageHWPParser(api_key)
    skip = args.skip_existing and not args.force

    results = parser.parse_directory(input_dir, output_dir, skip_existing=skip)

    # 결과 저장
    summary_file = output_dir / 'parse_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n요약 파일 저장: {summary_file}")

    # 분할 필요 파일 별도 저장
    if results['oversized_files']:
        oversized_file = output_dir / 'oversized_files.json'
        with open(oversized_file, 'w', encoding='utf-8') as f:
            json.dump(results['oversized_files'], f, ensure_ascii=False, indent=2)
        print(f"크기 초과 파일 목록: {oversized_file}")

    return 0 if results['failed'] == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
