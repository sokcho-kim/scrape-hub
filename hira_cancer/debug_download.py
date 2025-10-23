"""
첨부파일 다운로드 메커니즘 디버깅
실제로 다운로드 URL에 접근했을 때 무슨 일이 일어나는지 확인
"""
import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path


async def test_download():
    """실제 다운로드 URL 테스트"""

    # 이미 수집한 JSON에서 첨부파일 정보 가져오기
    base_dir = Path(__file__).parent.parent
    json_file = base_dir / 'data' / 'hira_cancer' / 'raw' / 'hira_cancer_20251023_163624.json'

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 첫 번째 첨부파일 찾기
    sample_attachment = None
    sample_post = None

    for board_key, posts in data['data'].items():
        for post in posts:
            if post.get('attachments'):
                sample_post = post
                sample_attachment = post['attachments'][0]
                break
        if sample_attachment:
            break

    if not sample_attachment:
        print("첨부파일을 찾을 수 없습니다.")
        return

    print("="*80)
    print("첨부파일 다운로드 디버깅")
    print("="*80)
    print(f"\n게시판: {sample_post['board_name']}")
    print(f"게시글: {sample_post['title'][:50]}...")
    print(f"첨부파일: {sample_attachment['filename']}")
    print(f"다운로드 URL: {sample_attachment.get('download_url')}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 방법 1: expect_download 테스트 (현재 사용중)
        print("\n[방법 1] expect_download() 테스트")
        print("-" * 80)
        try:
            print("다운로드 이벤트 대기중...")
            async with page.expect_download(timeout=10000) as download_info:
                response = await page.goto(sample_attachment['download_url'])
                print(f"페이지 이동 완료")
                print(f"Response status: {response.status if response else 'None'}")
                print(f"Response headers: {response.headers if response else 'None'}")

            download = await download_info.value
            print(f"다운로드 성공!")
            print(f"파일명: {download.suggested_filename}")

        except Exception as e:
            print(f"다운로드 실패: {e}")

            # 페이지 내용 확인
            print(f"\n페이지 URL: {page.url}")
            print(f"페이지 제목: {await page.title()}")

            # HTML 일부 확인
            html = await page.content()
            print(f"\nHTML 길이: {len(html)}자")
            if len(html) < 1000:
                print(f"HTML 내용:\n{html}")
            else:
                print(f"HTML 일부:\n{html[:1000]}...")

        # 방법 2: Response 직접 확인
        print("\n\n[방법 2] Response 직접 분석")
        print("-" * 80)

        page2 = await context.new_page()
        response = await page2.goto(sample_attachment['download_url'])

        print(f"Status: {response.status}")
        print(f"URL: {response.url}")
        print(f"Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

        # Content-Type이 application/octet-stream이면 다운로드
        content_type = response.headers.get('content-type', '')
        print(f"\nContent-Type: {content_type}")

        if 'application' in content_type or 'octet-stream' in content_type:
            print("파일 다운로드 응답!")
            body = await response.body()
            print(f"파일 크기: {len(body)} bytes ({len(body)/1024:.1f} KB)")
        else:
            # HTML 응답인 경우
            text = await response.text()
            print(f"HTML 응답 (길이: {len(text)}자)")
            if len(text) < 1000:
                print(f"내용:\n{text}")
            else:
                print(f"내용 일부:\n{text[:1000]}...")

        # 방법 3: 실제 상세 페이지에서 onclick 실행
        print("\n\n[방법 3] 실제 상세 페이지에서 다운로드 링크 클릭")
        print("-" * 80)

        page3 = await context.new_page()

        # 상세 페이지로 이동
        print(f"상세 페이지 이동: {sample_post['detail_url']}")
        await page3.goto(sample_post['detail_url'], wait_until='networkidle')

        # 다운로드 링크 찾기
        file_links = await page3.locator('a[onclick*="downLoad"]').all()
        print(f"다운로드 링크 발견: {len(file_links)}개")

        if file_links:
            # 첫 번째 링크의 onclick 확인
            first_link = file_links[0]
            onclick = await first_link.get_attribute('onclick')
            text = await first_link.text_content()
            print(f"첫 번째 링크: {text.strip()}")
            print(f"onclick: {onclick}")

            # 링크 클릭 시도
            print("\n링크 클릭 시도...")
            try:
                async with page3.expect_download(timeout=10000) as dl:
                    await first_link.click()

                download = await dl.value
                print(f"다운로드 성공!")
                print(f"파일명: {download.suggested_filename}")

                # 실제 저장
                save_path = base_dir / 'data' / 'hira_cancer' / 'raw' / 'test_download.tmp'
                await download.save_as(save_path)
                print(f"저장 완료: {save_path} ({save_path.stat().st_size / 1024:.1f} KB)")

            except Exception as e:
                print(f"클릭 다운로드 실패: {e}")

        await browser.close()

    print("\n" + "="*80)
    print("디버깅 완료")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_download())
