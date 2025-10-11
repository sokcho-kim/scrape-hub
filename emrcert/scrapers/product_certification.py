from playwright.sync_api import sync_playwright, Page, TimeoutError
import time
from typing import List, Dict
from ..utils.logger import setup_logger
from ..utils.checkpoint import (
    load_checkpoint, save_checkpoint, is_processed,
    add_processed, update_last_page
)
from ..utils.csv_handler import save_to_csv, remove_duplicates

logger = setup_logger('product_certification')

BASE_URL = 'https://emrcert.mohw.go.kr/certifiState/productCertifiStateList.es?mid=a10106010000'
SAVE_INTERVAL = 10  # 10개마다 저장
MAX_RETRIES = 3
PAGE_TIMEOUT = 30000

class ProductCertificationScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.checkpoint = load_checkpoint()
        self.buffer_main = []  # 제품인증 메인 데이터 버퍼
        self.buffer_history = []  # 제품인증 이력 데이터 버퍼
        self.context = None  # Playwright context

    def run(self):
        """크롤러 실행"""
        logger.info("제품인증 크롤러 시작")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            self.context = browser.new_context()
            page = self.context.new_page()
            page.set_default_timeout(PAGE_TIMEOUT)

            try:
                # 첫 페이지 로드
                page.goto(BASE_URL)
                page.wait_for_selector('div.table2', timeout=PAGE_TIMEOUT)

                # 총 페이지 수 확인
                total_pages = self._get_total_pages(page)
                logger.info(f"총 {total_pages}페이지 발견")

                # 체크포인트에서 마지막 페이지 확인
                start_page = self.checkpoint['product_cert']['last_page'] + 1
                logger.info(f"{start_page}페이지부터 시작")

                # 각 페이지 처리
                for current_page in range(start_page, total_pages + 1):
                    logger.info(f"[{current_page}/{total_pages}] 페이지 처리 중...")

                    # 페이지 이동
                    if current_page > 1:
                        self._navigate_to_page(page, current_page)

                    # 목록에서 각 행 처리
                    self._process_list_page(page, current_page)

                    # 체크포인트 업데이트
                    update_last_page('product_cert', current_page, self.checkpoint)
                    save_checkpoint(self.checkpoint)

                # 남은 버퍼 저장
                self._flush_buffers()

                # 중복 제거
                remove_duplicates('product_certifications.csv', '인증번호')
                remove_duplicates('product_certification_history.csv', '인증번호')

                logger.info("제품인증 크롤링 완료")

            except Exception as e:
                logger.error(f"크롤러 실행 중 오류: {e}", exc_info=True)
                self._flush_buffers()  # 오류 발생 시에도 버퍼 저장
            finally:
                browser.close()

    def _get_total_pages(self, page: Page) -> int:
        """총 페이지 수 확인"""
        try:
            # "마지막" 버튼의 href에서 페이지 수 추출
            last_link = page.query_selector('div.paginate a.last')
            if last_link:
                href = last_link.get_attribute('href')
                # ?currentPage=16&... 형태에서 페이지 번호 추출
                import re
                match = re.search(r'currentPage=(\d+)', href)
                if match:
                    return int(match.group(1))
            return 1
        except Exception as e:
            logger.error(f"총 페이지 수 확인 실패: {e}")
            return 1

    def _navigate_to_page(self, page: Page, page_number: int):
        """특정 페이지로 이동"""
        url = f"{BASE_URL}&currentPage={page_number}&pageCnt=10"
        page.goto(url)
        page.wait_for_selector('div.table2', timeout=PAGE_TIMEOUT)
        time.sleep(1)  # 페이지 안정화 대기

    def _process_list_page(self, page: Page, current_page: int):
        """목록 페이지의 각 행 처리"""
        try:
            # 모든 링크의 onclick 속성에서 파라미터 추출
            links = page.query_selector_all('div.table2 table tbody tr td.orgn_nm a')
            logger.info(f"페이지 {current_page}에서 {len(links)}개 링크 발견")

            # onclick 파라미터 수집
            params_list = []
            for link in links:
                onclick = link.get_attribute('onclick')
                if onclick:
                    # fn_certifiView(apply_no, hptl_no, reg_id) 파싱
                    import re
                    match = re.search(r'fn_certifiView\(([^)]+)\)', onclick)
                    if match:
                        params_str = match.group(1)
                        # 파라미터를 쉼표로 분리하고 따옴표 제거
                        params = [p.strip().strip("'\"") for p in params_str.split(',')]
                        if len(params) >= 3:
                            params_list.append({
                                'apply_no': params[0],
                                'hptl_no': params[1],
                                'reg_id': params[2]
                            })

            logger.info(f"  {len(params_list)}개 파라미터 추출 완료")

            # 각 상세 페이지 접근
            for idx, params in enumerate(params_list):
                try:
                    # POST 방식으로 상세 페이지 이동
                    detail_url = f"{BASE_URL}&apply_no={params['apply_no']}&hptl_no={params['hptl_no']}&reg_id={params['reg_id']}"

                    # 새 탭에서 상세 페이지 열기
                    detail_page = self.context.new_page()
                    detail_page.goto(
                        'https://emrcert.mohw.go.kr/certifiState/productCertifiStateView.es?mid=a10106010000',
                        timeout=PAGE_TIMEOUT
                    )

                    # 폼 데이터 설정 및 제출
                    detail_page.evaluate(f"""
                        () => {{
                            const form = document.createElement('form');
                            form.method = 'POST';
                            form.action = '/certifiState/productCertifiStateView.es?mid=a10106010000';

                            const apply_no = document.createElement('input');
                            apply_no.name = 'apply_no';
                            apply_no.value = '{params['apply_no']}';
                            form.appendChild(apply_no);

                            const hptl_no = document.createElement('input');
                            hptl_no.name = 'hptl_no';
                            hptl_no.value = '{params['hptl_no']}';
                            form.appendChild(hptl_no);

                            const reg_id = document.createElement('input');
                            reg_id.name = 'reg_id';
                            reg_id.value = '{params['reg_id']}';
                            form.appendChild(reg_id);

                            document.body.appendChild(form);
                            form.submit();
                        }}
                    """)

                    # 페이지 로딩 대기
                    detail_page.wait_for_selector('div.table2', timeout=PAGE_TIMEOUT)
                    time.sleep(0.5)

                    # 상세 정보 추출
                    self._extract_detail_data(detail_page)

                    # 페이지 닫기
                    detail_page.close()

                    logger.info(f"  [{idx + 1}/{len(params_list)}] 처리 완료")

                except Exception as e:
                    logger.error(f"  [{idx + 1}/{len(params_list)}] 행 처리 실패: {e}")
                    try:
                        if detail_page and not detail_page.is_closed():
                            detail_page.close()
                    except:
                        pass
                    continue

        except Exception as e:
            logger.error(f"목록 페이지 처리 실패: {e}", exc_info=True)

    def _extract_detail_data(self, page: Page):
        """상세 페이지에서 데이터 추출"""
        try:
            # 메인 테이블 데이터 추출
            main_data = self._parse_main_table(page)

            # 인증번호로 중복 체크
            cert_number = main_data.get('인증번호', '')
            if is_processed('product_cert', cert_number, self.checkpoint):
                logger.info(f"  이미 처리된 인증번호: {cert_number}")
                return

            # 인증이력 데이터 추출
            history_data = self._parse_history_table(page, cert_number)

            # 버퍼에 추가
            self.buffer_main.append(main_data)
            self.buffer_history.extend(history_data)

            # 처리된 인증번호로 등록
            add_processed('product_cert', cert_number, self.checkpoint)

            # 일정 개수마다 저장
            if len(self.buffer_main) >= SAVE_INTERVAL:
                self._flush_buffers()

        except Exception as e:
            logger.error(f"상세 데이터 추출 실패: {e}", exc_info=True)

    def _parse_main_table(self, page: Page) -> Dict:
        """메인 테이블 파싱"""
        data = {}
        try:
            rows = page.query_selector_all('div.table2 table tbody tr')
            for row in rows:
                ths = row.query_selector_all('th')
                tds = row.query_selector_all('td')

                for i in range(len(ths)):
                    key = ths[i].inner_text().strip()
                    value = tds[i].inner_text().strip() if i < len(tds) else ''
                    data[key] = value

        except Exception as e:
            logger.error(f"메인 테이블 파싱 실패: {e}")

        return data

    def _parse_history_table(self, page: Page, cert_number: str) -> List[Dict]:
        """인증이력 테이블 파싱"""
        history_list = []
        try:
            history_div = page.query_selector('div#content_history')
            if not history_div:
                return history_list

            rows = history_div.query_selector_all('table tbody tr')

            # 첫 번째 행은 헤더이므로 제외
            for row in rows[1:]:
                cells = row.query_selector_all('td')
                if len(cells) >= 4:
                    history_list.append({
                        '인증번호': cert_number,
                        '인증제품명': cells[0].inner_text().strip(),
                        '버전': cells[1].inner_text().strip(),
                        '인증일자': cells[2].inner_text().strip(),
                        '만료일자': cells[3].inner_text().strip()
                    })

        except Exception as e:
            logger.error(f"인증이력 테이블 파싱 실패: {e}")

        return history_list

    def _flush_buffers(self):
        """버퍼의 데이터를 CSV에 저장"""
        if self.buffer_main:
            save_to_csv(self.buffer_main, 'product_certifications.csv')
            logger.info(f"{len(self.buffer_main)}개 메인 데이터 저장")
            self.buffer_main = []

        if self.buffer_history:
            save_to_csv(self.buffer_history, 'product_certification_history.csv')
            logger.info(f"{len(self.buffer_history)}개 이력 데이터 저장")
            self.buffer_history = []
