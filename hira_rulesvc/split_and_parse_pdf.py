#!/usr/bin/env python3
"""
대용량 PDF를 분할하여 파싱 후 병합
"""
import os
import json
import requests
import time
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class PDFSplitterParser:
    """PDF 분할 및 파싱"""

    MAX_PAGES_PER_CHUNK = 100

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.upstage.ai/v1/document-ai/document-parse"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def split_pdf(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """
        PDF를 100페이지씩 분할

        Returns:
            분할된 PDF 파일 경로 리스트
        """
        print(f"\n[SPLIT] {pdf_path.name}")

        # PDF 열기
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"  [INFO] Total pages: {total_pages}")

        # 분할 개수 계산
        num_chunks = (total_pages + self.MAX_PAGES_PER_CHUNK - 1) // self.MAX_PAGES_PER_CHUNK
        print(f"  [INFO] Will split into {num_chunks} chunks")

        # 출력 디렉토리 생성
        output_dir.mkdir(parents=True, exist_ok=True)

        split_files = []

        for i in range(num_chunks):
            start_page = i * self.MAX_PAGES_PER_CHUNK
            end_page = min((i + 1) * self.MAX_PAGES_PER_CHUNK, total_pages)

            # 새 PDF 생성
            split_doc = fitz.open()
            split_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)

            # 파일명 생성
            split_filename = f"{pdf_path.stem}_part{i+1:02d}.pdf"
            split_path = output_dir / split_filename

            split_doc.save(str(split_path))
            split_doc.close()

            split_files.append(split_path)
            print(f"  [CREATED] Part {i+1}: pages {start_page+1}-{end_page} → {split_filename}")

        doc.close()

        return split_files

    def parse_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """단일 PDF 파싱"""
        try:
            with open(pdf_path, 'rb') as f:
                files = {'document': f}
                data = {'ocr': 'auto', 'coordinates': 'true'}

                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    files=files,
                    data=data,
                    timeout=300
                )

            if response.status_code != 200:
                print(f"    [ERROR] API {response.status_code}: {response.text[:200]}")
                return None

            return response.json()

        except Exception as e:
            print(f"    [ERROR] {str(e)}")
            return None

    def merge_parsed_results(
        self,
        parsed_parts: List[Dict],
        original_filename: str
    ) -> Dict:
        """
        분할 파싱된 결과를 하나로 병합

        Args:
            parsed_parts: 각 부분의 파싱 결과 리스트
            original_filename: 원본 파일명

        Returns:
            병합된 파싱 결과
        """
        print(f"\n[MERGE] Combining {len(parsed_parts)} parts")

        # 전체 텍스트 병합
        merged_content = ""
        merged_elements = []
        total_pages = 0

        for part_idx, part_result in enumerate(parsed_parts):
            # 텍스트 병합
            part_content = part_result.get('content', {}).get('text', '')
            if part_content:
                merged_content += part_content
                if part_idx < len(parsed_parts) - 1:  # 마지막이 아니면 개행 추가
                    merged_content += "\n\n"

            # 요소 병합 (페이지 번호 조정)
            part_elements = part_result.get('elements', [])
            for element in part_elements:
                # 페이지 번호를 전체 문서 기준으로 조정
                if 'page' in element:
                    element['page'] = element['page'] + total_pages

                merged_elements.append(element)

            # 페이지 수 누적
            total_pages += len(part_result.get('pages', []))

        # 병합된 결과 생성
        merged_result = {
            'file_name': original_filename,
            'page_count': total_pages,
            'content': merged_content,
            'elements': merged_elements,
            'metadata': {
                'parsed_at': datetime.now().isoformat(),
                'api': 'upstage-document-parse',
                'method': 'split_and_merge',
                'num_parts': len(parsed_parts)
            }
        }

        print(f"  [INFO] Merged: {total_pages} pages, {len(merged_elements)} elements")

        return merged_result

    def split_parse_and_merge(
        self,
        pdf_path: Path,
        temp_dir: Path,
        output_file: Path
    ) -> bool:
        """
        PDF 분할 → 파싱 → 병합 전체 프로세스

        Returns:
            성공 여부
        """
        start_time = time.time()

        print("=" * 80)
        print(f"대용량 PDF 분할 파싱: {pdf_path.name}")
        print("=" * 80)

        # 1. PDF 분할
        split_start = time.time()
        split_files = self.split_pdf(pdf_path, temp_dir)
        split_time = time.time() - split_start
        print(f"\n[TIMING] Split: {split_time:.2f}s")

        # 2. 각 부분 파싱
        parse_start = time.time()
        parsed_parts = []

        for i, split_file in enumerate(split_files, 1):
            print(f"\n[PARSE] Part {i}/{len(split_files)}: {split_file.name}")

            result = self.parse_pdf(split_file)

            if result:
                parsed_parts.append(result)
                pages = len(result.get('pages', []))
                chars = len(result.get('content', {}).get('text', ''))
                print(f"    [OK] {pages} pages, {chars} chars")
            else:
                print(f"    [FAILED] Could not parse {split_file.name}")
                return False

            # API Rate Limit
            if i < len(split_files):
                time.sleep(2)

        parse_time = time.time() - parse_start
        print(f"\n[TIMING] Parse: {parse_time:.2f}s")

        # 3. 결과 병합
        merge_start = time.time()
        merged_result = self.merge_parsed_results(parsed_parts, pdf_path.name)
        merge_time = time.time() - merge_start
        print(f"[TIMING] Merge: {merge_time:.2f}s")

        # 4. 저장
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_result, f, ensure_ascii=False, indent=2)

        total_time = time.time() - start_time

        print("\n" + "=" * 80)
        print("완료")
        print("=" * 80)
        print(f"총 소요 시간: {total_time:.2f}s ({total_time/60:.2f}분)")
        print(f"  - 분할: {split_time:.2f}s")
        print(f"  - 파싱: {parse_time:.2f}s")
        print(f"  - 병합: {merge_time:.2f}s")
        print(f"결과 파일: {output_file}")
        print("=" * 80)

        return True


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='대용량 PDF 분할 파싱')
    parser.add_argument('--file1',
                        default='data/hira_rulesvc/documents/요양급여비용 심사청구서·명세서 세부작성요령(2025년 8월 1일).pdf',
                        help='첫 번째 파일 (370페이지)')
    parser.add_argument('--file2',
                        default='data/hira_rulesvc/documents/의료급여수가의 기준 및 일반기준(고시 제2025-171호, 25.10.1. 시행)_전문.pdf',
                        help='두 번째 파일 (112페이지)')
    parser.add_argument('--temp-dir',
                        default='data/hira_rulesvc/temp_split',
                        help='분할 PDF 임시 디렉토리')
    parser.add_argument('--output-dir',
                        default='data/hira_rulesvc/parsed',
                        help='출력 디렉토리')

    args = parser.parse_args()

    # API 키 확인
    api_key = os.getenv('UPSTAGE_API_KEY')
    if not api_key:
        print("[ERROR] UPSTAGE_API_KEY 환경변수가 설정되지 않았습니다.")
        return 1

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    file1 = base_dir / args.file1
    file2 = base_dir / args.file2
    temp_dir = base_dir / args.temp_dir
    output_dir = base_dir / args.output_dir

    # 파서 초기화
    parser = PDFSplitterParser(api_key)

    # 두 파일 처리
    total_start = time.time()
    success_count = 0

    for pdf_file in [file1, file2]:
        if not pdf_file.exists():
            print(f"[SKIP] File not found: {pdf_file}")
            continue

        output_file = output_dir / f"{pdf_file.stem}.json"

        success = parser.split_parse_and_merge(
            pdf_file,
            temp_dir / pdf_file.stem,
            output_file
        )

        if success:
            success_count += 1

        print("\n")

    total_time = time.time() - total_start

    print("=" * 80)
    print("전체 작업 완료")
    print("=" * 80)
    print(f"처리한 파일: {success_count}/2")
    print(f"총 소요 시간: {total_time:.2f}s ({total_time/60:.2f}분)")
    print("=" * 80)

    return 0 if success_count == 2 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
