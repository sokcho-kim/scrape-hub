"""
Ajax 응답 디버깅
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_ajax():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = "https://www.cancer.go.kr/lay1/program/S1T523C837/dictionaryworks/list.do?rows=30&cpage=1"
        print(f"페이지 로딩: {url}\n")

        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # 테스트할 키워드들
        test_keywords = [
            "1-메틸-디-트립토판",
            "1상 임상시험",
            "암",
            "항암제"
        ]

        for keyword in test_keywords:
            print(f"\n{'='*80}")
            print(f"테스트 키워드: {keyword}")
            print('='*80)

            # 방법 1: fetch로 JSON 응답 받기
            print("\n[방법 1] fetch + JSON 응답:")
            try:
                import urllib.parse
                encoded = urllib.parse.quote(keyword)

                result = await page.evaluate(f'''
                    async () => {{
                        const response = await fetch('/inc/searchWorks/search.do', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/x-www-form-urlencoded',
                            }},
                            body: 'work={encoded}'
                        }});

                        const contentType = response.headers.get('content-type');
                        console.log('Content-Type:', contentType);

                        const text = await response.text();
                        console.log('Raw Response:', text);

                        try {{
                            const json = JSON.parse(text);
                            return {{ type: 'json', data: json }};
                        }} catch (e) {{
                            return {{ type: 'text', data: text }};
                        }}
                    }}
                ''')

                print(f"응답 타입: {result.get('type')}")
                print(f"응답 데이터: {result.get('data')}")

            except Exception as e:
                print(f"오류: {e}")

            # 방법 2: 실제 버튼 클릭해서 팝업 확인
            print("\n[방법 2] 버튼 클릭 + 팝업 내용:")
            try:
                # 버튼 찾기
                buttons = await page.query_selector_all('.word-box button.word')

                for btn in buttons[:5]:  # 처음 5개만
                    text = await btn.inner_text()
                    if keyword in text:
                        print(f"버튼 클릭: {text}")

                        # 클릭
                        await btn.click()
                        await asyncio.sleep(1)

                        # 팝업 내용 확인
                        popup = await page.query_selector('.layer_popup')
                        if popup:
                            title = await popup.query_selector('.tit')
                            desc = await popup.query_selector('.desc')

                            if title:
                                title_text = await title.inner_text()
                                print(f"  팝업 제목: {title_text}")

                            if desc:
                                desc_text = await desc.inner_text()
                                print(f"  팝업 설명: {desc_text[:200]}...")

                            # 팝업 닫기
                            close_btn = await popup.query_selector('.btn_pop_close')
                            if close_btn:
                                await close_btn.click()
                                await asyncio.sleep(0.5)

                        break

            except Exception as e:
                print(f"오류: {e}")

            await asyncio.sleep(1)

        await asyncio.sleep(3)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_ajax())
