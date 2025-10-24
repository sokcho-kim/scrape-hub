# 데이터 동기화 가이드

## 현재 상황
- 데이터 총 크기: **347 MB**
- 데이터 위치: `data/` 디렉토리
- `.gitignore`에 이미 제외됨 ✓

## 추천 방법

### 방법 1: 클라우드 드라이브 (추천!)

**OneDrive / Google Drive 사용**

#### Windows (심볼릭 링크)
```powershell
# 1. data 폴더를 OneDrive로 이동
Move-Item "C:\Jimin\scrape-hub\data" "C:\Users\[YourName]\OneDrive\scrape-hub-data"

# 2. 심볼릭 링크 생성 (관리자 권한 필요)
New-Item -ItemType SymbolicLink -Path "C:\Jimin\scrape-hub\data" -Target "C:\Users\[YourName]\OneDrive\scrape-hub-data"
```

#### 장점
- 자동 동기화 (집/회사 모두)
- 버전 관리 (파일 복구 가능)
- 무료 (OneDrive 5GB, Google Drive 15GB)
- 추가 작업 불필요

#### 단점
- 초기 업로드 시간 (347MB)
- 인터넷 필요

---

### 방법 2: Git LFS (대안)

**대용량 파일을 Git으로 관리**

```bash
# 1. Git LFS 설치
# Windows: https://git-lfs.github.com/

# 2. 프로젝트에서 활성화
git lfs install

# 3. 추적할 파일 타입 지정
git lfs track "data/**/*.json"
git lfs track "data/**/*.pdf"
git lfs track "data/**/*.xlsx"
git lfs track "data/**/*.hwp"

# 4. .gitattributes 추가
git add .gitattributes

# 5. .gitignore에서 data/ 제거
# .gitignore 파일 편집 필요

# 6. 커밋 및 푸시
git add data/
git commit -m "Add data files with Git LFS"
git push
```

#### 장점
- Git과 완전 통합
- 버전 관리
- 팀 작업 용이

#### 단점
- GitHub Free: **1GB 저장소 + 1GB/월 대역폭 제한**
- 초과 시 유료 ($5/50GB)
- 현재 데이터 347MB → 여유 있음

---

### 방법 3: 외장하드 / USB

**수동 복사**

```bash
# 데이터 복사
cp -r data/ D:/scrape-hub-backup/data/

# 또는 robocopy (Windows)
robocopy data D:\scrape-hub-backup\data /E /MIR
```

#### 장점
- 완전한 제어
- 인터넷 불필요
- 무제한 용량

#### 단점
- 수동 동기화 필요
- 분실 위험
- 버전 관리 어려움

---

## 권장 사항

### 소규모 프로젝트 (현재)
**OneDrive/Google Drive** 추천
- 347MB는 여유롭게 수용
- 자동 동기화로 편리함

### 대규모 프로젝트 (1GB 이상)
**Git LFS + 클라우드 하이브리드**
1. 원본 데이터 (PDF, XLSX) → 클라우드
2. 파싱 결과 (JSON) → Git LFS

### 팀 작업
**Git LFS** 추천
- 모든 팀원이 동일한 데이터 접근
- 버전 관리로 충돌 방지

---

## 데이터 복구 방법

### OneDrive/Google Drive
```bash
# 심볼릭 링크가 깨진 경우
mklink /D "C:\Jimin\scrape-hub\data" "C:\Users\[YourName]\OneDrive\scrape-hub-data"
```

### Git LFS
```bash
# LFS 데이터 다운로드
git lfs pull
```

---

## 현재 데이터 구조

```
data/
├── hira_cancer/        # 암질환 데이터
│   ├── posts/          # 게시물 (484개)
│   └── parsed/         # 파싱 결과 (823개)
├── hira_master/        # 마스터 데이터
│   ├── KCD-8 1권.pdf   # 13 MB
│   ├── KDRG 분류집.pdf # 17 MB
│   └── parsed/         # 파싱 결과 (16.5 MB)
├── emrcert/            # EMR 인증
├── hira/               # HIRA 기타
├── hira_rulesvc/       # 규칙 서비스
├── likms/              # 국회 법령
└── pharma/             # 약제
```

---

## 다음 단계

1. **클라우드 드라이브 선택** (OneDrive/Google Drive)
2. **심볼릭 링크 설정**
3. **초기 동기화 완료 확인**
4. **집에서 테스트**

질문이 있으시면 언제든지 물어보세요!
