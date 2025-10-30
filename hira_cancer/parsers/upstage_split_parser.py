#!/usr/bin/env python3
"""
대용량 PDF를 100페이지씩 분할해서 Upstage API로 파싱

배경: Upstage API는 최대 100페이지 제한
전략: PyMuPDF로 100페이지씩 분할 → 각각 파싱 → 병합
"""
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
from datetime import datetime

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import pymupdf  # PyMuPDF
except ImportError:
    print("[ERROR] PyMuPDF not installed. Install with: uv pip install pymupdf")
    exit(1)


class UpstageSplitParser:
    """대용량 PDF 분할 파싱"""

    def __init__(self, api_key: str = None, chunk_size: int = 100):
        """
        Args:
            api_key: Upstage API 키
            chunk_size: 분할 크기 (기본 100페이지)
        """
        self.api_key = api_key or os.getenv('UPSTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY not found")

        self.chunk_size = chunk_size
        self.base_url = "https://api.upstage.ai/v1/document-ai/document-parse"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def get_pdf_info(self, pdf_path: Path) -> Dict[str, Any]:
        """PDF 정보 확인"""
        doc = pymupdf.open(pdf_path)
        info = {
            'total_pages': doc.page_count,
            'file_size_mb': pdf_path.stat().st_size / 1024 / 1024,
            'chunks_needed': (doc.page_count + self.chunk_size - 1) // self.chunk_size
        }
        doc.close()
        return info

    def split_pdf(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """
        PDF를 chunk_size 페이지씩 분할

        Returns:
            분할된 PDF 경로 리스트
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        doc = pymupdf.open(pdf_path)
        total_pages = doc.page_count

        chunk_paths = []
        for i in range(0, total_pages, self.chunk_size):
            start = i
            end = min(i + self.chunk_size, total_pages)

            # 새 PDF 생성
            chunk_doc = pymupdf.open()
            chunk_doc.insert_pdf(doc, from_page=start, to_page=end - 1)

            # 저장
            chunk_path = output_dir / f"{pdf_path.stem}_chunk_{start+1:04d}-{end:04d}.pdf"
            chunk_doc.save(chunk_path)
            chunk_doc.close()

            chunk_paths.append(chunk_path)
            print(f"[SPLIT] Pages {start+1}-{end} → {chunk_path.name}")

        doc.close()
        print(f"[SPLIT] Total {len(chunk_paths)} chunks created")
        return chunk_paths

    def parse_chunk(self, chunk_path: Path, output_format: str = "html") -> Dict[str, Any]:
        """단일 청크 파싱"""
        print(f"\n[PARSE] {chunk_path.name}")

        with open(chunk_path, 'rb') as f:
            files = {'document': (chunk_path.name, f, 'application/pdf')}
            data = {
                'ocr': 'true',
                'output_formats': f'["{output_format}"]',
            }

            start_time = time.time()
            response = requests.post(
                self.base_url,
                headers=self.headers,
                files=files,
                data=data,
                timeout=300
            )
            elapsed = time.time() - start_time

        if response.status_code != 200:
            error_msg = f"API Error {response.status_code}: {response.text}"
            print(f"  [ERROR] {error_msg}")
            return {'error': error_msg, 'chunk': str(chunk_path)}

        result = response.json()

        # content는 dict 형태: {'html': '...', 'markdown': '...', 'text': '...'}
        content_dict = result.get('content', {})
        content_text = content_dict.get(output_format, '') if isinstance(content_dict, dict) else str(content_dict)

        result['chunk_metadata'] = {
            'chunk_file': str(chunk_path),
            'elapsed_seconds': elapsed,
            'content_length': len(content_text)
        }

        print(f"  [SUCCESS] {elapsed:.2f}s, {len(content_text)} chars")
        return result

    def merge_results(self, results: List[Dict[str, Any]], original_pdf: Path, output_format: str = 'html') -> Dict[str, Any]:
        """파싱 결과 병합"""
        merged = {
            'content': '',
            'metadata': {
                'source_file': str(original_pdf),
                'total_pages': sum(r.get('usage', {}).get('pages', 0) for r in results if 'usage' in r),
                'total_chunks': len(results),
                'parsed_at': datetime.now().isoformat(),
                'output_format': output_format,
                'chunks': []
            },
            'elements': []
        }

        for i, result in enumerate(results):
            if 'error' in result:
                print(f"[WARNING] Chunk {i+1} failed: {result['error']}")
                continue

            # Content 병합 (dict 형태에서 특정 format 추출)
            content_dict = result.get('content', {})
            if isinstance(content_dict, dict):
                content_text = content_dict.get(output_format, '')
            else:
                content_text = str(content_dict)

            merged['content'] += content_text

            # Elements 병합
            if 'elements' in result:
                merged['elements'].extend(result['elements'])

            # Chunk 메타데이터 저장
            if 'chunk_metadata' in result:
                merged['metadata']['chunks'].append(result['chunk_metadata'])

        print(f"\n[MERGE] Total content: {len(merged['content'])} chars")
        print(f"[MERGE] Total elements: {len(merged['elements'])}")
        return merged

    def parse_large_pdf(
        self,
        pdf_path: str,
        output_path: str,
        output_format: str = "html",
        keep_chunks: bool = False
    ):
        """
        대용량 PDF 전체 파싱 워크플로우

        Args:
            pdf_path: 입력 PDF 경로
            output_path: 출력 JSON 경로
            output_format: 출력 형식
            keep_chunks: 분할 PDF 유지 여부
        """
        pdf_path = Path(pdf_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. PDF 정보 확인
        print(f"[INFO] Analyzing PDF: {pdf_path.name}")
        info = self.get_pdf_info(pdf_path)
        print(f"  - Total pages: {info['total_pages']}")
        print(f"  - File size: {info['file_size_mb']:.2f} MB")
        print(f"  - Chunks needed: {info['chunks_needed']}")

        if info['total_pages'] <= self.chunk_size:
            print("\n[INFO] PDF within limit, parsing directly...")
            # 직접 파싱 (분할 불필요)
            result = self.parse_chunk(pdf_path, output_format)
            result['metadata'] = {
                'source_file': str(pdf_path),
                'total_pages': info['total_pages'],
                'parsed_at': datetime.now().isoformat()
            }
        else:
            # 2. PDF 분할
            print(f"\n[STEP 1] Splitting PDF into {info['chunks_needed']} chunks...")
            temp_dir = pdf_path.parent / f"_temp_{pdf_path.stem}"
            chunk_paths = self.split_pdf(pdf_path, temp_dir)

            # 3. 각 청크 파싱
            print(f"\n[STEP 2] Parsing {len(chunk_paths)} chunks...")
            results = []
            for i, chunk_path in enumerate(chunk_paths):
                print(f"\n--- Chunk {i+1}/{len(chunk_paths)} ---")
                chunk_result = self.parse_chunk(chunk_path, output_format)
                results.append(chunk_result)

                # Rate limit 방지
                if i < len(chunk_paths) - 1:
                    time.sleep(1)

            # 4. 결과 병합
            print(f"\n[STEP 3] Merging results...")
            result = self.merge_results(results, pdf_path, output_format)

            # 5. 임시 파일 정리
            if not keep_chunks:
                print(f"\n[CLEANUP] Removing temporary chunks...")
                for chunk_path in chunk_paths:
                    chunk_path.unlink()
                temp_dir.rmdir()
            else:
                print(f"\n[INFO] Chunks kept in: {temp_dir}")

        # 6. 결과 저장
        print(f"\n[SAVE] Saving to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # Raw content 저장
        format_ext = output_format
        raw_path = output_path.with_suffix(f'.{format_ext}')
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(result['content'])

        print(f"\n[DONE] Parsing complete!")
        print(f"  - JSON: {output_path}")
        print(f"  - Raw: {raw_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Parse large PDF with Upstage API (split mode)')
    parser.add_argument('--input', required=True, help='Input PDF path')
    parser.add_argument('--output', required=True, help='Output JSON path')
    parser.add_argument('--format', default='html', choices=['html', 'markdown'],
                        help='Output format (default: html)')
    parser.add_argument('--chunk-size', type=int, default=100,
                        help='Pages per chunk (default: 100)')
    parser.add_argument('--keep-chunks', action='store_true',
                        help='Keep split PDF files')

    args = parser.parse_args()

    try:
        parser_obj = UpstageSplitParser(chunk_size=args.chunk_size)
        parser_obj.parse_large_pdf(
            pdf_path=args.input,
            output_path=args.output,
            output_format=args.format,
            keep_chunks=args.keep_chunks
        )
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
