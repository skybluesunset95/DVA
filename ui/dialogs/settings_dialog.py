# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from ui.components.tooltip import ToolTip

class SettingsDialog:
    def __init__(self, parent, get_setting_func, save_callback, close_callback):
        self.parent = parent
        self.get_setting = get_setting_func
        self.save_callback = save_callback
        self.close_callback = close_callback
        
        self.setting_vars = {}
        self._seminar_sub_widgets = []
        
        self.settings_window = tk.Toplevel(parent)
        self.settings_window.title("⚙️ 설정")
        
        # 저장된 창 크기 불러오기
        width = self.get_setting('settings_window_width') or 600
        height = self.get_setting('settings_window_height') or 800
        self.settings_window.geometry(f"{width}x{height}")
        
        self.settings_window.configure(bg='#f0f0f0')
        self.settings_window.resizable(True, True)
        
        # 부모 창이 보일 때만 transient로 묶어줍니다 (트레이에 있을 때는 독립적으로 띄움)
        if parent.state() != 'withdrawn':
            self.settings_window.transient(parent)
        
        self.settings_window.grab_set()
        self.settings_window.lift()
        self.settings_window.focus_force()
        
        self._setup_ui()
        
        # 창이 닫힐 때 처리
        self.settings_window.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        # 1. 하단 버튼 프레임
        bottom_frame = tk.Frame(self.settings_window, bg='#ffffff', pady=15, padx=20, relief='raised', borderwidth=1)
        bottom_frame.pack(side='bottom', fill='x')
        
        btn_container = tk.Frame(bottom_frame, bg='#ffffff')
        btn_container.pack()
        
        save_button = tk.Button(
            btn_container, text="💾 설정 저장", font=("맑은 고딕", 12, "bold"),
            bg='#27ae60', fg='white', activebackground='#229954', activeforeground='white',
            borderwidth=0, padx=20, pady=8, relief='flat', cursor='hand2',
            command=self._on_save
        )
        save_button.pack(side='left', padx=10)
        
        close_button = tk.Button(
            btn_container, text="❌ 닫기", font=("맑은 고딕", 12, "bold"),
            bg='#e74c3c', fg='white', activebackground='#c0392b', activeforeground='white',
            borderwidth=0, padx=20, pady=8, relief='flat', cursor='hand2',
            command=self._on_closing
        )
        close_button.pack(side='left', padx=10)
        
        # 2. 스크롤 가능한 영역
        container = tk.Frame(self.settings_window, bg='#f0f0f0')
        container.pack(side='top', fill='both', expand=True)
        
        canvas = tk.Canvas(container, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        self.scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_frame = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def _configure_canvas(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind("<Configure>", _configure_canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas = canvas # Store for unbinding
        
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        scrollbar.pack(side="right", fill="y", pady=20)
        
        # 3. 설정 내용 채우기
        tk.Label(
            self.scrollable_frame, text="⚙️ 프로그램 설정",
            font=("맑은 고딕", 18, "bold"), bg='#f0f0f0', fg='#2c3e50'
        ).pack(pady=(0, 20))
        
        self._setup_options(self.scrollable_frame)

    def _setup_options(self, parent):
        # 자동 실행 설정 섹션
        auto_frame = tk.LabelFrame(
            parent, text="🤖 자동 실행 설정", font=("맑은 고딕", 12, "bold"),
            bg='#f0f0f0', fg='#2c3e50', padx=10, pady=5
        )
        auto_frame.pack(fill='x', pady=(0, 10))
        
        # 1. 자동 출석체크
        self.setting_vars['auto_attendance'] = tk.BooleanVar(value=self.get_setting('auto_attendance'))
        attendance_check = tk.Checkbutton(
            auto_frame, text="✅ 자동 출석체크", variable=self.setting_vars['auto_attendance'],
            font=("맑은 고딕", 11), bg='#f0f0f0', fg='#2c3e50',
            activebackground='#f0f0f0', activeforeground='#2c3e50'
        )
        attendance_check.pack(anchor='w', pady=(2, 0))
        
        attendance_time_frame = tk.Frame(auto_frame, bg='#f0f0f0')
        attendance_time_frame.pack(anchor='w', pady=(0, 5), padx=25)
        
        attendance_widgets = []
        def _on_attendance_toggle():
            state = 'normal' if self.setting_vars['auto_attendance'].get() else 'disabled'
            for w in attendance_widgets:
                try: w.configure(state=state)
                except: pass
        
        lbl_time = tk.Label(attendance_time_frame, text="⏰ 실행 시간:", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#2c3e50')
        lbl_time.pack(side='left')
        attendance_widgets.append(lbl_time)
        attendance_check.configure(command=_on_attendance_toggle)
        
        self.setting_vars['auto_attendance_hour'] = tk.StringVar(value=str(self.get_setting('auto_attendance_hour')))
        hour_spin = tk.Spinbox(attendance_time_frame, from_=0, to=23, textvariable=self.setting_vars['auto_attendance_hour'], width=3, font=("맑은 고딕", 10, "bold"), justify='center')
        hour_spin.pack(side='left', padx=2)
        attendance_widgets.append(hour_spin)
        
        tk.Label(attendance_time_frame, text="시", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#2c3e50').pack(side='left')
        
        self.setting_vars['auto_attendance_min'] = tk.StringVar(value=str(self.get_setting('auto_attendance_min')))
        min_spin = tk.Spinbox(attendance_time_frame, from_=0, to=59, textvariable=self.setting_vars['auto_attendance_min'], width=3, font=("맑은 고딕", 10, "bold"), justify='center')
        min_spin.pack(side='left', padx=2)
        attendance_widgets.append(min_spin)
        
        tk.Label(attendance_time_frame, text="분", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#2c3e50').pack(side='left')
        
        tk.Label(
            auto_frame, text="  └ 지정한 시간에 오늘의 출석체크를 자동으로 진행합니다.",
            font=("맑은 고딕", 9), bg='#f0f0f0', fg='#7f8c8d'
        ).pack(anchor='w', pady=(0, 5), padx=25)

        # 2. 자동 퀴즈풀기
        self.setting_vars['auto_quiz'] = tk.BooleanVar(value=self.get_setting('auto_quiz'))
        quiz_check = tk.Checkbutton(
            auto_frame, text="🧠 자동 퀴즈풀기", variable=self.setting_vars['auto_quiz'],
            font=("맑은 고딕", 11), bg='#f0f0f0', fg='#2c3e50',
            activebackground='#f0f0f0', activeforeground='#2c3e50'
        )
        quiz_check.pack(anchor='w', pady=(2, 0))
        
        quiz_time_frame = tk.Frame(auto_frame, bg='#f0f0f0')
        quiz_time_frame.pack(anchor='w', pady=(0, 5), padx=25)
        
        quiz_widgets = []
        def _on_quiz_toggle():
            state = 'normal' if self.setting_vars['auto_quiz'].get() else 'disabled'
            for w in quiz_widgets:
                try: w.configure(state=state)
                except: pass
        
        lbl_q_time = tk.Label(quiz_time_frame, text="⏰ 실행 시간:", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#2c3e50')
        lbl_q_time.pack(side='left')
        quiz_widgets.append(lbl_q_time)
        quiz_check.configure(command=_on_quiz_toggle)
        
        self.setting_vars['auto_quiz_hour'] = tk.StringVar(value=str(self.get_setting('auto_quiz_hour')))
        q_hour_spin = tk.Spinbox(quiz_time_frame, from_=0, to=23, textvariable=self.setting_vars['auto_quiz_hour'], width=3, font=("맑은 고딕", 10, "bold"), justify='center')
        q_hour_spin.pack(side='left', padx=2)
        quiz_widgets.append(q_hour_spin)
        
        tk.Label(quiz_time_frame, text="시", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#2c3e50').pack(side='left')
        
        self.setting_vars['auto_quiz_min'] = tk.StringVar(value=str(self.get_setting('auto_quiz_min')))
        q_min_spin = tk.Spinbox(quiz_time_frame, from_=0, to=59, textvariable=self.setting_vars['auto_quiz_min'], width=3, font=("맑은 고딕", 10, "bold"), justify='center')
        q_min_spin.pack(side='left', padx=2)
        quiz_widgets.append(q_min_spin)
        
        tk.Label(quiz_time_frame, text="분", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#2c3e50').pack(side='left')
        
        tk.Label(
            auto_frame, text="  └ 지정한 시간에 미완료된 수강 퀴즈를 자동으로 풀이합니다.",
            font=("맑은 고딕", 9), bg='#f0f0f0', fg='#7f8c8d'
        ).pack(anchor='w', pady=(0, 5), padx=25)

        # 3. 자동 세미나 입장하기
        self.setting_vars['auto_seminar_enter'] = tk.BooleanVar(value=self.get_setting('auto_seminar_enter'))
        seminar_enter_check = tk.Checkbutton(
            auto_frame, text="🚪 자동 세미나 입장하기", variable=self.setting_vars['auto_seminar_enter'],
            font=("맑은 고딕", 11), bg='#f0f0f0', fg='#2c3e50',
            activebackground='#f0f0f0', activeforeground='#2c3e50'
        )
        seminar_enter_check.pack(anchor='w', pady=(2, 0))
        
        tk.Label(
            auto_frame, text="  └ 세미나 시작 시간 부근에 자동으로 시청 페이지에 입장합니다.",
            font=("맑은 고딕", 9), bg='#f0f0f0', fg='#7f8c8d'
        ).pack(anchor='w', pady=(0, 2), padx=25)
        
        enter_delay_frame = tk.Frame(auto_frame, bg='#f0f0f0')
        enter_delay_frame.pack(anchor='w', pady=(5, 10), padx=25)
        
        enter_widgets = []
        def _on_enter_toggle():
            state = 'normal' if self.setting_vars['auto_seminar_enter'].get() else 'disabled'
            for w in enter_widgets:
                try: w.configure(state=state)
                except: pass
        
        seminar_enter_check.configure(command=_on_enter_toggle)
        
        lbl_delay = tk.Label(enter_delay_frame, text="⏳ 입장 대기시간: 시작시간 +", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#2c3e50')
        lbl_delay.pack(side='left')
        enter_widgets.append(lbl_delay)
        
        self.setting_vars['seminar_enter_delay'] = tk.StringVar(value=str(self.get_setting('seminar_enter_delay')))
        enter_delay_spinbox = tk.Spinbox(enter_delay_frame, from_=0, to=30, textvariable=self.setting_vars['seminar_enter_delay'], width=4, font=("맑은 고딕", 10, "bold"), justify='center')
        enter_delay_spinbox.pack(side='left', padx=5)
        enter_widgets.append(enter_delay_spinbox)
        
        tk.Label(enter_delay_frame, text="분 후 자동 입장", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#7f8c8d').pack(side='left')

        # 4. 자동 세미나 새로고침
        self.setting_vars['auto_seminar_refresh'] = tk.BooleanVar(value=self.get_setting('auto_seminar_refresh'))
        
        def _on_refresh_toggle():
            is_enabled = self.setting_vars['auto_seminar_refresh'].get()
            state = 'normal' if is_enabled else 'disabled'
            for widget in self._seminar_sub_widgets:
                try: widget.configure(state=state)
                except: pass
            if not is_enabled:
                self.setting_vars['auto_seminar_join'].set(False)
                self.setting_vars['auto_survey'].set(False)
        
        refresh_check = tk.Checkbutton(
            auto_frame, text="🔄 자동 세미나 새로고침", variable=self.setting_vars['auto_seminar_refresh'],
            command=_on_refresh_toggle, font=("맑은 고딕", 11), bg='#f0f0f0', fg='#2c3e50',
            activebackground='#f0f0f0', activeforeground='#2c3e50'
        )
        refresh_check.pack(anchor='w', pady=(5, 0))
        
        tk.Label(
            auto_frame, text="  └ 세미나 목록을 설정한 간격을 주기로 새로고침합니다",
            font=("맑은 고딕", 9), bg='#f0f0f0', fg='#7f8c8d'
        ).pack(anchor='w', pady=(0, 2), padx=25)
        
        interval_frame = tk.Frame(auto_frame, bg='#f0f0f0')
        interval_frame.pack(anchor='w', pady=(2, 10), padx=25)
        
        refresh_label = tk.Label(interval_frame, text="⏱️ 세미나 새로고침 간격:", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#2c3e50')
        refresh_label.pack(side='left')
        self._seminar_sub_widgets.append(refresh_label)
        
        self.setting_vars['seminar_refresh_interval'] = tk.StringVar(value=str(self.get_setting('seminar_refresh_interval')))
        interval_spin = tk.Spinbox(interval_frame, from_=1, to=3600, textvariable=self.setting_vars['seminar_refresh_interval'], width=5, font=("맑은 고딕", 10, "bold"), justify='center')
        interval_spin.pack(side='left', padx=2)
        self._seminar_sub_widgets.append(interval_spin)
        
        refresh_unit = tk.Label(interval_frame, text="초 (권장: 5초 이상)", font=("맑은 고딕", 10), bg='#f0f0f0', fg='#7f8c8d')
        refresh_unit.pack(side='left')
        self._seminar_sub_widgets.append(refresh_unit)

        # 5. 자동 세미나 신청
        self.setting_vars['auto_seminar_join'] = tk.BooleanVar(value=self.get_setting('auto_seminar_join'))
        seminar_join_check = tk.Checkbutton(
            auto_frame, text="📝 자동 세미나 신청", variable=self.setting_vars['auto_seminar_join'],
            font=("맑은 고딕", 11), bg='#f0f0f0', fg='#2c3e50',
            activebackground='#f0f0f0', activeforeground='#2c3e50'
        )
        seminar_join_check.pack(anchor='w', pady=(2, 0))
        self._seminar_sub_widgets.append(seminar_join_check)
        
        tk.Label(
            auto_frame, text="  └ 발견된 새로운 세미나를 자동으로 신청합니다.\n  └ 자동 세미나 새로고침 간격에 따릅니다 (활성화 필요)",
            font=("맑은 고딕", 9), bg='#f0f0f0', fg='#7f8c8d', justify='left'
        ).pack(anchor='w', pady=(0, 5), padx=25)
        
        # 6. 자동 설문참여
        self.setting_vars['auto_survey'] = tk.BooleanVar(value=self.get_setting('auto_survey'))
        survey_check = tk.Checkbutton(
            auto_frame, text="📋 자동 설문참여", variable=self.setting_vars['auto_survey'],
            font=("맑은 고딕", 11), bg='#f0f0f0', fg='#2c3e50',
            activebackground='#f0f0f0', activeforeground='#2c3e50'
        )
        survey_check.pack(anchor='w', pady=(2, 0))
        self._seminar_sub_widgets.append(survey_check)
        
        tk.Label(
            auto_frame, text="  └ 강의 종료 후 출력되는 설문조사에 자동으로 응답합니다.\n  └ 자동 세미나 새로고침 간격에 따릅니다 (활성화 필요)",
            font=("맑은 고딕", 9), bg='#f0f0f0', fg='#7f8c8d', justify='left'
        ).pack(anchor='w', pady=(0, 5), padx=25)

        # 브라우저 설정 섹션
        browser_frame = tk.LabelFrame(
            parent, text="🌐 브라우저 설정", font=("맑은 고딕", 12, "bold"),
            bg='#f0f0f0', fg='#2c3e50', padx=10, pady=5
        )
        browser_frame.pack(fill='x', pady=(0, 10))

        # 크롬 창 숨기기
        self.setting_vars['browser_headless'] = tk.BooleanVar(value=self.get_setting('browser_headless'))
        headless_check = tk.Checkbutton(
            browser_frame, text="🛡️ 크롬 창 숨기기 (백그라운드 실행)", variable=self.setting_vars['browser_headless'],
            font=("맑은 고딕", 11), bg='#f0f0f0', fg='#2c3e50',
            activebackground='#f0f0f0', activeforeground='#2c3e50'
        )
        headless_check.pack(anchor='w', pady=(2, 0))
        
        tk.Label(
            browser_frame, text="  └ 브라우저 화면을 숨기고 백그라운드에서 조용히 실행합니다.",
            font=("맑은 고딕", 9), bg='#f0f0f0', fg='#7f8c8d'
        ).pack(anchor='w', pady=(0, 5), padx=25)
        
        ToolTip(headless_check, "크롬 창을 띄우지 않고 백그라운드에서 작업을 수행합니다.\n체크하면 작업 중 컴퓨터 사용이 더 편리해집니다.", delay=500)

        # 초기 상태 업데이트
        _on_attendance_toggle()
        _on_quiz_toggle()
        _on_enter_toggle()
        _on_refresh_toggle()

    def _on_save(self):
        new_settings = {}
        for key, var in self.setting_vars.items():
            val = var.get()
            if isinstance(val, str) and val.isdigit():
                try: new_settings[key] = int(val, 10)
                except: new_settings[key] = val
            else:
                new_settings[key] = val
        
        # 창 크기 정보 추가
        width = self.settings_window.winfo_width()
        height = self.settings_window.winfo_height()
        if width > 100 and height > 100:
            new_settings['settings_window_width'] = width
            new_settings['settings_window_height'] = height
            
        self.save_callback(new_settings)

    def _on_closing(self):
        # 마우스 휠 바인딩 해제
        self.canvas.unbind_all("<MouseWheel>")
        
        # 창 크기 정보 수집
        dimensions = {}
        width = self.settings_window.winfo_width()
        height = self.settings_window.winfo_height()
        if width > 100 and height > 100:
            dimensions['width'] = width
            dimensions['height'] = height
            
        self.settings_window.destroy()
        self.close_callback(dimensions)
