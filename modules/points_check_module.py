# -*- coding: utf-8 -*-
"""
포인트 확인 모듈
출석체크와 퀴즈풀기 완료 후 포인트 변화를 확인합니다.
"""

from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from modules.base_module import BaseModule, STATUS_ATTENDANCE_COMPLETE, STATUS_ATTENDANCE_INCOMPLETE, STATUS_QUIZ_COMPLETE, STATUS_QUIZ_INCOMPLETE, STATUS_KEY_ATTENDANCE, STATUS_KEY_QUIZ
from selenium.common.exceptions import TimeoutException

# URL 상수 정의
POINTS_PAGE_URL = "https://www.doctorville.co.kr/my/point/pointUseHistoryList"
MAIN_PAGE_URL = "https://www.doctorville.co.kr/my/main"

# CSS 선택자 상수 정의
POINTS_BOX_SELECTOR = ".box_point"
POINTS_VALUE_SELECTOR = ".box_point .point em"
USER_INFO_SELECTOR = ".myinfo"
USER_NAME_SELECTOR = ".myinfo .txt_blue"
POINT_HISTORY_ROWS_SELECTOR = "tbody tr.tr_add"
DATE_CELL_SELECTOR = "td.date"
CONTENT_CELL_SELECTOR = "td:nth-child(3)"

# 활동 타입 상수 정의
ACTIVITY_TYPE_ATTENDANCE = "출석체크"
ACTIVITY_TYPE_QUIZ = "퀴즈"

# 날짜 형식 상수 정의
DATE_FORMAT = "%Y.%m.%d"
CACHE_DURATION_MINUTES = 5

# 에러 메시지 상수 정의
ERROR_POINTS_CHECK_FAILED = "포인트 확인 실패"
ERROR_ACTIVITY_SUMMARY_FAILED = "활동 요약 수집 실패"
ERROR_USER_INFO_FAILED = "사용자 정보 요약 수집 실패"
ERROR_GUI_UPDATE_FAILED = "GUI 업데이트 실패"
ERROR_UNKNOWN_ACTIVITY = "알 수 없는 활동 타입"

