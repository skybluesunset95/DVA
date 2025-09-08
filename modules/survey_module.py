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
            
            def auto_click_first_seminar():
                try:
                    # 페이지 로딩 완료 대기 (세미나 목록이 나타날 때까지)
                    self.web_automation.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, LIVE_LIST_CONTAINER_SELECTOR))
                    )
                    
                    # 첫 번째 세미나 링크 찾기
                    first_seminar = self.web_automation.driver.find_element(
                        By.CSS_SELECTOR, 
                        FIRST_SEMINAR_LINK_SELECTOR
                    )
                    
                    # 세미나 제목 가져오기
                    seminar_title = first_seminar.find_element(By.CSS_SELECTOR, SEMINAR_TITLE_SELECTOR).text.strip()
                    
                    if self.gui_logger:
                        self.gui_logger(f"첫 번째 세미나 발견: {seminar_title}")
                    
                    # 링크 클릭
                    first_seminar.click()
                    
                    if self.gui_logger:
                        self.log_info("✅ 첫 번째 세미나 자동 선택 완료")
                        self.log_info("재입장하기 버튼을 찾는 중...")
                    
                    # 🔥 재입장하기 버튼 자동 클릭
                    self.auto_click_reenter_button()
                    
                except Exception as e:
                    if self.gui_logger:
                        self.gui_logger(f"❌ {ERROR_FIRST_SEMINAR_SELECTION}: {str(e)}")
            
            # 백그라운드에서 실행
            threading.Thread(target=auto_click_first_seminar, daemon=True).start()
            
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
            
            # 페이지 로딩 대기 (재입장하기 버튼이 나타날 때까지)
            self.web_automation.wait.until(
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
                
                # 현재 페이지에서 모든 질문의 첫 번째 보기 자동 선택
                self.auto_select_first_options()
                
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
                        time.sleep(0.02)  # 대기 시간 단축
                except:
                    continue
            
            # 2. 주관식 - 모든 텍스트 입력 필드에 "." 입력
            text_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
            text_count = 0
            
            for text_input in text_inputs:
                try:
                    text_input.clear()
                    text_input.send_keys(".")
                    text_count += 1
                    if self.gui_logger:
                        self.gui_logger(f"주관식 {text_count}번 답변 입력 완료")
                    time.sleep(0.02)  # 대기 시간 단축
                except:
                    continue
            
            if self.gui_logger:
                self.gui_logger(f"✅ 객관식 {selected_count}개, 주관식 {text_count}개 자동 답변 완료")
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"❌ 자동 답변 실패: {str(e)}")
            return False
