"""
질병코딩지침서 PDF 파싱
- PDF를 20페이지씩 분할하여 Upstage API로 파싱
"""
import sys
import codecs
from pathlib import Path
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter
import requests
import time

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()


class PDFSplitParser:
    """PDF 분할 파서"""

    def __init__(self, output_dir: str = 'data/hira_master/parsed', chunk_pages: int = 50):
        """
        Args:
            output_dir: 출력 디렉토리
            chunk_pages: 한 번에 처리할 페이지 수
        """
        self.api_key = os.getenv('UPSTAGE_API_KEY')
        if not self.api_key:
            raise ValueError('UPSTAGE_API_KEY not found in .env')

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.chunk_pages = chunk_pages
        self.base_url = "https://api.upstage.ai/v1/document-ai/document-parse"

        # 임시 분할 파일 저장 위치
        self.temp_dir = self.output_dir / 'temp_chunks'
        self.temp_dir.mkdir(exist_ok=True)

    def split_pdf(self, pdf_path: Path) -> list:
        """PDF를 여러 파일로 분할

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            분할된 PDF 파일 경로 리스트
        """
        print(f'\n📄 PDF 분할: {pdf_path.name}')

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        print(f'  총 페이지: {total_pages}p')
        print(f'  분할 단위: {self.chunk_pages}p')
        print(f'  예상 파일: {(total_pages + self.chunk_pages - 1) // self.chunk_pages}개')

        chunks = []

        for start_page in range(0, total_pages, self.chunk_pages):
            end_page = min(start_page + self.chunk_pages, total_pages)

            # 새 PDF 생성
            writer = PdfWriter()
            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])

            # 저장
            chunk_filename = f'{pdf_path.stem}_pages_{start_page+1:04d}-{end_page:04d}.pdf'
            chunk_path = self.temp_dir / chunk_filename
            writer.write(chunk_path)

            chunks.append(chunk_path)
            print(f'  ✅ {chunk_filename} ({end_page - start_page}p)')

        return chunks

    def parse_chunk(self, chunk_path: Path, output_format: str = "html") -> dict:
        """단일 청크 파싱"""
        print(f'\n[파싱] {chunk_path.name}')

        with open(chunk_path, 'rb') as f:
            files = {'document': (chunk_path.name, f, 'application/pdf')}
            data = {
                'ocr': 'true',
                'output_formats': f'["{output_format}"]',
            }

            start_time = time.time()
            try:
                response = requests.post(
                    self.base_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    data=data,
                    timeout=300
                )
                elapsed = time.time() - start_time

                if response.status_code != 200:
                    error_msg = f"API Error {response.status_code}: {response.text}"
                    print(f'  ❌ 실패: {error_msg}')
                    return {'error': error_msg, 'chunk': str(chunk_path)}

                result = response.json()

                # content 추출
                content_dict = result.get('content', {})
                if isinstance(content_dict, dict):
                    content_text = content_dict.get(output_format, '')
                else:
                    content_text = str(content_dict)

                result['chunk_metadata'] = {
                    'chunk_file': str(chunk_path),
                    'elapsed_seconds': elapsed,
                    'content_length': len(content_text),
                    'pages': result.get('usage', {}).get('pages', 0)
                }

                print(f'  ✅ 성공: {elapsed:.1f}초, {len(content_text):,}자')
                return result

            except Exception as e:
                print(f'  ❌ 에러: {e}')
                return {'error': str(e), 'chunk': str(chunk_path)}

    def parse_chunks(self, chunk_paths: list) -> list:
        """분할된 PDF 파일들 파싱

        Args:
            chunk_paths: 분할된 PDF 경로 리스트

        Returns:
            파싱 결과 리스트
        """
        print(f'\n🔄 청크 파싱: {len(chunk_paths)}개')

        results = []

        for i, chunk_path in enumerate(chunk_paths, 1):
            print(f'\n[{i}/{len(chunk_paths)}]')
            result = self.parse_chunk(chunk_path)
            results.append(result)

            # Rate limit 방지
            if i < len(chunk_paths):
                time.sleep(1)

        return results

    def merge_results(self, results: list, source_file: str, output_format: str = 'html') -> dict:
        """파싱 결과 병합

        Args:
            results: 파싱 결과 리스트
            source_file: 원본 파일명
            output_format: 출력 형식

        Returns:
            병합된 결과
        """
        print(f'\n🔗 결과 병합')

        # 에러가 없는 결과만 필터링
        valid_results = [r for r in results if 'error' not in r]

        if not valid_results:
            print('  ❌ 모든 청크 파싱 실패')
            return None

        # Content 병합
        merged_content = []
        for r in valid_results:
            content_dict = r.get('content', {})
            if isinstance(content_dict, dict):
                content_text = content_dict.get(output_format, '')
            else:
                content_text = str(content_dict)
            merged_content.append(content_text)

        merged_content_str = '\n\n<hr>\n\n'.join(merged_content)

        # Elements 병합
        merged_elements = []
        for r in valid_results:
            if 'elements' in r:
                merged_elements.extend(r['elements'])

        # 총 페이지 수
        total_pages = sum(r.get('chunk_metadata', {}).get('pages', 0) for r in valid_results)

        merged = {
            'source_file': source_file,
            'total_pages': total_pages,
            'chunks_parsed': len(valid_results),
            'chunks_failed': len(results) - len(valid_results),
            'content': merged_content_str,
            'elements': merged_elements,
            'output_format': output_format,
            'parsed_at': datetime.now().isoformat(),
            'chunks_metadata': [r.get('chunk_metadata') for r in valid_results]
        }

        print(f'  ✅ 병합 완료: {total_pages}p, {len(merged_content_str):,}자')
        print(f'  ✅ Elements: {len(merged_elements)}개')

        return merged

    def cleanup_temp_files(self):
        """임시 파일 삭제"""
        print(f'\n🧹 임시 파일 정리')

        for file in self.temp_dir.glob('*.pdf'):
            file.unlink()
            print(f'  삭제: {file.name}')

    def parse_large_pdf(self, pdf_path: Path, output_format: str = 'html') -> dict:
        """대용량 PDF 전체 파싱 프로세스

        Args:
            pdf_path: PDF 파일 경로
            output_format: 출력 형식

        Returns:
            병합된 파싱 결과
        """
        print(f'\n{"="*80}')
        print(f'📚 대용량 PDF 파싱: {pdf_path.name}')
        print(f'{"="*80}')

        # 1. PDF 분할
        chunks = self.split_pdf(pdf_path)

        # 2. 각 청크 파싱
        results = self.parse_chunks(chunks)

        # 3. 결과 병합
        merged = self.merge_results(results, pdf_path.name, output_format)

        # 4. 저장
        if merged:
            # JSON 저장
            output_file = self.output_dir / f'{pdf_path.stem}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            print(f'\n💾 JSON 저장: {output_file}')

            # Raw content 저장 (HTML)
            raw_file = self.output_dir / f'{pdf_path.stem}.{output_format}'
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(merged['content'])

            print(f'💾 Raw 저장: {raw_file}')

            # 미리보기
            print(f'\n[{output_format.upper()} 미리보기 (처음 500자)]')
            print('-' * 80)
            print(merged['content'][:500])
            print('-' * 80)

        # 5. 임시 파일 정리
        self.cleanup_temp_files()

        return merged


