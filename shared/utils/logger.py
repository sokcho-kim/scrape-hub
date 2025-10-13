import logging
from datetime import datetime
import os

def setup_logger(name: str, project: str = None) -> logging.Logger:
    """
    로거 설정

    Args:
        name: 로거 이름 (예: 'product_certification')
        project: 프로젝트 이름 (예: 'emrcert', 'hira_rulesvc')
                 지정하면 logs/{project}/ 하위에 저장
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 로그 디렉토리 생성
    if project:
        log_dir = os.path.join('logs', project)
    else:
        log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    # 파일 핸들러
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
