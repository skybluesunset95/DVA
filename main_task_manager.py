# -*- coding: utf-8 -*-
"""
닥터빌 자동화 프로그램 - Task Manager
기능 실행 로직을 담당합니다.
"""

import threading
import logging
from datetime import datetime
from web_automation import WebAutomation
from modules.base_module import (
    BaseModule,
    STATUS_ATTENDANCE_COMPLETE, 
    STATUS_ATTENDANCE_INCOMPLETE,
    STATUS_QUIZ_COMPLETE, 
    STATUS_QUIZ_INCOMPLETE,
    STATUS_KEY_ATTENDANCE, 
    STATUS_KEY_QUIZ
)

class TaskManagerState:
    """TaskManager 상태를 체계적으로 관리하는 클래스"""
    
    def __init__(self):
        self._web_automation = None
        self._is_logging_in = False
        self._current_module = None
        self._module_queue = []
        self._last_activity = None
        self._logger = logging.getLogger(__name__)
        
        # 스케줄러 상태
        self._last_auto_attendance_date = None
        self._last_auto_quiz_date = None
        self._startup_time = datetime.now()
    
    @property
    def last_auto_attendance_date(self):
        return self._last_auto_attendance_date
    
    @last_auto_attendance_date.setter
    def last_auto_attendance_date(self, value):
        self._last_auto_attendance_date = value

    @property
    def last_auto_quiz_date(self):
        return self._last_auto_quiz_date
    
    @last_auto_quiz_date.setter
    def last_auto_quiz_date(self, value):
        self._last_auto_quiz_date = value

    @property
    def startup_time(self):
        return self._startup_time
    
    @property
    def web_automation(self):
        """웹 자동화 상태 반환"""
        return self._web_automation
    
    @web_automation.setter
    def web_automation(self, value):
        """웹 자동화 상태 설정"""
        old_value = self._web_automation
        self._web_automation = value
        self._last_activity = datetime.now()
        
        if old_value != value:
            if value:
                self._logger.info("웹 자동화 초기화됨")
            else:
                self._logger.info("웹 자동화 정리됨")
    
    @property
    def is_logging_in(self):
        """로그인 상태 반환"""
        return self._is_logging_in
    
    @is_logging_in.setter
    def is_logging_in(self, value):
        """로그인 상태 설정 - 관련 상태도 함께 관리"""
        old_value = self._is_logging_in
        self._is_logging_in = value
        
        # 로그인 상태 변경 시 관련 상태도 함께 관리
        if old_value != value:
            if value:  # 로그인 시작
                self._current_module = 'login'
                self._last_activity = datetime.now()
                self._logger.info("로그인 상태: 시작됨")
            else:  # 로그인 종료
                self._current_module = None
                self._last_activity = datetime.now()
                self._logger.info("로그인 상태: 종료됨")
    
    @property
    def current_module(self):
        """현재 실행 중인 모듈 반환"""
        return self._current_module
    
    @current_module.setter
    def current_module(self, value):
        """현재 실행 중인 모듈 설정"""
        old_value = self._current_module
        self._current_module = value
        self._last_activity = datetime.now()
        
        if old_value != value:
            if value:
                self._logger.info(f"현재 모듈: {value} 시작")
            else:
                self._logger.info("모듈 실행 완료")
    
    def add_module_to_queue(self, module_name):
        """모듈을 큐에 추가"""
        if module_name not in self._module_queue:
            self._module_queue.append(module_name)
            self._logger.info(f"모듈 큐에 추가: {module_name}")
    
    def remove_module_from_queue(self, module_name):
        """모듈을 큐에서 제거"""
        if module_name in self._module_queue:
            self._module_queue.remove(module_name)
            self._logger.info(f"모듈 큐에서 제거: {module_name}")
    
    def get_status_summary(self):
        """현재 상태 요약 반환"""
        return {
            'web_automation_active': self._web_automation is not None,
            'is_logging_in': self._is_logging_in,
            'current_module': self._current_module,
            'queued_modules': self._module_queue.copy(),
            'last_activity': self._last_activity.isoformat() if self._last_activity else None
        }
    
    def cleanup(self):
        """상태 정리"""
        self._web_automation = None
        self._is_logging_in = False
        self._current_module = None
        self._module_queue.clear()
        self._last_activity = None
        self._logger.info("상태 정리 완료")

