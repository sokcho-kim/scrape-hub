"""
건강보험요양급여비용 PDF 파싱 - Procedure 데이터 추출

목적:
1. 전체 페이지에서 EDI 코드와 수가 정보 추출
2. Procedure 노드 생성을 위한 데이터 준비
3. 정규화된 JSON 형식으로 저장
"""

import pdfplumber
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

pdf_path = Path("data/hira/ebook/2025년 1월판 건강보험요양급여비용-(G000A37-2025-16).pdf")
output_dir = Path("data/hira/parsed")
output_dir.mkdir(parents=True, exist_ok=True)


class SUGAProcedureParser:
    """건강보험요양급여비용 파서"""

    def __init__(self):
        self.procedures = []
        self.errors = []
        self.stats = {
            'total_pages': 0,
            'pages_with_tables': 0,
            'total_procedures': 0,
            'parsing_errors': 0
        }

        # EDI 코드 패턴 (확장된 패턴)
        self.edi_patterns = [
            r'\b[A-Z]{1}\d{4}\b',      # A1234 형태
            r'\b[A-Z]{2}\d{3}\b',       # AA123 형태 (가장 일반적)
            r'\b[A-Z]{2}\d{4}\b',       # AA1234 형태
            r'\b\d{5}\b',               # 12345 형태 (숫자만)
        ]

    def is_edi_code(self, text: str) -> bool:
        """텍스트가 EDI 코드인지 확인"""
        if not text:
            return False

        text = text.strip()
        for pattern in self.edi_patterns:
            if re.match(pattern, text):
                return True
        return False

    def clean_text(self, text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""

        # None 처리
        if text is None:
            return ""

        # 공백 문자 정리
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def extract_code_from_cell(self, cell_text: str) -> List[str]:
        """셀에서 EDI 코드 추출 (여러 코드 가능)"""
        if not cell_text:
            return []

        codes = []

        # 정규식으로 모든 EDI 코드 찾기
        for pattern in self.edi_patterns:
            found_codes = re.findall(pattern, cell_text)
            codes.extend(found_codes)

        # 중복 제거 (순서 유지)
        seen = set()
        unique_codes = []
        for code in codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)

        return unique_codes

    def parse_table_row(self, row: List[str]) -> Optional[List[Dict]]:
        """테이블 행 파싱 - 멀티라인 셀 처리"""
        try:
            # 4열 구조: 분류번호 | 코드 | 분류(설명) | 점수
            if not row or len(row) < 4:
                return None

            # 각 셀을 라인별로 분리
            classification_lines = [self.clean_text(line) for line in str(row[0] or "").split('\n')]
            code_lines = [self.clean_text(line) for line in str(row[1] or "").split('\n')]
            description_lines = [self.clean_text(line) for line in str(row[2] or "").split('\n')]
            points_lines = [self.clean_text(line) for line in str(row[3] or "").split('\n')]

            # 코드가 있는 라인만 필터링
            valid_entries = []
            for i, code_line in enumerate(code_lines):
                # EDI 코드 추출
                codes = self.extract_code_from_cell(code_line)

                if not codes:
                    continue

                # 해당 라인의 다른 정보
                classification = classification_lines[i] if i < len(classification_lines) else ""
                description = description_lines[i] if i < len(description_lines) else ""
                points_text = points_lines[i] if i < len(points_lines) else ""

                # 점수 추출
                points_value = None
                if points_text:
                    points_match = re.search(r'[\d,]+\.?\d*', points_text)
                    if points_match:
                        points_str = points_match.group().replace(',', '')
                        try:
                            points_value = float(points_str)
                        except ValueError:
                            pass

                # 각 코드에 대해 procedure 생성
                for code in codes:
                    procedure = {
                        'edi_code': code,
                        'classification_number': classification,
                        'name': description[:500] if description else "",
                        'points': points_value,
                        'source': 'HIRA_SUGA_2025_01'
                    }
                    valid_entries.append(procedure)

            return valid_entries if valid_entries else None

        except Exception as e:
            self.errors.append({
                'type': 'row_parsing_error',
                'row': str(row)[:200],
                'error': str(e)
            })
            return None

    def parse_page(self, page_num: int, page) -> List[Dict]:
        """페이지 파싱"""
        page_procedures = []

        try:
            # 표 추출
            tables = page.extract_tables()

            if not tables:
                return page_procedures

            self.stats['pages_with_tables'] += 1

            # 각 표 처리
            for table_idx, table in enumerate(tables):
                if not table:
                    continue

                # 각 행 처리 (헤더 제외)
                for row_idx, row in enumerate(table):
                    # 헤더 스킵 (첫 행 또는 "분류번호" 포함)
                    if row_idx == 0 or (row and any(cell and '분류번호' in str(cell) for cell in row)):
                        continue

                    # 행 파싱
                    result = self.parse_table_row(row)

                    if result:
                        # 리스트로 반환된 경우
                        if isinstance(result, list):
                            for proc in result:
                                proc['page'] = page_num + 1
                                proc['table_index'] = table_idx
                                page_procedures.append(proc)
                        # 단일 딕셔너리로 반환된 경우
                        else:
                            result['page'] = page_num + 1
                            result['table_index'] = table_idx
                            page_procedures.append(result)

        except Exception as e:
            self.errors.append({
                'type': 'page_parsing_error',
                'page': page_num + 1,
                'error': str(e)
            })
            self.stats['parsing_errors'] += 1

        return page_procedures

    def parse_pdf(self, max_pages: Optional[int] = None):
        """PDF 전체 파싱"""
        print(f"PDF 파싱 시작: {pdf_path}")
        print(f"출력 디렉토리: {output_dir}")
        print("="*80)

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            self.stats['total_pages'] = total_pages

            # 최대 페이지 제한 (테스트용)
            pages_to_parse = min(total_pages, max_pages) if max_pages else total_pages

            print(f"총 페이지: {total_pages}")
            print(f"파싱할 페이지: {pages_to_parse}")
            print("="*80)

            # 각 페이지 처리
            for page_num in range(pages_to_parse):
                if (page_num + 1) % 100 == 0:
                    print(f"진행: {page_num + 1}/{pages_to_parse} 페이지 처리 중... (수집: {len(self.procedures)} procedures)")

                page = pdf.pages[page_num]
                page_procedures = self.parse_page(page_num, page)
                self.procedures.extend(page_procedures)

            self.stats['total_procedures'] = len(self.procedures)

            print("="*80)
            print(f"파싱 완료!")
            print(f"  총 페이지: {self.stats['total_pages']}")
            print(f"  표 있는 페이지: {self.stats['pages_with_tables']}")
            print(f"  추출된 procedures: {self.stats['total_procedures']}")
            print(f"  파싱 에러: {self.stats['parsing_errors']}")

    def remove_duplicates(self):
        """중복 제거 (EDI 코드 기준)"""
        print("\n중복 제거 중...")

        unique_procedures = {}
        for proc in self.procedures:
            edi_code = proc['edi_code']

            # 이미 있는 경우 페이지 정보 추가
            if edi_code in unique_procedures:
                # 기존 것 유지 (첫 번째 발견된 것 유지)
                continue
            else:
                unique_procedures[edi_code] = proc

        original_count = len(self.procedures)
        self.procedures = list(unique_procedures.values())
        duplicates_removed = original_count - len(self.procedures)

        print(f"  원본: {original_count}")
        print(f"  중복 제거 후: {len(self.procedures)}")
        print(f"  제거된 중복: {duplicates_removed}")

    def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Procedures JSON 저장
        procedures_file = output_dir / f"suga_procedures_{timestamp}.json"
        with open(procedures_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'source': 'HIRA 건강보험요양급여비용 2025년 1월판',
                    'parsed_at': datetime.now().isoformat(),
                    'total_procedures': len(self.procedures),
                    'stats': self.stats
                },
                'procedures': self.procedures
            }, f, ensure_ascii=False, indent=2)

        print(f"\nProcedures 저장: {procedures_file}")

        # 2. 에러 로그 저장
        if self.errors:
            errors_file = output_dir / f"suga_parsing_errors_{timestamp}.json"
            with open(errors_file, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)
            print(f"에러 로그 저장: {errors_file} ({len(self.errors)} errors)")

        # 3. 통계 저장
        stats_file = output_dir / f"suga_parsing_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': self.stats,
                'sample_procedures': self.procedures[:10],  # 샘플 10개
                'error_count': len(self.errors)
            }, f, ensure_ascii=False, indent=2)

        print(f"통계 저장: {stats_file}")

    def print_samples(self, n: int = 10):
        """샘플 출력"""
        print(f"\nSample Procedures (first {n}):")
        print("="*80)

        for i, proc in enumerate(self.procedures[:n], 1):
            # ASCII-safe output (avoid Korean encoding issues)
            edi_code = proc['edi_code']
            points = proc['points']
            print(f"{i}. Code: {edi_code}, Points: {points}")


def main():
    """메인 실행"""
    parser = SUGAProcedureParser()

    # PDF 파싱 - 전체 페이지
    parser.parse_pdf(max_pages=None)

    # 중복 제거
    parser.remove_duplicates()

    # 샘플 출력
    parser.print_samples(20)

    # 결과 저장
    parser.save_results()

    print("\n파싱 완료!")


if __name__ == "__main__":
    main()
