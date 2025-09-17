# -*- coding: utf-8 -*-
"""
설문참여 모듈
닥터빌 세미나 설문참여 기능을 담당합니다.
"""

import threading
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_module import BaseModule

# URL 상수 정의
VOD_LIST_PAGE_URL = "https://www.doctorville.co.kr/seminar/seminarVodReplayList?categoryCd=&metaCd=&sort=apply&query="

# CSS 선택자 상수 정의
LIVE_LIST_CONTAINER_SELECTOR = ".live_list .list_cont"
FIRST_SEMINAR_LINK_SELECTOR = ".live_list .list_cont:first-child a.list_detail"
SEMINAR_TITLE_SELECTOR = ".tit"
REENTER_BUTTON_SELECTOR = ".btn_bn.btn_enter.btn_seminar_agree"

# 에러 메시지 상수 정의
ERROR_FIRST_SEMINAR_SELECTION = "첫 번째 세미나 자동 선택 실패"
ERROR_REENTER_BUTTON_CLICK = "재입장하기 버튼 클릭 실패"
ERROR_SURVEY_PAGE_NAVIGATION = "설문참여 페이지 이동 중 오류"
ERROR_SURVEY_BUTTON_CLICK = "설문참여 버튼 클릭 실패"

class SurveyModule(BaseModule):
    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
    
    def execute(self):
        """설문참여 페이지로 이동하고 첫 번째 세미나 자동 선택"""
        try:
            if not self.web_automation or not self.web_automation.driver:
                if self.gui_logger:
                    self.log_info("웹드라이버가 초기화되지 않았습니다. 먼저 로그인해주세요.")
                return False
            
            if self.gui_logger:
                self.log_info("설문참여 페이지로 이동합니다...")
            
            # VOD 목록 페이지로 이동
            self.web_automation.driver.get(VOD_LIST_PAGE_URL)
            
            if self.gui_logger:
                self.log_info("설문참여 페이지로 이동 완료")
            
            # 🔥 첫 번째 세미나 자동 클릭
            if self.gui_logger:
                self.log_info("첫 번째 세미나를 자동으로 선택합니다...")
            
            def auto_click_seminar():
                try:
                    # 페이지 로딩 완료 대기 (세미나 목록이 나타날 때까지)
                    self.web_automation.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, LIVE_LIST_CONTAINER_SELECTOR))
                    )
                    
                    # 세미나 목록 가져오기
                    seminar_list = self.web_automation.driver.find_elements(
                        By.CSS_SELECTOR, 
                        ".live_list .list_cont a.list_detail"
                    )
                    
                    if not seminar_list:
                        if self.gui_logger:
                            self.gui_logger("❌ 세미나 목록을 찾을 수 없습니다")
                        return
                    
                    # 첫 번째 세미나 시도
                    if self.gui_logger:
                        self.log_info("첫 번째 세미나를 시도합니다...")
                    
                    first_seminar = seminar_list[0]
                    seminar_title = first_seminar.find_element(By.CSS_SELECTOR, SEMINAR_TITLE_SELECTOR).text.strip()
                    
                    if self.gui_logger:
                        self.gui_logger(f"첫 번째 세미나 발견: {seminar_title}")
                    
                    # 링크 클릭
                    first_seminar.click()
                    
                    if self.gui_logger:
                        self.log_info("✅ 첫 번째 세미나 자동 선택 완료")
                        self.log_info("재입장하기 버튼을 찾는 중...")
                    
                    # 🔥 재입장하기 버튼 자동 클릭
                    if not self.auto_click_reenter_button():
                        # 첫 번째 세미나에 재입장 버튼이 없으면 두 번째 세미나 시도
                        if len(seminar_list) >= 2:
                            if self.gui_logger:
                                self.log_info("첫 번째 세미나에 재입장 버튼이 없습니다. 두 번째 세미나를 시도합니다...")
                            
                            # 뒤로가기
                            self.web_automation.driver.back()
                            time.sleep(2)  # 페이지 로딩 대기
                            
                            # 두 번째 세미나 클릭
                            second_seminar = seminar_list[1]
                            seminar_title = second_seminar.find_element(By.CSS_SELECTOR, SEMINAR_TITLE_SELECTOR).text.strip()
                            
                            if self.gui_logger:
                                self.gui_logger(f"두 번째 세미나 발견: {seminar_title}")
                            
                            second_seminar.click()
                            
                            if self.gui_logger:
                                self.log_info("✅ 두 번째 세미나 자동 선택 완료")
                                self.log_info("재입장하기 버튼을 찾는 중...")
                            
                            # 두 번째 세미나에서도 재입장 버튼 확인
                            if not self.auto_click_reenter_button():
                                if self.gui_logger:
                                    self.gui_logger("두 번째 세미나에도 재입장 버튼이 없습니다. 포인트 확인을 진행합니다...")
                                self._run_points_check_module()
                        else:
                            if self.gui_logger:
                                self.gui_logger("두 번째 세미나가 없습니다. 포인트 확인을 진행합니다...")
                            self._run_points_check_module()
                    
                except Exception as e:
                    if self.gui_logger:
                        self.gui_logger(f"❌ {ERROR_FIRST_SEMINAR_SELECTION}: {str(e)}")
            
            # 백그라운드에서 실행
            threading.Thread(target=auto_click_seminar, daemon=True).start()
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"{ERROR_SURVEY_PAGE_NAVIGATION}: {str(e)}")
            return False
    
    def auto_click_reenter_button(self):
        """재입장하기 버튼을 자동으로 클릭합니다."""
        try:
            if self.gui_logger:
                self.log_info("재입장하기 버튼 검색 중...")
            
            # 재입장하기 버튼이 있는지 먼저 확인 (타임아웃 2초로 단축)
            try:
                # 페이지 로딩 대기 (재입장하기 버튼이 나타날 때까지)
                WebDriverWait(self.web_automation.driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, REENTER_BUTTON_SELECTOR))
                )
                
                # 재입장하기 버튼 찾기
                reenter_button = self.web_automation.driver.find_element(
                    By.CSS_SELECTOR, 
                    REENTER_BUTTON_SELECTOR
                )
                
                if self.gui_logger:
                    self.log_info("재입장하기 버튼 발견")
                
                # 버튼 클릭
                reenter_button.click()
                
                if self.gui_logger:
                    self.log_info("✅ 재입장하기 버튼 자동 클릭 완료")
                    self.log_info("새로운 팝업 창에서 설문참여 버튼을 찾는 중...")
                
                # 🔥 새로운 팝업 창에서 설문참여 버튼 자동 클릭
                self.auto_click_survey_in_popup()
                
                return True
                
            except TimeoutException:
                # 재입장하기 버튼이 없는 경우 (이미 설문 완료)
                if self.gui_logger:
                    self.log_info("⚠ 재입장하기 버튼이 없습니다. 이미 설문이 완료되었거나 참여할 설문이 없습니다.")
                return False
                
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ {ERROR_REENTER_BUTTON_CLICK}: {str(e)}")
            return False
    
    def auto_click_survey_in_popup(self):
        """새로운 팝업 창에서 설문참여 버튼을 자동으로 클릭합니다."""
        try:
            if self.gui_logger:
                self.log_info("새로운 팝업 창 대기 중...")
            
            # 새로운 팝업 창이 열릴 때까지 대기
            import time
            time.sleep(2)  # 팝업 창 로딩 대기
            
            # 현재 열려있는 모든 창 핸들 가져오기
            original_window = self.web_automation.driver.current_window_handle
            all_windows = self.web_automation.driver.window_handles
            
            # 새로 열린 팝업 창 찾기
            popup_window = None
            for window in all_windows:
                if window != original_window:
                    popup_window = window
                    break
            
            if not popup_window:
                if self.gui_logger:
                    self.log_info("❌ 새로운 팝업 창을 찾을 수 없습니다")
                return False
            
            # 팝업 창으로 전환
            self.web_automation.driver.switch_to.window(popup_window)
            
            if self.gui_logger:
                self.log_info("팝업 창으로 전환 완료")
                self.log_info("설문참여 버튼 검색 중...")
            
            # 페이지 로딩 대기 (설문참여 버튼이 나타날 때까지)
            self.web_automation.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#surveyEnter"))
            )
            
            # 설문참여 버튼 찾기
            survey_button = self.web_automation.driver.find_element(
                By.CSS_SELECTOR, 
                "#surveyEnter"
            )
            
            if self.gui_logger:
                self.log_info("설문참여 버튼 발견")
            
            # 버튼 클릭
            survey_button.click()
            
            if self.gui_logger:
                self.log_info("✅ 설문참여 버튼 자동 클릭 완료")
                self.log_info("개인정보 동의 팝업에서 설문하기 버튼을 찾는 중...")
            
            # 🔥 개인정보 동의 팝업에서 설문하기 버튼 자동 클릭
            self.auto_click_survey_button_in_agree_popup()
            
            # 원래 창으로 돌아가기
            self.web_automation.driver.switch_to.window(original_window)
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ 팝업 창에서 설문참여 버튼 클릭 실패: {str(e)}")
            
            # 오류 발생 시 원래 창으로 돌아가기
            try:
                self.web_automation.driver.switch_to.window(original_window)
            except:
                pass
            
            return False
    
    def auto_click_survey_button_in_agree_popup(self):
        """개인정보 동의 팝업에서 설문하기 버튼을 자동으로 클릭합니다."""
        try:
            if self.gui_logger:
                self.log_info("개인정보 동의 팝업 대기 중...")
            
            # 개인정보 동의 팝업이 나타날 때까지 대기
            self.web_automation.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#agreeInfo"))
            )
            
            if self.gui_logger:
                self.log_info("개인정보 동의 팝업 발견")
                self.log_info("동의 체크박스 자동 체크 중...")
            
            # 동의 체크박스 자동 체크
            try:
                agree_checkbox = self.web_automation.driver.find_element(
                    By.CSS_SELECTOR, 
                    "#agreeInfo #agree"
                )
                
                # 체크박스가 체크되지 않은 경우에만 체크
                if not agree_checkbox.is_selected():
                    agree_checkbox.click()
                    if self.gui_logger:
                        self.log_info("✅ 동의 체크박스 자동 체크 완료")
                else:
                    if self.gui_logger:
                        self.log_info("동의 체크박스가 이미 체크되어 있습니다")
                        
            except Exception as e:
                if self.gui_logger:
                    self.gui_logger(f"⚠ 동의 체크박스 처리 중 오류: {str(e)}")
            
            # 설문하기 버튼 찾기 및 클릭
            if self.gui_logger:
                self.log_info("설문하기 버튼 검색 중...")
            
            # 페이지 로딩 대기 (설문하기 버튼이 나타날 때까지)
            self.web_automation.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#agreeInfo .btn_answer"))
            )
            
            # 설문하기 버튼 찾기
            survey_button = self.web_automation.driver.find_element(
                By.CSS_SELECTOR, 
                "#agreeInfo .btn_answer"
            )
            
            if self.gui_logger:
                self.log_info("설문하기 버튼 발견")
            
            # 버튼 클릭
            survey_button.click()
            
            if self.gui_logger:
                self.log_info("✅ 설문하기 버튼 자동 클릭 완료")
                self.log_info("설문 페이지로 이동 중...")
                self.log_info("새로운 설문 창에서 자동 답변을 시작합니다...")
            
            # 🔥 새로운 설문 창에서 자동 답변 및 제출
            self.auto_fill_and_submit_survey()
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ 개인정보 동의 팝업에서 설문하기 버튼 클릭 실패: {str(e)}")
            return False
    
    def auto_fill_and_submit_survey(self):
        """새로운 설문 창에서 모든 질문의 첫 번째 보기를 자동 선택하고 제출합니다."""
        try:
            if self.gui_logger:
                self.log_info("새로운 설문 창 대기 중...")
            
            # 새로운 설문 창이 열릴 때까지 대기
            import time
            time.sleep(3)  # 설문 창 로딩 대기 (1초 → 3초로 증가)
            
            # 현재 열려있는 모든 창 핸들 가져오기
            original_window = self.web_automation.driver.current_window_handle
            all_windows = self.web_automation.driver.window_handles
            
            # 새로 열린 설문 창 찾기
            survey_window = None
            for window in all_windows:
                if window != original_window:
                    # 설문 창인지 확인 (URL에 survey.villeway.com이 포함된 창)
                    try:
                        self.web_automation.driver.switch_to.window(window)
                        if "survey.villeway.com" in self.web_automation.driver.current_url:
                            survey_window = window
                            break
                    except:
                        continue
            
            if not survey_window:
                if self.gui_logger:
                    self.log_info("❌ 새로운 설문 창을 찾을 수 없습니다")
                return False
            
            if self.gui_logger:
                self.log_info("설문 창으로 전환 완료")
                self.log_info("설문 페이지 로딩 대기 중...")
            
            # 설문 페이지 로딩 완료 대기
            self.web_automation.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form[id^='surveyForm']"))
            )
            
            if self.gui_logger:
                self.log_info("설문 페이지 로딩 완료")
                self.log_info("여러 페이지 설문 처리 시작...")
            
            # 🔥 팝업 확인 및 처리
            self.handle_survey_popup()
            
            # 🔥 여러 페이지 설문 처리 (간단한 방식)
            page_count = 1
            
            while True:
                if self.gui_logger:
                    self.log_info(f"=== {page_count}페이지 처리 중 ===")
                
                # 현재 페이지에서 문제 순서대로 하나씩 처리
                self.auto_fill_questions_in_order()
                
                # 🔥 모든 필수 항목이 제대로 채워졌는지 확인
                if not self.validate_required_fields():
                    if self.gui_logger:
                        self.gui_logger("❌ 필수 항목이 모두 채워지지 않았습니다. 재시도합니다...")
                    
                    # 재시도: 안 채워진 부분만 다시 채우기
                    if not self.retry_fill_missing_fields():
                        if self.gui_logger:
                            self.gui_logger("❌ 재시도 후에도 필수 항목이 채워지지 않았습니다. 설문 제출을 중단합니다.")
                        return False
                    else:
                        if self.gui_logger:
                            self.gui_logger("✅ 재시도 후 모든 필수 항목이 채워졌습니다.")
                
                if self.gui_logger:
                    self.log_info(f"{page_count}페이지 답변 완료")
                
                # 페이지 하단 버튼 확인
                try:
                    footer_button = self.web_automation.driver.find_element(
                        By.CSS_SELECTOR, 
                        'footer input[type="submit"][value="다음"], footer input[type="submit"][value="제출하기"]'
                    )
                    
                    # 버튼 텍스트 확인
                    button_text = footer_button.get_attribute('value') or footer_button.text
                    
                    if self.gui_logger:
                        self.log_info(f"페이지 하단 버튼 발견: {button_text}")
                    
                    if "다음" in button_text:
                        # 다음 버튼 클릭
                        if self.gui_logger:
                            self.log_info("다음 버튼 클릭, 다음 페이지로 이동...")
                        
                        footer_button.click()
                        
                        # 다음 페이지 로딩 대기
                        time.sleep(2)
                        
                        # 다음 페이지에서 답변할 수 있도록 대기
                        try:
                            self.web_automation.wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "form[id^='surveyForm']"))
                            )
                        except TimeoutException:
                            if self.gui_logger:
                                self.log_info("⚠ 다음 페이지 로딩 대기 시간 초과, 계속 진행...")
                        
                        page_count += 1
                        
                    elif "제출하기" in button_text:
                        # 제출 버튼 클릭
                        if self.gui_logger:
                            self.log_info("제출하기 버튼 발견, 설문 제출 중...")
                        
                        footer_button.click()
                        
                        if self.gui_logger:
                            self.log_info("✅ 설문 제출 완료!")
                        
                        break  # 반복문 종료
                        
                    else:
                        # 예상하지 못한 버튼
                        if self.gui_logger:
                            self.log_info(f"⚠ 예상하지 못한 버튼: {button_text}")
                        break
                        
                except NoSuchElementException:
                    if self.gui_logger:
                        self.log_info("❌ 페이지 하단 버튼을 찾을 수 없습니다")
                    break
                except Exception as e:
                    if self.gui_logger:
                        self.log_info(f"⚠ 버튼 처리 중 오류: {str(e)}")
                    break
            
            if self.gui_logger:
                self.log_info(f"총 {page_count}페이지 처리 완료")
            
            # 확인 팝업 처리
            self._handle_submit_confirmation_popup()
            
            # 원래 창으로 돌아가기
            self.web_automation.driver.switch_to.window(original_window)
            
            # 설문 완료 후 포인트 확인 모듈 실행
            self._run_points_check_module()
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ 설문 자동 답변 및 제출 실패: {str(e)}")
            
            # 오류 발생 시 원래 창으로 돌아가기
            try:
                self.web_automation.driver.switch_to.window(original_window)
            except:
                pass
            
            return False
    
    def handle_survey_popup(self):
        """설문 시작 시 나타날 수 있는 팝업을 처리합니다."""
        try:
            if self.gui_logger:
                self.log_info("설문 시작 팝업 확인 중...")
            
            # 팝업이 나타날 때까지 동적 대기
            try:
                popup_container = self.web_automation.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#headlessui-portal-root"))
                )
                
                if self.gui_logger:
                    self.log_info("팝업 발견, 닫기 버튼 검색 중...")
                
                # 팝업 내부에 "닫기" 버튼이 있는지 확인 (XPath 사용)
                try:
                    close_button = popup_container.find_element(
                        By.XPATH, 
                        './/button[contains(text(), "닫기")]'
                    )
                    
                    if close_button:
                        if self.gui_logger:
                            self.log_info("설문 시작 팝업 발견, 닫기 버튼 클릭 중...")
                        
                        # 닫기 버튼 클릭
                        close_button.click()
                        
                        if self.gui_logger:
                            self.log_info("✅ 설문 시작 팝업 닫기 완료")
                        
                        # 팝업이 사라질 때까지 짧게 대기
                        time.sleep(0.5)
                        
                except NoSuchElementException:
                    # "닫기" 텍스트가 없는 경우, btn-primary 클래스를 가진 버튼 찾기
                    try:
                        close_button = popup_container.find_element(
                            By.CSS_SELECTOR, 
                            'button.btn-primary'
                        )
                        
                        if close_button:
                            if self.gui_logger:
                                self.log_info("팝업 버튼 발견 (btn-primary), 클릭 중...")
                            
                            # 버튼 클릭
                            close_button.click()
                            
                            if self.gui_logger:
                                self.log_info("✅ 팝업 버튼 클릭 완료")
                            
                            # 팝업이 사라질 때까지 짧게 대기
                            time.sleep(0.5)
                            
                    except NoSuchElementException:
                        if self.gui_logger:
                            self.log_info("팝업은 있지만 닫기 버튼을 찾을 수 없습니다")
                        
                except Exception as e:
                    if self.gui_logger:
                        self.log_info(f"⚠ 닫기 버튼 처리 중 오류: {str(e)}")
                        
            except TimeoutException:
                if self.gui_logger:
                    self.log_info("설문 시작 팝업이 없습니다. 바로 진행합니다.")
            except Exception as e:
                if self.gui_logger:
                    self.log_info(f"⚠ 팝업 처리 중 오류: {str(e)}")
                    
        except Exception as e:
            if self.gui_logger:
                self.log_info(f"⚠ 팝업 확인 중 오류: {str(e)}")
    
    def _handle_submit_confirmation_popup(self):
        """제출 확인 팝업에서 확인 버튼을 자동으로 클릭합니다."""
        try:
            # 팝업이 나타날 때까지 대기
            time.sleep(2)
            
            # 확인 버튼 찾기 (여러 방법 시도)
            confirm_selectors = [
                "//button[contains(text(), '확인')]",
                "//input[@value='확인']", 
                "//button[contains(@class, 'btn') and contains(text(), '확인')]",
                "//div[contains(@class, 'popup')]//button[contains(text(), '확인')]"
            ]
            
            confirm_button = None
            for selector in confirm_selectors:
                try:
                    confirm_button = self.web_automation.driver.find_element(By.XPATH, selector)
                    if confirm_button:
                        break
                except:
                    continue
            
            if confirm_button:
                if self.gui_logger:
                    self.log_info("확인 팝업 발견, 확인 버튼 클릭 중...")
                
                confirm_button.click()
                
                if self.gui_logger:
                    self.log_info("✅ 확인 팝업 처리 완료")
            else:
                if self.gui_logger:
                    self.log_info("⚠ 확인 팝업을 찾을 수 없습니다")
                    
        except Exception as e:
            if self.gui_logger:
                self.log_info(f"⚠ 확인 팝업 처리 중 오류: {str(e)}")
    
    def _run_points_check_module(self):
        """설문 완료 후 포인트 확인 모듈을 실행합니다 - BaseModule의 공통 메서드 사용"""
        self.check_points_after_activity()
    
    def validate_required_fields(self):
        """모든 필수 항목이 제대로 채워졌는지 확인합니다."""
        try:
            missing_fields = []
            
            # 1. 라디오 버튼 그룹별로 하나씩 선택되었는지 확인
            radio_groups = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            processed_groups = set()
            
            for radio in radio_groups:
                name = radio.get_attribute('name')
                if name and name not in processed_groups:
                    # 해당 그룹에서 선택된 라디오 버튼이 있는지 확인
                    try:
                        selected_radio = self.web_automation.driver.find_element(
                            By.CSS_SELECTOR, f'input[type="radio"][name="{name}"]:checked'
                        )
                    except:
                        missing_fields.append(f"라디오 버튼 그룹 '{name}'")
                    processed_groups.add(name)
            
            # 2. 텍스트 입력 필드가 비어있지 않은지 확인
            text_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
            for i, text_input in enumerate(text_inputs):
                if not text_input.get_attribute('value').strip():
                    missing_fields.append(f"텍스트 입력 필드 {i+1}번")
            
            # 3. 이메일 필드가 유효한 이메일 형식인지 확인
            email_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')
            for i, email_input in enumerate(email_inputs):
                email_value = email_input.get_attribute('value').strip()
                if not email_value or '@' not in email_value:
                    missing_fields.append(f"이메일 필드 {i+1}번")
            
            # 4. textarea 필드가 비어있지 않은지 확인
            textarea_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'textarea')
            for i, textarea in enumerate(textarea_inputs):
                if not textarea.get_attribute('value').strip():
                    missing_fields.append(f"textarea 필드 {i+1}번")
            
            # 5. 체크박스 필드가 최소 1개 이상 선택되었는지 확인
            checkbox_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
            if checkbox_inputs:
                selected_checkboxes = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]:checked')
                if not selected_checkboxes:
                    missing_fields.append("체크박스")
            
            if missing_fields:
                if self.gui_logger:
                    self.gui_logger(f"❌ 채워지지 않은 필수 항목: {', '.join(missing_fields)}")
                return False
            
            if self.gui_logger:
                self.gui_logger("✅ 모든 필수 항목이 올바르게 채워졌습니다")
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ 필수 항목 검증 중 오류: {str(e)}")
            return False
    
    def retry_fill_missing_fields(self):
        """안 채워진 필수 항목만 다시 채우기"""
        try:
            if self.gui_logger:
                self.gui_logger("재시도: 안 채워진 필수 항목을 다시 채우는 중...")
            
            # 1. 라디오 버튼 그룹별로 안 선택된 것들 다시 선택
            radio_groups = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            processed_groups = set()
            
            for radio in radio_groups:
                name = radio.get_attribute('name')
                if name and name not in processed_groups:
                    try:
                        # 해당 그룹에서 선택된 라디오 버튼이 있는지 확인
                        selected_radio = self.web_automation.driver.find_element(
                            By.CSS_SELECTOR, f'input[type="radio"][name="{name}"]:checked'
                        )
                    except:
                        # 선택되지 않은 경우 첫 번째 라디오 버튼 클릭
                        try:
                            first_radio = self.web_automation.driver.find_element(
                                By.CSS_SELECTOR, f'input[type="radio"][name="{name}"]'
                            )
                            first_radio.click()
                            if self.gui_logger:
                                self.gui_logger(f"재시도: 라디오 버튼 그룹 '{name}' 첫 번째 옵션 선택")
                        except:
                            pass
                    processed_groups.add(name)
            
            # 2. 텍스트 입력 필드가 비어있는 것들 다시 채우기
            text_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
            for i, text_input in enumerate(text_inputs):
                if not text_input.get_attribute('value').strip():
                    try:
                        text_input.clear()
                        text_input.send_keys(".")
                        if self.gui_logger:
                            self.gui_logger(f"재시도: 텍스트 입력 필드 {i+1}번 답변 입력")
                    except:
                        pass
            
            # 3. 이메일 필드가 유효하지 않은 것들 다시 채우기
            email_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')
            for i, email_input in enumerate(email_inputs):
                email_value = email_input.get_attribute('value').strip()
                if not email_value or '@' not in email_value:
                    try:
                        email_input.clear()
                        email_input.send_keys("a@gmail.com")
                        if self.gui_logger:
                            self.gui_logger(f"재시도: 이메일 필드 {i+1}번 답변 입력")
                    except:
                        pass
            
            # 4. textarea 필드가 비어있는 것들 다시 채우기
            textarea_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'textarea')
            for i, textarea in enumerate(textarea_inputs):
                if not textarea.get_attribute('value').strip():
                    try:
                        textarea.clear()
                        textarea.send_keys(".")
                        if self.gui_logger:
                            self.gui_logger(f"재시도: textarea 필드 {i+1}번 답변 입력")
                    except:
                        pass
            
            # 5. 체크박스가 하나도 선택되지 않은 경우 다시 선택
            checkbox_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
            if checkbox_inputs:
                selected_checkboxes = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]:checked')
                if not selected_checkboxes:
                    try:
                        # sr-only나 readonly가 아닌 실제 클릭 가능한 체크박스 찾기
                        clickable_checkbox = None
                        for checkbox in checkbox_inputs:
                            # sr-only 클래스나 readonly 속성이 없는 체크박스 찾기
                            checkbox_class = checkbox.get_attribute('class') or ''
                            checkbox_readonly = checkbox.get_attribute('readonly')
                            
                            if 'sr-only' not in checkbox_class and not checkbox_readonly:
                                clickable_checkbox = checkbox
                                break
                        
                        # 클릭 가능한 체크박스를 찾지 못한 경우, 두 번째 체크박스 시도
                        if not clickable_checkbox and len(checkbox_inputs) >= 2:
                            clickable_checkbox = checkbox_inputs[1]
                        
                        if clickable_checkbox and not clickable_checkbox.is_selected():
                            clickable_checkbox.click()
                            if self.gui_logger:
                                self.gui_logger("재시도: 체크박스 선택")
                    except:
                        pass
            
            # 재시도 후 다시 검증
            return self.validate_required_fields()
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ 재시도 중 오류: {str(e)}")
            return False
    
    def auto_fill_questions_in_order(self):
        """문제 순서대로 하나씩 처리합니다."""
        try:
            if self.gui_logger:
                self.log_info("문제 순서대로 처리 시작...")
            
            # 모든 질문 요소를 순서대로 찾기
            questions = self.web_automation.driver.find_elements(
                By.CSS_SELECTOR, 
                'li[data-question-number]'
            )
            
            processed_count = 0
            
            for question in questions:
                try:
                    question_number = question.get_attribute('data-question-number')
                    if not question_number:
                        continue
                    
                    if self.gui_logger:
                        self.log_info(f"문제 {question_number}번 처리 중...")
                    
                    # 각 질문에서 첫 번째 input/textarea 요소만 찾아서 유형별로 바로 처리
                    question_processed = False
                    
                    try:
                        # 첫 번째 input 또는 textarea 요소 찾기
                        first_input = question.find_element(By.CSS_SELECTOR, 'input, textarea')
                        input_type = first_input.get_attribute('type')
                        
                        if input_type == 'radio':
                            # 라디오 버튼: 첫 번째 옵션 선택
                            if not first_input.is_selected():
                                first_input.click()
                                if self.gui_logger:
                                    self.log_info(f"문제 {question_number}번: 라디오 버튼 첫 번째 옵션 선택")
                                question_processed = True
                                
                        elif input_type == 'checkbox':
                            # 체크박스: 두 번째 체크박스 선택 (첫 번째는 sr-only)
                            checkbox_inputs = question.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                            if len(checkbox_inputs) >= 2:
                                clickable_checkbox = checkbox_inputs[1]
                                if not clickable_checkbox.is_selected():
                                    clickable_checkbox.click()
                                    if self.gui_logger:
                                        self.log_info(f"문제 {question_number}번: 체크박스 첫 번째 옵션 선택")
                                    question_processed = True
                                    
                        elif input_type == 'text':
                            # 텍스트 입력: "." 입력
                            if not first_input.get_attribute('value').strip():
                                first_input.clear()
                                first_input.send_keys(".")
                                if self.gui_logger:
                                    self.log_info(f"문제 {question_number}번: 텍스트 입력 답변 완료")
                                question_processed = True
                                
                        elif input_type == 'email':
                            # 이메일 입력: "a@gmail.com" 입력
                            email_value = first_input.get_attribute('value').strip()
                            if not email_value or '@' not in email_value:
                                first_input.clear()
                                first_input.send_keys("a@gmail.com")
                                if self.gui_logger:
                                    self.log_info(f"문제 {question_number}번: 이메일 입력 답변 완료")
                                question_processed = True
                                
                        elif first_input.tag_name == 'textarea':
                            # textarea: "." 입력
                            if not first_input.get_attribute('value').strip():
                                first_input.clear()
                                first_input.send_keys(".")
                                if self.gui_logger:
                                    self.log_info(f"문제 {question_number}번: textarea 답변 완료")
                                question_processed = True
                                
                    except Exception as e:
                        if self.gui_logger:
                            self.gui_logger(f"문제 {question_number}번 처리 중 오류: {str(e)}")
                        pass
                    
                    if question_processed:
                        processed_count += 1
                    
                except Exception as e:
                    if self.gui_logger:
                        self.gui_logger(f"문제 {question_number}번 처리 중 오류: {str(e)}")
                    continue
            
            if self.gui_logger:
                self.log_info(f"✅ 총 {processed_count}개 문제 순서대로 처리 완료")
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ 문제 순서대로 처리 실패: {str(e)}")
            return False
    
    def auto_select_first_options(self):
        """모든 질문의 첫 번째 보기를 자동으로 선택하고 텍스트 필드에 점을 입력합니다."""
        try:
            # 1. 객관식 - 모든 라디오 버튼 그룹의 첫 번째 옵션 선택
            radio_groups = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            selected_count = 0
            processed_groups = set()
            
            for radio in radio_groups:
                try:
                    name = radio.get_attribute('name')
                    if name not in processed_groups:
                        radio.click()
                        processed_groups.add(name)
                        selected_count += 1
                        if self.gui_logger:
                            self.gui_logger(f"객관식 {selected_count}번 첫 번째 보기 선택 완료")
                except:
                    continue
            
            # 2. 체크박스 - 모든 체크박스 그룹의 첫 번째 옵션 선택
            checkbox_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
            checkbox_count = 0
            
            for checkbox in checkbox_inputs:
                try:
                    # 체크박스가 체크되지 않은 경우에만 체크
                    if not checkbox.is_selected():
                        checkbox.click()
                        checkbox_count += 1
                        if self.gui_logger:
                            self.gui_logger(f"체크박스 {checkbox_count}번 선택 완료")
                except:
                    continue
            
            # 3. 주관식 - 텍스트 입력 필드에 "." 입력
            text_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
            text_count = 0
            
            for text_input in text_inputs:
                try:
                    text_input.clear()
                    text_input.send_keys(".")
                    text_count += 1
                    if self.gui_logger:
                        self.gui_logger(f"주관식 {text_count}번 답변 입력 완료")
                except:
                    continue
            
            # 4. 이메일 필드 - "a@gmail.com" 입력
            email_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')
            email_count = 0
            
            for email_input in email_inputs:
                try:
                    email_input.clear()
                    email_input.send_keys("a@gmail.com")
                    email_count += 1
                    if self.gui_logger:
                        self.gui_logger(f"이메일 {email_count}번 답변 입력 완료")
                except:
                    continue
            
            # 5. textarea 필드 - "." 입력
            textarea_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'textarea')
            textarea_count = 0
            
            for textarea in textarea_inputs:
                try:
                    textarea.clear()
                    textarea.send_keys(".")
                    textarea_count += 1
                    if self.gui_logger:
                        self.gui_logger(f"textarea {textarea_count}번 답변 입력 완료")
                except:
                    continue
            
            if self.gui_logger:
                self.gui_logger(f"✅ 객관식 {selected_count}개, 체크박스 {checkbox_count}개, 주관식 {text_count}개, 이메일 {email_count}개, textarea {textarea_count}개 자동 답변 완료")
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ 자동 답변 실패: {str(e)}")
            return False
