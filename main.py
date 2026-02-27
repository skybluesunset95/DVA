import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import logging
import time

from main_task_manager import TaskManager
from ui.main_window import MainWindow
from ui.dialogs.baemin_dialog import show_baemin_purchase_dialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.seminar_dialog import show_seminar_info_dialog

class DoctorBillApp:
    def __init__(self, root):
        self.root = root
        
        # 환경변수에서 계정 이름 가져오기 (기본값: 'default')
        account_name = os.environ.get('ACCOUNT_NAME', 'default')
        self.settings_file = f"settings_{account_name}.json" if account_name != 'default' else "settings.json"
        
        self.default_settings = {
            'auto_attendance': True,
            'auto_attendance_hour': 9,
            'auto_attendance_min': 0,
            'auto_quiz': True,
            'auto_quiz_hour': 9,
            'auto_quiz_min': 5,
            'auto_survey': True,
            'auto_seminar_refresh': True,
            'auto_seminar_join': False,
            'auto_seminar_enter': False,
            'seminar_enter_delay': 5,
            'seminar_refresh_interval': 5,
            'browser_headless': True,
            'settings_window_width': 520,
            'settings_window_height': 850
        }
        
        # 1. 설정 로드
        self.settings = self.load_settings()
        
        # 2. 작업 관리자 초기화
        self.task_manager = TaskManager()
        
        # 3. UI 생성 및 이벤트 와이어링
        self.ui = MainWindow(self.root, self.get_callbacks())
        
        # 4. 로깅 설정 (내부 로거를 UI 창으로 연결)
        self.setup_logging()
        
        # 5. 초기 작업 스케줄링
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(200, self.auto_login)
        self.root.after(5000, self.check_scheduled_tasks)

        self.ui.work_log.log_message("프로그램이 시작되었습니다.")

    # ================= Settings =================
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                merged = self.default_settings.copy()
                merged.update(settings)
                return merged
            else:
                self.save_settings(self.default_settings)
                return self.default_settings.copy()
        except:
            return self.default_settings.copy()

    def save_settings(self, settings=None):
        if settings is None:
            settings = self.settings
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"❌ 설정 저장 실패: {e}")

    def get_setting(self, key):
        return self.settings.get(key, self.default_settings.get(key, False))

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

    # ================= Callbacks Registration =================
    def get_callbacks(self):
        """UI와 TaskManager가 통신할 콜백 모음집입니다."""
        return {
            # UI Actions (UI -> App -> TaskManager)
            'on_attendance': self.on_attendance,
            'on_quiz': self.on_quiz,
            'on_seminar_check': self.on_seminar_check,
            'on_survey_open': self.on_survey_open,
            'on_survey_problem': self.on_survey_problem,
            'on_baemin_purchase': self.on_baemin_purchase,
            'on_settings': self.open_settings,
            'on_exit': self.on_closing,
            'on_seminar_refresh_toggle': self.on_seminar_refresh_toggle,
            'on_seminar_double_click': self.on_seminar_double_click,
            
            # Application Actions (TaskManager -> App -> UI)
            'log_message': self.log_message,
            'log_info': lambda m: self.log_message(f"ℹ {m}"),
            'log_error': lambda m: self.log_message(f"❌ {m}"),
            'log_success': lambda m: self.log_message(f"✅ {m}"),
            'log_warning': lambda m: self.log_message(f"⚠ {m}"),
            'update_status': self.gui_update_status,
            'update_user_info': self.gui_update_user_info,
            'update_display': self.gui_update_display,
            'log_and_update_status': self.log_and_update_status,
            'show_seminar_dialog': lambda seminars, cb: show_seminar_info_dialog(self.root, seminars, cb),
            'update_seminar_dialog': self.update_seminar_dialog,
            'gui_instance': self
        }

    # ================= UI Actions -> TaskManager =================
    def auto_login(self):
        self.gui_update_status("로그인 중...")
        self.task_manager.execute_login(self.get_callbacks())

    def on_attendance(self):
        self.task_manager.execute_attendance(self.get_callbacks())

    def on_quiz(self):
        self.task_manager.execute_quiz(self.get_callbacks())

    def on_seminar_check(self):
        self.task_manager.execute_seminar(self.get_callbacks())

    def on_survey_open(self):
        self.task_manager.execute_survey(self.get_callbacks())

    def on_survey_problem(self):
        self.open_survey_problem()
        
    def open_survey_problem(self, initial_question=None, initial_category=None, image_path=None):
        try:
            from ui.dialogs.survey_problem_dialog import open_survey_problem_manager
            
            # 스크린샷이 있으면 먼저 열어서 보여주기
            if image_path and os.path.exists(image_path):
                try:
                    os.startfile(image_path)
                except Exception as e:
                    self.log_message(f"❌ 스크린샷 열기 실패: {e}")
                    
            self.log_message("설문 문제 관리 창을 열고 있습니다...")
            open_survey_problem_manager(self.root, self.log_message, initial_question, initial_category)
        except Exception as e:
            self.log_message(f"❌ 문제 관리자를 열 수 없습니다: {e}")

    def on_baemin_purchase(self):
        try:
            self.gui_update_status("정보 조회 중...")
            # Thread에서 조회하도록 하는게 좋지만, 일단 간단히 실행
            info = self.task_manager.get_baemin_info(self.get_callbacks())
            self.gui_update_status("대기 중")
            
            def handle_purchase(quantity, phone, total_cost=None):
                self.task_manager.execute_baemin_purchase(quantity, phone, self.get_callbacks())
                
            show_baemin_purchase_dialog(
                self.root, 
                current_points=info.get('points', 0), 
                max_coupons=info.get('max_coupons', 0), 
                phone_number=info.get('phone', ''), 
                on_confirm_callback=handle_purchase,
                on_cancel_callback=lambda: None
            )
        except Exception as e:
            self.log_message(f"❌ 배민 정보 조회 불가: {e}")
            self.gui_update_status("에러 발생")

    def on_seminar_refresh_toggle(self, btn):
        # TODO: 실제 토글 로직은 추후 구현 가능. UI의 멈춤/재개 조작.
        current_text = btn.cget('text')
        if "멈춤" in current_text:
            btn.config(text="▶ 재개", bg="#27ae60")
            self.log_message("세미나 새로고침이 일시정지되었습니다.")
        else:
            btn.config(text="⏸ 멈춤", bg="#e74c3c")
            self.log_message("세미나 새로고침이 재개되었습니다.")

    def on_seminar_double_click(self, event):
        selection = self.ui.seminar_panel.seminar_tree.selection()
        if not selection: return
        item = selection[0]
        tags = self.ui.seminar_panel.seminar_tree.item(item, "tags")
        if 'date_separator' in tags: return
        
        detail_link = tags[0] if len(tags) > 0 else ""
        if not detail_link: return
        
        status_tag = tags[1] if len(tags) > 1 else None
        
        self.log_message("세미나 상세 요청을 처리중입니다...")
        if detail_link.startswith('/'):
            detail_link = "https://www.doctorville.co.kr" + detail_link
        
        # TaskManager로 전달하여 처리
        self.task_manager._handle_seminar_single_action(detail_link, status_tag, self.get_callbacks())
        self.ui.seminar_panel.seminar_tree.selection_remove(item)

    def open_settings(self):
        def on_save(new_set):
            old_headless = self.get_setting('browser_headless')
            for k, v in new_set.items(): self.set_setting(k, v)
            if old_headless != self.get_setting('browser_headless'):
                if messagebox.askyesno("재시작", "브라우저 설정이 변경되었습니다. 재시작하시겠습니까?"):
                    self.task_manager.cleanup_web_automation()
                    self.auto_login()
            else:
                messagebox.showinfo("저장", "저장되었습니다.")
                
        def on_close(dims):
            if dims:
                self.set_setting('settings_window_width', dims.get('width', 520))
                self.set_setting('settings_window_height', dims.get('height', 850))

        SettingsDialog(self.root, self.get_setting, on_save, on_close)

    def on_closing(self):
        self.log_message("프로그램을 종료합니다...")
        
        # 1. 화면 창을 즉시 숨깁니다 (사용자 입장에서는 꺼진 것처럼 보임)
        self.root.withdraw()
        
        # 2. 백그라운드에서 크롬을 안전하게 끄고 완전히 프로세스를 종료합니다
        def fast_exit():
            try:
                self.task_manager.cleanup() # 크롬 종료 대기 (1~2초 소요)
            except:
                pass
            import os
            os._exit(0) # 완벽한 종료
            
        threading.Thread(target=fast_exit, daemon=True).start()

    # ================= TaskManager -> UI Effects =================
    def log_message(self, message):
        self.root.after(0, lambda: self.ui.work_log.log_message(message))

    def gui_update_status(self, status):
        self.root.after(0, lambda: self.ui.update_status(status))

    def gui_update_user_info(self, user_name=None, account_type=None):
        self.root.after(0, lambda: self.ui.dashboard.update_user_info(user_name, account_type))

    def gui_update_display(self, display_type, value):
        self.root.after(0, lambda: self.ui.dashboard.update_display(display_type, value))

    def log_and_update_status(self, log_msg, status_msg):
        self.log_message(log_msg)
        self.gui_update_status(status_msg)
        
    def update_seminar_dialog(self, seminars):
        self.root.after(0, lambda: self._update_main_seminar_tree(seminars))

    def _update_main_seminar_tree(self, seminars):
        self.ui.seminar_panel.clear_all()
        if not seminars:
            self.ui.seminar_panel.insert_item(("", "", "", "오늘 예정된 세미나가 없습니다", "", "", ""))
            return
            
        current_date = None
        for s in seminars:
            if current_date != s.get('date', ''):
                current_date = s.get('date', '')
                if current_date:
                    self.ui.seminar_panel.insert_item((f"📅 {current_date} {s.get('day','')}", "", "", "", "", "", ""), tags=('date_separator',))
            from modules.utils import get_status_tag
            status_tag = get_status_tag(s.get('status',''))
            self.ui.seminar_panel.insert_item(
                (s.get('date',''), s.get('day',''), s.get('time',''), s.get('title',''), s.get('lecturer',''), s.get('person',''), s.get('status','')),
                tags=(s.get('detail_link',''), status_tag)
            )

    # ================= Utils =================
    def setup_logging(self):
        class GUILogHandler(logging.Handler):
            def __init__(self, log_func):
                super().__init__()
                self.log_func = log_func
            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.log_func(msg)
                except Exception:
                    pass
                
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        gui_handler = GUILogHandler(self.log_message)
        gui_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(gui_handler)

    def check_scheduled_tasks(self):
        self.task_manager.check_scheduled_tasks(self.settings, self.get_callbacks())
        # 반복 실행 (5초)
        self.root.after(5000, self.check_scheduled_tasks)


def main():
    root = tk.Tk()
    
    # 창 제목에 계정 이름 표시
    account_name = os.environ.get('ACCOUNT_NAME', '')
    title_suffix = f" [{account_name}]" if account_name else ""
    root.title(f"닥터빌 자동화 프로그램{title_suffix}")
    
    app = DoctorBillApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