class ModuleFactory:
    """모듈을 만드는 공장 - 모듈 생성 로직 통합"""
    
    # 모듈 정보를 딕셔너리로 관리
    MODULE_INFO = {
        'login': ('modules.login_module', 'LoginModule'),
        'attendance': ('modules.attendance_module', 'AttendanceModule'),
        'quiz': ('modules.quiz_module_new', 'QuizModuleNew'),
        'survey': ('modules.survey_module', 'SurveyModule'),
        'seminar': ('modules.seminar_module', 'SeminarModule'),
        'baemin': ('modules.baemin_module', 'BaeminModule'),
        'points': ('modules.points_check_module', 'PointsCheckModule')
    }
    
    # 간단한 모듈 설정 - 로그인 체크 필요 여부만 관리
    MODULES_REQUIRE_LOGIN = {
        'attendance', 'quiz', 'survey', 'seminar'
    }
    
    @classmethod
    def create_module_class(cls, module_type):
        """모듈 타입에 따라 모듈 클래스 반환"""
        if module_type in cls.MODULE_INFO:
            module_path, module_name = cls.MODULE_INFO[module_type]
            try:
                # 동적으로 모듈 import
                module_class = getattr(__import__(module_path, fromlist=[module_name]), module_name)
                return module_class
            except (ImportError, AttributeError) as e:
                raise ValueError(f"모듈 '{module_type}' 로드 실패: {str(e)}")
        else:
            raise ValueError(f"알 수 없는 모듈 타입: {module_type}")

