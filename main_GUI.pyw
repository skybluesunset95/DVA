# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import locale
import logging
import json
import os
from datetime import datetime
from main_task_manager import TaskManager
from modules.base_module import (
    STATUS_ATTENDANCE_COMPLETE, 
    STATUS_ATTENDANCE_INCOMPLETE,
    STATUS_QUIZ_COMPLETE, 
    STATUS_QUIZ_INCOMPLETE,
    STATUS_KEY_ATTENDANCE, 
    STATUS_KEY_QUIZ
)
from modules.survey_problem import open_survey_problem_manager


class DoctorBillAutomation:
    def __init__(self, root):
        self.root = root
        self.root.title("닥터빌 자동화 프로그램")
        self.root.geometry("1000x800")  # 창 크기 확대
        self.root.minsize(800, 600)  # 최소 창 크기 설정
        self.root.configure(bg='#f0f0f0')
        
        # 설정 파일 경로
        self.settings_file = "settings.json"
        
        # 기본 설정값 정의
        self.default_settings = {
            'auto_attendance': True,             # 자동 출석체크
            'auto_quiz': True,                   # 자동 문제풀기
            'auto_seminar_check': True,          # 자동 라이브세미나 현황 열기
            'auto_survey': True                  # 자동 설문참여
        }
        
        # 설정 로드
        self.settings = self.load_settings()
        
        # TaskManager 초기화
        self.task_manager = TaskManager()
        
        # GUI 구성
        self.setup_gui()
        
        # 로깅 설정
        self.setup_logging()
        
        # 모듈 초기화
        self.initialize_modules()
        
        # 프로그램 시작 시 자동 로그인 실행
        self.root.after(200, self.auto_login)
    
    def setup_gui(self):
        """GUI 구성"""
        # root에 가중치 설정
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # 메인 프레임
        self.main_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        
        # main_frame에 가중치 설정
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)  # content_frame이 확장
        
        # 제목과 설정 버튼을 담을 프레임
        self.title_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        self.title_frame.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        
        # 제목을 title_frame에 배치
        self.title_label = tk.Label(
            self.title_frame,
            text="닥터빌 자동화 프로그램",
            font=("맑은 고딕", 24, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        self.title_label.pack(side='left')
        
        # 설정 버튼 (제목 우측에 작게)
        self.settings_button = tk.Button(
            self.title_frame,
            text="⚙️",
            font=("맑은 고딕", 12),
            bg='#95a5a6',
            fg='white',
            activebackground='#7f8c8d',
            activeforeground='white',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            width=3,
            height=1,
            command=self.open_settings
        )
        self.settings_button.pack(side='right', padx=(10, 0))
        
        
        # 사용자 정보 대시보드 패널
        self.info_panel = tk.Frame(self.main_frame, bg='#ffffff', relief='solid', borderwidth=1)
        self.info_panel.grid(row=2, column=0, sticky='ew', pady=(0, 20), padx=10)
        
        # 정보 패널 제목
        self.info_title = tk.Label(
            self.info_panel,
            text="📊 사용자 정보 대시보드",
            font=("맑은 고딕", 12, "bold"),
            bg='#ffffff',
            fg='#2c3e50'
        )
        self.info_title.pack(pady=(10, 5))
        
        # 사용자 정보 표시 영역 (직접 관리)
        self.user_info_frame = None
        
        # 상태 표시
        self.status_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        self.status_frame.grid(row=3, column=0, sticky='ew', pady=(0, 20))
        
        self.status_label = tk.Label(
            self.status_frame,
            text="상태: 대기 중",
            font=("맑은 고딕", 12),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.status_label.pack()
        
        # 좌우 분할 프레임
        self.content_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        self.content_frame.grid(row=4, column=0, sticky='nsew')
        
        # content_frame에 가중치 설정
        self.content_frame.grid_columnconfigure(0, weight=0)  # 왼쪽 프레임 (고정 크기)
        self.content_frame.grid_columnconfigure(1, weight=1)  # 오른쪽 프레임 (확장)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # 왼쪽 프레임 (버튼들)
        self.left_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        self.left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 20))
        
        # 오른쪽 프레임 (로그 및 정보)
        self.right_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        self.right_frame.grid(row=0, column=1, sticky='nsew')
        
        # 오른쪽 프레임을 pack으로 변경하여 더 정확한 비율 제어
        # 오른쪽 상단 프레임 (작업로그)
        self.right_top_frame = tk.Frame(self.right_frame, bg='#f0f0f0')
        self.right_top_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        # 오늘의 세미나와 작업로그를 절반씩 차지하도록 설정
        self.right_top_frame.pack_propagate(False)
        
        # 오른쪽 하단 프레임 (오늘의 세미나)
        self.right_bottom_frame = tk.Frame(self.right_frame, bg='#f0f0f0')
        self.right_bottom_frame.pack(fill='both', expand=True, pady=(5, 0))
        
        # 오늘의 세미나도 절반씩 차지하도록 설정
        self.right_bottom_frame.pack_propagate(False)
        
        # 버튼 스타일
        button_style = {
            'font': ("맑은 고딕", 12, "bold"),
            'borderwidth': 0,
            'relief': 'flat',
            'cursor': 'hand2'
        }
        
        # 왼쪽 프레임을 pack 방식으로 변경하여 버튼들이 균등하게 배치되도록 함
        
        # 출석체크 버튼
        self.attendance_button = tk.Button(
            self.left_frame,
            text="✅ 출석체크",
            bg='#27ae60',
            fg='white',
            activebackground='#229954',
            activeforeground='white',
            command=self.attendance_check,
            **button_style
        )
        self.attendance_button.pack(fill='x', padx=10, pady=(10, 8))
        
        # 퀴즈풀기 버튼
        self.quiz_button = tk.Button(
            self.left_frame,
            text="🧠 퀴즈풀기",
            bg='#e74c3c',
            fg='white',
            activebackground='#c0392b',
            activeforeground='white',
            command=self.solve_quiz,
            **button_style
        )
        self.quiz_button.pack(fill='x', padx=10, pady=8)
        
        # 라이브세미나 버튼
        self.seminar_button = tk.Button(
            self.left_frame,
            text="📺 라이브세미나",
            bg='#9b59b6',
            fg='white',
            activebackground='#8e44ad',
            activeforeground='white',
            command=self.check_seminar,
            **button_style
        )
        self.seminar_button.pack(fill='x', padx=10, pady=8)
        
        # 설문참여 버튼
        self.survey_button = tk.Button(
            self.left_frame,
            text="📋 설문참여",
            bg='#f39c12',
            fg='white',
            activebackground='#e67e22',
            activeforeground='white',
            command=self.open_survey,
            **button_style
        )
        self.survey_button.pack(fill='x', padx=10, pady=8)
        
        # 설문문제 버튼
        self.survey_problem_button = tk.Button(
            self.left_frame,
            text="🎯 설문문제",
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            activeforeground='white',
            command=self.open_survey_problem,
            **button_style
        )
        self.survey_problem_button.pack(fill='x', padx=10, pady=8)
        
        # 프로그램 종료 버튼
        self.exit_button = tk.Button(
            self.left_frame,
            text="🚪 프로그램 종료",
            bg='#e67e22',
            fg='white',
            activebackground='#d35400',
            activeforeground='white',
            command=self.exit_program,
            **button_style
        )
        self.exit_button.pack(fill='x', padx=10, pady=(8, 10))
        
        # 작업 로그 섹션 (상단)
        self.setup_work_log_section()
        
        # 오늘의 세미나 섹션 (하단)
        self.setup_today_seminar_section()
        
        # 초기 로그
        self.log_message("프로그램이 시작되었습니다.")
        
        # 버튼 호버 효과
        self.setup_hover_effects()
        
        # 프로그램 종료 시 정리 작업
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_settings(self):
        """설정 파일에서 설정값을 로드합니다."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # 기본 설정과 병합 (새로운 설정이 추가되어도 안전)
                merged_settings = self.default_settings.copy()
                merged_settings.update(settings)
                return merged_settings
            else:
                # 설정 파일이 없으면 기본값으로 생성
                self.save_settings(self.default_settings)
                return self.default_settings.copy()
        except Exception as e:
            self.log_error(f"설정 로드 실패: {str(e)}")
            return self.default_settings.copy()
    
    def save_settings(self, settings=None):
        """설정값을 파일에 저장합니다."""
        try:
            if settings is None:
                settings = self.settings
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.log_success("설정이 저장되었습니다.")
        except Exception as e:
            self.log_error(f"설정 저장 실패: {str(e)}")
    
    def get_setting(self, key):
        """특정 설정값을 가져옵니다."""
        return self.settings.get(key, self.default_settings.get(key, False))
    
    def set_setting(self, key, value):
        """특정 설정값을 설정합니다."""
        self.settings[key] = value
        self.save_settings()
    
    def setup_logging(self):
        """로깅 설정 - 모듈들의 로그를 GUI에 표시"""
        # GUI 로그 핸들러 클래스
        class GUILogHandler(logging.Handler):
            def __init__(self, gui_instance):
                super().__init__()
                self.gui = gui_instance
            
            def emit(self, record):
                try:
                    msg = self.format(record)
                    # GUI 스레드에서 안전하게 로그 추가
                    self.gui.root.after(0, lambda: self.gui.log_message(msg))
                except Exception as e:
                    print(f"GUI 로그 핸들러 오류: {e}")
        
        # 로거 설정
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # GUI 핸들러 추가
        gui_handler = GUILogHandler(self)
        gui_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(formatter)
        
        logger.addHandler(gui_handler)
    
    def initialize_modules(self):
        """사용자 정보 표시 영역 초기화"""
        try:
            # 사용자 정보 프레임 생성
            self.user_info_frame = tk.Frame(self.info_panel, bg='#ffffff')
            self.user_info_frame.pack(fill='x', padx=20, pady=10)
            
            # 사용자 정보 표시 요소들 생성
            self.setup_user_info_display()
            
        except Exception as e:
            self.handle_error('gui', f"사용자 정보 표시 영역 초기화 실패: {str(e)}")
    
    def setup_user_info_display(self):
        """사용자 정보 표시 섹션을 설정합니다."""
        try:
            # grid 레이아웃을 위한 설정
            self.user_info_frame.grid_columnconfigure(0, weight=1)
            self.user_info_frame.grid_columnconfigure(1, weight=1)
            self.user_info_frame.grid_columnconfigure(2, weight=1)
            self.user_info_frame.grid_columnconfigure(3, weight=1)
            
            # 사용자 이름 (더 큰 글자, 중앙 정렬)
            self.user_name_label = tk.Label(
                self.user_info_frame,
                text="사용자: 로그인 필요",
                font=("맑은 고딕", 14, "bold"),
                bg='#ffffff',
                fg='#7f8c8d'
            )
            self.user_name_label.grid(row=0, column=0, columnspan=4, pady=(10, 15), sticky='ew')
            
            # 포인트 정보 (더 큰 글자)
            self.points_label = tk.Label(
                self.user_info_frame,
                text="포인트: 0",
                font=("맑은 고딕", 12),
                bg='#ffffff',
                fg='#2c3e50'
            )
            self.points_label.grid(row=1, column=0, pady=(0, 10), padx=(0, 20), sticky='ew')
            
            # 출석체크 상태 (더 큰 글자, 간결한 텍스트)
            self.attendance_label = tk.Label(
                self.user_info_frame,
                text="출석체크: 미완료",
                font=("맑은 고딕", 12),
                bg='#ffffff',
                fg='#e74c3c'
            )
            self.attendance_label.grid(row=1, column=1, pady=(0, 10), padx=(20, 20), sticky='ew')
            
            # 퀴즈 참여 상태 (더 큰 글자, "퀴즈참여"로 변경)
            self.quiz_label = tk.Label(
                self.user_info_frame,
                text="퀴즈참여: 미완료",
                font=("맑은 고딕", 12),
                bg='#ffffff',
                fg='#e74c3c'
            )
            self.quiz_label.grid(row=1, column=2, pady=(0, 10), padx=(20, 0), sticky='ew')
            
            self.log_success("사용자 정보 표시 섹션 설정 완료")
            
        except Exception as e:
            self.handle_error('gui', f"사용자 정보 표시 섹션 설정 실패: {str(e)}")
    
    def setup_work_log_section(self):
        """작업 로그 섹션을 설정합니다."""
        # 로그 제목
        self.log_title = tk.Label(
            self.right_top_frame,
            text="📝 작업 로그",
            font=("맑은 고딕", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        self.log_title.pack(anchor='w', pady=(0, 10))
        
        # 로그 텍스트 영역
        self.log_text = tk.Text(
            self.right_top_frame,
            height=15,
            width=60,
            font=("맑은 고딕", 10),
            bg='#ffffff',
            fg='#2c3e50',
            relief='solid',
            borderwidth=1,
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True)
        
        # 스크롤바
        log_scrollbar = tk.Scrollbar(self.right_top_frame, orient='vertical', command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # 로그 지우기 버튼
        clear_log_button = tk.Button(
            self.right_top_frame,
            text="🗑️ 로그 지우기",
            font=("맑은 고딕", 10),
            bg='#95a5a6',
            fg='white',
            activebackground='#7f8c8d',
            activeforeground='white',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            command=self.clear_log
        )
        clear_log_button.pack(pady=(10, 0))
    
    def setup_today_seminar_section(self):
        """오늘의 세미나 섹션을 설정합니다."""
        # 세미나 제목
        self.seminar_title = tk.Label(
            self.right_bottom_frame,
            text="📺 오늘의 세미나",
            font=("맑은 고딕", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        self.seminar_title.pack(anchor='w', pady=(0, 10))
        
        # 세미나 정보 표시 영역
        self.seminar_info_frame = tk.Frame(self.right_bottom_frame, bg='#ffffff', relief='solid', borderwidth=1)
        self.seminar_info_frame.pack(fill='both', expand=True, padx=10)
        
        
        # 트리뷰 생성 (체크박스 컬럼 제외하고 간소화)
        columns = ('날짜', '요일', '시간', '강의명', '강의자', '신청인원', '신청상태')
        self.seminar_tree = ttk.Treeview(self.seminar_info_frame, columns=columns, show='headings', height=8)
        
        # 컬럼 설정
        self.seminar_tree.heading('날짜', text='날짜')
        self.seminar_tree.heading('요일', text='요일')
        self.seminar_tree.heading('시간', text='시간')
        self.seminar_tree.heading('강의명', text='강의명')
        self.seminar_tree.heading('강의자', text='강의자')
        self.seminar_tree.heading('신청인원', text='신청인원')
        self.seminar_tree.heading('신청상태', text='신청상태')
        
        # 컬럼 너비 설정 (메인 화면에 맞게 조정)
        self.seminar_tree.column('날짜', width=70, anchor='center')
        self.seminar_tree.column('요일', width=50, anchor='center')
        self.seminar_tree.column('시간', width=80, anchor='center')
        self.seminar_tree.column('강의명', width=200, anchor='w')
        self.seminar_tree.column('강의자', width=120, anchor='w')
        self.seminar_tree.column('신청인원', width=70, anchor='center')
        self.seminar_tree.column('신청상태', width=80, anchor='center')
        
        # 스크롤바 추가
        seminar_scrollbar = ttk.Scrollbar(self.seminar_info_frame, orient=tk.VERTICAL, command=self.seminar_tree.yview)
        self.seminar_tree.configure(yscrollcommand=seminar_scrollbar.set)
        
        # 트리뷰와 스크롤바 배치
        self.seminar_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        seminar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # 초기 메시지 표시
        self.seminar_tree.insert('', 'end', values=("", "", "", "자동 로그인 후 세미나 정보가 자동으로 수집됩니다", "", "", ""))
        
        # 상태별 색상 설정
        self.seminar_tree.tag_configure('신청가능', background='#d5f4e6', foreground='#2e7d32')  # 연한 초록
        self.seminar_tree.tag_configure('신청완료', background='#fef9e7', foreground='#f39c12')  # 연한 노랑
        self.seminar_tree.tag_configure('신청마감', background='#fadbd8', foreground='#e74c3c')  # 연한 빨강
        self.seminar_tree.tag_configure('입장하기', background='#d6eaf8', foreground='#3498db')  # 연한 파랑
        self.seminar_tree.tag_configure('대기중', background='#f8f9fa', foreground='#6c757d')    # 연한 회색
        self.seminar_tree.tag_configure('기타', background='#f4f6f6', foreground='#34495e')      # 기본색
        
        # 더블클릭 이벤트
        self.seminar_tree.bind('<Double-1>', self.on_seminar_double_click)
        
    
    def setup_hover_effects(self):
        """버튼 호버 효과를 설정합니다."""
        # 호버 효과를 위한 색상 매핑
        hover_colors = {
            '✅ 출석체크': '#229954',
            '🧠 퀴즈풀기': '#c0392b',
            '📺 라이브세미나': '#8e44ad',
            '📋 설문참여': '#e67e22',
            '🚪 프로그램 종료': '#d35400'
        }
        
        # 각 버튼에 호버 효과 적용
        for button_text, hover_color in hover_colors.items():
            for child in self.left_frame.winfo_children():
                if isinstance(child, tk.Button) and child.cget('text') == button_text:
                    child.bind('<Enter>', lambda e, btn=child, color=hover_color: btn.config(bg=color))
                    child.bind('<Leave>', lambda e, btn=child, text=button_text: self.restore_button_color(btn, text))
    
    def restore_button_color(self, button, button_text):
        """버튼의 원래 색상을 복원합니다."""
        original_colors = {
            '✅ 출석체크': '#27ae60',
            '🧠 퀴즈풀기': '#e74c3c',
            '📺 라이브세미나': '#9b59b6',
            '📋 설문참여': '#f39c12',
            '🚪 프로그램 종료': '#e67e22'
        }
        button.config(bg=original_colors.get(button_text, '#95a5a6'))
    
    def log_message(self, message):
        """로그 메시지를 추가합니다."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            # GUI 스레드에서 안전하게 로그 추가
            self.root.after(0, lambda: self._add_log_entry(log_entry))
            
        except Exception as e:
            print(f"로그 메시지 추가 실패: {e}")
    
    def log_info(self, message):
        """정보 로그를 기록합니다."""
        self.log_message(f"ℹ {message}")
    
    def log_error(self, message):
        """에러 로그를 기록합니다."""
        self.log_message(f"❌ {message}")
    
    def log_success(self, message):
        """성공 로그를 기록합니다."""
        self.log_message(f"✅ {message}")
    
    def log_warning(self, message):
        """경고 로그를 기록합니다."""
        self.log_message(f"⚠ {message}")
    
    def handle_error(self, error_type, error_message, recovery_suggestion=None):
        """일관된 에러 처리 - base_module.py와 동일한 방식"""
        try:
            # 에러 타입별 사용자 친화적 메시지
            user_friendly_messages = {
                'network': f"네트워크 연결 문제: {error_message}",
                'webpage': f"웹페이지 로딩 문제: {error_message}",
                'element': f"페이지 요소를 찾을 수 없음: {error_message}",
                'timeout': f"시간 초과: {error_message}",
                'login': f"로그인 문제: {error_message}",
                'data': f"데이터 처리 문제: {error_message}",
                'gui': f"GUI 처리 문제: {error_message}",
                'unknown': f"알 수 없는 오류: {error_message}"
            }
            
            # 에러 메시지 생성
            error_msg = user_friendly_messages.get(error_type, user_friendly_messages['unknown'])
            
            # 복구 방법 제시
            if recovery_suggestion:
                error_msg += f"\n💡 해결 방법: {recovery_suggestion}"
            else:
                # 기본 복구 방법
                default_suggestions = {
                    'network': "인터넷 연결을 확인하고 다시 시도해주세요.",
                    'webpage': "페이지를 새로고침하고 다시 시도해주세요.",
                    'element': "웹사이트가 변경되었을 수 있습니다. 관리자에게 문의하세요.",
                    'timeout': "잠시 후 다시 시도해주세요.",
                    'login': "아이디와 비밀번호를 확인하고 다시 시도해주세요.",
                    'data': "데이터를 다시 수집해보세요.",
                    'gui': "프로그램을 재시작하고 다시 시도해주세요.",
                    'unknown': "프로그램을 재시작하고 다시 시도해주세요."
                }
                error_msg += f"\n💡 해결 방법: {default_suggestions.get(error_type, default_suggestions['unknown'])}"
            
            # 로그 기록
            self.log_error(error_msg)
            
            return error_msg
            
        except Exception as e:
            # 에러 처리 중 오류 발생 시 기본 메시지
            fallback_msg = f"오류 발생: {error_message}"
            self.log_error(fallback_msg)
            return fallback_msg
    
    def _add_log_entry(self, log_entry):
        """로그 엔트리를 실제로 추가합니다."""
        try:
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            
            # 로그가 너무 많아지면 오래된 것 삭제
            if int(self.log_text.index('end-1c').split('.')[0]) > 1000:
                self.log_text.delete('1.0', '100.0')
                
        except Exception as e:
            print(f"로그 엔트리 추가 실패: {e}")
    
    def clear_log(self):
        """로그를 지웁니다."""
        try:
            self.log_text.delete('1.0', tk.END)
            self.log_message("로그가 지워졌습니다.")
        except Exception as e:
            print(f"로그 지우기 실패: {e}")
    
    def update_status(self, status):
        """상태를 업데이트합니다."""
        self.status_label.config(text=f"상태: {status}")
        self.root.update_idletasks()
    
    def update_user_info(self, user_name=None, account_type=None):
        """사용자 정보를 업데이트합니다."""
        try:
            if hasattr(self, 'user_name_label') and self.user_name_label:
                # "(기본값)" 제거하고 사용자 이름만 표시
                display_name = user_name if user_name != "사용자" else "로그인 필요"
                self.user_name_label.config(
                    text=f"사용자: {display_name}",
                    fg='#27ae60'  # 초록색으로 변경
                )
        except Exception as e:
            self.handle_error('data', f"사용자 정보 업데이트 실패: {str(e)}")
        self.root.update_idletasks()
    
    def update_display(self, display_type, value):
        """통합된 디스플레이 업데이트 메서드"""
        try:
            # 업데이트할 라벨과 설정을 정의
            display_configs = {
                'points': {
                    'label': 'points_label',
                    'prefix': '포인트: ',
                    'color': '#f39c12'  # 주황색
                },
                STATUS_KEY_ATTENDANCE: {
                    'label': 'attendance_label',
                    'prefix': '출석체크: ',
                    'color': '#e74c3c' if value == STATUS_ATTENDANCE_INCOMPLETE else '#27ae60',
                    'transform': lambda x: "미완료" if x == STATUS_ATTENDANCE_INCOMPLETE else "완료"
                },
                STATUS_KEY_QUIZ: {
                    'label': 'quiz_label',
                    'prefix': '퀴즈참여: ',
                    'color': '#e74c3c' if value == STATUS_QUIZ_INCOMPLETE else '#27ae60',
                    'transform': lambda x: "미완료" if x == STATUS_QUIZ_INCOMPLETE else "완료"
                }
            }
            
            if display_type not in display_configs:
                self.handle_error('data', f"알 수 없는 디스플레이 타입: {display_type}")
                return
            
            config = display_configs[display_type]
            label_attr = config['label']
            
            if hasattr(self, label_attr) and getattr(self, label_attr):
                label = getattr(self, label_attr)
                
                # 값 변환 (필요한 경우)
                display_value = value
                if 'transform' in config:
                    display_value = config['transform'](value)
                
                # 라벨 업데이트
                label.config(
                    text=f"{config['prefix']}{display_value}",
                    fg=config['color']
                )
                
        except Exception as e:
            self.handle_error('gui', f"{display_type} 표시 업데이트 실패: {str(e)}")
        
        self.root.update_idletasks()
    
    # 중복 메서드 제거 (PointsCheckModule에서 update_display를 직접 호출하므로 불필요)
    # def update_points_display(self, new_points):
    #     """포인트 표시를 업데이트합니다."""
    #     self.update_display('points', new_points)
    
    # def update_attendance_display(self, status):
    #     """출석체크 상태를 업데이트합니다."""
    #     self.update_display('attendance', status)
    
    # def update_quiz_display(self, status):
    #     """퀴즈 참여 상태를 업데이트합니다."""
    #     self.update_display('quiz', status)
    
    def open_settings(self):
        """설정 창을 엽니다."""
        try:
            # 기존 설정 창이 열려있으면 닫기
            if hasattr(self, 'settings_window') and self.settings_window:
                self.settings_window.destroy()
                delattr(self, 'settings_window')
            
            # 설정 창 생성
            self.settings_window = tk.Toplevel(self.root)
            self.settings_window.title("⚙️ 설정")
            self.settings_window.geometry("500x600")
            self.settings_window.configure(bg='#f0f0f0')
            self.settings_window.resizable(False, False)
            self.settings_window.transient(self.root)
            self.settings_window.grab_set()
            
            # 메인 프레임
            main_frame = tk.Frame(self.settings_window, bg='#f0f0f0')
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            # 제목
            title_label = tk.Label(
                main_frame,
                text="⚙️ 프로그램 설정",
                font=("맑은 고딕", 18, "bold"),
                bg='#f0f0f0',
                fg='#2c3e50'
            )
            title_label.pack(pady=(0, 20))
            
            # 설정 옵션들 (스크롤 없이)
            self.setup_settings_options(main_frame)
            
            # 버튼 프레임 (하단 중앙 정렬)
            button_frame = tk.Frame(main_frame, bg='#f0f0f0')
            button_frame.pack(fill='x', pady=(30, 0))
            
            # 저장 버튼
            save_button = tk.Button(
                button_frame,
                text="💾 저장",
                font=("맑은 고딕", 12, "bold"),
                bg='#27ae60',
                fg='white',
                activebackground='#229954',
                activeforeground='white',
                borderwidth=0,
                relief='flat',
                cursor='hand2',
                command=self.save_settings_from_ui
            )
            save_button.pack(side='left', padx=(0, 10))
            
            # 닫기 버튼
            close_button = tk.Button(
                button_frame,
                text="❌ 닫기",
                font=("맑은 고딕", 12, "bold"),
                bg='#e74c3c',
                fg='white',
                activebackground='#c0392b',
                activeforeground='white',
                borderwidth=0,
                relief='flat',
                cursor='hand2',
                command=self.close_settings_window
            )
            close_button.pack(side='left')
            
            # X 버튼 클릭 시 close_settings_window 함수 호출
            self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)
            
        except Exception as e:
            self.handle_error('gui', f"설정 창 열기 실패: {str(e)}")
            messagebox.showerror("오류", f"설정 창을 열 수 없습니다: {str(e)}")
    
    def setup_settings_options(self, parent):
        """설정 옵션들을 설정합니다."""
        # 설정 변수들 (체크박스 상태를 저장)
        self.setting_vars = {}
        
        
        # 자동 실행 설정 섹션
        auto_frame = tk.LabelFrame(
            parent,
            text="🤖 자동 실행 설정",
            font=("맑은 고딕", 12, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        auto_frame.pack(fill='x', pady=(0, 15))
        
        # 자동 출석체크
        self.setting_vars['auto_attendance'] = tk.BooleanVar(value=self.get_setting('auto_attendance'))
        attendance_check = tk.Checkbutton(
            auto_frame,
            text="✅ 자동 출석체크",
            variable=self.setting_vars['auto_attendance'],
            font=("맑은 고딕", 11),
            bg='#f0f0f0',
            fg='#2c3e50',
            activebackground='#f0f0f0',
            activeforeground='#2c3e50'
        )
        attendance_check.pack(anchor='w', pady=2)
        
        # 자동 문제풀기
        self.setting_vars['auto_quiz'] = tk.BooleanVar(value=self.get_setting('auto_quiz'))
        quiz_check = tk.Checkbutton(
            auto_frame,
            text="🧠 자동 문제풀기",
            variable=self.setting_vars['auto_quiz'],
            font=("맑은 고딕", 11),
            bg='#f0f0f0',
            fg='#2c3e50',
            activebackground='#f0f0f0',
            activeforeground='#2c3e50'
        )
        quiz_check.pack(anchor='w', pady=2)
        
        # 자동 라이브세미나 현황 열기
        self.setting_vars['auto_seminar_check'] = tk.BooleanVar(value=self.get_setting('auto_seminar_check'))
        seminar_check = tk.Checkbutton(
            auto_frame,
            text="📺 자동 라이브세미나 현황 열기",
            variable=self.setting_vars['auto_seminar_check'],
            font=("맑은 고딕", 11),
            bg='#f0f0f0',
            fg='#2c3e50',
            activebackground='#f0f0f0',
            activeforeground='#2c3e50'
        )
        seminar_check.pack(anchor='w', pady=2)
        
        # 자동 설문참여
        self.setting_vars['auto_survey'] = tk.BooleanVar(value=self.get_setting('auto_survey'))
        survey_check = tk.Checkbutton(
            auto_frame,
            text="📋 자동 설문참여",
            variable=self.setting_vars['auto_survey'],
            font=("맑은 고딕", 11),
            bg='#f0f0f0',
            fg='#2c3e50',
            activebackground='#f0f0f0',
            activeforeground='#2c3e50'
        )
        survey_check.pack(anchor='w', pady=2)
        
        
        # 설명 텍스트
        info_text = tk.Text(
            parent,
            height=4,
            width=50,
            font=("맑은 고딕", 10),
            bg='#ffffff',
            fg='#7f8c8d',
            relief='solid',
            borderwidth=1,
            wrap='word'
        )
        info_text.pack(fill='x', pady=(0, 10))
        info_text.insert('1.0', "💡 설정 안내:\n• 자동 실행 설정은 프로그램 시작 시에만 적용됩니다.")
        info_text.config(state='disabled')
    
    def save_settings_from_ui(self):
        """UI에서 설정값을 저장합니다."""
        try:
            # UI의 체크박스 값들을 설정에 반영
            for key, var in self.setting_vars.items():
                self.set_setting(key, var.get())
            
            self.log_success("설정이 저장되었습니다.")
            messagebox.showinfo("설정 저장", "설정이 성공적으로 저장되었습니다!")
            
        except Exception as e:
            self.handle_error('gui', f"설정 저장 실패: {str(e)}")
            messagebox.showerror("오류", f"설정 저장에 실패했습니다: {str(e)}")
    
    def close_settings_window(self):
        """설정 창을 닫습니다."""
        try:
            if hasattr(self, 'settings_window') and self.settings_window:
                self.settings_window.destroy()
                delattr(self, 'settings_window')
        except Exception as e:
            self.handle_error('gui', f"설정 창 닫기 실패: {str(e)}")
    
    def get_callbacks(self):
        """표준 GUI 콜백 함수들을 반환합니다."""
        return {
            'log_message': self.log_message,
            'log_info': self.log_info,
            'log_error': self.log_error,
            'log_success': self.log_success,
            'log_warning': self.log_warning,
            'handle_error': self.handle_error,
            'update_status': self.update_status,
            'update_user_info': self.update_user_info,
            'update_display': self.update_display,
            'safe_gui_update': self.safe_gui_update,
            'log_and_update_status': self.log_and_update_status,
            'gui_instance': self  # 항상 포함
        }
    
    def auto_login(self):
        """자동 로그인 기능"""
        # 이미 로그인 중이면 중복 실행 방지
        if self.task_manager.state.is_logging_in:
            self.log_message("이미 로그인 중입니다. 잠시 기다려주세요...")
            return
        
        self.log_message("자동 로그인을 시작합니다...")
        self.update_status("로그인 중...")
        
        # 표준 GUI 콜백 생성
        gui_callbacks = self.get_callbacks()
        
        # TaskManager를 통해 로그인 실행
        self.task_manager.execute_login(gui_callbacks)
        
        # 로그인 완료 후 세미나 정보 자동 수집을 위한 스레드 시작
        threading.Thread(target=self._auto_collect_seminar_after_login, daemon=True).start()
    
    def _auto_collect_seminar_after_login(self):
        """로그인 완료 후 설정에 따른 자동 작업 실행"""
        try:
            # 로그인 완료까지 대기 (최대 30초)
            max_wait_time = 30
            wait_interval = 0.5
            waited_time = 0
            
            while waited_time < max_wait_time:
                if not self.task_manager.state.is_logging_in:
                    # 로그인 완료됨
                    self.log_message("로그인 완료! 설정에 따른 자동 작업을 시작합니다...")
                    
                    # 설정에 따른 자동 작업 실행
                    self._execute_auto_tasks_after_login()
                    
                    break
                
                time.sleep(wait_interval)
                waited_time += wait_interval
            
            if waited_time >= max_wait_time:
                self.log_message("로그인 대기 시간 초과. 수동으로 작업을 실행해주세요.")
                
        except Exception as e:
            self.handle_error('data', f"자동 작업 실행 중 오류: {str(e)}")
    
    def _execute_auto_tasks_after_login(self):
        """로그인 후 설정에 따른 자동 작업들을 실행합니다."""
        try:
            gui_callbacks = self.get_callbacks()
            
            # 1. 세미나 정보 수집 (항상 실행)
            self.log_message("세미나 정보를 수집합니다...")
            self.update_status("세미나 정보 수집 중...")
            self._collect_seminar_info_for_main_gui()
            
            # 2. 자동 출석체크
            if self.get_setting('auto_attendance'):
                self.log_message("자동 출석체크를 시작합니다...")
                self.update_status("자동 출석체크 중...")
                self.task_manager.execute_attendance(gui_callbacks)
                time.sleep(2)  # 작업 간 대기
            
            # 3. 자동 문제풀기
            if self.get_setting('auto_quiz'):
                self.log_message("자동 문제풀기를 시작합니다...")
                self.update_status("자동 문제풀기 중...")
                self.task_manager.execute_quiz(gui_callbacks)
                time.sleep(2)  # 작업 간 대기
            
            # 4. 자동 라이브세미나 현황 열기
            if self.get_setting('auto_seminar_check'):
                self.log_message("자동 라이브세미나 현황을 확인합니다...")
                self.update_status("라이브세미나 현황 확인 중...")
                self.task_manager.execute_seminar(gui_callbacks)
                time.sleep(2)  # 작업 간 대기
            
            # 5. 자동 설문참여
            if self.get_setting('auto_survey'):
                self.log_message("자동 설문참여를 시작합니다...")
                self.update_status("자동 설문참여 중...")
                self.task_manager.execute_survey(gui_callbacks)
                time.sleep(2)  # 작업 간 대기
            
            
            self.log_message("모든 자동 작업이 완료되었습니다!")
            self.update_status("자동 작업 완료")
            
        except Exception as e:
            self.handle_error('data', f"자동 작업 실행 중 오류: {str(e)}")
    
    
    def _collect_seminar_info_for_main_gui(self):
        """메인 GUI용 세미나 정보 수집"""
        try:
            # 세미나 모듈을 직접 사용하여 정보 수집
            from modules.seminar_module import SeminarModule
            
            if not self.task_manager.state.web_automation:
                self.log_message("웹드라이버가 초기화되지 않았습니다.")
                return
            
            # 세미나 모듈 생성
            seminar_module = SeminarModule(self.task_manager.state.web_automation, self.log_message)
            
            # 세미나 정보만 수집 (GUI 창 표시 없음)
            seminars = seminar_module.collect_seminar_info_only()
            
            if seminars:
                self.log_message(f"세미나 정보 {len(seminars)}개 수집 완료!")
                # 메인 GUI 트리뷰에 표시
                self.update_today_seminars(seminars)
            else:
                self.log_message("수집할 세미나 정보가 없습니다.")
                # 빈 상태로 업데이트
                self.update_today_seminars([])
                
        except Exception as e:
            self.handle_error('data', f"세미나 정보 수집 실패: {str(e)}")
    
    def attendance_check(self):
        """출석체크 기능"""
        if self.task_manager.state.is_logging_in:
            self.log_message("로그인 중입니다. 잠시 기다려주세요...")
            return
        
        self.log_message("출석체크 페이지로 이동합니다...")
        self.update_status("출석체크 페이지 이동 중...")
        
        # 표준 GUI 콜백 생성
        gui_callbacks = self.get_callbacks()
        
        # TaskManager를 통해 출석체크 실행
        self.task_manager.execute_attendance(gui_callbacks)
    
    def solve_quiz(self):
        """퀴즈 풀기 기능"""
        if self.task_manager.state.is_logging_in:
            self.log_message("로그인 중입니다. 잠시 기다려주세요...")
            return
        
        self.log_message("퀴즈풀기 페이지로 이동합니다...")
        self.update_status("퀴즈풀기 페이지 이동 중...")
        
        # 표준 GUI 콜백 생성
        gui_callbacks = self.get_callbacks()
        
        # TaskManager를 통해 퀴즈 실행
        self.task_manager.execute_quiz(gui_callbacks)
    
    def open_survey(self):
        """설문참여 페이지 열기"""
        try:
            if not self.task_manager.state.web_automation or not self.task_manager.state.web_automation.driver:
                self.log_message("웹드라이버가 초기화되지 않았습니다. 먼저 로그인해주세요.")
                return
            
            self.log_message("설문참여 페이지로 이동합니다...")
            self.update_status("설문참여 페이지 이동 중...")
            
            # 표준 GUI 콜백 생성
            gui_callbacks = self.get_callbacks()
            
            # TaskManager를 통해 설문참여 실행
            self.task_manager.execute_survey(gui_callbacks)
            
        except Exception as e:
            self.handle_error('webpage', f"설문참여 페이지 이동 중 오류: {str(e)}")
            self.update_status("설문참여 페이지 오류")
    
    def open_survey_problem(self):
        """설문 문제 관리 창 열기"""
        try:
            self.log_message("설문 문제 관리 창을 열고 있습니다...")
            open_survey_problem_manager(self.root, self.log_message)
            self.log_message("✅ 설문 문제 관리 창이 열렸습니다.")
        except Exception as e:
            self.handle_error('gui', f"설문 문제 관리 창 오류: {str(e)}")
    
    def check_seminar(self):
        """라이브세미나 확인 기능"""
        if self.task_manager.state.is_logging_in:
            self.log_message("로그인 중입니다. 잠시 기다려주세요...")
            return
        
        self.log_message("라이브세미나 정보를 확인합니다...")
        self.update_status("라이브세미나 확인 중...")
        
        # 표준 GUI 콜백 생성
        gui_callbacks = self.get_callbacks()
        
        # TaskManager를 통해 세미나 확인 실행 (기존 창 표시 기능)
        self.task_manager.execute_seminar(gui_callbacks)
        
        # 추가로 메인 GUI 트리뷰도 업데이트
        threading.Thread(target=self._update_main_gui_seminar_after_check, daemon=True).start()
    
    def _update_main_gui_seminar_after_check(self):
        """라이브세미나 확인 후 메인 GUI 트리뷰 업데이트"""
        try:
            # 세미나 모듈을 직접 사용하여 정보 수집
            from modules.seminar_module import SeminarModule
            
            if not self.task_manager.state.web_automation:
                self.log_message("웹드라이버가 초기화되지 않았습니다.")
                return
            
            # 세미나 모듈 생성
            seminar_module = SeminarModule(self.task_manager.state.web_automation, self.log_message)
            
            # 세미나 정보만 수집 (GUI 창 표시 없음)
            seminars = seminar_module.collect_seminar_info_only()
            
            if seminars:
                self.log_message(f"메인 화면 세미나 정보 {len(seminars)}개 업데이트 완료!")
                # 메인 GUI 트리뷰에 표시
                self.update_today_seminars(seminars)
            else:
                self.log_message("수집할 세미나 정보가 없습니다.")
                # 빈 상태로 업데이트
                self.update_today_seminars([])
                
        except Exception as e:
            self.handle_error('data', f"메인 GUI 세미나 정보 업데이트 실패: {str(e)}")
    
    def exit_program(self):
        """프로그램 종료"""
        self.log_message("프로그램을 종료합니다...")
        self.update_status("종료 중...")
        
        # GUI 즉시 종료하고 정리는 백그라운드에서 처리
        threading.Thread(target=self.cleanup, daemon=True).start()
        self.root.destroy()
    
    def on_closing(self):
        """프로그램 종료 시 정리 작업"""
        try:
            # TaskManager를 통해 웹드라이버 정리
            self.task_manager.cleanup()
            self.log_message("프로그램을 종료합니다.")
        except Exception as e:
            print(f"프로그램 종료 중 오류: {e}")
        finally:
            self.root.destroy()
    
    def cleanup(self):
        """백그라운드에서 정리 작업 수행"""
        try:
            # TaskManager를 통해 정리
            self.task_manager.cleanup()
        except Exception as e:
            # 백그라운드 정리 중 오류는 무시 (GUI는 이미 종료됨)
            pass

    def safe_gui_update(self, func, *args, **kwargs):
        """GUI 스레드에서 안전하게 함수를 실행합니다."""
        try:
            self.root.after(0, lambda: func(*args, **kwargs))
        except Exception as e:
            print(f"GUI 업데이트 오류: {e}")
    
    def log_and_update_status(self, log_message, status_message):
        """로그와 상태를 동시에 안전하게 업데이트합니다."""
        self.safe_gui_update(self.log_message, log_message)
        self.safe_gui_update(self.update_status, status_message)
    
    
    def update_today_seminars(self, seminars_data):
        """오늘의 세미나 정보를 트리뷰에 표시합니다."""
        try:
            from datetime import datetime
            
            # 기존 데이터 삭제
            for item in self.seminar_tree.get_children():
                self.seminar_tree.delete(item)
            
            if not seminars_data:
                # 세미나가 없는 경우 메시지 표시
                self.seminar_tree.insert('', 'end', values=("", "", "", "오늘 예정된 세미나가 없습니다", "", "", ""))
            else:
                # 오늘 날짜만 필터링 (세미나 날짜 형식에 맞춤)
                today = datetime.now()
                today_md = f"{today.month}/{today.day}"  # M/D 형식으로 변환
                    
                # 디버깅: 세미나 데이터의 날짜 형식 확인
                self.log_message(f"오늘 날짜 (M/D 형식): {today_md}")
                if seminars_data:
                    sample_dates = [s.get('date', '') for s in seminars_data[:3]]
                    self.log_message(f"세미나 날짜 샘플: {sample_dates}")
                
                today_seminars = [s for s in seminars_data if s.get('date', '') == today_md]
                
                if today_seminars:
                    self.log_message(f"오늘 세미나 {len(today_seminars)}개 발견")
                    # 오늘 세미나 데이터를 트리뷰에 삽입
                    self._insert_seminar_data_to_main_tree(today_seminars)
                else:
                    self.log_message("오늘 예정된 세미나가 없습니다")
                    self.seminar_tree.insert('', 'end', values=("", "", "", "오늘 예정된 세미나가 없습니다", "", "", ""))
            
        except Exception as e:
            self.handle_error('data', f"세미나 정보 표시 중 오류: {str(e)}")
    
    def _insert_seminar_data_to_main_tree(self, seminars):
        """메인 GUI 트리뷰에 세미나 데이터를 삽입합니다."""
        try:
            current_date = None
            
            for seminar in seminars:
                # 날짜가 바뀌면 구분선 추가
                if current_date != seminar.get('date', ''):
                    current_date = seminar.get('date', '')
                    if current_date:  # 날짜가 있는 경우에만 구분선 추가
                        self.seminar_tree.insert('', 'end', values=(
                            f"📅 {seminar.get('date', '')} {seminar.get('day', '')}",
                            "", "", "", "", "", ""
                        ), tags=('date_separator',))
                
                # 세미나 데이터 추가
                self._insert_seminar_item_to_main_tree(seminar)
            
        except Exception as e:
            self.handle_error('data', f"세미나 데이터 삽입 중 오류: {str(e)}")
    
    def _insert_seminar_item_to_main_tree(self, seminar):
        """개별 세미나 항목을 메인 GUI 트리뷰에 삽입합니다."""
        try:
            status_tag = self._get_status_tag(seminar.get('status', ''))
            
            self.seminar_tree.insert('', 'end', values=(
                seminar.get('date', ''),
                seminar.get('day', ''),
                seminar.get('time', ''),
                seminar.get('title', ''),
                seminar.get('lecturer', ''),
                seminar.get('person', ''),
                seminar.get('status', '')
            ), tags=(seminar.get('detail_link', ''), status_tag))
            
        except Exception as e:
            self.handle_error('data', f"세미나 항목 삽입 중 오류: {str(e)}")
    
    def _get_status_tag(self, status):
        """신청상태에 따른 태그 반환"""
        status_lower = status.lower().strip()
        
        if '신청가능' in status_lower or '신청' in status_lower and '가능' in status_lower:
            return '신청가능'
        elif '신청완료' in status_lower or '완료' in status_lower:
            return '신청완료'
        elif '신청마감' in status_lower or '마감' in status_lower:
            return '신청마감'
        elif '입장' in status_lower or '입장하기' in status_lower:
            return '입장하기'
        elif '대기' in status_lower or '대기중' in status_lower:
            return '대기중'
        else:
            return '기타'
    
    def clear_today_seminars(self):
        """오늘의 세미나 정보를 지웁니다."""
        try:
            # 기존 데이터 삭제
            for item in self.seminar_tree.get_children():
                self.seminar_tree.delete(item)
            
            # 초기 메시지 표시
            self.seminar_tree.insert('', 'end', values=("", "", "", "세미나 정보가 없습니다", "", "", ""))
        except Exception as e:
            self.handle_error('gui', f"세미나 정보 지우기 중 오류: {str(e)}")
    
    def on_seminar_double_click(self, event):
        """세미나 트리뷰 더블클릭 이벤트 핸들러"""
        try:
            # 선택된 항목 확인
            selection = self.seminar_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            tags = self.seminar_tree.item(item, "tags")
            
            # 날짜 구분선은 클릭 불가
            if 'date_separator' in tags:
                return
            
            # 첫 번째 태그가 링크인지 확인
            if len(tags) > 0 and tags[0]:
                detail_link = tags[0]
                # 상대 경로인 경우 절대 경로로 변환
                if detail_link.startswith('/'):
                    detail_link = "https://www.doctorville.co.kr" + detail_link
                
                self.log_message("선택된 세미나 페이지로 이동합니다...")
                
                # 현재 탭에서 열기
                if self.task_manager.state.web_automation and self.task_manager.state.web_automation.driver:
                    self.task_manager.state.web_automation.driver.get(detail_link)
                    self.log_message("세미나 상세 페이지로 이동 완료")
                    
                    # 세미나 상태에 따라 다른 동작 수행
                    status_tag = None
                    for tag in tags:
                        if tag in ['신청가능', '신청완료', '신청마감', '입장하기', '대기중']:
                            status_tag = tag
                            break
                    
                    if status_tag:
                        # 세미나 모듈 생성하여 상태별 액션 수행
                        from modules.seminar_module import SeminarModule
                        seminar_module = SeminarModule(self.task_manager.state.web_automation, self.log_message)
                        
                        if status_tag == '신청완료':
                            self.log_message("세미나 신청취소를 시도합니다...")
                            success = seminar_module.cancel_seminar()
                        elif status_tag == '입장하기':
                            self.log_message("세미나 입장을 시도합니다...")
                            success = seminar_module.enter_seminar()
                        else:
                            self.log_message("세미나 신청을 시도합니다...")
                            success = seminar_module.click_seminar_button()
                        
                        # 결과에 따른 로그
                        if success:
                            self.log_message("세미나 액션 완료!")
                            # 액션 완료 후 잠시 대기
                            import time
                            time.sleep(0.5)
                            
                            # 메인 GUI 트리뷰 업데이트
                            self._update_main_gui_seminar_after_check()
                        else:
                            self.log_message("세미나 액션 실패")
                    else:
                        self.log_message("세미나 상태를 확인할 수 없습니다")
                else:
                    self.log_message("웹드라이버가 초기화되지 않았습니다. 먼저 로그인해주세요.")
                
                # 선택된 항목 해제
                self.seminar_tree.selection_remove(item)
            else:
                self.log_message("세미나 링크를 찾을 수 없습니다")
                # 실패한 경우에도 선택 해제
                self.seminar_tree.selection_remove(item)
                        
        except Exception as e:
            self.handle_error('gui', f"세미나 더블클릭 처리 중 오류: {str(e)}")
            # 예외 발생 시에도 선택 해제
            try:
                selection = self.seminar_tree.selection()
                if selection:
                    self.seminar_tree.selection_remove(selection[0])
            except:
                pass
    


def main():
    """메인 함수"""
    root = tk.Tk()
    app = DoctorBillAutomation(root)
    root.mainloop()


if __name__ == "__main__":
    main()
