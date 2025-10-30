#!/usr/bin/env python3
"""
Upstage Document Parse API를 사용한 PDF 파싱

API Docs: https://developers.upstage.ai/docs/apis/document-parse
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# .env 파일 로드 (선택적)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class UpstagePDFParser:
    """Upstage Document Parse API 래퍼"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Upstage API 키 (None이면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv('UPSTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY not found in environment variables")

        self.base_url = "https://api.upstage.ai/v1/document-ai/document-parse"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def parse_pdf(
        self,
        pdf_path: str,
        output_format: str = "html",
        ocr: bool = True,
        coordinates: bool = False
    ) -> Dict[str, Any]:
        """
        PDF 파일을 파싱합니다.

        Args:
            pdf_path: PDF 파일 경로
            output_format: 출력 형식 ("html" or "markdown")
            ocr: OCR 사용 여부
            coordinates: 좌표 정보 포함 여부

        Returns:
            파싱 결과 딕셔너리
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        print(f"[Upstage] Parsing PDF: {pdf_path.name}")
        print(f"  - Format: {output_format}")
        print(f"  - OCR: {ocr}")
        print(f"  - Size: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")

        # API 요청 준비
        with open(pdf_path, 'rb') as f:
            files = {
                'document': (pdf_path.name, f, 'application/pdf')
            }

            data = {
                'ocr': str(ocr).lower(),
                'output_formats': f'["{output_format}"]',
            }

            if coordinates:
                data['coordinates'] = 'true'

            # API 호출
            start_time = time.time()
            response = requests.post(
                self.base_url,
                headers=self.headers,
                files=files,
                data=data,
                timeout=300  # 5분 타임아웃
            )

            elapsed = time.time() - start_time

        # 응답 확인
        if response.status_code != 200:
            error_msg = f"API Error {response.status_code}: {response.text}"
            print(f"[ERROR] {error_msg}")
            raise Exception(error_msg)

        result = response.json()

        # 메타데이터 추가
        result['metadata'] = {
            'source_file': str(pdf_path),
            'file_size_mb': pdf_path.stat().st_size / 1024 / 1024,
            'parsed_at': datetime.now().isoformat(),
            'elapsed_seconds': elapsed,
            'output_format': output_format,
            'ocr_enabled': ocr
        }

        print(f"[SUCCESS] Parsed in {elapsed:.2f}s")
        if 'content' in result:
            print(f"  - Content length: {len(result['content'])} chars")

        return result

    def save_result(
        self,
        result: Dict[str, Any],
        output_path: str,
        save_raw: bool = True
    ):
        """
        파싱 결과를 저장합니다.

        Args:
            result: 파싱 결과
            output_path: 출력 파일 경로 (.json)
            save_raw: 원본 content도 별도 파일로 저장 여부
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # JSON 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[SAVED] JSON: {output_path}")

        # Content 별도 저장
        if save_raw and 'content' in result:
            format_ext = result['metadata'].get('output_format', 'html')
            raw_path = output_path.with_suffix(f'.{format_ext}')
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(result['content'])
            print(f"[SAVED] Raw content: {raw_path}")


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Parse PDF using Upstage API')
    parser.add_argument('--input', required=True, help='Input PDF path')
    parser.add_argument('--output', required=True, help='Output JSON path')
    parser.add_argument('--format', default='html', choices=['html', 'markdown'],
                        help='Output format (default: html)')
    parser.add_argument('--no-ocr', action='store_true', help='Disable OCR')
    parser.add_argument('--coordinates', action='store_true', help='Include coordinates')
    parser.add_argument('--no-raw', action='store_true', help='Do not save raw content file')

    args = parser.parse_args()

    # API 키 확인
    api_key = os.getenv('UPSTAGE_API_KEY')
    if not api_key:
        print("[ERROR] UPSTAGE_API_KEY environment variable not set")
        print("Set it with: export UPSTAGE_API_KEY='your-api-key'")
        return 1

    # 파서 초기화
    parser_obj = UpstagePDFParser(api_key=api_key)

    try:
        # PDF 파싱
        result = parser_obj.parse_pdf(
            pdf_path=args.input,
            output_format=args.format,
            ocr=not args.no_ocr,
            coordinates=args.coordinates
        )

        # 결과 저장
        parser_obj.save_result(
            result=result,
            output_path=args.output,
            save_raw=not args.no_raw
        )

        print("\n[DONE] PDF parsing complete!")
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