class TaskManager:
    def __init__(self):
        self.state = TaskManagerState()  # 상태 관리 클래스 사용
        self.logger = logging.getLogger(__name__)
        self._module_cache = {}  # 모듈 클래스 캐시
    
    def initialize_web_automation(self):
        """웹드라이버가 없으면 초기화"""
        if not self.state.web_automation:
            self.state.web_automation = WebAutomation()
        return self.state.web_automation
    
    def create_gui_logger(self, gui_callbacks):
        """통일된 GUI 로거 생성 - 단순화"""
        def gui_log(message):
            # 모듈의 로그를 GUI에 표시
            if 'log_message' in gui_callbacks:
                gui_callbacks['log_message'](message)
        
        return gui_log
    

    def check_login_status(self, gui_callbacks):
        """로그인 상태 체크 공통 로직"""
        if self.state.is_logging_in:
            gui_callbacks['log_message']("로그인 중입니다. 잠시 기다려주세요...")
            self.logger.info("로그인 상태 체크: 이미 로그인 중")
            return False
        return True
    
    def execute_module_in_thread(self, module_class, module_name, gui_callbacks):
        """모듈을 스레드에서 실행하는 공통 메서드"""
        def module_task():
            self.execute_module_safely(module_class, module_name, gui_callbacks)
        
        threading.Thread(target=module_task, daemon=True).start()
        return True
    
    def execute_module_by_config(self, module_type, gui_callbacks):
        """설정 기반으로 모듈 실행 - 단순화"""
        # 유효한 모듈 타입인지 확인
        if module_type not in ModuleFactory.MODULE_INFO:
            self.logger.error(f"알 수 없는 모듈 타입: {module_type}")
            return False
        
        # 로그인이 필요한 모듈인지 확인
        if module_type in ModuleFactory.MODULES_REQUIRE_LOGIN and not self.check_login_status(gui_callbacks):
            return False
        
        # 모듈 클래스 가져오기
        try:
            module_class = self.get_module_class(module_type)
        except ValueError as e:
            self.logger.error(f"모듈 클래스 생성 실패: {str(e)}")
            return False
        
        # 간단한 디스플레이 이름 매핑
        display_names = {
            'login': '로그인',
            'attendance': '출석체크', 
            'quiz': '퀴즈풀기',
            'survey': '설문참여',
            'seminar': '라이브세미나'
        }
        
        # 모듈 실행 (모든 모듈에 동일한 설정 적용)
        return self.execute_module_in_thread(
            module_class, 
            display_names.get(module_type, module_type), 
            gui_callbacks
        )
    
    def execute_module_safely(self, module_class, module_name, gui_callbacks):
        """모듈 실행 공통 로직"""
        try:
            web_auto = self.state.web_automation or self.initialize_web_automation()
            gui_logger = self.create_gui_logger(gui_callbacks)
            
            # 현재 모듈 상태 업데이트
            self.state.current_module = module_name
            
            # 모듈 생성
            module = module_class(web_auto, gui_logger)
            
            # BaseModule을 상속받은 모듈은 자동으로 set_callbacks 사용 가능
            if isinstance(module, BaseModule):
                module.set_callbacks(gui_callbacks)
                # 새로운 콜백 방식을 위한 속성 설정
                module.gui_callbacks = gui_callbacks
                
                # gui_instance가 있으면 모듈에 설정 (로그인과 대시보드 모듈)
                if module_name in ["로그인", "대시보드"] and 'gui_instance' in gui_callbacks and gui_callbacks['gui_instance']:
                    module.gui_instance = gui_callbacks['gui_instance']
                    
            elif hasattr(module, 'set_callbacks'):
                # 기존 방식 지원 (하위 호환성)
                module.set_callbacks(gui_callbacks)
                
                # gui_instance가 있으면 모듈에 설정
                if 'gui_instance' in gui_callbacks and gui_callbacks['gui_instance']:
                    module.gui_instance = gui_callbacks['gui_instance']
            

            
            # 모듈 실행
            result = module.execute()
            
            # 결과 해석 (딕셔너리 또는 불리언 대응)
            is_success = False
            message = ""
            if isinstance(result, dict):
                is_success = result.get('success', False)
                message = result.get('message', '')
                if message:
                    self.logger.info(f"[{module_name}] {message}")
            else:
                is_success = bool(result)
            
            if is_success:
                self.log_success(module_name, gui_callbacks, message)
                self.handle_special_actions(module_name, 'success')
            else:
                self.log_failure(module_name, gui_callbacks, message)
                self.handle_special_actions(module_name, 'failure')
                
        except Exception as e:
            self.log_error(module_name, str(e), gui_callbacks)
            self.handle_special_actions(module_name, 'error')
        finally:
            # 모듈 실행 완료 후 상태 정리
            self.state.current_module = None
    
    def cleanup_web_automation(self):
        """웹드라이버 정리"""
        if self.state.web_automation:
            self.state.web_automation.close_driver()
            self.state.web_automation = None
    
    def execute_login(self, gui_callbacks):
        """로그인 실행"""
        if self.state.is_logging_in:
            gui_callbacks['log_message']("이미 로그인 중입니다. 잠시 기다려주세요...")
            self.logger.info("로그인 실행 시도: 이미 로그인 중")
            return False
        
        self.state.is_logging_in = True
        self.logger.info("로그인 실행 시작")
        
        # 모듈을 큐에 추가
        self.state.add_module_to_queue('login')
        
        # 설정 기반으로 모듈 실행 (하드코딩 제거)
        result = self.execute_module_by_config('login', gui_callbacks)
        
        # 실행 완료 후 큐에서 제거
        if result:
            self.state.remove_module_from_queue('login')
        
        return result
    
    def execute_attendance(self, gui_callbacks):
        """출석체크 실행"""
        # 설정 기반으로 모듈 실행 (하드코딩 제거)
        return self.execute_module_by_config('attendance', gui_callbacks)
    
    def execute_quiz(self, gui_callbacks):
        """퀴즈 풀기 실행"""
        # 설정 기반으로 모듈 실행 (하드코딩 제거)
        return self.execute_module_by_config('quiz', gui_callbacks)
    
    def execute_survey(self, gui_callbacks):
        """설문참여 실행"""
        # 설정 기반으로 모듈 실행 (하드코딩 제거)
        return self.execute_module_by_config('survey', gui_callbacks)
    
    def execute_seminar(self, gui_callbacks):
        """라이브 세미나 정보를 확인하고 다이얼로그를 표시합니다."""
        def _run():
            try:
                self.state.current_module = 'seminar_view'
                module_class = self.get_module_class('seminar')
                web_auto = self.state.web_automation or self.initialize_web_automation()
                gui_logger = self.create_gui_logger(gui_callbacks)
                
                seminar = module_class(web_auto, gui_logger)
                seminar.set_callbacks(gui_callbacks)
                
                gui_callbacks['log_message']("🚀 라이브세미나 정보 수집을 시작합니다...")
                gui_callbacks['update_status']("세미나 정보 수집 중...")
                
                seminars_res = seminar.get_seminar_list()
                if isinstance(seminars_res, dict):
                    seminars = seminars_res.get('data', [])
                else:
                    seminars = seminars_res
                
                if not seminars:
                    gui_callbacks['log_message']("⚠ 세미나 정보를 찾을 수 없습니다.")
                    return

                # UI 스레드에서 다이얼로그 띄우기
                if 'show_seminar_dialog' in gui_callbacks:
                    dialog_callbacks = {
                        'on_apply': lambda checked: self._handle_seminar_batch_action(checked, 'apply', gui_callbacks),
                        'on_cancel': lambda checked: self._handle_seminar_batch_action(checked, 'cancel', gui_callbacks),
                        'on_refresh': lambda: self._handle_seminar_refresh(gui_callbacks),
                        'on_action': lambda link, status: self._handle_seminar_single_action(link, status, gui_callbacks),
                        'log_message': gui_callbacks['log_message']
                    }
                    gui_callbacks['show_seminar_dialog'](seminars, dialog_callbacks)
                
            except Exception as e:
                self.logger.error(f"세미나 확인 오류: {str(e)}")
                if 'log_error' in gui_callbacks:
                    gui_callbacks['log_error'](f"세미나 확인 중 오류: {str(e)}")
            finally:
                self.state.current_module = None
                gui_callbacks['update_status']("대기 중")

        threading.Thread(target=_run, daemon=True).start()
        return True

    def _handle_seminar_batch_action(self, checked_list, action_type, gui_callbacks):
        """세미나 일괄 처리 (신청/취소)"""
        if not checked_list:
            gui_callbacks['log_message']("⚠ 선택된 세미나가 없습니다.")
            return

        def _run():
            try:
                module_class = self.get_module_class('seminar')
                web_auto = self.state.web_automation or self.initialize_web_automation()
                gui_logger = self.create_gui_logger(gui_callbacks)
                seminar = module_class(web_auto, gui_logger)
                seminar.set_callbacks(gui_callbacks)

                success_count = 0
                for i, item in enumerate(checked_list, 1):
                    title = item['title']
                    gui_callbacks['log_message'](f"[{i}/{len(checked_list)}] {title} {action_type} 중...")
                    
                    status_to_send = '신청완료' if action_type == 'cancel' else '신청가능'
                    result = seminar.handle_seminar_action(item['detail_link'], status_to_send)
                    success = result.get('success', False) if isinstance(result, dict) else bool(result)
                    
                    if success:
                        success_count += 1
                        gui_callbacks['log_message'](f"✅ {title} 완료")
                    else:
                        msg = result.get('message', '실패') if isinstance(result, dict) else '실패'
                        gui_callbacks['log_message'](f"❌ {title} {msg}")
                    time.sleep(0.5)

                gui_callbacks['log_message'](f"🎉 일괄 처리 완료! 성공: {success_count}개")
                self._handle_seminar_refresh(gui_callbacks)
            except Exception as e:
                gui_callbacks['log_error'](f"일괄 처리 중 오류: {str(e)}")

        threading.Thread(target=_run, daemon=True).start()

    def _handle_seminar_single_action(self, link, status, gui_callbacks):
        """개별 세미나 액션 처리 (더블클릭)"""
        def _run():
            try:
                module_class = self.get_module_class('seminar')
                web_auto = self.state.web_automation or self.initialize_web_automation()
                gui_logger = self.create_gui_logger(gui_callbacks)
                seminar = module_class(web_auto, gui_logger)
                seminar.set_callbacks(gui_callbacks)

                result = seminar.handle_seminar_action(link, status)
                success = result.get('success', False) if isinstance(result, dict) else bool(result)
                if success:
                    gui_callbacks['log_message']("✅ 작업 완료")
                    self._handle_seminar_refresh(gui_callbacks)
                else:
                    msg = result.get('message', '작업 실패') if isinstance(result, dict) else '작업 실패'
                    gui_callbacks['log_message'](f"❌ {msg}")
            except Exception as e:
                gui_callbacks['log_error'](f"세미나 작업 중 오류: {str(e)}")

        threading.Thread(target=_run, daemon=True).start()

    def _handle_seminar_refresh(self, gui_callbacks):
        """세미나 목록 새로고침"""
        def _run():
            try:
                module_class = self.get_module_class('seminar')
                web_auto = self.state.web_automation or self.initialize_web_automation()
                gui_logger = self.create_gui_logger(gui_callbacks)
                seminar = module_class(web_auto, gui_logger)
                seminar.set_callbacks(gui_callbacks)

                gui_callbacks['log_message']("🔄 세미나 목록을 새로고침합니다...")
                seminars_res = seminar.get_seminar_list()
                if isinstance(seminars_res, dict):
                    seminars = seminars_res.get('data', [])
                else:
                    seminars = seminars_res
                
                if 'update_seminar_dialog' in gui_callbacks:
                    gui_callbacks['update_seminar_dialog'](seminars)
                
            except Exception as e:
                gui_callbacks['log_error'](f"새로고침 중 오류: {str(e)}")

        threading.Thread(target=_run, daemon=True).start()
    
    def get_baemin_info(self, gui_callbacks):
        """배민 쿠폰 구매를 위한 초기 정보(포인트, 번호)를 가져옵니다."""
        try:
            self.state.current_module = 'baemin'
            module_class = self.get_module_class('baemin')
            web_auto = self.state.web_automation or self.initialize_web_automation()
            gui_logger = self.create_gui_logger(gui_callbacks)
            
            baemin = module_class(web_auto, gui_logger)
            baemin.set_callbacks(gui_callbacks)
            
            points_res = baemin.get_current_points()
            if isinstance(points_res, dict):
                points = points_res.get('data', 0)
            else:
                points = points_res
                
            max_coupons = baemin.calculate_max_coupons(points)
            
            phone_res = baemin.get_phone_number()
            if isinstance(phone_res, dict):
                phone = phone_res.get('data', '')
            else:
                phone = phone_res or ''
            
            return {
                'points': points,
                'max_coupons': max_coupons,
                'phone': phone
            }
        except Exception as e:
            self.logger.error(f"배민 정보 조회 오류: {str(e)}")
            raise
        finally:
            self.state.current_module = None

    def execute_baemin_purchase(self, quantity, phone, gui_callbacks):
        """배민 쿠폰 구매를 실행합니다."""
        def _run():
            try:
                self.state.current_module = 'baemin'
                module_class = self.get_module_class('baemin')
                web_auto = self.state.web_automation or self.initialize_web_automation()
                gui_logger = self.create_gui_logger(gui_callbacks)
                
                baemin = module_class(web_auto, gui_logger)
                baemin.set_callbacks(gui_callbacks)
                
                result = baemin.execute(quantity=quantity, phone_number=phone)
                
                is_success = False
                message = ""
                if isinstance(result, dict):
                    is_success = result.get('success', False)
                    message = result.get('message', '')
                else:
                    is_success = bool(result)
                    
                if is_success:
                    self.log_success("배민 쿠폰 구매", gui_callbacks, message)
                else:
                    self.log_failure("배민 쿠폰 구매", gui_callbacks, message)
            except Exception as e:
                self.log_error("배민 쿠폰 구매", str(e), gui_callbacks)
            finally:
                self.state.current_module = None
        
        threading.Thread(target=_run, daemon=True).start()

    def get_seminar_list(self, gui_callbacks):
        """최신 세미나 목록을 수집하여 반환합니다."""
        try:
            self.state.current_module = 'seminar_collect'
            module_class = self.get_module_class('seminar')
            web_auto = self.state.web_automation or self.initialize_web_automation()
            gui_logger = self.create_gui_logger(gui_callbacks)
            
            seminar = module_class(web_auto, gui_logger)
            seminar.set_callbacks(gui_callbacks)
            
            result = seminar.collect_seminar_info_only()
            if isinstance(result, dict):
                return result.get('data', [])
            return result
        except Exception as e:
            self.logger.error(f"세미나 목록 수집 오류: {str(e)}")
            return []
        finally:
            self.state.current_module = None

    def auto_apply_and_refresh_seminars(self, gui_callbacks):
        """세미나 자동 신청 및 목록 새로고침을 수행합니다."""
        try:
            # 이 작업은 백그라운드 스레드에서 실행되므로 직접 클래스 생성
            module_class = self.get_module_class('seminar')
            web_auto = self.state.web_automation or self.initialize_web_automation()
            gui_logger = self.create_gui_logger(gui_callbacks)
            
            seminar = module_class(web_auto, gui_logger)
            seminar.set_callbacks(gui_callbacks)
            
            result = seminar.auto_apply_available_seminars()
            # auto_apply_available_seminars가 튜플 (count, list)을 반환하는지, dict를 반환하는지 처리
            if isinstance(result, dict):
                data = result.get('data', {})
                return data.get('count', 0), data.get('seminars', [])
            return result
        except Exception as e:
            self.logger.error(f"세미나 자동 신청/새로고침 오류: {str(e)}")
            return 0, []

    def auto_enter_seminar(self, link, title, gui_callbacks):
        """특정 세미나에 자동으로 입장합니다."""
        try:
            self.state.current_module = 'auto_enter'
            module_class = self.get_module_class('seminar')
            web_auto = self.state.web_automation or self.initialize_web_automation()
            gui_logger = self.create_gui_logger(gui_callbacks)
            
            # 상대 경로 처리
            full_link = link
            if link.startswith('/'):
                full_link = "https://www.doctorville.co.kr" + link
            
            web_auto.driver.get(full_link)
            time.sleep(2)
            
            seminar = module_class(web_auto, gui_logger)
            seminar.set_callbacks(gui_callbacks)
            
            result = seminar.enter_seminar()
            if isinstance(result, dict):
                return result.get('success', False)
            return bool(result)
        except Exception as e:
            self.logger.error(f"세미나 자동 입장 오류: {str(e)}")
            return False
        finally:
            self.state.current_module = None
    
    def check_scheduled_tasks(self, settings, gui_callbacks):
        """설정된 시간에 맞춰 자동 작업을 실행합니다."""
        try:
            # 브라우저가 준비되지 않았거나 다른 작업이 실행 중이면 건너뛰기
            if self.state.web_automation is None or self.state.current_module is not None:
                return False

            now = datetime.now()
            today = now.date()
            
            # 1. 자동 출석체크 체크
            if settings.get('auto_attendance') and self.state.last_auto_attendance_date != today:
                sch_hour = settings.get('auto_attendance_hour')
                sch_min = settings.get('auto_attendance_min')
                
                # 예약 시간 (오늘)
                scheduled_time = now.replace(hour=sch_hour, minute=sch_min, second=0, microsecond=0)
                
                # 현재 시간이 예약 시간 이후이고, 프로그램 시작 시간 이후인 경우에만 실행
                if now >= scheduled_time and scheduled_time >= self.state.startup_time:
                    gui_callbacks['log_message'](f"⏰ 예약된 자동 출석체크를 시작합니다. (설정시간: {sch_hour:02d}:{sch_min:02d})")
                    gui_callbacks['update_status']("자동 출석체크 중...")
                    self.execute_attendance(gui_callbacks)
                    self.state.last_auto_attendance_date = today
                    return True

            # 2. 자동 퀴즈풀기 체크
            if settings.get('auto_quiz') and self.state.last_auto_quiz_date != today:
                sch_hour = settings.get('auto_quiz_hour')
                sch_min = settings.get('auto_quiz_min')
                
                # 예약 시간 (오늘)
                scheduled_time = now.replace(hour=sch_hour, minute=sch_min, second=0, microsecond=0)
                
                # 현재 시간이 예약 시간 이후이고, 프로그램 시작 시간 이후인 경우에만 실행
                if now >= scheduled_time and scheduled_time >= self.state.startup_time:
                    gui_callbacks['log_message'](f"⏰ 예약된 자동 퀴즈풀기를 시작합니다. (설정시간: {sch_hour:02d}:{sch_min:02d})")
                    gui_callbacks['update_status']("자동 퀴즈풀기 중...")
                    self.execute_quiz(gui_callbacks)
                    self.state.last_auto_quiz_date = today
                    return True
            
            return False
            
        except Exception as e:
            if 'log_error' in gui_callbacks:
                gui_callbacks['log_error'](f"스케줄 작업 체크 중 오류: {str(e)}")
            return False
    
    def get_module_class(self, module_type):
        """모듈 클래스 캐시에서 가져오기 - 성능 최적화"""
        if module_type not in self._module_cache:
            # 캐시에 없으면 새로 생성하고 저장
            try:
                self._module_cache[module_type] = ModuleFactory.create_module_class(module_type)
                self.logger.debug(f"모듈 클래스 캐시에 추가: {module_type}")
            except ValueError as e:
                self.logger.error(f"모듈 클래스 생성 실패: {str(e)}")
                raise
        
        return self._module_cache[module_type]
    
    def log_success(self, module_name, gui_callbacks, custom_message=""):
        """성공 로깅 - 일관된 방식"""
        message = custom_message if custom_message else f"{module_name} 완료"
        gui_callbacks['log_and_update_status'](message, message)
        self.logger.info(message)
    
    def log_failure(self, module_name, gui_callbacks, custom_message=""):
        """실패 로깅 - 일관된 방식"""
        message = custom_message if custom_message else f"{module_name} 실패"
        gui_callbacks['log_and_update_status'](message, message)
        self.logger.warning(message)
    
    def log_error(self, module_name, error_msg, gui_callbacks):
        """오류 로깅 - 일관된 방식"""
        message = f"{module_name} 오류: {error_msg}"
        gui_callbacks['log_and_update_status'](message, message)
        self.logger.error(f"모듈 실행 오류: {module_name} - {error_msg}")
    
    def handle_special_actions(self, module_name, action_type):
        """모듈별 특별 액션 처리 - 한 곳에서 관리"""
        if module_name == "로그인":
            if action_type == 'success':
                self.state.is_logging_in = False
                self.logger.info("로그인 성공 - 로그인 상태 해제")
            elif action_type == 'failure':
                self.cleanup_web_automation()
                self.state.is_logging_in = False
                self.logger.warning("로그인 실패 - 웹드라이버 정리 및 로그인 상태 해제")
            elif action_type == 'error':
                self.cleanup_web_automation()
                self.state.is_logging_in = False
                self.logger.error("로그인 오류 - 웹드라이버 정리 및 로그인 상태 해제")
    
    def cleanup(self):
        """프로그램 종료 시 정리 작업"""
        try:
            self.cleanup_web_automation()
            self.state.cleanup()  # 상태도 함께 정리
            
            # 캐시 정리
            self._module_cache.clear()
            
            self.logger.info("모든 캐시 정리 완료")
        except Exception as e:
            # 백그라운드 정리 중 오류는 무시
            pass
    
    def get_status_summary(self):
        """현재 상태 요약 반환"""
        return self.state.get_status_summary()
    
    def get_cache_info(self):
        """캐시 정보 반환 - 성능 모니터링용"""
        return {
            'module_cache_size': len(self._module_cache),
            'cached_modules': list(self._module_cache.keys())
        }
