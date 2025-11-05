"""
KDRG 분류집 지능형 파싱
- 목차 구조를 기반으로 MDC 단위로 분할
- Upstage API로 각 청크 파싱
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


class SmartKDRGParser:
    """MDC 구조 기반 지능형 KDRG 파서"""

    def __init__(self, output_dir: str = 'data/hira_master/kdrg_parsed'):
        self.api_key = os.getenv('UPSTAGE_API_KEY')
        if not self.api_key:
            raise ValueError('UPSTAGE_API_KEY not found in .env')

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.base_url = "https://api.upstage.ai/v1/document-ai/document-parse"

        # 임시 분할 파일 저장 위치
        self.temp_dir = self.output_dir / 'temp_chunks'
        self.temp_dir.mkdir(exist_ok=True)

    def load_structure(self, structure_file: Path) -> dict:
        """저장된 구조 파일 로드"""
        with open(structure_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def split_pdf(self, pdf_path: Path, chunks: list) -> list:
        """구조 기반 PDF 분할"""
        print(f'\n📄 지능형 PDF 분할: {pdf_path.name}')

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        print(f'  총 페이지: {total_pages}p')
        print(f'  분할 계획: {len(chunks)}개 청크\n')

        split_files = []

        for i, chunk in enumerate(chunks, 1):
            start_page = chunk['start'] - 1  # 0-indexed
            end_page = chunk['end']

            # 새 PDF 생성
            writer = PdfWriter()
            for page_num in range(start_page, end_page):
                if page_num < total_pages:
                    writer.add_page(reader.pages[page_num])

            # 저장
            chunk_filename = f'kdrg_chunk{i:02d}_p{chunk["start"]:04d}-{chunk["end"]:04d}.pdf'
            chunk_path = self.temp_dir / chunk_filename

            writer.write(chunk_path)

            split_files.append({
                'path': chunk_path,
                'chunk_info': chunk,
                'index': i
            })

            print(f'  {i:2d}. {chunk["name"]:70s} p.{chunk["start"]:4d}-{chunk["end"]:4d} ({chunk["pages"]:3d}p)')

        print(f'\n  ✅ {len(split_files)}개 파일 생성 완료')

        return split_files

    def parse_chunk(self, chunk: dict, total_chunks: int, output_format: str = "html") -> dict:
        """단일 청크 파싱"""
        chunk_path = chunk['path']
        chunk_info = chunk['chunk_info']
        index = chunk['index']

        print(f'\n[{index}/{total_chunks}] {chunk_info["name"]}')
        print(f'  파일: {chunk_path.name}')

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
                    return {'error': error_msg, 'chunk': chunk_info}

                result = response.json()

                # content 추출
                content_dict = result.get('content', {})
                if isinstance(content_dict, dict):
                    content_text = content_dict.get(output_format, '')
                else:
                    content_text = str(content_dict)

                result['chunk_metadata'] = {
                    'chunk_info': chunk_info,
                    'chunk_file': str(chunk_path),
                    'elapsed_seconds': elapsed,
                    'content_length': len(content_text),
                    'api_pages': result.get('usage', {}).get('pages', 0)
                }

                print(f'  ✅ 성공: {elapsed:.1f}초, {len(content_text):,}자')
                return result

            except Exception as e:
                print(f'  ❌ 에러: {e}')
                return {'error': str(e), 'chunk': chunk_info}

    def parse_chunks(self, chunks: list) -> list:
        """분할된 PDF 파일들 파싱"""
        print(f'\n🔄 청크 파싱: {len(chunks)}개')

        results = []
        total = len(chunks)

        for chunk in chunks:
            result = self.parse_chunk(chunk, total)
            results.append(result)

            # Rate limit 방지
            time.sleep(1)

        return results

    def merge_results(self, results: list, source_file: str, output_format: str = 'html') -> dict:
        """파싱 결과 병합"""
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
        total_pages = sum(r.get('chunk_metadata', {}).get('api_pages', 0) for r in valid_results)

        # 청크 메타데이터
        chunks_metadata = []
        for r in valid_results:
            if 'chunk_metadata' in r:
                chunks_metadata.append(r['chunk_metadata'])

        merged = {
            'source_file': source_file,
            'total_pages': total_pages,
            'chunks_parsed': len(valid_results),
            'chunks_failed': len(results) - len(valid_results),
            'content': merged_content_str,
            'elements': merged_elements,
            'output_format': output_format,
            'parsing_method': 'mdc_structure_based_split',
            'parsed_at': datetime.now().isoformat(),
            'chunks_metadata': chunks_metadata
        }

        print(f'  ✅ 병합 완료: {total_pages}p, {len(merged_content_str):,}자')
        print(f'  ✅ Elements: {len(merged_elements)}개')

        # 청크별 요약
        print(f'\n  📋 청크별 분할:')
        for meta in chunks_metadata:
            chunk_info = meta['chunk_info']
            print(f'     {chunk_info["name"]:70s} p.{chunk_info["start"]:4d}-{chunk_info["end"]:4d} ({chunk_info["pages"]:3d}p)')

        return merged

    def cleanup_temp_files(self):
        """임시 파일 삭제"""
        print(f'\n🧹 임시 파일 정리')

        for file in self.temp_dir.glob('*.pdf'):
            file.unlink()
            print(f'  삭제: {file.name}')

    def parse_large_pdf(self, pdf_path: Path, structure_file: Path, output_format: str = 'html') -> dict:
        """대용량 PDF 전체 파싱 프로세스 (지능형 분할)"""
        print(f'\n{"="*80}')
        print(f'📚 지능형 KDRG 파싱: {pdf_path.name}')
        print(f'{"="*80}')

        # 1. 구조 정보 로드
        print('\n[단계 1] 구조 정보 로드')
        structure = self.load_structure(structure_file)
        chunks = structure['suggested_chunks']

        print(f'  총 페이지: {structure["total_pages"]}p')
        print(f'  MDC 섹션: {structure["mdc_count"]}개')
        print(f'  분할 청크: {len(chunks)}개')

        # 2. PDF 분할
        print('\n[단계 2] PDF 분할')
        split_files = self.split_pdf(pdf_path, chunks)

        # 3. 각 청크 파싱
        print('\n[단계 3] 청크 파싱')
        results = self.parse_chunks(split_files)

        # 4. 결과 병합
        print('\n[단계 4] 결과 병합')
        merged = self.merge_results(results, pdf_path.name, output_format)

        # 5. 저장
        if merged:
            # JSON 저장
            output_file = self.output_dir / 'kdrg_smart.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            print(f'\n💾 JSON 저장: {output_file}')

            # Raw content 저장 (HTML)
            raw_file = self.output_dir / f'kdrg_smart.{output_format}'
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(merged['content'])

            print(f'💾 Raw 저장: {raw_file}')

            # 미리보기
            print(f'\n[{output_format.upper()} 미리보기 (처음 500자)]')
            print('-' * 80)
            print(merged['content'][:500])
            print('-' * 80)

        # 6. 임시 파일 정리
        self.cleanup_temp_files()

        return merged


def main():
    """메인 실행"""
    print('='*80)
    print('🏥 KDRG 분류집 지능형 파싱')
    print('='*80)

    pdf_path = Path('data/hira_master/KDRG 분류집(신포괄지불제도용 ver1.4).pdf')
    structure_file = Path('data/hira_master/kdrg_structure.json')

    if not pdf_path.exists():
        print(f'❌ 파일 없음: {pdf_path}')
        return

    if not structure_file.exists():
        print(f'❌ 구조 파일 없음: {structure_file}')
        print('먼저 extract_kdrg_toc.py를 실행하세요.')
        return

    try:
        parser = SmartKDRGParser()
        result = parser.parse_large_pdf(pdf_path, structure_file, output_format='html')

        # 최종 요약
        print('\n\n' + '='*80)
        print('📊 파싱 완료')
        print('='*80)

        if result:
            print(f'✅ 총 페이지: {result.get("total_pages")}p')
            print(f'✅ 청크: {result.get("chunks_parsed")}개 성공, {result.get("chunks_failed")}개 실패')
            print(f'✅ Content: {len(result.get("content", "")):,}자')
            print(f'✅ Elements: {len(result.get("elements", []))}개')
            print(f'✅ 파싱 방식: {result.get("parsing_method")}')
        else:
            print('❌ 파싱 실패')

    except Exception as e:
        print(f'❌ 전체 에러: {e}')
        import traceback
        traceback.print_exc()

    print('\n' + '='*80)
    print('✅ 완료')
    print('='*80)


if __name__ == '__main__':
    main()
