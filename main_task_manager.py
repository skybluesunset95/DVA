# -*- coding: utf-8 -*-
"""
닥터빌 자동화 프로그램 - Task Manager
기능 실행 로직을 담당합니다.
"""

import threading
import logging
from datetime import datetime
from web_automation import WebAutomation
from modules.base_module import BaseModule

class TaskManagerState:
    """TaskManager 상태를 체계적으로 관리하는 클래스"""
    
    def __init__(self):
        self._web_automation = None
        self._is_logging_in = False
        self._current_module = None
        self._module_queue = []
        self._last_activity = None
        self._logger = logging.getLogger(__name__)
    
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
        'seminar': ('modules.seminar_module', 'SeminarModule')
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
            

            
            if module.execute():
                self.log_success(module_name, gui_callbacks)
                self.handle_special_actions(module_name, 'success')
                
                # 로그인 성공 시에는 LoginModule에서 자동으로 포인트 체크 수행
                # (출석체크와 동일한 방식으로 깔끔하게 처리)
                
            else:
                self.log_failure(module_name, gui_callbacks)
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
        """라이브세미나 확인 실행"""
        # 설정 기반으로 모듈 실행 (하드코딩 제거)
        return self.execute_module_by_config('seminar', gui_callbacks)
    
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
    
    def log_success(self, module_name, gui_callbacks):
        """성공 로깅 - 일관된 방식"""
        message = f"{module_name} 완료"
        gui_callbacks['log_and_update_status'](message, message)
        self.logger.info(f"모듈 실행 성공: {module_name}")
    
    def log_failure(self, module_name, gui_callbacks):
        """실패 로깅 - 일관된 방식"""
        message = f"{module_name} 실패"
        gui_callbacks['log_and_update_status'](message, message)
        self.logger.warning(f"모듈 실행 실패: {module_name}")
    
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
