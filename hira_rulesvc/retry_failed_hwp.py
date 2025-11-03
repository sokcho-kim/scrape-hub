#!/usr/bin/env python3
"""
실패한 HWP 파일 재처리

전략:
- API 413 (페이지 초과) → 비동기 API 사용
- API 500 (서버 에러) → 재시도
"""
import os
import json
import requests
import time
from pathlib import Path
from datetime import datetime


class UpstageAsyncParser:
    """Upstage 비동기 API 파서"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.sync_url = "https://api.upstage.ai/v1/document-ai/document-parse"
        self.async_url = "https://api.upstage.ai/v1/document-ai/document-parse/async"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def parse_sync(self, hwp_path: Path) -> dict:
        """동기 API로 파싱 (100페이지 이하)"""
        print(f"[SYNC] {hwp_path.name}")

        with open(hwp_path, 'rb') as f:
            files = {'document': f}
            data = {'ocr': 'auto', 'coordinates': 'true'}

            response = requests.post(
                self.sync_url,
                headers=self.headers,
                files=files,
                data=data,
                timeout=300
            )

        if response.status_code != 200:
            return {
                'error': f"API {response.status_code}",
                'response': response.text[:500]
            }

        return response.json()

    def parse_async(self, hwp_path: Path, max_wait: int = 600) -> dict:
        """
        비동기 API로 파싱 (1000페이지까지)

        Args:
            hwp_path: HWP 파일 경로
            max_wait: 최대 대기 시간 (초, 기본 10분)
        """
        print(f"[ASYNC] {hwp_path.name}")

        # 1. 비동기 작업 제출
        with open(hwp_path, 'rb') as f:
            files = {'document': f}
            data = {'ocr': 'auto', 'coordinates': 'true'}

            print(f"  [SUBMIT] Uploading to async API...")
            response = requests.post(
                self.async_url,
                headers=self.headers,
                files=files,
                data=data,
                timeout=300
            )

        if response.status_code != 200:
            return {
                'error': f"Async submit failed {response.status_code}",
                'response': response.text[:500]
            }

        job_data = response.json()
        job_id = job_data.get('id')
        if not job_id:
            return {'error': 'No job ID returned', 'response': str(job_data)}

        print(f"  [JOB_ID] {job_id}")

        # 2. 결과 폴링
        result_url = f"{self.async_url}/{job_id}"
        start_time = time.time()
        poll_interval = 10  # 10초마다 확인

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                return {'error': f'Timeout after {max_wait}s'}

            print(f"  [POLL] {elapsed:.0f}s elapsed...")
            response = requests.get(result_url, headers=self.headers)

            if response.status_code != 200:
                print(f"  [ERROR] Poll failed: {response.status_code}")
                time.sleep(poll_interval)
                continue

            result = response.json()
            status = result.get('status')

            if status == 'completed':
                print(f"  [SUCCESS] Completed in {elapsed:.0f}s")
                return result

            elif status == 'failed':
                return {
                    'error': 'Async job failed',
                    'response': str(result)
                }

            # 아직 처리 중
            print(f"  [STATUS] {status}")
            time.sleep(poll_interval)


def main():
    """실패 파일 재처리"""
    import argparse

    parser = argparse.ArgumentParser(description='실패한 HWP 파일 재처리')
    parser.add_argument('--summary',
                        default='data/hira_rulesvc/parsed/parse_summary.json',
                        help='파싱 요약 파일')
    parser.add_argument('--input-dir',
                        default='data/hira_rulesvc/documents',
                        help='HWP 파일 디렉토리')
    parser.add_argument('--output-dir',
                        default='data/hira_rulesvc/parsed',
                        help='출력 디렉토리')
    parser.add_argument('--retry-500', action='store_true',
                        help='500 에러도 재시도')

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    summary_path = base_dir / args.summary
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / args.output_dir

    # API 키
    api_key = os.getenv('UPSTAGE_API_KEY')
    if not api_key:
        print("[ERROR] UPSTAGE_API_KEY not set")
        return 1

    # 요약 파일 로드
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)

    failed_files = summary.get('results', {}).get('failed_files', [])

    if not failed_files:
        print("[INFO] No failed files to retry")
        return 0

    print("=" * 80)
    print(f"실패 파일 재처리 ({len(failed_files)}개)")
    print("=" * 80)

    parser_obj = UpstageAsyncParser(api_key)
    success_count = 0
    still_failed = []

    for i, failed_item in enumerate(failed_files, 1):
        file_path = Path(failed_item['path'])
        error_msg = failed_item.get('error', '')

        print(f"\n[{i}/{len(failed_files)}] {file_path.name}")
        print(f"  Previous error: {error_msg}")

        # 출력 파일
        output_file = output_dir / f"{file_path.stem}.json"

        # 에러 타입별 처리
        if '413' in error_msg or 'page limit' in error_msg.lower():
            # 페이지 초과 → 비동기 API
            print("  [STRATEGY] Using async API (page limit exceeded)")
            result = parser_obj.parse_async(file_path)

        elif '500' in error_msg and args.retry_500:
            # 서버 에러 → 재시도
            print("  [STRATEGY] Retry with sync API (server error)")
            result = parser_obj.parse_sync(file_path)

        else:
            print(f"  [SKIP] Not retrying (error: {error_msg})")
            still_failed.append(failed_item)
            continue

        # 결과 처리
        if 'error' in result:
            print(f"  [FAILED] {result['error']}")
            still_failed.append({
                'path': str(file_path),
                'error': result['error']
            })
        else:
            # 성공 - JSON 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  [SUCCESS] Saved to {output_file.name}")
            success_count += 1

        # API Rate Limit
        time.sleep(2)

    # 결과 요약
    print("\n" + "=" * 80)
    print("재처리 완료")
    print("=" * 80)
    print(f"총 시도: {len(failed_files)}개")
    print(f"성공: {success_count}개")
    print(f"여전히 실패: {len(still_failed)}개")

    if still_failed:
        print("\n[여전히 실패한 파일]")
        for item in still_failed:
            print(f"  - {Path(item['path']).name}: {item['error']}")

    # 결과 저장
    retry_summary = {
        'timestamp': datetime.now().isoformat(),
        'total_retried': len(failed_files),
        'success': success_count,
        'still_failed': len(still_failed),
        'failed_files': still_failed
    }

    retry_summary_file = output_dir / 'retry_summary.json'
    with open(retry_summary_file, 'w', encoding='utf-8') as f:
        json.dump(retry_summary, f, ensure_ascii=False, indent=2)

    print(f"\n재처리 요약: {retry_summary_file}")

    return 0 if len(still_failed) == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
