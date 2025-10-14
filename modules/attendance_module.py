# -*- coding: utf-8 -*-
"""
출석체크 모듈
닥터빌 출석체크 기능을 담당합니다.
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_module import BaseModule

# URL 상수 정의
ATTENDANCE_PAGE_URL = "https://www.doctorville.co.kr/event/attend"

# CSS 선택자 상수 정의
ATTEND_BUTTON_CLASS = "point_down"
SUCCESS_POPUP_ID = "popSuccessArea"

# 대기 시간 상수 정의
DEFAULT_IMPLICIT_WAIT = 5

# 에러 메시지 상수 정의
ERROR_WEBDRIVER_NOT_INITIALIZED = "웹드라이버가 초기화되지 않았습니다."
ERROR_ATTENDANCE_PAGE_NAVIGATION = "출석체크 페이지 이동 실패"
ERROR_ATTEND_BUTTON_CLICK = "출석하기 버튼 클릭 실패"
ERROR_ATTENDANCE_EXECUTION = "출석체크 실행 중 오류 발생"

class AttendanceModule(BaseModule):
    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
    
    def execute(self):
        """출석체크 페이지로 이동하고 포인트 받기 버튼 클릭"""
        try:
            if not self.web_automation.driver:
                self.log_error(ERROR_WEBDRIVER_NOT_INITIALIZED)
                return False
            
            self.log_info("출석체크 페이지로 이동 중...")
            
            # 출석체크 페이지로 이동
            if not self._navigate_to_attendance_page():
                return False
            
            # 출석하기 버튼 클릭
            if not self.click_attend_button():
                return False
            
            # 출석체크 완료
            self.log_info("출석체크 완료!")
            
            # 출석체크 후 자동으로 포인트 상태 확인
            self._check_points_after_attendance()
            
            return True
            
        except Exception as e:
            self.log_error(f"{ERROR_ATTENDANCE_EXECUTION}: {str(e)}")
            return False
    
    def _navigate_to_attendance_page(self):
        """출석체크 페이지로 이동"""
        try:
            self.web_automation.driver.get(ATTENDANCE_PAGE_URL)
            self.web_automation.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self.log_info("출석체크 페이지 로딩 완료")
            return True
        except Exception as e:
            self.log_error(f"{ERROR_ATTENDANCE_PAGE_NAVIGATION}: {str(e)}")
            return False
    
    def click_attend_button(self):
        """출석하기 버튼 클릭 또는 이미 완료된 경우 확인"""
        try:
            self.log_info("출석하기 버튼 찾는 중...")
            
            # 암시적 대기를 일시적으로 0으로 설정 (즉시 검색)
            self.web_automation.driver.implicitly_wait(0)
            
            try:
                # 출석하기 버튼을 즉시 찾기
                button = self.web_automation.driver.find_element(By.CLASS_NAME, ATTEND_BUTTON_CLASS)
                self.log_info("출석하기 버튼 발견")
                
                # 버튼 클릭
                button.click()
                self.log_info("출석하기 버튼 클릭 완료")
                
                # 성공 팝업 확인
                self._check_success_popup()
                
                return True
                
            except NoSuchElementException:
                self.log_info("출석하기 버튼을 찾을 수 없습니다. (이미 출석체크 완료되었을 수 있습니다)")
                # 이미 완료된 경우에도 True 반환 (포인트 확인을 위해)
                return True
            finally:
                # 원래 암시적 대기 시간으로 복원 (config.py의 값)
                self.web_automation.driver.implicitly_wait(DEFAULT_IMPLICIT_WAIT)
            
        except Exception as e:
            self.log_error(f"{ERROR_ATTEND_BUTTON_CLICK}: {str(e)}")
            return False
    
    def _check_success_popup(self):
        """성공 팝업 확인"""
        try:
            self.web_automation.wait.until(EC.visibility_of_element_located((By.ID, SUCCESS_POPUP_ID)))
            self.log_info("출석체크 성공! 포인트가 적립되었습니다.")
        except TimeoutException:
            self.log_info("출석체크 완료 (성공 팝업 확인 불가)")
    
    def _check_points_after_attendance(self):
        """출석체크 후 포인트 상태 확인 - BaseModule의 공통 메서드 사용"""
        self.check_points_after_activity()
    
    # 중복된 _log 메서드 제거 - BaseModule의 log_info 사용