class PointsCheckModule(BaseModule):
    """
    닥터빌 포인트 확인 모듈
    
    주요 기능:
    - 사용자 정보 수집 (이름, 포인트)
    - 출석체크 및 퀴즈 참여 상태 확인
    - GUI 대시보드 자동 업데이트
    
    성능 최적화:
    - 페이지 이동 최소화 (메인 페이지에서 포인트 정보도 수집)
    - 적응적 대기 시간 (기본 대기 실패 시 재시도)
    - 일관된 에러 처리 및 사용자 친화적 메시지
    """
    
    def __init__(self, web_automation, gui_logger=None):
        """
        PointsCheckModule 초기화
        
        Args:
            web_automation: 웹 자동화 인스턴스
            gui_logger: GUI 로깅 함수
        """
        super().__init__(web_automation, gui_logger)
    
    def _get_today_date(self):
        """오늘 날짜를 표준 형식으로 반환"""
        return datetime.now().strftime(DATE_FORMAT)
    
    def _update_gui_directly(self, result):
        """GUI 업데이트 - 직접 접근 방식으로 단순화"""
        try:
            # gui_instance를 통해 직접 업데이트
            if hasattr(self, 'gui_instance') and self.gui_instance:
                gui = self.gui_instance
                
                # 사용자 이름 업데이트
                if hasattr(gui, 'update_user_info'):
                    gui.update_user_info(result['user_name'])
                
                # 포인트, 출석체크, 퀴즈 상태 업데이트
                if hasattr(gui, 'update_display'):
                    gui.update_display('points', result['points'])
                    gui.update_display(STATUS_KEY_ATTENDANCE, result[STATUS_KEY_ATTENDANCE])
                    gui.update_display(STATUS_KEY_QUIZ, result[STATUS_KEY_QUIZ])
                
                self.log_info("✅ GUI 업데이트 완료!")
                return
            
            # gui_instance가 없는 경우
            self.log_info("⚠ GUI 인스턴스가 설정되지 않았습니다")
                
        except Exception as e:
            self.log_info(f"GUI 업데이트 실패: {str(e)}")
    
    def get_user_info_summary(self):
        """사용자 정보 수집 - 메인 진입점"""
        try:
            self.log_info("📊 사용자 정보 수집 시작...")
            
            # 1단계: 메인 페이지에서 사용자 이름만 수집
            user_name = self._get_user_name_from_main()
            
            # 2단계: 포인트 페이지에서 포인트+활동상태 모두 수집
            points_data = self._get_points_and_activities()
            
            # 3단계: 결과 합치기
            result = {
                'user_name': user_name,
                'points': points_data['points'],
                'attendance_status': points_data[STATUS_KEY_ATTENDANCE],
                'quiz_status': points_data[STATUS_KEY_QUIZ]
            }
            
            self.log_info(f"📋 최종 결과: {result}")
            
            # 4단계: GUI 업데이트
            self._update_gui_directly(result)
            
            return result
            
        except Exception as e:
            self.log_info(f"{ERROR_USER_INFO_FAILED}: {str(e)}")
            return None
    
    def _get_user_name_from_main(self):
        """메인 페이지에서 사용자 이름만 수집"""
        try:
            self.log_info("🏠 메인 페이지에서 사용자 이름 수집 중...")
            
            # 메인 페이지로 이동
            self.web_automation.driver.get(MAIN_PAGE_URL)
            
            # 페이지 로딩 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, USER_INFO_SELECTOR)))
            
            # 사용자 이름 추출
            user_info_element = self.web_automation.driver.find_element(By.CSS_SELECTOR, USER_INFO_SELECTOR)
            user_name_element = user_info_element.find_element(By.CSS_SELECTOR, USER_NAME_SELECTOR)
            user_name = user_name_element.text.strip()
            
            # "님," "님" 제거
            if user_name.endswith("님,"):
                user_name = user_name[:-2]
            elif user_name.endswith("님"):
                user_name = user_name[:-1]
            
            self.log_info(f"👤 사용자 이름: {user_name}")
            return user_name
            
        except Exception as e:
            self.log_info(f"❌ 메인 페이지에서 사용자 이름 수집 실패: {e}")
            return "사용자"
    
    def _get_points_and_activities(self):
        """포인트 페이지에서 포인트+활동상태 모두 수집"""
        try:
            self.log_info("💰 포인트 페이지에서 정보 수집 중...")
            
            # 포인트 페이지로 이동
            self.web_automation.driver.get(POINTS_PAGE_URL)
            self.web_automation.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, POINTS_BOX_SELECTOR)))
            
            # 포인트 정보 수집
            try:
                points_element = self.web_automation.driver.find_element(By.CSS_SELECTOR, POINTS_VALUE_SELECTOR)
                current_points = points_element.text.strip()
                self.log_info(f"💰 현재 포인트: {current_points}P")
            except NoSuchElementException:
                current_points = "0"
                self.log_info("⚠️ 포인트 정보를 찾을 수 없음")
            
            # 오늘 활동 상태 확인
            today = self._get_today_date()
            attendance_done = self._check_today_activity("출석체크", today)
            quiz_done = self._check_today_activity("퀴즈", today)
            
            return {
                'points': current_points,
                STATUS_KEY_ATTENDANCE: STATUS_ATTENDANCE_COMPLETE if attendance_done else STATUS_ATTENDANCE_INCOMPLETE,
                STATUS_KEY_QUIZ: STATUS_QUIZ_COMPLETE if quiz_done else STATUS_QUIZ_INCOMPLETE
            }
            
        except Exception as e:
            self.log_info(f"❌ 포인트 페이지 정보 수집 실패: {e}")
            return {
                'points': "0",
                STATUS_KEY_ATTENDANCE: STATUS_ATTENDANCE_INCOMPLETE,
                STATUS_KEY_QUIZ: STATUS_QUIZ_INCOMPLETE
            }
    
    def _check_today_activity(self, activity_type_key, today):
        """오늘 활동 여부 확인"""
        try:
            rows = self.web_automation.driver.find_elements(By.CSS_SELECTOR, POINT_HISTORY_ROWS_SELECTOR)
            
            for row in rows:
                try:
                    date_text = row.find_element(By.CSS_SELECTOR, DATE_CELL_SELECTOR).text.strip()
                    content_text = row.find_element(By.CSS_SELECTOR, CONTENT_CELL_SELECTOR).text.strip()
                    
                    if date_text == today and activity_type_key in content_text:
                        self.log_info(f"🎉 {activity_type_key} 활동 발견!")
                        return True
                        
                except NoSuchElementException:
                    continue
            
            self.log_info(f"❌ {activity_type_key} 활동을 찾을 수 없습니다.")
            return False
            
        except Exception as e:
            self.log_info(f"❌ {activity_type_key} 활동 확인 중 오류: {str(e)}")
            return False
