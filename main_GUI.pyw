# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import locale
import logging
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


class DoctorBillAutomation:
    def __init__(self, root):
        self.root = root
        self.root.title("닥터빌 자동화 프로그램")
        self.root.geometry("1000x700")  # 창 크기 확대
        self.root.minsize(800, 600)  # 최소 창 크기 설정
        self.root.configure(bg='#f0f0f0')
        
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
        
        # 디버그 정보 버튼 (설정 버튼 왼쪽에)
        self.debug_button = tk.Button(
            self.title_frame,
            text="🔍",
            font=("맑은 고딕", 12),
            bg='#e74c3c',
            fg='white',
            activebackground='#c0392b',
            activeforeground='white',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            width=3,
            height=1,
            command=self.show_debug_info
        )
        self.debug_button.pack(side='right', padx=(10, 0))
        
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
        # 로그인 버튼
        self.login_button = tk.Button(
            self.left_frame,
            text="🔑 자동 로그인",
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            activeforeground='white',
            command=self.auto_login,
            **button_style
        )
        self.login_button.pack(fill='x', padx=10, pady=(10, 8))
        
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
        self.attendance_button.pack(fill='x', padx=10, pady=8)
        
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
        
        # 세미나 정보 텍스트
        self.seminar_text = tk.Text(
            self.seminar_info_frame,
            height=8,
            width=60,
            font=("맑은 고딕", 10),
            bg='#ffffff',
            fg='#2c3e50',
            relief='flat',
            borderwidth=0,
            wrap='word',
            state='normal'
        )
        self.seminar_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 초기 메시지 표시
        self.seminar_text.insert(tk.END, "📺 오늘의 세미나 정보\n\n")
        self.seminar_text.insert(tk.END, "자동 로그인 후 세미나 정보가 자동으로 수집됩니다.\n\n")
        self.seminar_text.insert(tk.END, "또는 아래 새로고침 버튼을 클릭하여\n수동으로 정보를 가져올 수 있습니다.")
        
        # 읽기 전용으로 변경
        self.seminar_text.config(state='disabled')
        
        # 세미나 새로고침 버튼
        refresh_seminar_button = tk.Button(
            self.right_bottom_frame,
            text="🔄 세미나 새로고침",
            font=("맑은 고딕", 10),
            bg='#9b59b6',
            fg='white',
            activebackground='#8e44ad',
            activeforeground='white',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            command=self.refresh_seminar
        )
        refresh_seminar_button.pack(pady=(10, 0))
    
    def setup_hover_effects(self):
        """버튼 호버 효과를 설정합니다."""
        # 호버 효과를 위한 색상 매핑
        hover_colors = {
            '🔑 자동 로그인': '#2980b9',
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
            '🔑 자동 로그인': '#3498db',
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
            
            # 간단한 설정 창 생성 (나중에 확장 예정)
            self.settings_window = tk.Toplevel(self.root)
            self.settings_window.title("설정")
            self.settings_window.geometry("400x300")
            self.settings_window.configure(bg='#f0f0f0')
            self.settings_window.resizable(False, False)
            self.settings_window.transient(self.root)
            self.settings_window.grab_set()
            
            # 간단한 설정 내용
            main_frame = tk.Frame(self.settings_window, bg='#f0f0f0')
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            title_label = tk.Label(
                main_frame,
                text="⚙️ 설정",
                font=("맑은 고딕", 16, "bold"),
                bg='#f0f0f0',
                fg='#2c3e50'
            )
            title_label.pack(pady=(0, 20))
            
            info_label = tk.Label(
                main_frame,
                text="설정 기능은 준비 중입니다.\n\n나중에 다시 구현할 예정입니다.",
                font=("맑은 고딕", 12),
                bg='#f0f0f0',
                fg='#7f8c8d',
                justify='center'
            )
            info_label.pack(expand=True)
            
            close_button = tk.Button(
                main_frame,
                text="닫기",
                font=("맑은 고딕", 12),
                bg='#95a5a6',
                fg='white',
                activebackground='#7f8c8d',
                activeforeground='white',
                borderwidth=0,
                relief='flat',
                cursor='hand2',
                command=self.close_settings_window
            )
            close_button.pack(pady=(20, 0))
            
            # X 버튼 클릭 시 close_settings_window 함수 호출
            self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)
            
        except Exception as e:
            self.handle_error('gui', f"설정 창 열기 실패: {str(e)}")
            messagebox.showerror("오류", f"설정 창을 열 수 없습니다: {str(e)}")
    
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
    
    def check_seminar(self):
        """라이브세미나 확인 기능"""
        if self.task_manager.state.is_logging_in:
            self.log_message("로그인 중입니다. 잠시 기다려주세요...")
            return
        
        self.log_message("라이브세미나 정보를 확인합니다...")
        self.update_status("라이브세미나 확인 중...")
        
        # 표준 GUI 콜백 생성
        gui_callbacks = self.get_callbacks()
        
        # TaskManager를 통해 세미나 확인 실행
        self.task_manager.execute_seminar(gui_callbacks)
    
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
    
    def refresh_seminar(self):
        """세미나 정보를 새로고침합니다."""
        self.log_message("세미나 정보를 새로고침합니다...")
        self.check_seminar()
    
    def update_today_seminars(self, seminars_data):
        """오늘의 세미나 정보를 화면에 표시합니다."""
        try:
            # 세미나 텍스트 위젯을 편집 가능하게 변경
            self.seminar_text.config(state='normal')
            
            # 기존 내용 지우기
            self.seminar_text.delete(1.0, tk.END)
            
            if not seminars_data:
                self.seminar_text.insert(tk.END, "오늘 예정된 세미나가 없습니다.\n\n")
                self.seminar_text.insert(tk.END, "📅 다음 세미나 일정을 확인해보세요.")
            else:
                # 세미나 정보 표시
                self.seminar_text.insert(tk.END, f"📅 오늘 예정된 세미나: {len(seminars_data)}개\n\n")
                
                for i, seminar in enumerate(seminars_data[:10], 1):  # 최대 10개만 표시
                    self.seminar_text.insert(tk.END, f"{i}. {seminar.get('title', '제목 없음')}\n")
                    self.seminar_text.insert(tk.END, f"   ⏰ {seminar.get('time', '시간 미정')}\n")
                    self.seminar_text.insert(tk.END, f"   📍 {seminar.get('location', '장소 미정')}\n\n")
                
                if len(seminars_data) > 10:
                    self.seminar_text.insert(tk.END, f"... 외 {len(seminars_data) - 10}개 더\n")
            
            # 다시 읽기 전용으로 변경
            self.seminar_text.config(state='disabled')
            
        except Exception as e:
            self.handle_error('data', f"세미나 정보 표시 중 오류: {str(e)}")
    
    def clear_today_seminars(self):
        """오늘의 세미나 정보를 지웁니다."""
        try:
            self.seminar_text.config(state='normal')
            self.seminar_text.delete(1.0, tk.END)
            self.seminar_text.insert(tk.END, "세미나 정보가 없습니다.\n\n새로고침 버튼을 클릭하여 정보를 가져오세요.")
            self.seminar_text.config(state='disabled')
        except Exception as e:
            self.handle_error('gui', f"세미나 정보 지우기 중 오류: {str(e)}")
    
    def get_task_manager_status(self):
        """TaskManager 상태 정보를 가져옵니다."""
        try:
            status = self.task_manager.state.get_status_summary()
            self.log_message(f"📊 TaskManager 상태: {status}")
            return status
        except Exception as e:
            self.handle_error('data', f"상태 정보 가져오기 실패: {str(e)}")
            return None
    
    def get_cache_info(self):
        """캐시 정보를 가져옵니다."""
        try:
            cache_info = self.task_manager.get_cache_info()
            self.log_message(f"💾 캐시 정보: {cache_info}")
            return cache_info
        except Exception as e:
            self.handle_error('data', f"캐시 정보 가져오기 실패: {str(e)}")
            return None
    
    def show_debug_info(self):
        """디버그 정보를 표시합니다."""
        self.log_message("🔍 디버그 정보를 가져오는 중...")
        self.get_task_manager_status()
        self.get_cache_info()


def main():
    """메인 함수"""
    root = tk.Tk()
    app = DoctorBillAutomation(root)
    root.mainloop()


if __name__ == "__main__":
    main()
