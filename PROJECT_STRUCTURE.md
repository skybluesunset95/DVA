# 🏗️ DVA (닥터빌 자동화) 프로젝트 구조

이 문서는 DVA 프로젝트의 파일 구조와 각 모듈의 역할을 설명하여, 개발자와 AI가 프로젝트를 빠르게 이해할 수 있도록 돕습니다.

## 📂 폴더 구조 (Directory Structure)

```
DVA/
├── 📂 modules/                    # 기능별 로직이 담긴 모듈 디렉토리
│   ├── 📜 base_module.py            # [핵심] 모든 모듈의 부모 클래스 (로깅, 에러 처리, 공통 기능)
│   ├── 📜 login_module.py           # 자동 로그인 처리
│   ├── 📜 attendance_module.py      # 출석체크 기능
│   ├── 📜 quiz_module_new.py        # 퀴즈 풀기 기능 (최신 버전)
│   ├── 📜 seminar_module.py         # 라이브 세미나 확인, 신청/취소, 입장
│   ├── 📜 survey_module.py          # 설문조사 자동 참여 기능
│   ├── 📜 survey_problem.py         # 설문 퀴즈 문제/정답 관리 + GUI 관리 창
│   ├── 📜 points_check_module.py    # 포인트/출석/퀴즈 상태 확인 및 GUI 업데이트
│   ├── 📜 blog_search_module.py     # 블로그 검색 (퀴즈 정답 자동 검색)
│   └── 📂 backup/                   # 백업 파일 저장소
│
├── 📜 main_GUI.pyw                # [진입점] GUI 프로그램 메인 실행 파일 (Tkinter 기반)
├── 📜 main_task_manager.py        # [매니저] 작업 관리자 (스레드 관리, 모듈 실행 조율)
├── 📜 web_automation.py           # [코어] 웹 자동화 핵심 클래스 (Selenium 드라이버 관리)
├── 📜 update_program.py           # 프로그램 자동 업데이트 로직 (GitHub 기반)
│
├── 📜 install.ps1                 # PowerShell 설치 스크립트 (Python + 패키지 + 계정 설정)
├── 📜 설치하기.bat                # 설치 스크립트 실행용 배치 파일
├── 📜 업데이트.bat                # 업데이트 실행용 배치 파일
├── 📜 account.bat                 # 프로그램 실행용 배치 파일 (설치 시 자동 생성, gitignore 대상)
│
├── 📜 settings.json               # 사용자 설정 파일 (자동 생성됨)
├── 📜 survey_quizzes.json         # 설문 퀴즈 문제/정답 데이터 파일
├── 📜 requirements.txt            # 파이썬 의존성 패키지 목록
├── 📜 .gitignore                  # Git 버전 관리 제외 파일 목록
├── 📜 PROJECT_STRUCTURE.md        # 프로젝트 구조 설명 (이 파일)
└── 📜 README.md                   # 프로젝트 설명 및 사용법
```

---

## 🔑 주요 파일 상세 설명

### 1. 프로그램 진입점 (Entry Points)
*   **`main_GUI.pyw`** (1512줄):
    *   사용자가 실행하는 메인 프로그램입니다.
    *   **`ToolTip` 클래스**: 버튼 위에 마우스를 1.5초간 올려놓으면 기능 설명 툴팁이 표시됩니다.
    *   **`DoctorBillAutomation` 클래스**: 전체 GUI와 로직을 담당하는 핵심 클래스입니다.
        *   **GUI 구성**: `tkinter`를 사용하여 버튼, 로그 창, 상태 표시줄, 사용자 정보 패널, 오늘의 세미나 트리뷰를 그립니다.
        *   **설정 시스템**: `settings.json`을 통해 헤드리스 모드, 자동 출석/퀴즈/세미나확인/설문/세미나신청 등의 설정을 관리합니다.
        *   **설정 UI**: `open_settings()` 메서드로 설정 변경 팝업 창을 제공합니다.
        *   **이벤트 핸들링**: 사용자 클릭 이벤트를 받아 `TaskManager`에게 작업을 요청합니다.
        *   **자동 작업**: 로그인 후 설정에 따라 출석체크, 퀴즈풀기, 세미나 확인, 설문참여를 자동 실행합니다.
        *   **화면 갱신**: 로그 메시지, 작업 상태, 사용자 정보, 세미나 정보를 화면에 업데이트합니다.
        *   **로깅 시스템**: `GUILogHandler`를 통해 모듈들의 파이썬 로그를 GUI 로그 창에 표시합니다.
        *   **설문 문제 관리**: 설문 문제/정답을 관리하는 별도 팝업 창을 제공합니다.

