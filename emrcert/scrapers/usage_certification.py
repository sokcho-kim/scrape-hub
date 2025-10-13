from playwright.sync_api import sync_playwright, Page, TimeoutError
import time
from typing import List, Dict
from shared.utils.logger import setup_logger
from shared.utils.checkpoint import (
    load_checkpoint, save_checkpoint, is_processed,
    add_processed, update_last_page
)
from shared.utils.csv_handler import save_to_csv, remove_duplicates

logger = setup_logger('usage_certification', project='emrcert')

BASE_URL = 'https://emrcert.mohw.go.kr/certifiState/useCertifiStateList.es?mid=a10106020000'
SAVE_INTERVAL = 10
MAX_RETRIES = 3
PAGE_TIMEOUT = 30000

class UsageCertificationScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.checkpoint = load_checkpoint(project='emrcert')
        self.buffer_main = []
        self.buffer_history = []
        self.context = None

    def run(self):
        """크롤러 실행"""
        logger.info("사용인증 크롤러 시작")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            self.context = browser.new_context()
            page = self.context.new_page()
            page.set_default_timeout(PAGE_TIMEOUT)

            try:
                page.goto(BASE_URL)
                page.wait_for_selector('div.table2', timeout=PAGE_TIMEOUT)

                total_pages = self._get_total_pages(page)
                logger.info(f"총 {total_pages}페이지 발견")

                start_page = self.checkpoint['usage_cert']['last_page'] + 1
                logger.info(f"{start_page}페이지부터 시작")

                for current_page in range(start_page, total_pages + 1):
                    logger.info(f"[{current_page}/{total_pages}] 페이지 처리 중...")

                    if current_page > 1:
                        self._navigate_to_page(page, current_page)

                    self._process_list_page(page, current_page)

                    update_last_page('usage_cert', current_page, self.checkpoint)
                    save_checkpoint(self.checkpoint, project='emrcert')

                self._flush_buffers()

                remove_duplicates('usage_certifications.csv', '인증번호', project='emrcert')
                remove_duplicates('usage_certification_history.csv', '인증번호', project='emrcert')

                logger.info("사용인증 크롤링 완료")

            except Exception as e:
                logger.error(f"크롤러 실행 중 오류: {e}", exc_info=True)
                self._flush_buffers()
            finally:
                browser.close()

    def _get_total_pages(self, page: Page) -> int:
        """총 페이지 수 확인"""
        try:
            last_link = page.query_selector('div.paginate a.last')
            if last_link:
                href = last_link.get_attribute('href')
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
        time.sleep(1)

    def _process_list_page(self, page: Page, current_page: int):
        """목록 페이지의 각 행 처리"""
        try:
            links = page.query_selector_all('div.table2 table tbody tr td.orgn_nm a')
            logger.info(f"페이지 {current_page}에서 {len(links)}개 링크 발견")

            # onclick 파라미터 수집
            params_list = []
            for link in links:
                onclick = link.get_attribute('onclick')
                if onclick:
                    import re
                    match = re.search(r'fn_certifiView\(([^)]+)\)', onclick)
                    if match:
                        params_str = match.group(1)
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
                    detail_page = self.context.new_page()
                    detail_page.goto(
                        'https://emrcert.mohw.go.kr/certifiState/useCertifiStateView.es?mid=a10106020000',
                        timeout=PAGE_TIMEOUT
                    )

                    # 폼 데이터 설정 및 제출
                    detail_page.evaluate(f"""
                        () => {{
                            const form = document.createElement('form');
                            form.method = 'POST';
                            form.action = '/certifiState/useCertifiStateView.es?mid=a10106020000';

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

                    detail_page.wait_for_selector('div.table2', timeout=PAGE_TIMEOUT)
                    time.sleep(0.5)

                    self._extract_detail_data(detail_page)

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
            main_data = self._parse_main_table(page)

            cert_number = main_data.get('인증번호', '')
            if is_processed('usage_cert', cert_number, self.checkpoint):
                logger.info(f"  이미 처리된 인증번호: {cert_number}")
                return

            history_data = self._parse_history_table(page, cert_number)

            self.buffer_main.append(main_data)
            self.buffer_history.extend(history_data)

            add_processed('usage_cert', cert_number, self.checkpoint)

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
                # 한 행에 th-td 쌍이 여러 개 있을 수 있음
                # <th>key1</th><td>val1</td><th>key2</th><td>val2</td>
                cells = row.query_selector_all('th, td')

                i = 0
                while i < len(cells):
                    # th 다음에 td가 와야 함
                    if cells[i].evaluate('el => el.tagName') == 'TH':
                        key = cells[i].inner_text().strip()
                        # 다음 셀이 td인지 확인
                        if i + 1 < len(cells) and cells[i + 1].evaluate('el => el.tagName') == 'TD':
                            value = cells[i + 1].inner_text().strip()
                            data[key] = value
                            i += 2  # th-td 쌍 건너뛰기
                        else:
                            i += 1
                    else:
                        i += 1

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
            save_to_csv(self.buffer_main, 'usage_certifications.csv', project='emrcert')
            logger.info(f"{len(self.buffer_main)}개 메인 데이터 저장")
            self.buffer_main = []

        if self.buffer_history:
            save_to_csv(self.buffer_history, 'usage_certification_history.csv', project='emrcert')
            logger.info(f"{len(self.buffer_history)}개 이력 데이터 저장")
            self.buffer_history = []


if __name__ == '__main__':
    scraper = UsageCertificationScraper(headless=True)
    scraper.run()
