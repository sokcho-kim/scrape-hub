import pandas as pd
import os
from typing import List, Dict

def save_to_csv(data: List[Dict], filename: str, mode: str = 'a') -> None:
    """데이터를 CSV 파일에 저장"""
    os.makedirs('data', exist_ok=True)
    filepath = os.path.join('data', filename)

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

def remove_duplicates(filename: str, key_column: str) -> None:
    """CSV 파일에서 중복 제거"""
    filepath = os.path.join('data', filename)

    if not os.path.exists(filepath):
        return

    df = pd.read_csv(filepath, encoding='utf-8-sig')
    df_unique = df.drop_duplicates(subset=[key_column], keep='first')
    df_unique.to_csv(filepath, index=False, encoding='utf-8-sig')