*   **`main_task_manager.py`** (384줄):
    *   **중앙 관제탑** 역할을 합니다.
    *   **`TaskManagerState` 클래스**: 현재 로그인 상태, 실행 중인 모듈, 모듈 큐 등을 체계적으로 관리합니다.
    *   **`ModuleFactory` 클래스**: 모듈 타입(`login`, `attendance`, `quiz`, `survey`, `seminar`)에 따라 해당 모듈 클래스를 동적으로 로드합니다. 로그인 필요 여부 판단도 담당합니다.
    *   **`TaskManager` 클래스**: 여러 모듈의 실행 요청을 받아 별도 **스레드(Thread)**에서 실행합니다. (GUI 멈춤 방지)
        *   **모듈 캐시**: 한 번 로드된 모듈 클래스를 캐싱하여 재사용합니다.
        *   **설정 기반 실행**: `execute_module_by_config()`를 통해 로그인 상태 확인 → 모듈 생성 → 스레드 실행 → 에러 처리를 일원화합니다.
        *   **특수 액션** 처리: 세미나 신청/취소 등 모듈별 특수 동작을 지원합니다.

### 2. 코어 라이브러리 (Core Libraries)
*   **`web_automation.py`** (215줄):
    *   **웹 브라우저 제어**의 가장 밑단에 있는 클래스입니다.
    *   `Selenium` WebDriver를 초기화하고 옵션을 설정합니다.
    *   **로컬 우선 전략**: 로컬 `chromedriver.exe`를 먼저 시도하고, 실패 시 `webdriver-manager`로 자동 업데이트합니다. (Self-healing)
    *   **구 버전 정리**: 업데이트 후 백업된 구 버전 chromedriver를 자동 삭제합니다.
    *   **설정값**: 헤드리스 모드, 창 크기(1200x800), implicit wait(2초), page load timeout(15초) 등.

*   **`modules/base_module.py`** (169줄):
    *   모든 기능 모듈이 따라야 할 **표준 규격(Interface/Base Class)**입니다.
    *   **상태 상수 정의**: `STATUS_ATTENDANCE_COMPLETE`, `STATUS_QUIZ_COMPLETE` 등 상태 문자열을 통일 관리합니다.
    *   **공통 기능 제공**:
        *   로깅: `log_info`, `log_error`, `log_success`, `log_warning` (이모지 포함)
        *   에러 처리: `handle_error()` - 에러 타입별 사용자 친화적 메시지 + 복구 방법 제시
        *   포인트 확인: `check_points_after_activity()` - 활동 완료 후 자동 포인트 상태 확인
    *   **추상 메서드**: `execute()` (필수 구현), `cleanup()` (선택 오버라이드)

### 3. 기능 모듈 (Feature Modules)
각 모듈은 `modules/` 폴더 안에 있으며, `BaseModule`을 상속받아 독립적인 하나의 작업을 수행합니다.

*   **`login_module.py`** (287줄): 닥터빌 통합회원 로그인을 처리합니다.
    *   닥터빌 메인 → 통합회원 로그인 버튼 클릭 → 로그인 폼 입력 → 로그인 성공 확인
    *   로그인 후 자동으로 `check_points_after_activity()`를 호출하여 포인트 상태를 확인합니다.
    *   환경변수 `ACCOUNT_USERNAME`과 `ACCOUNT_PASSWORD`에서 계정 정보를 읽습니다.

*   **`attendance_module.py`** (121줄): 출석체크 페이지로 이동하여 버튼을 클릭합니다.
    *   이미 출석 완료된 경우에도 정상 처리합니다.
    *   완료 후 자동으로 포인트 상태를 확인합니다.

*   **`quiz_module_new.py`** (757줄): 오늘의 퀴즈를 자동으로 풀어줍니다.
    *   **4단계 프로세스**: 퀴즈 페이지 찾기 → 퀴즈 요소 클릭 → 블로그 검색으로 정답 획득 → 퀴즈 풀기
    *   여러 페이지(의약품, 기구 등)에서 퀴즈를 탐색합니다.
    *   `BlogSearchModule`과 연동하여 네이버 블로그에서 정답을 자동 검색합니다.
    *   주말 퀴즈 부재 상황도 처리합니다.

