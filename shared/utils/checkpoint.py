import json
import os
from typing import Dict, List, Any

def get_checkpoint_path(project: str = None) -> str:
    """
    체크포인트 파일 경로 반환

    Args:
        project: 프로젝트 이름 (예: 'emrcert', 'hira_rulesvc')
                 지정하면 checkpoint_{project}.json 형식으로 생성
    """
    if project:
        return f'checkpoint_{project}.json'
    return 'checkpoint.json'

def load_checkpoint(project: str = None, cert_types: List[str] = None) -> Dict[str, Any]:
    """
    체크포인트 파일 로드

    Args:
        project: 프로젝트 이름
        cert_types: 인증 타입 목록 (예: ['product_cert', 'usage_cert'])
                    없으면 기본값 사용
    """
    checkpoint_file = get_checkpoint_path(project)

    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # 기본 체크포인트 구조
    if cert_types is None:
        cert_types = ['product_cert', 'usage_cert']

    checkpoint = {}
    for cert_type in cert_types:
        checkpoint[cert_type] = {
            'last_page': 0,
            'processed_cert_numbers': []
        }
    return checkpoint

def save_checkpoint(data: Dict[str, Any], project: str = None) -> None:
    """
    체크포인트 파일 저장

    Args:
        data: 저장할 체크포인트 데이터
        project: 프로젝트 이름
    """
    checkpoint_file = get_checkpoint_path(project)
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_processed(cert_type: str, cert_number: str, checkpoint: Dict[str, Any]) -> bool:
    """이미 처리된 인증번호인지 확인"""
    return cert_number in checkpoint[cert_type]['processed_cert_numbers']

def add_processed(cert_type: str, cert_number: str, checkpoint: Dict[str, Any]) -> None:
    """처리된 인증번호 추가"""
    if cert_number not in checkpoint[cert_type]['processed_cert_numbers']:
        checkpoint[cert_type]['processed_cert_numbers'].append(cert_number)

def update_last_page(cert_type: str, page: int, checkpoint: Dict[str, Any]) -> None:
    """마지막 처리 페이지 업데이트"""
    checkpoint[cert_type]['last_page'] = page
