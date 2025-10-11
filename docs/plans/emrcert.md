# EMRCERT Project 
EMR 인증 제품 크롤링 작업 지시서

## 작업 개요

보건복지부 EMR 인증 현황 페이지에서 인증 제품 정보를 Playwright를 사용하여 크롤링합니다.

## 대상 사이트

```
<https://emrcert.mohw.go.kr/certifiState/productCertifiStateList.es?mid=a10106010000&returnUrlL=null>

```

## 작업 단계

* 아래 1,2 단계의 작업지시서에 따라 결과물을 csv에 누적하여 저장한다.
* 일정 단위 이상 적재시 저장을 하도록 하고 중간에 오류 발생하는 등의 중단이 일어날 경우 그 시점부터 다시 수집 할 수 있도록 한다.
* 데이터의 중복이나 오류가 없도록 저장한다.

### **기술적 요구사항**

* 동적 콘텐츠 로딩 대응 (JavaScript 렌더링)
* 페이지네이션 자동 처리
* 에러 핸들링 및 재시도 로직
* 출력 형식: CSV 또는 JSON

### 추가 확인 필요 사항

* 로그인/인증 필요 여부
* CAPTCHA 존재 여부
* 페이지 로딩 시간 (대기 시간 설정용)
* robots.txt 정책
* 데이터 업데이트 주기

## 1. EMR 인증제도 제품인증 페이지 작업 지시서

### [목록 페이지]

1. 목록 테이블 접근
   div class = "table2"
2. 목록 테이블 클릭
   <table></table> 안의 <tr>
   ```html
   <td class="orgn_nm" style="text-align:left;">
   	<a href="javascript:void(0);" onclick="fn_certifiView(4341, '39100022', 'halla');">(의) 한라의료재단 제주한라병원</a>
   	<div class="addrInfo" style="display:none;">
   		제주특별자치도 제주시 도령로
   	</div>
   </td>
   ```
3. 페이지네이션
   div class="paginate"
   총 16페이지  (a태그 class =last 누르면 확인 가능함)
   `<a>` 태그로 이루어져 있음 (href)
   class next 로 10 페이지 이후 데이터 조회
   ```html
   <div class="paginate">

   			<a href="?currentPage=1&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000" class="first"><span class="sr-only">처음</span></a>

   			<a href="?currentPage=1&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">1</a><a href="?currentPage=2&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">2</a><a href="?currentPage=3&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">3</a><a href="?currentPage=4&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">4</a><a href="?currentPage=5&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">5</a><a href="?currentPage=6&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">6</a><a href="?currentPage=7&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">7</a><a href="?currentPage=8&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">8</a><a href="?currentPage=9&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">9</a><strong>10</strong>
   			<a class="next" href="?currentPage=11&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000"><span class="sr-only">다음</span></a>

   			<a href="?currentPage=16&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000" class="last"><span class="sr-only">마지막</span></a>


   	</div>
   ```

### [상세 페이지]

div class="table2" 안의 내용과 div id="content_history" 전체의 내용을 다음과 같이 적재

제품인증 테이블 : 인증번호, 인증기간 , 인증제품명, 버전, 기관정보, 구분, 대표자, 소재지, 전화번호, 홈페이지, 비고

제품인증 이력 테이블 : 인증번호(제품인증 테이블의 내용을 사용), 인증제품명, 버전, 인증일자, 만료일자

