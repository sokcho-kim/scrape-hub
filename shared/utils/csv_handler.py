import pandas as pd
import os
from typing import List, Dict

def save_to_csv(data: List[Dict], filename: str, project: str = None, mode: str = 'a') -> None:
    """
    데이터를 CSV 파일에 저장

    Args:
        data: 저장할 데이터
        filename: 파일명
        project: 프로젝트 이름 (예: 'emrcert', 'hira_rulesvc')
                 지정하면 data/{project}/ 하위에 저장
        mode: 파일 모드 ('a' or 'w')
    """
    if project:
        data_dir = os.path.join('data', project)
    else:
        data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)

    filepath = os.path.join(data_dir, filename)

    df = pd.DataFrame(data)

    # 파일이 없으면 헤더 포함, 있으면 헤더 제외
    file_exists = os.path.exists(filepath)
    df.to_csv(
        filepath,
        mode=mode,
        header=not file_exists,
        index=False,
        encoding='utf-8-sig'
    )

def remove_duplicates(filename: str, key_column: str, project: str = None) -> None:
    """
    CSV 파일에서 중복 제거

    Args:
        filename: 파일명
        key_column: 중복 체크 기준 컬럼
        project: 프로젝트 이름 (예: 'emrcert', 'hira_rulesvc')
                 지정하면 data/{project}/ 하위에서 찾음
    """
    if project:
        data_dir = os.path.join('data', project)
    else:
        data_dir = 'data'

    filepath = os.path.join(data_dir, filename)

    if not os.path.exists(filepath):
        return

    df = pd.read_csv(filepath, encoding='utf-8-sig')
    df_unique = df.drop_duplicates(subset=[key_column], keep='first')
    df_unique.to_csv(filepath, index=False, encoding='utf-8-sig')
