"""
HIRA 암질환 첨부파일 파싱 스크립트

828개 첨부파일(HWP, PDF 등)을 Upstage API로 파싱하여
Markdown/HTML로 변환하고 게시글 메타데이터와 연결
"""
import sys
import json
import codecs
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse
from tqdm import tqdm

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.parsers import UpstageParser, ParserFactory

# 경로 설정
DATA_DIR = project_root / "data" / "hira_cancer"
RAW_DIR = DATA_DIR / "raw"
ATTACHMENTS_DIR = RAW_DIR / "attachments"
PARSED_DIR = DATA_DIR / "parsed"
PARSED_DIR.mkdir(parents=True, exist_ok=True)

# JSON 파일 경로
METADATA_JSON = RAW_DIR / "hira_cancer_20251023_184848.json"


class AttachmentParser:
    """암질환 첨부파일 파서"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Upstage API 키
        """
        self.parser = UpstageParser(api_key)
        self.metadata: Dict[str, Any] = {}
        self.posts: Dict[str, List[Dict]] = {}
        self.parsed_count = 0
        self.failed_files: List[Dict[str, str]] = []
        self.total_pages = 0
        self.total_cost = 0.0

    def load_metadata(self) -> None:
        """게시글 메타데이터 로드"""
        print(f"📖 메타데이터 로드 중: {METADATA_JSON}")
        with open(METADATA_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.metadata = data.get('metadata', {})
        self.posts = data.get('data', {})

        # 통계 출력
        total_posts = sum(board_data['posts'] for board_data in self.metadata['boards'].values())
        total_attachments = sum(board_data['attachments'] for board_data in self.metadata['boards'].values())

        print(f"✅ 게시판 수: {len(self.posts)}")
        print(f"✅ 총 게시글: {total_posts}개")
        print(f"✅ 총 첨부파일: {total_attachments}개")
        print()

    def collect_all_attachments(self) -> List[Dict[str, Any]]:
        """모든 첨부파일 정보 수집"""
        all_attachments = []

        for board_key, posts in self.posts.items():
            for post in posts:
                board_name = post.get('board_name', board_key)
                post_number = post.get('number', 'N/A')
                post_title = post.get('title', 'Untitled')

                for att_idx, attachment in enumerate(post.get('attachments', [])):
                    # local_path가 있는 파일만 (다운로드 성공한 파일)
                    if 'local_path' in attachment and attachment.get('downloaded', False):
                        att_info = {
                            'board': board_key,
                            'board_name': board_name,
                            'post_number': post_number,
                            'post_title': post_title,
                            'attachment_index': att_idx,
                            'filename': attachment.get('filename', 'unknown'),
                            'extension': attachment.get('extension', ''),
                            'local_path': Path(attachment['local_path']),
                            'download_url': attachment.get('download_url', ''),
                        }
                        all_attachments.append(att_info)

        return all_attachments

    def parse_attachment(self, att_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        단일 첨부파일 파싱

        Args:
            att_info: 첨부파일 정보

        Returns:
            파싱 결과 또는 None (실패 시)
        """
        file_path = att_info['local_path']

        # 파일 존재 확인
        if not file_path.exists():
            return None

        # 파일 형식 확인
        if not self.parser.supports(file_path.suffix):
            return None

        try:
            # 파싱 실행
            result = self.parser.parse(file_path)

            # 메타데이터 추가
            result['attachment_metadata'] = {
                'board': att_info['board'],
                'board_name': att_info['board_name'],
                'post_number': att_info['post_number'],
                'post_title': att_info['post_title'],
                'attachment_index': att_info['attachment_index'],
                'filename': att_info['filename'],
                'download_url': att_info['download_url'],
            }

            result['parsed_at'] = datetime.now().isoformat()

            # 통계 업데이트
            self.parsed_count += 1
            self.total_pages += result.get('pages', 0)

            return result

        except Exception as e:
            error_info = {
                'file': str(file_path),
                'board': att_info['board_name'],
                'post_number': att_info['post_number'],
                'filename': att_info['filename'],
                'error': str(e),
            }
            self.failed_files.append(error_info)
            return None

    def save_parsed_result(self, result: Dict[str, Any], att_info: Dict[str, Any]) -> None:
        """파싱 결과 저장"""
        # 게시판별 디렉토리 생성
        board_dir = PARSED_DIR / att_info['board']
        board_dir.mkdir(exist_ok=True)

        # 파일명 생성: {게시글번호}_{첨부파일인덱스}_{원본파일명}.json
        safe_filename = f"{att_info['post_number']}_{att_info['attachment_index']}_{att_info['filename']}.json"
        output_path = board_dir / safe_filename

        # JSON 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def parse_sample(self, n: int = 10) -> None:
        """샘플 파싱 (테스트용)"""
        print(f"🧪 샘플 파싱 시작 (최대 {n}개)")
        print()

        all_attachments = self.collect_all_attachments()

        # 게시판별로 고르게 샘플링
        sample_attachments = []
        boards = {}
        for att in all_attachments:
            board = att['board']
            if board not in boards:
                boards[board] = []
            boards[board].append(att)

        # 각 게시판에서 균등하게 선택
        samples_per_board = max(1, n // len(boards))
        for board, atts in boards.items():
            sample_attachments.extend(atts[:samples_per_board])

        sample_attachments = sample_attachments[:n]

        print(f"📋 선택된 샘플: {len(sample_attachments)}개")
        for att in sample_attachments:
            print(f"  - [{att['board_name']}] {att['post_number']}: {att['filename']}")
        print()

        # 파싱 실행
        for att_info in tqdm(sample_attachments, desc="샘플 파싱"):
            result = self.parse_attachment(att_info)
            if result:
                self.save_parsed_result(result, att_info)

        self._print_summary()

    def parse_all(self) -> None:
        """전체 828개 파일 파싱"""
        print("🚀 전체 파싱 시작")
        print()

        all_attachments = self.collect_all_attachments()

        print(f"📋 파싱 대상: {len(all_attachments)}개 파일")

        # 파싱 실행
        for att_info in tqdm(all_attachments, desc="전체 파싱"):
            result = self.parse_attachment(att_info)
            if result:
                self.save_parsed_result(result, att_info)

        self._print_summary()
        self._save_summary()
        self._save_failed_files()

    def parse_board(self, board_key: str) -> None:
        """특정 게시판만 파싱"""
        print(f"🎯 [{board_key}] 게시판 파싱 시작")
        print()

        all_attachments = self.collect_all_attachments()
        board_attachments = [att for att in all_attachments if att['board'] == board_key]

        if not board_attachments:
            print(f"❌ '{board_key}' 게시판의 첨부파일이 없습니다.")
            return

        print(f"📋 파싱 대상: {len(board_attachments)}개 파일")

        # 파싱 실행
        for att_info in tqdm(board_attachments, desc=f"{board_key} 파싱"):
            result = self.parse_attachment(att_info)
            if result:
                self.save_parsed_result(result, att_info)

        self._print_summary()

    def retry_failed(self) -> None:
        """실패한 파일 재시도"""
        failed_list_path = PARSED_DIR / "_failed_files.json"

        if not failed_list_path.exists():
            print("❌ 실패 파일 목록이 없습니다.")
            return

        print("♻️  실패 파일 재시도")
        print()

        with open(failed_list_path, 'r', encoding='utf-8') as f:
            previous_failed = json.load(f)

        print(f"📋 재시도 대상: {len(previous_failed)}개")

        # 파일 경로로 첨부파일 정보 재구성
        all_attachments = self.collect_all_attachments()
        retry_list = []

        for failed in previous_failed:
            file_path = Path(failed['file'])
            for att in all_attachments:
                if att['local_path'] == file_path:
                    retry_list.append(att)
                    break

        # 재파싱
        for att_info in tqdm(retry_list, desc="재시도"):
            result = self.parse_attachment(att_info)
            if result:
                self.save_parsed_result(result, att_info)

        self._print_summary()
        self._save_summary()
        self._save_failed_files()

    def _print_summary(self) -> None:
        """통계 출력"""
        print()
        print("=" * 60)
        print("📊 파싱 결과")
        print("=" * 60)
        print(f"✅ 성공: {self.parsed_count}개")
        print(f"❌ 실패: {len(self.failed_files)}개")
        print(f"📄 총 페이지: {self.total_pages}p")

        # 비용 추정 (Upstage: $0.01/page)
        self.total_cost = self.total_pages * 0.01
        print(f"💰 예상 비용: ${self.total_cost:.2f} (약 ₩{self.total_cost * 1300:.0f})")

        if self.failed_files:
            print()
            print("❌ 실패 파일:")
            for failed in self.failed_files[:10]:  # 최대 10개만 출력
                print(f"  - [{failed['board']}] {failed['filename']}: {failed['error']}")

            if len(self.failed_files) > 10:
                print(f"  ... 외 {len(self.failed_files) - 10}개")

        print("=" * 60)
        print()

    def _save_summary(self) -> None:
        """통계 저장"""
        summary = {
            'parsed_at': datetime.now().isoformat(),
            'total_parsed': self.parsed_count,
            'total_failed': len(self.failed_files),
            'total_pages': self.total_pages,
            'total_cost_usd': self.total_cost,
            'total_cost_krw': self.total_cost * 1300,
            'boards': {},
        }

        # 게시판별 통계
        for board_key, board_data in self.metadata['boards'].items():
            board_dir = PARSED_DIR / board_key
            if board_dir.exists():
                parsed_files = list(board_dir.glob('*.json'))
                summary['boards'][board_key] = {
                    'name': board_data['name'],
                    'total_attachments': board_data['attachments'],
                    'parsed_files': len(parsed_files),
                }

        summary_path = PARSED_DIR / "_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"💾 통계 저장: {summary_path}")

    def _save_failed_files(self) -> None:
        """실패 파일 목록 저장"""
        if not self.failed_files:
            return

        failed_path = PARSED_DIR / "_failed_files.json"
        with open(failed_path, 'w', encoding='utf-8') as f:
            json.dump(self.failed_files, f, ensure_ascii=False, indent=2)

        print(f"💾 실패 목록 저장: {failed_path}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="HIRA 암질환 첨부파일 파싱")

    parser.add_argument('--sample', type=int, metavar='N',
                        help='샘플 N개만 파싱 (테스트용)')
    parser.add_argument('--all', action='store_true',
                        help='전체 828개 파일 파싱')
    parser.add_argument('--board', type=str,
                        choices=['announcement', 'pre_announcement', 'chemotherapy', 'faq'],
                        help='특정 게시판만 파싱')
    parser.add_argument('--retry', action='store_true',
                        help='실패한 파일만 재시도')
    parser.add_argument('--api-key', type=str,
                        help='Upstage API 키 (생략 시 환경변수 사용)')

    args = parser.parse_args()

    # API 키 확인
    import os
    from dotenv import load_dotenv
    load_dotenv()

    api_key = args.api_key or os.getenv('UPSTAGE_API_KEY')
    if not api_key:
        print("❌ Upstage API 키가 필요합니다.")
        print("   --api-key 옵션 또는 UPSTAGE_API_KEY 환경변수를 설정하세요.")
        return

    # 파서 초기화
    att_parser = AttachmentParser(api_key)
    att_parser.load_metadata()

    # 모드 선택
    if args.sample:
        att_parser.parse_sample(args.sample)
    elif args.board:
        att_parser.parse_board(args.board)
    elif args.retry:
        att_parser.retry_failed()
    elif args.all:
        att_parser.parse_all()
    else:
        print("❌ 모드를 선택하세요:")
        print("   --sample N    : 샘플 N개 파싱")
        print("   --all         : 전체 파싱")
        print("   --board BOARD : 특정 게시판만 파싱")
        print("   --retry       : 실패 파일 재시도")


if __name__ == '__main__':
    main()
