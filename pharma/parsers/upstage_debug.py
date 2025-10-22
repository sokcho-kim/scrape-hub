"""
Upstage API 응답 확인용 디버그 스크립트
"""
import os
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")
UPSTAGE_DOCUMENT_PARSE_URL = "https://api.upstage.ai/v1/document-ai/document-parse"

def test_single_page():
    """단일 페이지 테스트 및 전체 응답 출력"""
    base_dir = Path(__file__).parent.parent.parent
    pdf_path = base_dir / "data" / "pharma" / "parsed" / "upstage_test" / "split_pdfs" / "page_100.pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    print(f"Testing: {pdf_path.name}")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}"
    }

    with open(pdf_path, 'rb') as f:
        files = {
            'document': (pdf_path.name, f, 'application/pdf')
        }

        data = {
            'ocr': 'force'
        }

        print("Calling Upstage API...")
        response = requests.post(
            UPSTAGE_DOCUMENT_PARSE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )

    print(f"Status Code: {response.status_code}")
    print("="*80)

    if response.status_code == 200:
        result = response.json()

        # 전체 응답 출력
        print("\n=== FULL API RESPONSE ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 저장
        output_dir = base_dir / "data" / "pharma" / "parsed" / "upstage_test"
        output_path = output_dir / "debug_page_100_full_response.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n\nFull response saved to: {output_path}")

        # 요약
        elements = result.get('elements', [])
        tables = [e for e in elements if e.get('category') == 'table']

        print("\n=== SUMMARY ===")
        print(f"Total elements: {len(elements)}")
        print(f"Tables found: {len(tables)}")

        if tables:
            print("\n=== TABLES ===")
            for i, table in enumerate(tables):
                print(f"\nTable {i+1}:")
                print(f"  ID: {table.get('id')}")
                print(f"  Page: {table.get('page')}")
                print(f"  Category: {table.get('category')}")
                print(f"  Bounding box: {table.get('bounding_box')}")
                print(f"  HTML length: {len(table.get('html', '') or '')}")
                print(f"  Text length: {len(table.get('text', '') or '')}")

                if table.get('html'):
                    print(f"\n  HTML (first 500 chars):")
                    print(f"  {table['html'][:500]}")

                if table.get('text'):
                    print(f"\n  Text (first 300 chars):")
                    print(f"  {table['text'][:300]}")

    else:
        print(f"ERROR: {response.text}")

if __name__ == "__main__":
    test_single_page()