def main():
    """메인 실행"""
    print('=' * 80)
    print('🏥 질병코딩지침서 PDF 파싱')
    print('=' * 80)

    # 파싱할 PDF
    pdf_path = Path('data/hira_master/붙임1_2021년+한국표준질병사인분류+질병코딩지침서.pdf')

    if not pdf_path.exists():
        print(f'❌ 파일 없음: {pdf_path}')
        return

    try:
        # 50페이지씩 분할 (Upstage 제한: 100페이지)
        parser = PDFSplitParser(chunk_pages=50)
        result = parser.parse_large_pdf(pdf_path, output_format='html')

        # 최종 요약
        print('\n\n' + '=' * 80)
        print('📊 파싱 완료')
        print('=' * 80)

        if result:
            print(f'✅ 총 페이지: {result.get("total_pages")}p')
            print(f'✅ 청크: {result.get("chunks_parsed")}개 성공, {result.get("chunks_failed")}개 실패')
            print(f'✅ Content: {len(result.get("content", "")):,}자')
            print(f'✅ Elements: {len(result.get("elements", []))}개')
        else:
            print('❌ 파싱 실패')

    except Exception as e:
        print(f'❌ 전체 에러: {e}')
        import traceback
        traceback.print_exc()

    print('\n' + '=' * 80)
    print('✅ 완료')
    print('=' * 80)


if __name__ == '__main__':
    main()