*   **`seminar_module.py`** (1420줄): 라이브 세미나를 관리합니다.
    *   세미나 정보 수집 (JavaScript 일괄 처리 최적화, 실패 시 기존 방식 폴백)
    *   세미나 현황 창 표시 (별도 Treeview 윈도우, 체크박스 지원)
    *   **일괄 신청/취소**: 체크된 세미나들을 한 번에 신청하거나 취소합니다.
    *   **더블클릭 액션**: 세미나 상세 페이지 이동, 자동 신청/취소/입장 처리
    *   **팝업 자동 처리**: JavaScript를 통해 확인 팝업들을 자동 클릭합니다.
    *   메인 GUI의 "오늘의 세미나" 트리뷰에도 데이터를 제공합니다.

*   **`survey_module.py`** (1088줄): 설문조사를 자동으로 참여합니다.
    *   설문 페이지 이동 → 세미나 선택 → 재입장 → 팝업 처리 → 설문 자동 입력 → 제출
    *   `SurveyProblemManager`와 연동하여 저장된 정답을 우선 사용합니다.
    *   저장된 정답이 없는 문제는 첫 번째 보기를 자동 선택합니다.
    *   **문제 정규화**: `[퀴즈]` 태그, 특수문자 등을 제거하여 매칭률을 높입니다.
    *   필수 항목 검증 및 미입력 항목 재시도 기능을 포함합니다.

*   **`survey_problem.py`** (593줄): 설문 퀴즈 문제와 정답을 관리합니다.
    *   **`SurveyProblemManager` 클래스**: JSON 파일 기반 CRUD (추가/수정/삭제/조회)
        *   `get_answer()`: 부분 문자열 매칭으로 정답을 검색합니다.
        *   카테고리별 관리를 지원합니다.
    *   **`open_survey_problem_manager()` 함수**: GUI 관리 창 (Treeview 목록 + 입력 폼)

*   **`points_check_module.py`** (216줄): 포인트 상태와 활동 내역을 확인합니다.
    *   메인 페이지에서 사용자 이름 수집
    *   포인트 페이지에서 포인트 + 출석/퀴즈 참여 상태 일괄 수집
    *   GUI 대시보드(사용자 정보 패널)를 직접 업데이트합니다.

*   **`blog_search_module.py`** (415줄): 네이버 블로그에서 퀴즈 정답을 검색합니다.
    *   날짜 기반 검색 URL 생성 (`닥터빌 + 월일 + 퀴즈`)
    *   새 탭에서 검색 → 첫 번째 게시글 클릭 → 정답 패턴 추출
    *   작업 완료 후 탭을 정리하고 원래 탭으로 복귀합니다.

### 4. 설치 및 업데이트

*   **`install.ps1`** (91줄): PowerShell 기반 설치 스크립트
    *   Python 설치 여부 확인 → 미설치 시 자동 다운로드/설치
    *   `requirements.txt` 기반 패키지 설치
    *   계정 정보 입력 → `account.bat` 파일 자동 생성
    *   비밀번호는 `SecureString`으로 입력받습니다.

*   **`update_program.py`** (359줄): GitHub 기반 자동 업데이트
    *   **`UpdateGUI` 클래스**: 업데이트 확인 팝업 + 진행 상태 표시
    *   **`DoctorBillUpdater` 클래스**: 
        *   백업 → GitHub ZIP 다운로드 → 압축 해제 → 파일 교체 → 정리
        *   개인 파일 보존: `.bat`, `.exe`, `.ini`, `.log`, `.json` 파일은 덮어쓰지 않습니다.
        *   실패 시 자동 백업 복원

### 5. 설정 및 데이터 파일

*   **`settings.json`**: 사용자 설정
    *   `browser_headless`: 브라우저 백그라운드 실행 여부
    *   `auto_attendance`: 로그인 후 자동 출석체크
    *   `auto_quiz`: 로그인 후 자동 퀴즈풀기
    *   `auto_seminar_check`: 로그인 후 자동 세미나 확인
    *   `auto_survey`: 로그인 후 자동 설문참여
    *   `auto_seminar_join`: 로그인 후 세미나 자동 신청

*   **`survey_quizzes.json`**: 설문 퀴즈 문제/정답 데이터 (카테고리 포함)

*   **`requirements.txt`**: 의존성 패키지
    *   `selenium` (웹 자동화), `webdriver-manager` (드라이버 관리)
    *   `requests` (HTTP 요청), `beautifulsoup4` (HTML 파싱)
    *   `openai`, `anthropic` (AI API - 퀴즈 정답 검색용)
    *   `PyPDF2`, `PyMuPDF` (PDF 처리)
    *   `Pillow` (이미지 처리)

### 6. 배치 파일 (Batch Files)

