#!/usr/bin/env python3
"""
수동 변환된 PDF 파일 파싱 (Upstage API 사용)
"""
import os
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class UpstagePDFParser:
    """Upstage API를 사용한 PDF 파서"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.upstage.ai/v1/document-ai/document-parse"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def parse_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """
        PDF 파일을 Upstage API로 파싱

        Returns:
            파싱 결과 또는 None (실패 시)
        """
        print(f"\n[PARSE] {pdf_path.name}")

        try:
            with open(pdf_path, 'rb') as f:
                files = {'document': f}
                data = {
                    'ocr': 'auto',
                    'coordinates': 'true'
                }

                print(f"  [API] Uploading to Upstage...")
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    files=files,
                    data=data,
                    timeout=300
                )

            if response.status_code != 200:
                error_msg = f"API {response.status_code}"
                print(f"  [ERROR] {error_msg}")
                print(f"  Response: {response.text[:200]}")
                return None

            # 응답 파싱
            result = response.json()

            # 데이터 구조화
            parsed_data = {
                'file_name': pdf_path.name,
                'file_size_mb': round(pdf_path.stat().st_size / 1024 / 1024, 2),
                'page_count': len(result.get('pages', [])),
                'content': result.get('content', {}).get('text', ''),
                'elements': result.get('elements', []),
                'metadata': {
                    'parsed_at': datetime.now().isoformat(),
                    'api': 'upstage-document-parse',
                    'model': result.get('model', 'unknown'),
                    'source': 'manual_pdf'
                }
            }

            print(f"  [OK] {parsed_data['page_count']} pages, {len(parsed_data['content'])} chars")
            return parsed_data

        except requests.exceptions.Timeout:
            print(f"  [ERROR] API timeout (5분 초과)")
            return None

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            return None

    def parse_directory(self, pdf_dir: Path, output_dir: Path) -> Dict:
        """디렉토리 내 모든 PDF 파일 파싱"""

        pdf_files = sorted(pdf_dir.glob('*.pdf'))

        if not pdf_files:
            print("[INFO] No PDF files found")
            return {'total': 0, 'success': 0, 'failed': 0}

        print("=" * 80)
        print(f"수동 변환 PDF 파싱 ({len(pdf_files)}개)")
        print("=" * 80)
        print(f"입력 디렉토리: {pdf_dir}")
        print(f"출력 디렉토리: {output_dir}")
        print("=" * 80)

        output_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        failed_files = []

        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}]", end=" ")

            # 출력 파일명
            output_file = output_dir / f"{pdf_file.stem}.json"

            # 이미 파싱되었으면 건너뛰기
            if output_file.exists():
                print(f"{pdf_file.name}")
                print(f"  [SKIP] 이미 파싱됨")
                continue

            # 파싱 실행
            parsed = self.parse_pdf(pdf_file)

            if parsed:
                # JSON 저장
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                print(f"  [SAVE] {output_file.name}")
                success_count += 1
            else:
                failed_files.append({
                    'path': str(pdf_file),
                    'error': 'Parsing failed'
                })

            # API Rate Limit
            if i < len(pdf_files):
                time.sleep(1)

        # 결과 요약
        print("\n" + "=" * 80)
        print("파싱 완료")
        print("=" * 80)
        print(f"총 파일: {len(pdf_files)}개")
        print(f"성공: {success_count}개")
        print(f"실패: {len(failed_files)}개")

        if failed_files:
            print("\n[실패 파일]")
            for item in failed_files:
                print(f"  - {Path(item['path']).name}")

        return {
            'total': len(pdf_files),
            'success': success_count,
            'failed': len(failed_files),
            'failed_files': failed_files
        }


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='수동 변환 PDF 파싱')
    parser.add_argument('--pdf-dir',
                        default='data/hira_rulesvc/documents',
                        help='PDF 디렉토리')
    parser.add_argument('--output-dir',
                        default='data/hira_rulesvc/parsed',
                        help='JSON 출력 디렉토리')

    args = parser.parse_args()

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    pdf_dir = base_dir / args.pdf_dir
    output_dir = base_dir / args.output_dir

    # API 키 확인
    api_key = os.getenv('UPSTAGE_API_KEY')
    if not api_key:
        print("[ERROR] UPSTAGE_API_KEY 환경변수가 설정되지 않았습니다.")
        return 1

    # PDF 디렉토리 확인
    if not pdf_dir.exists():
        print(f"[ERROR] PDF 디렉토리가 없습니다: {pdf_dir}")
        print("수동 변환된 PDF 파일을 이 디렉토리에 넣어주세요.")
        return 1

    # 파서 초기화 및 실행
    parser = UpstagePDFParser(api_key)
    results = parser.parse_directory(pdf_dir, output_dir)

    # 결과 저장
    summary_file = output_dir / 'manual_pdf_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n요약 파일: {summary_file}")

    return 0 if results['failed'] == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
