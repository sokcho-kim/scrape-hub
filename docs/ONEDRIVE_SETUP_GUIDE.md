# OneDrive 데이터 폴더 동기화 설정 가이드

## 1단계: OneDrive 설치 확인

### Windows 10/11에서 확인
1. **시작 메뉴** 열기 → "OneDrive" 검색
2. OneDrive 아이콘이 시스템 트레이(작업 표시줄 오른쪽)에 있는지 확인
3. 없으면 설치 필요: https://www.microsoft.com/ko-kr/microsoft-365/onedrive/download

### OneDrive 폴더 위치 확인
```powershell
# PowerShell 실행 (관리자 권한 불필요)
explorer $env:OneDrive
```

일반적인 경로:
- `C:\Users\[사용자명]\OneDrive`
- `C:\Users\[사용자명]\OneDrive - 회사명` (회사 계정)

---

## 2단계: 데이터 폴더 OneDrive로 이동

### 방법 A: GUI (추천 - 초보자용)

**회사 PC에서:**

1. **파일 탐색기** 열기
2. `C:\Jimin\scrape-hub` 폴더로 이동
3. `data` 폴더 **우클릭** → **잘라내기** (Ctrl+X)
4. OneDrive 폴더로 이동:
   - `C:\Users\[사용자명]\OneDrive` 또는
   - 파일 탐색기 왼쪽 사이드바에서 "OneDrive" 클릭
5. OneDrive 폴더 안에서 **우클릭** → **붙여넣기** (Ctrl+V)
6. 폴더 이름을 `scrape-hub-data`로 변경 (선택사항)

**동기화 시작됨**: OneDrive가 자동으로 347MB 업로드 시작 (1-5분 소요)

---

### 방법 B: 명령어 (PowerShell)

```powershell
# 관리자 권한으로 PowerShell 실행

# 1. data 폴더를 OneDrive로 이동
Move-Item "C:\Jimin\scrape-hub\data" "$env:OneDrive\scrape-hub-data"

# 2. 확인
ls "$env:OneDrive\scrape-hub-data"
```

---

## 3단계: 심볼릭 링크 생성

**심볼릭 링크란?**
- `data` 폴더가 OneDrive에 있지만, 프로그램은 원래 위치(`C:\Jimin\scrape-hub\data`)에 있는 것처럼 인식
- 바로가기와 비슷하지만, 프로그램이 완전히 투명하게 접근 가능

### PowerShell (관리자 권한 필요!)

```powershell
# 1. PowerShell을 관리자 권한으로 실행
# 방법: 시작 메뉴 → "PowerShell" 검색 → 우클릭 → "관리자 권한으로 실행"

# 2. 심볼릭 링크 생성
cd C:\Jimin\scrape-hub
New-Item -ItemType SymbolicLink -Path "data" -Target "$env:OneDrive\scrape-hub-data"

# 3. 확인
ls data
# OneDrive의 파일이 보이면 성공!
```

### 또는 CMD (관리자 권한 필요!)

```cmd
cd C:\Jimin\scrape-hub
mklink /D data "%OneDrive%\scrape-hub-data"
```

---

## 4단계: 동기화 완료 확인

### OneDrive 상태 확인
1. OneDrive 아이콘 (시스템 트레이) 클릭
2. "동기화 완료" 또는 "최신 상태" 확인
3. 업로드 중이면 진행률 표시됨

### 파일 확인
```powershell
# 링크가 정상 작동하는지 확인
ls C:\Jimin\scrape-hub\data
# 파일이 보이면 성공!
```

---

## 5단계: 집에서 설정

**집 PC에서:**

### A. OneDrive 로그인
1. OneDrive 설치 (이미 되어있으면 생략)
2. **같은 Microsoft 계정**으로 로그인
3. `scrape-hub-data` 폴더 자동 동기화 대기 (1-5분)

### B. Git 저장소 클론
```bash
cd C:\
git clone https://github.com/sokcho-kim/scrape-hub.git
cd scrape-hub
```

### C. 심볼릭 링크 생성 (관리자 PowerShell)
```powershell
cd C:\scrape-hub
New-Item -ItemType SymbolicLink -Path "data" -Target "$env:OneDrive\scrape-hub-data"
```

### D. 가상환경 설정
```bash
python -m venv scraphub
scraphub\Scripts\activate
pip install -r requirements.txt
```

**완료!** 이제 회사/집 모두에서 같은 데이터 사용 가능 🎉

---

## 문제 해결

### 문제 1: "관리자 권한이 필요합니다"
**해결:**
- PowerShell을 **관리자 권한으로 실행** 필요
- 시작 메뉴 → PowerShell 검색 → 우클릭 → "관리자 권한으로 실행"

### 문제 2: 심볼릭 링크가 깨짐
**원인:** OneDrive 폴더 경로가 다름

**해결:**
```powershell
# 1. 기존 링크 삭제
Remove-Item "C:\Jimin\scrape-hub\data"

# 2. 올바른 경로로 재생성
New-Item -ItemType SymbolicLink -Path "C:\Jimin\scrape-hub\data" -Target "$env:OneDrive\scrape-hub-data"
```

### 문제 3: OneDrive 동기화 느림
**해결:**
1. OneDrive 아이콘 클릭 → 설정
2. "네트워크" 탭 → "업로드 속도" → "제한 없음"
3. 큰 파일 제외:
   - `data/hira_master/*.pdf` (원본 PDF는 제외 가능)

### 문제 4: 용량 부족 (OneDrive 5GB 제한)
**옵션 A:** Google Drive 사용 (15GB)
- Google Drive 설치: https://www.google.com/drive/download/
- 같은 방식으로 설정

**옵션 B:** 선택적 동기화
```powershell
# 파싱 결과만 동기화 (원본 PDF 제외)
Move-Item data\hira_master\*.pdf D:\local-backup\
```

---

## 확인 체크리스트

- [ ] OneDrive 설치 및 로그인 완료
- [ ] `data` 폴더를 OneDrive로 이동
- [ ] 심볼릭 링크 생성 (관리자 권한)
- [ ] `ls data` 명령어로 파일 보임
- [ ] OneDrive 동기화 완료 (초록색 체크)
- [ ] 집 PC에서도 같은 설정 완료

---

## 요약

**회사 PC:**
1. data 폴더 → OneDrive로 이동
2. 심볼릭 링크 생성 (관리자)
3. 동기화 대기

**집 PC:**
1. OneDrive 로그인 (같은 계정)
2. Git clone
3. 심볼릭 링크 생성 (관리자)
4. 작업 시작!

**자동 동기화**: 회사에서 작업 → 집에서 자동 반영 ✨