*   **`설치하기.bat`**: `install.ps1`을 실행하는 래퍼 스크립트
*   **`업데이트.bat`**: `update_program.py`를 실행하는 래퍼 스크립트
*   **`account.bat`** (설치 시 자동 생성, gitignore 대상): 프로그램 실행 파일
    *   `ACCOUNT_USERNAME`, `ACCOUNT_PASSWORD` 환경변수를 설정하고 `main_GUI.pyw`를 최소화 상태로 실행합니다.
    *   다중 계정이 필요한 경우 `계정1_닥터빌.bat`, `계정2_닥터빌.bat` 등 별도 배치 파일을 수동으로 만들어 사용할 수 있습니다.

---

## 🔄 주요 프로세스 흐름 (Workflows)

### 1. 프로그램 시작 및 초기화
1.  **실행**: 사용자가 `account.bat` 실행 → `main_GUI.pyw` 실행.
2.  **초기화**: `DoctorBillAutomation` 클래스가 생성되며 설정(`settings.json`)을 로드.
3.  **GUI 구성**: 메인 창(버튼, 로그 영역, 사용자 정보 패널, 오늘의 세미나 트리뷰)을 그립니다.
4.  **로그인**: 프로그램 시작 직후 `auto_login()` 메서드 호출 → `TaskManager`에 로그인 작업 요청.
5.  **브라우저 실행**: `TaskManager`가 `WebAutomation`을 통해 크롬 브라우저 실행 (headless 설정 반영).
6.  **포인트 확인**: 로그인 성공 후 `PointsCheckModule`이 사용자 정보와 포인트를 수집하여 GUI에 표시.
7.  **자동 작업 실행**: 설정에 따라 세미나 확인 → 설문참여 → 출석체크 → 퀴즈풀기 순서로 자동 실행.

### 2. 작업 실행 (예: 출석체크 버튼 클릭)
1.  **요청**: 사용자가 [✅ 출석체크] 버튼 클릭.
2.  **전달**: `main_GUI.attendance_check()` → `TaskManager.execute_attendance()`.
3.  **설정 기반 실행**: `TaskManager.execute_module_by_config('attendance', ...)` 호출.
4.  **로그인 확인**: `ModuleFactory.MODULES_REQUIRE_LOGIN`을 참조하여 로그인 상태를 확인.
5.  **모듈 생성**: `ModuleFactory.create_module_class('attendance')` → `AttendanceModule` 클래스 반환.
6.  **스레드 실행**: 별도 스레드에서 `execute_module_safely()` 실행 (GUI 프리징 방지).
7.  **작업 수행**: `AttendanceModule.execute()` → 브라우저 제어하여 출석 완료.
8.  **포인트 확인**: `check_points_after_activity()` → GUI 대시보드 자동 업데이트.
9.  **결과 보고**: 작업 결과(성공/실패)와 로그를 GUI 콜백을 통해 메인 화면에 전달.

### 3. 업데이트 시스템
1.  `업데이트.bat` 실행 → `update_program.py` 실행.
2.  `UpdateGUI`가 업데이트 확인 팝업을 표시합니다.
3.  `DoctorBillUpdater`가 현재 파일을 백업합니다.
4.  GitHub에서 최신 ZIP 다운로드 → 압축 해제.
5.  개인 파일(`.bat`, `.exe` 등)은 보존하면서 나머지 파일을 교체합니다.
6.  실패 시 백업에서 자동 복원합니다.

---

## 🏛️ 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────┐
│                    main_GUI.pyw                      │
│  ┌────────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ ToolTip    │  │ Settings │  │ DoctorBill      │  │
│  │ (툴팁)     │  │ (설정)   │  │ Automation      │  │
│  └────────────┘  └──────────┘  │ (메인 GUI)      │  │
│                                └────────┬────────┘  │
└─────────────────────────────────────────┼───────────┘
                                          │
                            ┌─────────────▼──────────────┐
                            │    main_task_manager.py      │
                            │  ┌──────────────────────┐   │
                            │  │ TaskManagerState      │   │
                            │  │ ModuleFactory         │   │
                            │  │ TaskManager           │   │
                            │  └──────────┬───────────┘   │
                            └─────────────┼───────────────┘
                       ┌──────────────────┼──────────────────┐
                       │                  │                  │
              ┌────────▼────────┐ ┌───────▼───────┐ ┌───────▼───────┐
              │ web_automation  │ │ base_module   │ │ Feature       │
              │ .py             │ │ .py           │ │ Modules       │
              │ (Selenium)      │ │ (공통 기능)    │ │ (login,       │
              └─────────────────┘ └───────────────┘ │  attendance,  │
                                                    │  quiz, survey,│
                                                    │  seminar,     │
                                                    │  points_check,│
                                                    │  blog_search) │
                                                    └───────────────┘
```
