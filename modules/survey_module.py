# -*- coding: utf-8 -*-
"""
설문참여 모듈
닥터빌 세미나 설문참여 기능을 담당합니다.
"""

import os
import threading
import time
import re
import ctypes
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_module import BaseModule
from .survey_problem import SurveyProblemManager

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
    _is_running = False  # 정적 변수로 실행 중 여부 관리
    _lock = threading.Lock()

    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
        self.problem_manager = SurveyProblemManager()
    
    def execute(self):
        """설문참여 페이지로 이동하고 첫 번째 세미나 자동 선택"""
        original_window = None
        try:
            # 중복 실행 방지
            with SurveyModule._lock:
                if SurveyModule._is_running:
                    self.log_info("ℹ 이미 설문 참여가 진행 중입니다. 중복 방지를 위해 취소합니다.")
                    return self.create_result(False, "이미 설문 참여가 진행 중입니다.")
                SurveyModule._is_running = True

            if not self.web_automation or not self.web_automation.driver:
                self.log_error("웹드라이버가 초기화되지 않았습니다. 먼저 로그인해주세요.")
                SurveyModule._is_running = False
                return self.create_result(False, "웹드라이버가 초기화되지 않았습니다.")
            
            original_window = self.web_automation.driver.current_window_handle
            
            self.log_info("설문참여 페이지로 이동합니다...")
            
            # VOD 목록 페이지로 이동
            self.web_automation.driver.get(VOD_LIST_PAGE_URL)
            self.log_info("설문참여 페이지로 이동 완료")
            
            # 🔥 첫 번째 세미나 자동 클릭
            self.log_info("첫 번째 세미나를 자동으로 선택합니다...")
            
            return self._auto_click_seminar(original_window)
            
        except Exception as e:
            SurveyModule._is_running = False
            error_msg = f"{ERROR_SURVEY_PAGE_NAVIGATION}: {str(e)}"
            self.log_error(error_msg)
            return self.create_result(False, error_msg)

    def _auto_click_seminar(self, original_window):
        """내부에서 동기적으로 세미나 클릭 및 설문 로직을 수행합니다."""
        try:
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.log_info(f"📅 오늘 날짜({today_str}) 세미나 설문 조사를 시작합니다.")

            # 1. 대상 세미나 URL 선행 수집
            self.web_automation.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, LIVE_LIST_CONTAINER_SELECTOR))
            )
            
            containers = self.web_automation.driver.find_elements(By.CSS_SELECTOR, ".live_list .list_cont")
            targets = []
            
            for container in containers:
                try:
                    text = container.text
                    if today_str in text:
                        link_elem = container.find_element(By.CSS_SELECTOR, "a.list_detail")
                        href = link_elem.get_attribute('href')
                        title = container.find_element(By.CSS_SELECTOR, SEMINAR_TITLE_SELECTOR).text.strip()
                        
                        # 중복 방지를 위해 URL 기준 저장
                        if href and not any(t['url'] == href for t in targets):
                            targets.append({'url': href, 'title': title})
                except:
                    continue

            if not targets:
                self.log_warning(f"오늘 날짜({today_str})의 세미나를 찾을 수 없습니다.")
                return self.create_result(True, "오늘 참여할 세미나가 없습니다.")

            self.log_info(f"📋 오늘 참여 대상 세미나 {len(targets)}건을 발견했습니다.")

            # 2. 수집된 URL 순차 방문 및 처리
            success_count = 0
            for i, target in enumerate(targets):
                try:
                    self.log_info(f"🔍 세미나 확인 중 ({i+1}/{len(targets)}): {target['title']}")
                    
                    # 상세 페이지로 직접 이동
                    self.web_automation.driver.get(target['url'])
                    time.sleep(2)

                    # 재입장하기 버튼 확인 및 처리
                    if self.auto_click_reenter_button():
                        self.log_success(f"✅ 설문 참여 성공: {target['title']}")
                        success_count += 1
                        # 설문 페이지가 열렸을 수 있으므로 목록 페이지로 리셋
                        self.web_automation.driver.get(VOD_LIST_PAGE_URL)
                        time.sleep(1)
                    else:
                        self.log_info(f"ℹ 재입장 버튼 없음 (혹은 이미 완료): {target['title']}")
                        # 상세 페이지에서 바로 다음으로 넘어가면 되므로 get 생략 가능하지만 안전을 위해 호출
                        # (상태가 바뀌어 있을 수도 있으므로 다시 목록으로 나감)
                        self.web_automation.driver.get(VOD_LIST_PAGE_URL)
                        time.sleep(1)

                except Exception as ie:
                    self.log_error(f"⚠️ 세미나 처리 중 오류 ({target['title']}): {str(ie)}")
                    self.web_automation.driver.get(VOD_LIST_PAGE_URL)
                    time.sleep(1)
            
            return self.create_result(True, f"총 {len(targets)}건 중 {success_count}건의 설문을 처리했습니다.")

        except Exception as e:
            error_msg = f"설문 세미나 순회 중 오류: {str(e)}"
            self.log_error(error_msg)
            return self.create_result(False, error_msg)

        except Exception as e:
            error_msg = f"{ERROR_FIRST_SEMINAR_SELECTION}: {str(e)}"
            self.log_error(error_msg)
            return self.create_result(False, error_msg)

        finally:
            if original_window and self.web_automation and self.web_automation.driver:
                try:
                    self.log_info("설문참여 완료 후 추가 창을 정리합니다...")
                    self.web_automation.close_other_windows(original_window)
                except Exception as e:
                    self.log_warning(f"창 정리 중 오류: {str(e)}")
                finally:
                    # 추가 창 정리 후 가장 마지막에, 기본 창에서 단위 작업 종료 시 포인트 확인 실행
                    self.log_info("모든 창 정리 완료, 포인트 확인을 진행합니다...")
                    self._run_points_check_module()
                    
                    # 🔥 임시 스크린샷 파일 삭제
                    try:
                        temp_img = os.path.join(os.getcwd(), "survey_quiz_temp.png")
                        if os.path.exists(temp_img):
                            # 약간 대기 후 삭제 (이미지 뷰어가 파일을 물고 있을 수 있음)
                            time.sleep(2)
                            os.remove(temp_img)
                            self.log_info("🧹 임시 스크린샷 파일을 삭제했습니다.")
                    except:
                        pass
                    finally:
                        # 실행 종료 표시
                        SurveyModule._is_running = False
    
    def auto_click_reenter_button(self):
        """재입장하기 버튼을 자동으로 클릭합니다."""
        try:
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
                
                self.log_info("재입장하기 버튼 발견")
                
                # 버튼 클릭
                reenter_button.click()
                
                self.log_info("✅ 재입장하기 버튼 자동 클릭 완료")
                self.log_info("새로운 팝업 창에서 설문참여 버튼을 찾는 중...")
                
                # 🔥 새로운 팝업 창에서 설문참여 버튼 자동 클릭
                self.auto_click_survey_in_popup()
                
                return True
                
            except TimeoutException:
                # 재입장하기 버튼이 없는 경우 (이미 설문 완료)
                self.log_warning("재입장하기 버튼이 없습니다. 이미 설문이 완료되었거나 참여할 설문이 없습니다.")
                return False
                
        except Exception as e:
            self.log_error(f"{ERROR_REENTER_BUTTON_CLICK}: {str(e)}")
            return False
    
    def auto_click_survey_in_popup(self):
        """새로운 팝업 창에서 설문참여 버튼을 자동으로 클릭합니다."""
        try:
            self.log_info("새로운 팝업 창 대기 중...")
            
            # 새로운 팝업 창이 열릴 때까지 대기
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
                self.log_error("새로운 팝업 창을 찾을 수 없습니다")
                return False
            
            # 팝업 창으로 전환
            self.web_automation.driver.switch_to.window(popup_window)
            
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
            
            self.log_info("설문참여 버튼 발견")
            
            # 버튼 클릭
            survey_button.click()
            
            self.log_info("✅ 설문참여 버튼 자동 클릭 완료")
            self.log_info("개인정보 동의 팝업에서 설문하기 버튼을 찾는 중...")
            
            # 🔥 개인정보 동의 팝업에서 설문하기 버튼 자동 클릭
            self.auto_click_survey_button_in_agree_popup()
            
            # 원래 창으로 돌아가기
            self.web_automation.driver.switch_to.window(original_window)
            
            return True
            
        except Exception as e:
            self.log_error(f"팝업 창에서 설문참여 버튼 클릭 실패: {str(e)}")
            
            # 오류 발생 시 원래 창으로 돌아가기
            try:
                self.web_automation.driver.switch_to.window(original_window)
            except:
                pass
            
            return False
    
    def auto_click_survey_button_in_agree_popup(self):
        """개인정보 동의 팝업에서 설문하기 버튼을 자동으로 클릭합니다."""
        try:
            self.log_info("개인정보 동의 팝업 대기 중...")
            
            # 개인정보 동의 팝업이 나타날 때까지 대기
            self.web_automation.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#agreeInfo"))
            )
            
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
                    self.log_info("✅ 동의 체크박스 자동 체크 완료")
                else:
                    self.log_info("동의 체크박스가 이미 체크되어 있습니다")
                        
            except Exception as e:
                self.log_warning(f"동의 체크박스 처리 중 오류: {str(e)}")
            
            # 설문하기 버튼 찾기 및 클릭
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
            
            self.log_info("설문하기 버튼 발견")
            
            # 버튼 클릭
            survey_button.click()
            
            self.log_info("✅ 설문하기 버튼 자동 클릭 완료")
            self.log_info("설문 페이지로 이동 중...")
            self.log_info("새로운 설문 창에서 자동 답변을 시작합니다...")
            
            # 🔥 새로운 설문 창에서 자동 답변 및 제출
            self.auto_fill_and_submit_survey()
            
            return True
            
        except Exception as e:
            self.log_error(f"개인정보 동의 팝업에서 설문하기 버튼 클릭 실패: {str(e)}")
            return False
    
    def auto_fill_and_submit_survey(self):
        """새로운 설문 창에서 모든 질문의 첫 번째 보기를 자동 선택하고 제출합니다."""
        try:
            self.log_info("새로운 설문 창 대기 중...")
            
            # 새로운 설문 창이 열릴 때까지 대기
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
                self.log_error("❌ 새로운 설문 창을 찾을 수 없습니다")
                return False
            
            self.log_info("설문 창으로 전환 완료")
            self.log_info("설문 페이지 로딩 대기 중...")
            
            # 설문 페이지 로딩 완료 대기
            self.web_automation.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form[id^='surveyForm']"))
            )
            
            self.log_info("설문 페이지 로딩 완료")
            self.log_info("여러 페이지 설문 처리 시작...")
            
            # 🔥 팝업 확인 및 처리
            self.handle_survey_popup()
            
            # 🔥 여러 페이지 설문 처리 (간단한 방식)
            page_count = 1
            
            while True:
                self.log_info(f"=== {page_count}페이지 처리 중 ===")
                
                # 현재 페이지에서 문제 순서대로 하나씩 처리
                if not self.auto_fill_questions_in_order():
                    self.log_error("퀴즈 정답 미등록으로 설문 자동 답변을 중단합니다.")
                    return False
                
                # 🔥 모든 필수 항목이 제대로 채워졌는지 확인
                if not self.validate_required_fields():
                    self.log_warning("필수 항목이 모두 채워지지 않았습니다. 재시도합니다...")
                    
                    # 재시도: 안 채워진 부분만 다시 채우기
                    if not self.retry_fill_missing_fields():
                        self.log_error("재시도 후에도 필수 항목이 채워지지 않았습니다. 설문 제출을 중단합니다.")
                        return False
                    else:
                        self.log_success("재시도 후 모든 필수 항목이 채워졌습니다.")
                
                self.log_info(f"{page_count}페이지 답변 완료")
                
                # 페이지 하단 버튼 확인
                try:
                    footer_button = self.web_automation.driver.find_element(
                        By.CSS_SELECTOR, 
                        'footer input[type="submit"][value="다음"], footer input[type="submit"][value="제출하기"]'
                    )
                    
                    # 버튼 텍스트 확인
                    button_text = footer_button.get_attribute('value') or footer_button.text
                    
                    self.log_info(f"페이지 하단 버튼 발견: {button_text}")
                    
                    if "다음" in button_text:
                        # 다음 버튼 클릭
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
                            self.log_warning("다음 페이지 로딩 대기 시간 초과, 계속 진행...")
                        
                        page_count += 1
                        
                    elif "제출하기" in button_text:
                        # 제출 버튼 클릭
                        self.log_info("제출하기 버튼 발견, 설문 제출 중...")
                        
                        footer_button.click()
                        
                        self.log_success("설문 제출 완료!")
                        
                        break  # 반복문 종료
                        
                    else:
                        # 예상하지 못한 버튼
                        self.log_warning(f"예상하지 못한 버튼: {button_text}")
                        break
                        
                except NoSuchElementException:
                    self.log_info("페이지 하단 버튼을 찾을 수 없습니다")
                    break
                except Exception as e:
                    self.log_warning(f"버튼 처리 중 오류: {str(e)}")
                    break
            
            self.log_info(f"총 {page_count}페이지 처리 완료")
            
            # 확인 팝업 처리
            self._handle_submit_confirmation_popup()
            
            # 원래 창으로 돌아가기
            self.web_automation.driver.switch_to.window(original_window)
            
            # 포인트 확인 모듈 실행은 상위로직(execute의 finally)에서 일괄 처리합니다.
            
            return True
            
        except Exception as e:
            self.log_error(f"설문 자동 답변 및 제출 실패: {str(e)}")
            
            # 오류 발생 시 원래 창으로 돌아가기
            try:
                self.web_automation.driver.switch_to.window(original_window)
            except:
                pass
            
            return False
    
    def handle_survey_popup(self):
        """설문 시작 시 나타날 수 있는 팝업을 처리합니다."""
        try:
            self.log_info("설문 시작 팝업 확인 중...")
            
            # 팝업이 나타날 때까지 동적 대기
            try:
                popup_container = self.web_automation.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#headlessui-portal-root"))
                )
                
                self.log_info("팝업 발견, 닫기 버튼 검색 중...")
                
                # 팝업 내부에 "닫기" 버튼이 있는지 확인 (XPath 사용)
                try:
                    close_button = popup_container.find_element(
                        By.XPATH, 
                        './/button[contains(text(), "닫기")]'
                    )
                    
                    if close_button:
                        self.log_info("설문 시작 팝업 발견, 닫기 버튼 클릭 중...")
                        
                        # 닫기 버튼 클릭
                        close_button.click()
                        
                        self.log_success("설문 시작 팝업 닫기 완료")
                        
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
                            self.log_info("팝업 버튼 발견 (btn-primary), 클릭 중...")
                            
                            # 버튼 클릭
                            close_button.click()
                            
                            self.log_success("팝업 버튼 클릭 완료")
                            
                            # 팝업이 사라질 때까지 짧게 대기
                            time.sleep(0.5)
                            
                    except NoSuchElementException:
                        self.log_info("팝업은 있지만 닫기 버튼을 찾을 수 없습니다")
                        
                except Exception as e:
                    self.log_warning(f"닫기 버튼 처리 중 오류: {str(e)}")
                        
            except TimeoutException:
                self.log_info("설문 시작 팝업이 없습니다. 바로 진행합니다.")
            except Exception as e:
                self.log_warning(f"팝업 처리 중 오류: {str(e)}")
                    
        except Exception as e:
            self.log_warning(f"팝업 확인 중 오류: {str(e)}")
    
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
                self.log_info("확인 팝업 발견, 확인 버튼 클릭 중...")
                
                confirm_button.click()
                
                self.log_success("확인 팝업 처리 완료")
            else:
                self.log_warning("확인 팝업을 찾을 수 없습니다")
                    
        except Exception as e:
            self.log_warning(f"확인 팝업 처리 중 오류: {str(e)}")
    
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
                self.log_error(f"채워지지 않은 필수 항목: {', '.join(missing_fields)}")
                return False
            
            self.log_success("모든 필수 항목이 올바르게 채워졌습니다")
            
            return True
            
        except Exception as e:
            self.log_error(f"필수 항목 검증 중 오류: {str(e)}")
            return False
    
    def retry_fill_missing_fields(self):
        """안 채워진 필수 항목만 다시 채우기"""
        try:
            self.log_info("재시도: 안 채워진 필수 항목을 다시 채우는 중...")
            
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
                            self.log_info(f"재시도: 라디오 버튼 그룹 '{name}' 첫 번째 옵션 선택")
                        except:
                            pass
                    processed_groups.add(name)
            
            # 2. 텍스트 입력 필드가 비어있는 것들 다시 채우기
            text_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
            for i, text_input in enumerate(text_inputs):
                if not text_input.get_attribute('value').strip():
                    try:
                        # 최소 글자수 제한이 있는지 확인
                        parent_li = text_input.find_element(By.XPATH, "./ancestor::li")
                        if self._check_char_limit(parent_li):
                            self.log_warning(f"재시도: 텍스트 입력 필드 {i+1}번은 글자수 제한이 있어 자동 입력을 건너뜁니다.")
                            continue
                            
                        text_input.clear()
                        text_input.send_keys("없습니다.")
                        self.log_info(f"재시도: 텍스트 입력 필드 {i+1}번 답변 입력")
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
                        self.log_info(f"재시도: 이메일 필드 {i+1}번 답변 입력")
                    except:
                        pass
            
            # 4. textarea 필드가 비어있는 것들 다시 채우기
            textarea_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'textarea')
            for i, textarea in enumerate(textarea_inputs):
                if not textarea.get_attribute('value').strip():
                    try:
                        # 최소 글자수 제한이 있는지 확인
                        parent_li = textarea.find_element(By.XPATH, "./ancestor::li")
                        if self._check_char_limit(parent_li):
                            self.log_warning(f"재시도: textarea {i+1}번은 글자수 제한이 있어 자동 입력을 건너뜁니다.")
                            continue

                        textarea.clear()
                        textarea.send_keys("없습니다.")
                        self.log_info(f"재시도: textarea 필드 {i+1}번 답변 입력")
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
                            self.log_info("재시도: 체크박스 선택")
                    except:
                        pass
            
            # 재시도 후 다시 검증
            return self.validate_required_fields()
            
        except Exception as e:
            self.log_error(f"재시도 중 오류: {str(e)}")
            return False
    
    def auto_fill_questions_in_order(self):
        """문제 순서대로 하나씩 처리합니다."""
        try:
            self.log_info("문제 순서대로 처리 시작...")
            
            # 모든 질문 요소를 순서대로 찾기
            questions = self.web_automation.driver.find_elements(
                By.CSS_SELECTOR, 
                'li[data-question-number]'
            )
            
            processed_count = 0
            
            for question in questions:
                # 세션 유효성 확인
                try:
                    _ = self.web_automation.driver.title
                except:
                    return False

                try:
                    question_number = question.get_attribute('data-question-number')
                    if not question_number:
                        continue
                    
                    self.log_info(f"문제 {question_number}번 처리 중...")
                    
                    # 🔥 문제 제목 추출 (퀴즈 여부 판단용)
                    question_text = ""
                    try:
                        # 실제 HTML 구조: li > label > div.whitespace-pre-wrap
                        text_elem = question.find_element(By.CSS_SELECTOR, 'div.whitespace-pre-wrap')
                        
                        # div 안의 모든 텍스트 추출 (span[퀴즈] 포함)
                        question_text = text_elem.text.strip() if text_elem else ""
                        
                        if not question_text:
                            # 대체 선택자
                            try:
                                question_text = question.find_element(By.CSS_SELECTOR, 'label').text.strip()
                            except:
                                pass
                    except:
                        # 제목을 찾지 못한 경우 빈 문자열 사용
                        question_text = ""
                    
                    # 문제 제목 정규화 (저장된 정답과 비교하기 위해)
                    normalized_question = self._normalize_question_text(question_text)
                    
                    # 각 질문에서 첫 번째 input/textarea 요소만 찾아서 유형별로 바로 처리
                    question_processed = False
                    
                    try:
                        # 첫 번째 input 또는 textarea 요소 찾기
                        first_input = question.find_element(By.CSS_SELECTOR, 'input, textarea')
                        input_type = first_input.get_attribute('type')
                        
                        # 🔥 [퀴즈] 문제 여부 확인
                        is_quiz = "[퀴즈]" in question_text
                        quiz_answer = None
                        
                        if is_quiz:
                            # 퀴즈 정답 조회 (원본 문제 텍스트로 - get_answer에서 정규화함)
                            quiz_answer = self.problem_manager.get_answer(question_text)
                            if quiz_answer:
                                self.log_success(f"퀴즈 정답 발견: {normalized_question[:40]}... → {quiz_answer}")
                            else:
                                self.log_warning(f"퀴즈이지만 정답 미등록: {normalized_question[:45]}...")
                                    
                            if not quiz_answer:
                                # 퀴즈지만 정답이 없는 경우, 보기 선택하지 않고 '설문문제' 창 띄우기
                                if hasattr(self, 'gui_callbacks') and 'gui_instance' in self.gui_callbacks:
                                    gui = self.gui_callbacks['gui_instance']
                                    if hasattr(gui, 'root') and hasattr(gui, 'open_survey_problem'):
                                        self.log_warning(f"문제 {question_number}번: 정답 미등록. 설문 문제 자동 관리 창을 엽니다.")

                                        # 스크린샷 캡처 (특히 헤드리스 모드에서 유용)
                                        screenshot_path = os.path.join(os.getcwd(), "survey_quiz_temp.png")
                                        try:
                                            # 🔥 해당 문제를 화면 중앙으로 스크롤하여 캡처
                                            self.web_automation.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", question)
                                            time.sleep(0.5)  # 스크롤 후 안정화 대기
                                            
                                            self.web_automation.driver.save_screenshot(screenshot_path)
                                            self.log_info(f"📸 {question_number}번 문제 위치로 스크롤하여 캡처했습니다.")
                                        except Exception as e:
                                            self.log_warning(f"스크린샷 캡처 실패: {str(e)}")
                                            screenshot_path = None
                                        
                                        # 카테고리 추출 (페이지 타이틀에서)
                                        category = ""
                                        try:
                                            title_text = self.web_automation.driver.title
                                            matches = re.findall(r'\(([^)]+)\)', title_text)
                                            if matches:
                                                last_paren = matches[-1]
                                                category = last_paren.split('_')[0].strip()
                                        except Exception:
                                            pass
                                            
                                        # 문제 텍스트에서 첫 줄만 추출 (보기 제외)
                                        display_question = ""
                                        for line in question_text.split('\n'):
                                            cleaned_line = line.strip()
                                            if cleaned_line:
                                                display_question = cleaned_line
                                                break
                                        
                                        # "1. " 같은 말머리 번호 제거
                                        display_question = re.sub(r'^\d+\.\s*', '', display_question)
                                        # [퀴즈] 태그 및 불필요한 별표(*) 제거
                                        display_question = display_question.replace('[퀴즈]', '').replace('*', '').strip()
                                            
                                        # 람다 함수로 인수 전달 (이미지 경로 포함)
                                        gui.root.after(0, lambda q=display_question, c=category, img=screenshot_path: gui.open_survey_problem(initial_question=q, initial_category=c, image_path=img))
                                        
                                        # 정답이 새로 등록될 때까지 대기
                                        self.log_info(f"⌛ 문제 {question_number}번 정답이 등록될 때까지 대기합니다...")
                                        
                                        waiting_count = 0
                                        while True:
                                            # 세션 유효성 확인
                                            try:
                                                _ = self.web_automation.driver.title
                                            except:
                                                return False

                                            time.sleep(1.0)
                                            waiting_count += 1
                                            
                                            # 다시 정답 확인
                                            self.problem_manager.load_quizzes()
                                            new_answer = self.problem_manager.get_answer(question_text)
                                            if new_answer:
                                                quiz_answer = new_answer
                                                self.log_success(f"새로운 정답 확인완료, 답변을 계속 진행합니다: {quiz_answer}")
                                                break
                                                
                                            if waiting_count > 300: # 5분 타임아웃
                                                self.log_error("대기 시간(5분) 초과로 설문 자동 답변을 중단합니다.")
                                                return False
                                                
                            if not quiz_answer:
                                return False  # 전체 처리 중단 (gui를 열 수 없거나 팝업 이후 대기 타임아웃/오류 발생 시)
                        
                        if input_type == 'radio':
                            # 라디오 버튼: 퀴즈면 정답 선택, 아니면 첫 번째 옵션 선택
                            if is_quiz and quiz_answer:
                                # 퀴즈 정답에 해당하는 라디오 버튼 선택
                                try:
                                    radios = question.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                                    answer_value = str(quiz_answer).strip()
                                    
                                    radio_selected = False
                                    
                                    # 전략 1: 숫자 정답인 경우 (1, 2, 3, 4, 5 등)
                                    if answer_value.isdigit():
                                        answer_num = int(answer_value)
                                        if 1 <= answer_num <= len(radios):
                                            target_radio = radios[answer_num - 1]  # 0부터 시작하므로 -1
                                            if not target_radio.is_selected():
                                                target_radio.click()
                                                self.log_info(f"문제 {question_number}번: 퀴즈 정답 {answer_value}번 선택")
                                                question_processed = True
                                                radio_selected = True
                                    
                                    # 전략 2: 텍스트 정답인 경우 (O, X, 또는 선택지 문구)
                                    if not radio_selected:
                                        for idx, radio in enumerate(radios):
                                            try:
                                                # 라디오 버튼의 형제 span에서 텍스트 추출
                                                label_elem = radio.find_element(By.XPATH, './ancestor::label')
                                                option_text = label_elem.text.strip() if label_elem else ""
                                                
                                                # 정답과 선택지 텍스트 비교
                                                if answer_value.upper() in option_text.upper() or option_text.upper() in answer_value.upper():
                                                    if not radio.is_selected():
                                                        radio.click()
                                                        self.log_success(f"문제 {question_number}번: 퀴즈 정답 '{answer_value}' 선택")
                                                        question_processed = True
                                                        radio_selected = True
                                                    break
                                            except:
                                                continue
                                    
                                    # 정답을 찾지 못한 경우 첫 번째 선택
                                    if not radio_selected:
                                        if not first_input.is_selected():
                                            first_input.click()
                                            self.log_warning(f"문제 {question_number}번: 퀴즈 정답 '{answer_value}' 미등록, 첫 번째 옵션 선택")
                                            question_processed = True
                                except Exception as e:
                                    self.log_error(f"문제 {question_number}번 퀴즈 정답 선택 오류: {str(e)}")
                                    if not first_input.is_selected():
                                        first_input.click()
                                        question_processed = True
                            else:
                                # 일반 문제: 첫 번째 옵션 선택
                                if not first_input.is_selected():
                                    first_input.click()
                                    self.log_info(f"문제 {question_number}번: 라디오 버튼 첫 번째 옵션 선택")
                                    question_processed = True
                                
                        elif input_type == 'checkbox':
                            # 체크박스: 두 번째 체크박스 선택 (첫 번째는 sr-only)
                            checkbox_inputs = question.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                            if len(checkbox_inputs) >= 2:
                                clickable_checkbox = checkbox_inputs[1]
                                if not clickable_checkbox.is_selected():
                                    clickable_checkbox.click()
                                    self.log_info(f"문제 {question_number}번: 체크박스 첫 번째 옵션 선택")
                                    question_processed = True
                                
                        elif input_type == 'text':
                            # 텍스트 입력: 글자수 제한 확인
                            char_limit = self._check_char_limit(question)
                            if char_limit:
                                self.log_warning(f"⚠️ {question_number}번 문제: 최소 {char_limit}자 제한이 발견되었습니다. 직접 입력을 대기합니다 (2분)...")
                                if self._wait_for_manual_input(first_input, char_limit):
                                    self.log_success(f"✅ {question_number}번 문제: 직접 입력 확인 완료.")
                                    question_processed = True
                                else:
                                    self.log_error(f"❌ {question_number}번 문제: 대기 시간 초과")
                                    return False
                            else:
                                if not first_input.get_attribute('value').strip():
                                    first_input.clear()
                                    text_to_enter = "없습니다."
                                    first_input.send_keys(text_to_enter)
                                    self.log_info(f"문제 {question_number}번: 텍스트 '{text_to_enter}' 자동 입력 완료")
                                    question_processed = True
                                
                        elif input_type == 'email':
                            # 이메일 입력: "a@gmail.com" 입력
                            email_value = first_input.get_attribute('value').strip()
                            if not email_value or '@' not in email_value:
                                first_input.clear()
                                first_input.send_keys("a@gmail.com")
                                self.log_info(f"문제 {question_number}번: 이메일 입력 답변 완료")
                                question_processed = True
                                
                        elif first_input.tag_name == 'textarea': # input_type for textarea is usually None or empty string, so check tag_name
                            # 텍스트란 글자수 제한 확인
                            char_limit = self._check_char_limit(question)
                            if char_limit:
                                self.log_warning(f"⚠️ {question_number}번 문제: 최소 {char_limit}자 주관식 제한이 발견되었습니다. 직접 입력을 대기합니다 (2분)...")
                                if self._wait_for_manual_input(first_input, char_limit):
                                    self.log_success(f"✅ {question_number}번 문제: 주관식 직접 입력 확인 완료.")
                                    question_processed = True
                                else:
                                    self.log_error(f"❌ {question_number}번 문제: 주관식 대기 시간 초과")
                                    return False
                            else:
                                if not first_input.get_attribute('value'):
                                    text_to_enter = "없습니다."
                                    first_input.send_keys(text_to_enter)
                                    self.log_info(f"문제 {question_number}번: 주관식 '{text_to_enter}' 자동 입력 완료")
                                    question_processed = True
                                else:
                                    self.log_info(f"문제 {question_number}번: 주관식 이미 입력되어 있음")
                                
                    except Exception as e:
                        self.log_error(f"문제 {question_number}번 처리 중 오류: {str(e)}")
                        pass
                    
                    if question_processed:
                        processed_count += 1
                    
                except Exception as e:
                    self.log_error(f"문제 {question_number}번 처리 중 오류: {str(e)}")
                    continue
            
            self.log_info(f"✅ 총 {processed_count}개 문제 순서대로 처리 완료")
            
            return True
            
        except Exception as e:
            self.log_error(f"문제 순서대로 처리 실패: {str(e)}")
            return False
    
    def _check_char_limit(self, question_elem):
        """질문 항목 내에 최소 글자 수 제한이 있는지 확인합니다."""
        try:
            text = question_elem.text
            if "최소" in text and "자" in text:
                match = re.search(r'최소\s*(\d+)\s*자', text)
                if match:
                    return int(match.group(1))
        except:
            pass
        return None

    def _wait_for_manual_input(self, input_elem, limit, timeout=600): # 10분으로 증가
        """사용자가 직접 최소 글자 수 이상 입력할 때까지 대기합니다."""
        # 팝업 알림 띄우기
        self._show_manual_input_alert(limit)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 세션 유효성 확인
            try:
                _ = self.web_automation.driver.title
            except:
                return False

            try:
                current_value = input_elem.get_attribute('value').strip()
                if len(current_value) >= limit:
                    return True
            except:
                pass
            
            time.sleep(1)
        return False

    def _show_manual_input_alert(self, limit):
        """윈도우 팝업 알림을 띄웁니다."""
        try:
            def run_popup():
                msg = f"⚠️ 주관식 답변에 최소 {limit}자 제한이 발견되었습니다.\n\n브라우저 창을 열어 직접 입력을 완료해주세요.\n(내용 입력 후 질문 창을 벗어나면 자동으로 다음 단계가 진행됩니다.)"
                # MB_OK(0) | MB_ICONINFORMATION(0x40) | MB_SYSTEMMODAL(0x1000)
                ctypes.windll.user32.MessageBoxW(0, msg, "DVA 설문 알림", 0x40 | 0x1000)
            
            threading.Thread(target=run_popup, daemon=True).start()
        except:
            pass

    def _normalize_question_text(self, question: str) -> str:
        
        # [퀴즈] 태그 제거
        cleaned = question.replace("[퀴즈]", "").strip()
        
        # 후행 특수문자 제거 (*, ?, 공백 등)
        cleaned = re.sub(r'[\*\?]+\s*$', '', cleaned).strip()
        
        # 여러 개의 공백을 단일 공백으로 정규화
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
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
                        self.log_info(f"객관식 {selected_count}번 첫 번째 보기 선택 완료")
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
                        self.log_info(f"체크박스 {checkbox_count}번 선택 완료")
                except:
                    continue
            
            # 3. 주관식 - 텍스트 입력 필드에 "." 입력
            text_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
            text_count = 0
            
            for text_input in text_inputs:
                try:
                    # 최소 글자수 제한이 있는지 확인
                    parent_li = text_input.find_element(By.XPATH, "./ancestor::li")
                    if self._check_char_limit(parent_li):
                        self.log_warning(f"주관식 {text_count+1}번은 글자수 제한이 있어 자동 입력을 건너뜁니다.")
                        continue

                    text_input.clear()
                    text_input.send_keys("없습니다.")
                    text_count += 1
                    self.log_info(f"주관식 {text_count}번 답변 입력 완료")
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
                    self.log_info(f"이메일 {email_count}번 답변 입력 완료")
                except:
                    continue
            
            # 5. textarea 필드 - "." 입력
            textarea_inputs = self.web_automation.driver.find_elements(By.CSS_SELECTOR, 'textarea')
            textarea_count = 0
            
            for textarea in textarea_inputs:
                try:
                    # 최소 글자수 제한이 있는지 확인
                    parent_li = textarea.find_element(By.XPATH, "./ancestor::li")
                    if self._check_char_limit(parent_li):
                        self.log_warning(f"textarea {textarea_count+1}번은 글자수 제한이 있어 자동 입력을 건너뜁니다.")
                        continue

                    textarea.clear()
                    textarea.send_keys("없습니다.")
                    textarea_count += 1
                    self.log_info(f"textarea {textarea_count}번 답변 입력 완료")
                except:
                    continue
            
            self.log_success(f"객관식 {selected_count}개, 체크박스 {checkbox_count}개, 주관식 {text_count}개, 이메일 {email_count}개, textarea {textarea_count}개 자동 답변 완료")
            
            return True
            
        except Exception as e:
            self.log_error(f"자동 답변 실패: {str(e)}")
            return False
