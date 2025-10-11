import json
import os
from typing import Dict, List, Any

CHECKPOINT_FILE = 'checkpoint.json'

def load_checkpoint() -> Dict[str, Any]:
    """체크포인트 파일 로드"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'product_cert': {
            'last_page': 0,
            'processed_cert_numbers': []
        },
        'usage_cert': {
            'last_page': 0,
            'processed_cert_numbers': []
        }
    }

def save_checkpoint(data: Dict[str, Any]) -> None:
    """체크포인트 파일 저장"""
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
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
