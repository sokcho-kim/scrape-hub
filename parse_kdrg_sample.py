"""
KDRG 분류집 샘플 파싱 - 구조 파악용
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


def parse_sample_pages(pdf_path: Path, start_page: int, end_page: int, output_dir: Path):
    """샘플 페이지 파싱"""

    print(f'📄 KDRG 샘플 파싱: p.{start_page}-{end_page}')

    # 샘플 페이지 추출
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page_num in range(start_page - 1, end_page):
        writer.add_page(reader.pages[page_num])

    # 임시 파일 저장
    sample_path = output_dir / f'kdrg_sample_p{start_page:04d}-{end_page:04d}.pdf'
    writer.write(sample_path)
    print(f'✅ 샘플 PDF 생성: {sample_path.name}')

    # Upstage API로 파싱
    api_key = os.getenv('UPSTAGE_API_KEY')
    if not api_key:
        raise ValueError('UPSTAGE_API_KEY not found')

    print(f'\n🔄 Upstage API 파싱 시작...')

    with open(sample_path, 'rb') as f:
        files = {'document': (sample_path.name, f, 'application/pdf')}
        data = {
            'ocr': 'true',
            'output_formats': '["html"]',
        }

        start_time = time.time()
        response = requests.post(
            "https://api.upstage.ai/v1/document-ai/document-parse",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data=data,
            timeout=300
        )
        elapsed = time.time() - start_time

        if response.status_code != 200:
            print(f'❌ API 에러: {response.status_code}')
            print(response.text)
            return None

        result = response.json()
        print(f'✅ 파싱 완료: {elapsed:.1f}초')

        # 결과 저장
        json_path = output_dir / f'kdrg_sample_p{start_page:04d}-{end_page:04d}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f'💾 JSON 저장: {json_path.name}')

        # HTML 저장
        content = result.get('content', {})
        if isinstance(content, dict):
            html_content = content.get('html', '')
        else:
            html_content = str(content)

        html_path = output_dir / f'kdrg_sample_p{start_page:04d}-{end_page:04d}.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f'💾 HTML 저장: {html_path.name}')

        # 미리보기
        print(f'\n[HTML 미리보기 (처음 1000자)]')
        print('-' * 80)
        print(html_content[:1000])
        print('-' * 80)

        return result


def main():
    """메인 실행"""
    print('=' * 80)
    print('📚 KDRG 분류집 샘플 파싱 (구조 분석용)')
    print('=' * 80)

    pdf_path = Path('data/hira_master/KDRG 분류집(신포괄지불제도용 ver1.4).pdf')
    output_dir = Path('data/hira_master/kdrg_samples')
    output_dir.mkdir(exist_ok=True, parents=True)

    if not pdf_path.exists():
        print(f'❌ 파일 없음: {pdf_path}')
        return

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f'\n총 페이지: {total_pages}p')

    # 여러 구간 샘플링
    sample_ranges = [
        (1, 10, '표지 및 목차'),
        (20, 30, '초반부 내용'),
        (100, 110, '중반부 내용'),
        (500, 510, '후반부 내용'),
    ]

    for start, end, desc in sample_ranges:
        if end <= total_pages:
            print(f'\n\n{"="*80}')
            print(f'📖 샘플링: p.{start}-{end} ({desc})')
            print(f'{"="*80}')

            result = parse_sample_pages(pdf_path, start, end, output_dir)

            if result:
                print(f'\n✅ 샘플 파싱 완료: {desc}')

            # Rate limit 방지
            time.sleep(2)

    print('\n\n' + '=' * 80)
    print('✅ 모든 샘플 파싱 완료')
    print(f'📁 결과 위치: {output_dir}')
    print('=' * 80)


if __name__ == '__main__':
    main()
