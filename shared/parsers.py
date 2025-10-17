"""
공통 문서 파서 모듈

Upstage Document Parse API를 사용하여
HWP, PDF 등의 문서를 Markdown/HTML로 변환
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class BaseParser(ABC):
    """문서 파서 기본 추상 클래스"""

    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        파일을 파싱하여 구조화된 데이터 반환

        Args:
            file_path: 파싱할 파일 경로

        Returns:
            {
                "content": "Markdown 형식 텍스트",
                "html": "HTML 형식 텍스트",
                "metadata": {...},
                "pages": int
            }
        """
        pass

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """
        해당 파일 확장자를 지원하는지 확인

        Args:
            file_extension: 확장자 (예: '.hwp', '.pdf')

        Returns:
            지원 여부
        """
        pass


class UpstageParser(BaseParser):
    """
    Upstage Document Parse API 파서

    지원 형식: HWP, PDF, DOCX, PPTX, XLSX, JPEG, PNG 등
    """

    # Upstage가 지원하는 파일 형식
    SUPPORTED_EXTENSIONS = [
        '.pdf', '.hwp', '.hwpx',  # 한글 문서
        '.docx', '.pptx', '.xlsx',  # MS Office
        '.jpeg', '.jpg', '.png', '.bmp', '.tiff', '.heic'  # 이미지
    ]

    API_URL = "https://api.upstage.ai/v1/document-ai/document-parse"
    API_URL_DIGITIZATION = "https://api.upstage.ai/v1/document-digitization"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Upstage API 키
        """
        self.api_key = api_key

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        파일 파싱

        Args:
            file_path: 파싱할 파일 경로

        Returns:
            파싱 결과

        Raises:
            FileNotFoundError: 파일이 없는 경우
            ValueError: 지원하지 않는 파일 형식
            requests.HTTPError: API 호출 실패
        """
        # 1. 파일 검증
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.supports(file_path.suffix):
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # 파일 크기 확인
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file_size/1024/1024:.2f}MB "
                f"(max {self.MAX_FILE_SIZE/1024/1024:.0f}MB)"
            )

        # 2. API 호출
        result = self._call_api(file_path)

        # 3. 결과 정리
        return self._format_result(result)

    def supports(self, file_extension: str) -> bool:
        """지원 확장자 확인"""
        return file_extension.lower() in self.SUPPORTED_EXTENSIONS

    def _call_api(self, file_path: Path) -> Dict:
        """
        Upstage API 호출

        Args:
            file_path: 업로드할 파일 경로

        Returns:
            API 응답 (JSON)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {
                'output_formats': 'markdown,html'  # Markdown + HTML 요청
            }

            response = requests.post(
                self.API_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=60  # 60초 타임아웃
            )

        # 에러 체크
        response.raise_for_status()
        return response.json()

    def _call_api_digitization(self, file_path: Path) -> Dict:
        """
        Upstage Document Digitization API 호출 (강제 OCR)

        Args:
            file_path: 업로드할 파일 경로

        Returns:
            API 응답 (JSON)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {
                'ocr': 'force',  # 강제 OCR
                'model': 'document-parse',
                'output_formats': 'markdown,html'
            }

            response = requests.post(
                self.API_URL_DIGITIZATION,
                headers=headers,
                files=files,
                data=data,
                timeout=120  # 120초 타임아웃 (OCR은 더 오래 걸림)
            )

        # 에러 체크
        response.raise_for_status()
        return response.json()

    def parse_with_ocr(self, file_path: Path) -> Dict[str, Any]:
        """
        강제 OCR로 파일 파싱 (Digitization API 사용)

        Args:
            file_path: 파싱할 파일 경로

        Returns:
            파싱 결과

        Raises:
            FileNotFoundError: 파일이 없는 경우
            ValueError: 지원하지 않는 파일 형식
            requests.HTTPError: API 호출 실패
        """
        # 1. 파일 검증
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.supports(file_path.suffix):
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # 파일 크기 확인
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file_size/1024/1024:.2f}MB "
                f"(max {self.MAX_FILE_SIZE/1024/1024:.0f}MB)"
            )

        # 2. Digitization API 호출
        result = self._call_api_digitization(file_path)

        # 3. 결과 정리
        return self._format_result(result)

    def _format_result(self, api_result: Dict) -> Dict[str, Any]:
        """
        API 결과를 표준 형식으로 변환

        Args:
            api_result: Upstage API 응답

        Returns:
            표준화된 파싱 결과
        """
        content = api_result.get('content', {})
        usage = api_result.get('usage', {})

        return {
            "content": content.get('markdown', ''),
            "html": content.get('html', ''),
            "metadata": api_result.get('metadata', {}),
            "pages": usage.get('pages', 0),  # usage.pages에서 실제 페이지 수 가져오기
            "model": api_result.get('model', 'unknown'),
            "usage": usage
        }


class ParserFactory:
    """
    파서 생성 팩토리
    """

    @staticmethod
    def create(parser_type: str = "upstage", api_key: Optional[str] = None) -> BaseParser:
        """
        파서 인스턴스 생성

        Args:
            parser_type: 파서 종류 ("upstage")
            api_key: API 키 (None이면 환경변수에서 로드)

        Returns:
            파서 인스턴스

        Raises:
            ValueError: 알 수 없는 파서 타입 또는 API 키 없음
        """
        if parser_type == "upstage":
            # API 키 확인
            if api_key is None:
                api_key = os.getenv("UPSTAGE_API_KEY")

            if not api_key:
                raise ValueError(
                    "UPSTAGE_API_KEY not found. "
                    "Set it in .env file or pass as argument."
                )

            return UpstageParser(api_key)

        raise ValueError(f"Unknown parser type: {parser_type}")


# 편의 함수
def create_parser(parser_type: str = "upstage") -> BaseParser:
    """
    파서 생성 단축 함수

    Args:
        parser_type: 파서 종류

    Returns:
        파서 인스턴스
    """
    return ParserFactory.create(parser_type)