```html
<section id="content_detail" class="content_body">
			
			
			

 
 
<script>
//<![CDATA[


//]]>
</script>
<div class="table2">
    <table>
    	<caption>제품인증된 인증제품의 상세내용을 담은 표로, 인증번호, 인증기간, 인증제품명, 버전, 기관정보, 구분, 대표자, 소재지, 전화번호, 홈페이지, 비고 항목으로 구분되어 있습니다.</caption>
        <colgroup>
            <col width="40%">
            <col width="60%">
            <col width="40%">
            <col width="60%">
        </colgroup>
    <tbody>
        <tr>
        	<th scope="row">인증번호</th>
        	<td>제-2025-00006</td>
        	<th scope="row">인증기간</th>
        	<td>2026-06-14 ~ 2029-06-13</td>
        </tr>
        <tr>
            <th scope="row">인증제품명</th>
            <td>PHIS</td>
            <th scope="row">버전</th>
            <td>1.0</td>
        </tr>
        <tr>
        	<th scope="row">기관정보</th>
        	<td colspan="3" class="txt-left">고려대학교의료원</td>
        </tr>
        <tr>
        	<th scope="row">구분</th>
        	<td colspan="3" class="txt-left">의료기관</td>
        </tr>
        <tr>
        	<th scope="row">대표자</th>
        	<td colspan="3" class="txt-left">김영훈</td>
        </tr>
        <tr>
        	<th scope="row">소재지</th>
        	<td colspan="3" class="txt-left">서울 성북구 고려대로 73 (안암동5가, 고려대병원)  </td>
        </tr>
        <tr>
        	<th scope="row">전화번호</th>
        	<td colspan="3" class="txt-left">02-920-5862</td>
        </tr>
        <tr>
        	<th scope="row">홈페이지</th>
        	<td colspan="3" class="txt-left">www.kumc.or.kr</td>
        </tr>
        <tr>
        	<th scope="row">비고</th>
        	<td colspan="3" class="txt-left">
        	
        	</td>
        </tr>
    </tbody>
    </table>
</div>

<div id="content_history" style="margin-top: 20px;">
	<h3>인증이력</h3>
	<div class="table2">
		<table>
			<caption>인증이력</caption>
			<colgroup>
	            <col width="*">
	            <col width="20%">
	            <col width="20%">
	            <col width="20%">
	        </colgroup>
	        <tbody>
	        	<tr>
	        		<th>인증제품명</th>
	        		<th>버전</th>
	        		<th>인증일자</th>
	        		<th>만료일자</th>
	        	</tr>
	      
		      
			      
				        	<tr>
				        		<td class="txt-left">PHIS</td>
				        		<td>1.0</td>
				        		<td>2026-06-14</td>
				        		<td>2029-06-13</td>
				        	</tr>
				      
				        	<tr>
				        		<td class="txt-left">PHIS</td>
				        		<td>1.0</td>
				        		<td>2022-06-14</td>
				        		<td>2026-06-13</td>
				        	</tr>
				      
			      
		      
		      
	        </tbody>
		</table>
	</div>
</div>

<p class="txt-center btns">

</p>

 <!-- ì´ë©ì¼ ì ê·ì -->
 <!-- ì íë²í¸ ì ê·ì -->

			</section>
```

## 2. EMR 인증제도 사용 인증 페이지 작업 지시서

### [목록 페이지]

1. 목록 테이블 접근
   div class = "table2"
2. 목록 테이블 클릭
   <table></table> 안의 <tr>
   ```html
   <td class="orgn_nm" style="text-align:left;">
   	<a href="javascript:void(0);" onclick="fn_certifiView(4820, '11100117', 'KUMC_01');">고려대학교의료원</a>
   	<div class="addrInfo" style="top: 602.625px; left: 52px; display: none;">
   		서울 성북구 고려대로
   	</div>
   </td>
   ```
3. 페이지네이션
   div class="paginate"
   총 406 페이지 (a태그 class =last 누르면 확인 가능함)
   `<a>` 태그로 이루어져 있음 (href)
   class next 로 10 페이지 이후 데이터 조회
   ```html
   <div class="paginate">

   			<a href="?currentPage=1&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000" class="first"><span class="sr-only">처음</span></a>

   			<a href="?currentPage=1&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">1</a><a href="?currentPage=2&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">2</a><a href="?currentPage=3&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">3</a><a href="?currentPage=4&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">4</a><a href="?currentPage=5&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">5</a><a href="?currentPage=6&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">6</a><a href="?currentPage=7&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">7</a><a href="?currentPage=8&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">8</a><a href="?currentPage=9&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000">9</a><strong>10</strong>
   			<a class="next" href="?currentPage=11&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000"><span class="sr-only">다음</span></a>

   			<a href="?currentPage=16&pageCnt=10&apply_certifi_date=&apply_certifi_type=&expire_YN=null&mid=a10106010000" class="last"><span class="sr-only">마지막</span></a>


   	</div>
   ```

### [상세 페이지]

div class="table2" 안의 내용과 div id="content_history" 전체의 내용을 다음과 같이 적재

사용인증 테이블 : 인증번호 , 인증기간, 개발사명, 사용제품명, 버전, 기관정보, 종별구분, 병상수(설치병상수 기준), 대표자, 소재지, 전화번호, 홈페이지, 비고

사용인증 이력 테이블 : 인증번호(제품인증 테이블의 내용을 사용), 인증제품명, 버전, 인증일자, 만료일자
