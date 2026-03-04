# -*- coding: utf-8 -*-
"""
새로운 퀴즈풀기 모듈
닥터빌 퀴즈풀기 기능을 담당합니다.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from .base_module import BaseModule
from .quiz_problem import QuizProblemManager
import time
import os

# URL 상수 정의
MEDICINE_PAGE_URL = "https://www.doctorville.co.kr/product/medicineList"
INSTRUMENT_PAGE_URL = "https://www.doctorville.co.kr/product/instrumentList"

# CSS 선택자 상수 정의
QUIZ_CSS_SELECTOR = ".quiz_bg"
QUIZ_BANNER_BUTTON_ID = "btn_quiz_banner"
QUIZ_LAYER_POP_ID = "quizLayerPop"
QUESTION_AREA_CONTAINER_ID = "questionArea"  # 퀴즈 문제 영역 컨테이너 (여기 안에서만 수집)
PRODUCT_TITLE_ID = "product_title"
PRODUCT_CATEGORY_ID = "product_categoryNm"
PRODUCT_TITLE_ENG_ID = "product_titleEng"
QUIZ_POINT_ID = "quiz_point"
QUESTION_AREA_SELECTOR = ".question_area"
QUESTION_TEXT_SELECTOR = ".txt_question"
QUESTION_CHOICE_SELECTOR = ".question_choice li"
ANSWER_CONFIRM_BUTTON_ID = "answerConfirmBtn"
CHOICE_LABEL_SELECTOR = "label"
CHOICE_INPUT_SELECTOR = "input"

# 대기 시간 상수 정의
DEFAULT_SHORT_TIMEOUT = 1

# 정답 매핑 상수
ANSWER_MAPPING = {'O': '1', 'X': '2'}

# 유효한 답안 값들
VALID_ANSWER_VALUES = ['1', '2', '3', '4', '5']

# 최소 퀴즈 요소 개수
MIN_QUIZ_ELEMENTS = 2

class QuizModule(BaseModule):
    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
        self.problem_manager = QuizProblemManager()
        self.original_window = None
        self.blog_window = None
    
    def wait_for_page_load(self, timeout=None):
        """페이지 로딩 완료 대기"""
        try:
            # 기존 web_automation.wait 사용 (timeout 설정됨)
            self.web_automation.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_element_presence(self, element_id, timeout=None):
        """특정 요소의 존재 대기"""
        try:
            # 더 짧은 timeout으로 빠르게 실패
            short_timeout = timeout or DEFAULT_SHORT_TIMEOUT  # 기본 1초로 단축
            from selenium.webdriver.support.ui import WebDriverWait
            short_wait = WebDriverWait(self.web_automation.driver, short_timeout)
            short_wait.until(
                EC.presence_of_element_located((By.ID, element_id))
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_element_clickable(self, element_id, timeout=None):
        """특정 요소의 클릭 가능 상태 대기"""
        try:
            # 더 짧은 timeout으로 빠르게 실패
            short_timeout = timeout or DEFAULT_SHORT_TIMEOUT  # 기본 1초로 단축
            from selenium.webdriver.support.ui import WebDriverWait
            short_wait = WebDriverWait(self.web_automation.driver, short_timeout)
            short_wait.until(
                EC.element_to_be_clickable((By.ID, element_id))
            )
            return True
        except TimeoutException:
            return False
    
    def handle_element_not_found(self, element_name):
        """요소를 찾을 수 없을 때의 공통 처리 (하위 호환성 위해 BaseModule로 전달)"""
        return self.handle_error('element', element_name, "페이지가 갱신 중이거나 구조가 변경되었을 수 있습니다.")

    def handle_general_error(self, operation_name, error):
        """일반적인 오류 처리 (하위 호환성 위해 BaseModule로 전달)"""
        return self.handle_error('unknown', f"{operation_name} 실패: {str(error)}")
    
    def execute(self):
        """퀴즈풀기 실행 - 로컬 DB 연동 및 블로그 검색 하이브리드 방식"""
        try:
            self.log_info("퀴즈풀기 시작...")
            
            # 0단계: 현재 창 핸들 저장
            self.original_window = self.web_automation.driver.current_window_handle
            
            # 1단계: 퀴즈가 있는 페이지 찾기
            quiz_page = self.find_quiz_page()
            if not quiz_page:
                self.log_warning("오늘은 퀴즈가 제공되지 않습니다.")
                self.check_points_after_activity()
                return self.create_result(False, "오늘은 퀴즈가 제공되지 않습니다.")
            
            # 2단계: 퀴즈 팝업 열기
            if not self.open_quiz_popup():
                return self.create_result(False, "퀴즈 팝업 열기 실패")
            
            # 3단계: 문제 정보 수집 (팝업 열린 직후 수집)
            quiz_data = self.collect_quiz_info()
            if not quiz_data:
                return self.create_result(False, "퀴즈 정보 수집 실패")
            
            # 4단계: 각 문제별 정답 확보 및 즉시 선택 (survey_module 방식)
            blog_answers_str = None
            blog_searched = False
            
            for i, q_info in enumerate(quiz_data['questions']):
                self.log_info(f"--- [문제 {i+1}] 분석 및 답변 시작 ---")
                
                success, blog_answers_str, blog_searched = self._process_single_question(
                    q_info, i, quiz_data, blog_answers_str, blog_searched
                )
                
                if not success:
                    return self.create_result(False, f"문제 {i+1} 정답 부재 또는 선택 실패로 인해 진행 불가")
            
            # 5단계: 모든 정답 선택 후 제출
            self.log_info("✨ 모든 문제 답변 완료. '정답 도전' 버튼을 클릭합니다.")
            if self.click_submit_button():
                # 블로그에서 새로 찾은 정답이 있다면 DB에 학습 (나중에 또 안물어보게)
                if blog_answers_str:
                    self.save_to_local_db(quiz_data, blog_answers_str)
                
                self.check_points_after_activity()
                self.log_success("🎉 일일 퀴즈 풀기 대성공!")
                return self.create_result(True, "일일 퀴즈 풀기 성공 및 데이터 학습 완료")
            else:
                return self.create_result(False, "답안 제출 버튼 클릭 실패")
            
        except Exception as e:
            error_msg = f"퀴즈풀기 실행 실패: {str(e)}"
            self.log_error(error_msg)
            return self.create_result(False, error_msg)
        finally:
            # 🗑️ 블로그 탭 정리 (남아있다면)
            try:
                if self.blog_window:
                    self.web_automation.driver.switch_to.window(self.blog_window)
                    self.web_automation.driver.close()
                    self.log_info("🔓 블로그 참고 탭을 닫았습니다.")
                    self.web_automation.driver.switch_to.window(self.original_window)
            except:
                pass

    def _process_single_question(self, q_info, index, quiz_data, blog_answers_str, blog_searched):
        """단일 문제에 대해 정답을 찾고 선택하는 로직 처리"""
        q_text = q_info['question']
        
        # 1. 로컬 DB에서 정답 찾기
        ans = self._find_answer_in_local_db(q_text)
        
        # 2. 로컬 DB에 없으면 블로그 검색 (최초 1회만)
        if not ans and not blog_searched:
            blog_searched = True
            ans, blog_answers_str = self._search_answer_from_blog(index)
        
        # 3. 블로그에도 없거나 이미 검색했었다면 캐시된 블로그 정답 확인
        if not ans and blog_answers_str and index < len(blog_answers_str):
            ans = blog_answers_str[index]
            
        # 4. 그래도 없으면 수동 개입 유도
        if not ans:
            self.log_warning(f"문제 {index+1}의 정답을 찾을 수 없습니다. 수동 입력을 요청합니다.")
            if self.prompt_single_question_intervention(quiz_data, index):
                self.problem_manager.load_quizzes()
                ans = self.problem_manager.get_answer(q_text)
                
        # 5. 정답 선택
        if ans:
            if self.select_single_answer(q_info, ans):
                self.log_success(f"✅ 문제 {index+1} 답변 선택 완료: {ans}")
                return True, blog_answers_str, blog_searched
            else:
                self.log_error(f"❌ 문제 {index+1} 답변 선택 실패")
                return False, blog_answers_str, blog_searched
                
        self.log_error(f"❌ 문제 {index+1}의 정답을 끝내 확보하지 못했습니다.")
        return False, blog_answers_str, blog_searched

    def _find_answer_in_local_db(self, q_text):
        """DB에서 문제를 정규화하여 정답 검색"""
        self.log_info(f"🔍 [DEBUG] 웹 문제 원문: '{q_text[:60]}...'")
        normalized = self.problem_manager._normalize_question(q_text)
        self.log_info(f"🔍 [DEBUG] 정규화 후: '{normalized[:60]}...'")
        
        self.log_info(f"🔍 [DEBUG] DB에 저장된 키 {len(self.problem_manager.quiz_answers)}개:")
        for db_key in self.problem_manager.quiz_answers:
            if db_key in normalized:
                self.log_info(f"   ✅ 부분일치 발견! (DB키 ⊂ 정규화문제): '{db_key[:60]}...'")
            elif normalized in db_key:
                self.log_info(f"   ✅ 역방향 부분일치 발견! (정규화문제 ⊂ DB키): '{db_key[:60]}...'")
                
        ans = self.problem_manager.get_answer(q_text)
        self.log_info(f"🔍 [DEBUG] get_answer 결과: {ans}")
        return ans

    def _search_answer_from_blog(self, current_index):
        """1회성 블로그 검색 수행 및 탭 정리"""
        self.log_info("로컬 DB에 정답이 없어 블로그 검색을 1회 수행합니다...")
        
        # 블로그 검색 전 현재 열린 탭 상태 저장
        initial_handles = set(self.web_automation.driver.window_handles)
        
        blog_answers_str = self.try_blog_search()
        
        # 블로그 검색에 따른 탭 정리 (새로 열린 탭만 식별)
        self._close_blog_tab_safely(initial_handles)
        
        ans = None
        if blog_answers_str and current_index < len(blog_answers_str):
            ans = blog_answers_str[current_index]
            
        return ans, blog_answers_str

    def _close_blog_tab_safely(self, initial_handles):
        """검색 목록 탭은 닫고 게시글 탭만 남기는 로직 (원래 창으로 복귀 포함)"""
        current_handles = self.web_automation.driver.window_handles
        new_handles = [h for h in current_handles if h not in initial_handles]
        
        if new_handles:
            # 새로 열린 탭 중 가장 마지막 탭(게시글 본문)을 힌트용으로 저장
            self.blog_window = new_handles[-1]
            
            # 나머지 중간 과정 탭(검색 결과 등)은 모두 닫음
            for handle in new_handles[:-1]:
                try:
                    self.web_automation.driver.switch_to.window(handle)
                    self.web_automation.driver.close()
                    self.log_info("🗑️ 블로그 검색 중간 목록 탭 닫기 완료")
                except Exception:
                    pass
        else:
            self.blog_window = None
            
        # 원래 탭으로 복귀
        try:
            self.web_automation.driver.switch_to.window(self.original_window)
        except Exception as e:
            self.log_error(f"원본 탭 복귀 실패: {str(e)}")

    def find_quiz_page(self):
        """1단계: 퀴즈가 있는 페이지 찾기"""
        try:
            self.log_info("퀴즈가 있는 페이지를 찾는 중...")
            
            # 의약품 페이지에서 시도
            if self.check_page_for_quiz(MEDICINE_PAGE_URL, "의약품"):
                return "medicine"
                
            # 기구 페이지에서 시도  
            if self.check_page_for_quiz(INSTRUMENT_PAGE_URL, "기구"):
                return "instrument"
                
            return None  # 퀴즈가 있는 페이지 없음
            
        except Exception as e:
            self.log_error(f"퀴즈 페이지 찾기 실패: {str(e)}")
            return None

    def check_page_for_quiz(self, url, page_name):
        """특정 페이지에 퀴즈가 있는지 확인"""
        try:
            self.log_info(f"{page_name} 페이지에서 퀴즈 확인 중...")
            
            # 페이지로 이동
            if not self.navigate_to_page(url, page_name):
                return False
            
            # 퀴즈 요소만 확인 (클릭하지 않음)
            if self.has_quiz_elements():
                self.log_success(f"{page_name} 페이지에서 퀴즈 발견!")
                return True
            else:
                self.log_warning(f"{page_name} 페이지에 퀴즈가 없습니다.")
                return False
                
        except Exception as e:
            self.log_error(f"{page_name} 페이지 확인 실패: {str(e)}")
            return False



    def navigate_to_page(self, url, page_name):
        """페이지로 이동하고 로딩 완료 대기"""
        try:
            self.log_info(f"{page_name} 페이지로 이동 중...")
            
            self.web_automation.driver.get(url)
            
            # 페이지 로딩 대기
            if self.wait_for_page_load():
                self.log_success(f"{page_name} 페이지 로딩 완료")
                return True
            else:
                self.log_error(f"{page_name} 페이지 로딩 시간 초과")
                return False
                
        except Exception as e:
            self.log_error(f"{page_name} 페이지 이동 실패: {str(e)}")
            return False



    def has_quiz_elements(self):
        """퀴즈 요소가 있는지 확인 (1단계용 - 클릭하지 않음)"""
        try:
            self.log_info("퀴즈 요소 확인 중...")
            
            # JavaScript를 사용하여 더 빠르게 퀴즈 요소 확인
            try:
                quiz_count = self.web_automation.driver.execute_script(
                    f"return document.querySelectorAll('{QUIZ_CSS_SELECTOR}').length;"
                )
                
                if quiz_count >= MIN_QUIZ_ELEMENTS:
                    self.log_success(f"퀴즈 요소 {quiz_count}개 발견")
                    return True
                else:
                    self.log_warning(f"퀴즈 요소 {quiz_count}개 발견 (최소 {MIN_QUIZ_ELEMENTS}개 필요)")
                    return False
                    
            except Exception as js_error:
                self.log_warning(f"JavaScript 확인 실패, 일반 방법으로 시도: {str(js_error)}")
                
                # JavaScript 실패 시 일반 방법으로 확인
                quiz_elements = self.web_automation.driver.find_elements(By.CSS_SELECTOR, QUIZ_CSS_SELECTOR)
                
                if len(quiz_elements) >= MIN_QUIZ_ELEMENTS:
                    self.log_success(f"퀴즈 요소 {len(quiz_elements)}개 발견")
                    return True
                else:
                    self.log_warning(f"퀴즈 요소 {len(quiz_elements)}개 발견 (최소 {MIN_QUIZ_ELEMENTS}개 필요)")
                    return False
                
        except Exception as e:
            self.log_error(f"퀴즈 요소 확인 실패: {str(e)}")
            return False
    
    def click_quiz_element(self):
        """2단계: 퀴즈 요소 클릭 (페이지 이동)"""
        try:
            self.log_info("퀴즈 요소를 클릭하는 중...")
            
            # quiz_bg 클래스를 가진 요소들 찾기
            quiz_elements = self.web_automation.driver.find_elements(By.CSS_SELECTOR, QUIZ_CSS_SELECTOR)
            
            if len(quiz_elements) >= MIN_QUIZ_ELEMENTS:
                self.log_success(f"퀴즈 요소 {len(quiz_elements)}개 발견")
                
                # 두 번째 퀴즈 요소 클릭 (페이지 이동)
                if self.click_second_quiz_element(quiz_elements[1]):
                    self.log_success("퀴즈 요소 클릭 완료 - 페이지 이동됨")
                    return True
                
                return False
            else:
                self.log_warning(f"퀴즈 요소가 {len(quiz_elements)}개 발견되었습니다. (최소 {MIN_QUIZ_ELEMENTS}개 필요)")
                return False
                
        except Exception as e:
            self.log_error(f"퀴즈 요소 클릭 실패: {str(e)}")
            return False

    def click_second_quiz_element(self, second_quiz):
        """두 번째 퀴즈 요소 클릭 (페이지 이동)"""
        try:
            # 부모 요소(링크)를 찾아서 JavaScript로 클릭
            parent_link = second_quiz.find_element(By.XPATH, "./..")
            
            # JavaScript를 사용한 클릭 (더 빠르고 안정적)
            self.web_automation.driver.execute_script("arguments[0].click();", parent_link)
            
            self.log_success("퀴즈 요소 클릭 완료 - 페이지 이동 중...")
            
            # 페이지 로딩 대기
            if not self.wait_for_page_load():
                self.log_error("페이지 로딩 시간 초과")
                return False
            return True
                
        except Exception as e:
            self.log_error(f"퀴즈 요소 클릭 실패: {str(e)}")
            return False



    def click_quiz_button(self):
        """2단계: 퀴즈 버튼 클릭 (팝업 열기)"""
        try:
            self.log_info("퀴즈 버튼을 클릭하는 중...")
            
            # 퀴즈 버튼 찾기
            quiz_button = self.web_automation.driver.find_element(By.ID, QUIZ_BANNER_BUTTON_ID)
            
            if quiz_button:
                # 버튼이 클릭 가능한 상태가 될 때까지 대기
                if not self.wait_for_element_clickable(QUIZ_BANNER_BUTTON_ID):
                    return self.handle_element_not_found("클릭 가능한 퀴즈 버튼")
                
                # 퀴즈 버튼 클릭
                quiz_button.click()
                
                self.log_success("퀴즈 버튼 클릭 완료 - 팝업창이 열렸습니다")
                return True
            else:
                self.log_error("퀴즈 버튼을 찾을 수 없습니다.")
                return False
                
        except NoSuchElementException:
            return self.handle_element_not_found("퀴즈 버튼")
        except Exception as e:
            return self.handle_general_error("퀴즈 버튼 클릭", e)



    def collect_quiz_info(self):
        """퀴즈 팝업창에서 문제와 보기 정보를 수집"""
        try:
            self.log_info("퀴즈 정보 수집 시작...")
            
            # 제품 정보 수집
            product_title = self.web_automation.driver.find_element(By.ID, PRODUCT_TITLE_ID).text.strip()
            product_category = self.web_automation.driver.find_element(By.ID, PRODUCT_CATEGORY_ID).text.strip()
            product_title_eng = self.web_automation.driver.find_element(By.ID, PRODUCT_TITLE_ENG_ID).text.strip()
            quiz_point = self.web_automation.driver.find_element(By.ID, QUIZ_POINT_ID).text.strip()
            
            self.log_info(f"=== 퀴즈 정보 ===")
            self.log_info(f"제품명: {product_title}")
            self.log_info(f"카테고리: {product_category}")
            self.log_info(f"영문명: {product_title_eng}")
            self.log_info(f"포인트: {quiz_point}")
            self.log_info(f"==================")
            
            # 퀴즈 데이터 구조 생성
            quiz_data = {
                'product_info': {
                    'title': product_title,
                    'category': product_category,
                    'title_eng': product_title_eng,
                    'point': quiz_point
                },
                'questions': []
            }
            
            # 퀴즈 문제 영역 컨테이너만 사용 (다른 영역의 .question_area 제외)
            try:
                quiz_container = self.web_automation.driver.find_element(By.ID, QUESTION_AREA_CONTAINER_ID)
            except NoSuchElementException:
                self.log_error(f"퀴즈 문제 영역(id={QUESTION_AREA_CONTAINER_ID})을 찾을 수 없습니다.")
                return None
            
            # 실제 존재하는 문제 개수 확인 (.question1, .question2, ... 순으로 확인)
            question_count = 0
            for n in range(1, 10):
                try:
                    quiz_container.find_element(By.CSS_SELECTOR, f".question{n}")
                    question_count = n
                except NoSuchElementException:
                    break
            
            if question_count == 0:
                self.log_error("존재하는 퀴즈 문제(.questionN)를 찾을 수 없습니다.")
                return None
            
            self.log_info(f"실제 퀴즈 문제 개수: {question_count}개")
            
            # 각 문제 번호(n)에 대해 해당 .question{n}을 포함한 .question_area만 수집
            for n in range(1, question_count + 1):
                try:
                    question_num_elem = quiz_container.find_element(By.CSS_SELECTOR, f".question{n}")
                    question_number = question_num_elem.text.strip()
                    # .question{n}이 속한 .question_area 찾기 (closest)
                    question_area = self.web_automation.driver.execute_script(
                        "return arguments[0].closest('.question_area');", question_num_elem
                    )
                    if not question_area:
                        self.log_error(f"문제 {n}: .question_area를 찾을 수 없습니다.")
                        continue
                    
                    # 문제 내용
                    question_text = question_area.find_element(By.CSS_SELECTOR, QUESTION_TEXT_SELECTOR).text.strip()
                    
                    # 보기들 수집
                    choices = question_area.find_elements(By.CSS_SELECTOR, QUESTION_CHOICE_SELECTOR)
                    choice_list = []
                    
                    for choice in choices:
                        choice_text = choice.find_element(By.CSS_SELECTOR, CHOICE_LABEL_SELECTOR).text.strip()
                        choice_value = choice.find_element(By.CSS_SELECTOR, CHOICE_INPUT_SELECTOR).get_attribute("value")
                        choice_list.append(f"{choice_value}. {choice_text}")
                    
                    choice_values = []
                    for choice in choice_list:
                        if '. ' in choice:
                            choice_values.append(choice.split('. ', 1)[0])
                        else:
                            choice_values.append(choice)
                    
                    quiz_data['questions'].append({
                        'number': question_number,
                        'question': question_text,
                        'choices': choice_list,
                        'choice_values': choice_values
                    })
                    
                    self.log_info(f"--- {question_number} ---")
                    self.log_info(f"문제: {question_text}")
                    for choice in choice_list:
                        self.log_info(f"보기: {choice}")
                    self.log_info(f"----------------")
                        
                except Exception as e:
                    self.log_error(f"문제 {n} 수집 중 오류: {str(e)}")
                    continue
            
            return quiz_data
            
        except Exception as e:
            self.log_error(f"퀴즈 정보 수집 실패: {str(e)}")
            return None

    def select_single_answer(self, question, answer):
        """특정 문제 하나에 대한 정답 선택 (번호 및 텍스트 매핑 지원)"""
        try:
            # 🔥 0. 항상 닥터빌 메인 탭으로 전환 후 시작
            if self.original_window:
                self.web_automation.driver.switch_to.window(self.original_window)
            
            # 🔥 1. 퀴즈 팝업이 아직 열려있는지 확인
            try:
                quiz_popup = self.web_automation.driver.find_element(By.ID, QUIZ_LAYER_POP_ID)
                if not quiz_popup.is_displayed():
                    self.log_warning("퀴즈 팝업이 숨겨져 있습니다. 다시 표시 시도...")
                    self.web_automation.driver.execute_script(
                        "arguments[0].style.display = 'block';", quiz_popup
                    )
                    time.sleep(0.5)
            except:
                self.log_warning("퀴즈 팝업 상태 확인 실패 - 계속 진행합니다.")
                
            question_num = question['number']
            
            # 입력값 정규화 (대문자 변환 등)
            clean_input = str(answer).strip().upper()
            
            # 2. 명시적 매핑 확인 (O -> 1, X -> 2 등)
            correct_val = ANSWER_MAPPING.get(clean_input, clean_input)
            
            # 3. 숫자가 아닌 경우 숫자로 파싱 시도 (1.0 -> 1 등)
            if correct_val not in VALID_ANSWER_VALUES:
                try:
                    correct_val = str(int(float(clean_input)))
                except (ValueError, TypeError):
                    pass
            
            # 4. 라디오 버튼 선택 (JS 완전 제어 - 팝업 내부 요소 대응)
            try:
                num_only = "".join(filter(str.isdigit, question_num))
                radio_selector = f"input[name='an_{num_only}'][value='{correct_val}']"
                self.log_info(f"🔍 셀렉터: {radio_selector}")
                
                # 🔥 순수 JS로 모든 작업 수행 (Selenium 클릭 우회) 헬퍼 메서드로 분리
                click_result = self._inject_radio_click_js(radio_selector)
                
                self.log_info(f"🔍 클릭 결과: {click_result}")
                
                if click_result and 'FAILED' not in click_result and 'NOT_FOUND' not in click_result:
                    return True
                else:
                    self.log_error(f"라디오 버튼 선택 실패: {click_result}")
                    return False
            except Exception as e:
                self.log_error(f"라디오 버튼(값:{correct_val}) 오류: {str(e)}")
                return False
        except Exception as e:
            self.log_error(f"단일 답안 선택 로직 오류: {str(e)}")
            return False

    def _inject_radio_click_js(self, radio_selector):
        """라디오 버튼 강제 클릭을 위한 순수 JavaScript 헬퍼 메서드"""
        js_code = """
            var radio = document.querySelector(arguments[0]);
            if (!radio) return 'RADIO_NOT_FOUND';
            
            // 방법 1: 부모 li 안의 label을 JS 클릭
            var li = radio.closest('li');
            if (li) {
                var label = li.querySelector('label');
                if (label) {
                    label.click();
                    if (radio.checked) return 'LABEL_CLICK_OK';
                }
            }
            
            // 방법 2: label[for=id] 클릭
            if (radio.id) {
                var forLabel = document.querySelector("label[for='" + radio.id + "']");
                if (forLabel) {
                    forLabel.click();
                    if (radio.checked) return 'FOR_LABEL_CLICK_OK';
                }
            }
            
            // 방법 3: 강제 체크 + change 이벤트
            radio.checked = true;
            radio.dispatchEvent(new Event('change', {bubbles: true}));
            radio.dispatchEvent(new Event('click', {bubbles: true}));
            return radio.checked ? 'FORCE_CHECK_OK' : 'FAILED';
        """
        return self.web_automation.driver.execute_script(js_code, radio_selector)



    def click_submit_button(self):
        """정답 도전 버튼 클릭"""
        try:
            self.log_info("정답 도전 버튼을 찾는 중...")
            
            # 정답 도전 버튼이 클릭 가능한 상태가 될 때까지 대기
            if not self.wait_for_element_clickable(ANSWER_CONFIRM_BUTTON_ID):
                return self.handle_element_not_found("클릭 가능한 정답 도전 버튼")
            
            # 정답 도전 버튼 찾기
            submit_button = self.web_automation.driver.find_element(By.ID, ANSWER_CONFIRM_BUTTON_ID)
            
            if submit_button:
                # 정답 도전 버튼 클릭
                submit_button.click()
                
                self.log_success("정답 도전 버튼 클릭 완료")
                
                # 결과 처리 대기 (성공/실패 메시지 등)
                time.sleep(2)
                
                return True
            else:
                self.log_error("정답 도전 버튼을 찾을 수 없습니다.")
                return False
                
        except NoSuchElementException:
            return self.handle_element_not_found("정답 도전 버튼")
        except Exception as e:
            return self.handle_general_error("정답 도전 버튼 클릭", e)



    def save_to_local_db(self, quiz_data, extracted_answer):
        """새로 알아낸 정답을 로컬 DB에 자동 저장 (학습)"""
        try:
            self.log_info("새로운 퀴즈 정보를 로컬 DB에 학습시키는 중...")
            answer_chars = list(extracted_answer)
            product_title = quiz_data['product_info']['title'] # 카테고리로 제품명 사용
            
            saved_count = 0
            for i, question_info in enumerate(quiz_data['questions']):
                if i < len(answer_chars):
                    q_text = question_info['question']
                    ans = answer_chars[i]
                    # SurveyProblemManager에 추가 (파일 자동 저장 포함됨)
                    if self.problem_manager.add_quiz(q_text, ans, product_title):
                        saved_count += 1
            
            if saved_count > 0:
                self.log_success(f"{saved_count}개의 새로운 퀴즈 데이터를 로컬 DB에 저장했습니다.")
                return True
            return False
        except Exception as e:
            self.log_error(f"로컬 DB 저장 중 오류: {str(e)}")
            return False

    def prompt_single_question_intervention(self, quiz_data, question_index):
        """특정 문제 하나에 대해 수동 개입 유도 (설문 방식 + 블로그 힌트 지원)"""
        try:
            q_info = quiz_data['questions'][question_index]
            q_text = q_info['question']
            prod_title = quiz_data['product_info']['title']
            
            screenshot_paths = []
            
            # 🔥 1. 블로그 힌트 캡처 (있는 경우)
            if self.blog_window:
                try:
                    self.log_info(f"🔎 블로그 탭에서 문제 {question_index+1} 힌트 캡처 중...")
                    self.web_automation.driver.switch_to.window(self.blog_window)
                    
                    # 네이버 블로그 전용: 본문 iframe으로 전환 시도 및 스크롤
                    try:
                        # 1단계: mainFrame 찾기
                        main_frame = self.web_automation.driver.find_element(By.ID, "mainFrame")
                        self.web_automation.driver.switch_to.frame(main_frame)
                        
                        # 2단계: 정답이 몰려있는 영역(보통 이미지나 텍스트 하단)으로 스크롤
                        # 3번째 이미지 혹은 특정 텍스트 요소를 찾아 중앙 배치 시도
                        se_images = self.web_automation.driver.find_elements(By.CLASS_NAME, "se-image-resource")
                        if len(se_images) >= 3:
                            target_hint = se_images[2] # 3번째 이미지가 보통 퀴즈 영역 근처
                            self.web_automation.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_hint)
                        else:
                            # 이미지가 부족하면 그냥 적당히 스크롤
                            self.web_automation.driver.execute_script("window.scrollTo(0, 1000);")
                        
                        time.sleep(1.0) # 로딩/정지 대기
                    except:
                        # iframe을 못 찾거나 스크롤 실패 시 그냥 진행
                        pass

                    # 현재 뷰포트 캡처
                    hint_path = os.path.join(os.getcwd(), f"quiz_hint_q{question_index+1}.png")
                    self.web_automation.driver.save_screenshot(hint_path)
                    screenshot_paths.append(hint_path)
                    
                    # 마무리: 반드시 메인 컨텐츠로 복귀 후 닥터빌 탭으로 전환
                    self.web_automation.driver.switch_to.default_content()
                    self.web_automation.driver.switch_to.window(self.original_window)
                except Exception as b_err:
                    self.log_warning(f"블로그 힌트 캡처 중 경미한 오류: {b_err}")
                    # 실패 시에도 원래 창으로는 돌아와야 함
                    try: self.web_automation.driver.switch_to.window(self.original_window)
                    except: pass

            # 2. 닥터빌 문제는 캡처하지 않음 (사용자 요청: 블로그 힌트만 필요)
            if not screenshot_paths:
                # 블로그 힌트가 없는 경우에만 현재 화면(닥터빌)을 폴백으로 캡처
                f_path = os.path.join(os.getcwd(), f"quiz_full_fallback.png")
                self.web_automation.driver.save_screenshot(f_path)
                screenshot_paths.append(f_path)

            # 3. GUI 호출 (모든 스크린샷 전달)
            if 'on_quiz_problem' in self.gui_callbacks:
                self.gui_callbacks['on_quiz_problem'](
                    initial_question=q_text,
                    initial_category=prod_title,
                    image_path=screenshot_paths
                )
                self.log_info(f"❓ 사진들을 보고 문제 {question_index+1} 정답을 입력해 주세요.")
                
                # 4. 동기식 실시간 루프 대기
                self.log_info(f"⌛ 정답 등록 대기 중... (최대 10분)")
                waiting_seconds = 0
                max_wait = 600
                
                while waiting_seconds < max_wait:
                    # 🔥 사용자의 작업 중지(취소) 요청 시 루프 강제 탈출 (Graceful Exit)
                    if hasattr(self.web_automation, 'is_running') and not self.web_automation.is_running:
                        self.log_warning("작업 중지 신호 감지: 대기를 강제 종료합니다.")
                        return False

                    try: _ = self.web_automation.driver.title
                    except: return False

                    self.problem_manager.load_quizzes()
                    if self.problem_manager.get_answer(q_text):
                        self.log_success(f"새로운 정답 확인완료 ({waiting_seconds}초 대기함)")
                        return True
                        
                    time.sleep(1.0)
                    waiting_seconds += 1
                
                self.log_warning(f"입력 대기 시간({max_wait}초)이 초과되었습니다.")
            else:
                self.log_error("GUI 콜백(on_quiz_problem) 누락")
                
        except Exception as e:
            self.log_error(f"수동 개입 유도 오류: {str(e)}")
        finally:
            # 🔥 사용이 끝난 임시 스크린샷 파일들 정리
            if 'screenshot_paths' in locals() and screenshot_paths:
                for path in screenshot_paths:
                    if os.path.exists(path):
                        try:
                            # 약간의 지연 후 삭제 (이미지 뷰어가 파일을 놓아줄 시간)
                            time.sleep(0.5) 
                            os.remove(path)
                            self.log_info(f"🗑️ 임시 파일 삭제 완료: {os.path.basename(path)}")
                        except:
                            # 파일이 열려있어 삭제 실패해도 무시
                            pass
        return False

    def open_quiz_popup(self):
        """2단계: 퀴즈 팝업 열기"""
        try:
            self.log_info("퀴즈 팝업을 여는 중...")
            
            # 1. 퀴즈 요소 클릭 (페이지 이동)
            if not self.click_quiz_element():
                return False
            
            # 2. 새 페이지에서 퀴즈 버튼 찾기
            if not self.wait_for_quiz_button():
                return False
            
            # 3. 퀴즈 버튼 클릭 (팝업 열기)
            if not self.click_quiz_button():
                return False
            
            self.log_success("퀴즈 팝업 열기 완료!")
            return True
            
        except Exception as e:
            self.log_error(f"퀴즈 팝업 열기 실패: {str(e)}")
            return False

    def wait_for_quiz_button(self):
        """새 페이지에서 퀴즈 버튼이 나타날 때까지 대기"""
        try:
            self.log_info("새 페이지에서 퀴즈 버튼을 찾는 중...")
            
            # 페이지 로딩 대기
            if not self.wait_for_page_load():
                self.log_error("페이지 로딩 시간 초과")
                return False
            
            # 퀴즈 버튼이 나타날 때까지 대기
            if not self.wait_for_element_presence(QUIZ_BANNER_BUTTON_ID):
                self.log_error("퀴즈 버튼을 찾을 수 없습니다")
                return False
            
            self.log_success("퀴즈 버튼 발견!")
            return True
            
        except Exception as e:
            self.log_error(f"퀴즈 버튼 대기 실패: {str(e)}")
            return False



    def try_blog_search(self):
        """블로그 검색 모듈 안전하게 실행"""
        try:
            # 블로그 검색 모듈 임포트 시도
            try:
                from modules.blog_search_module import BlogSearchModule
            except ImportError as import_error:
                self.log_error(f"블로그 검색 모듈 임포트 실패: {import_error}")
                return None
            
            # 블로그 검색 모듈 초기화 시도
            try:
                blog_search_module = BlogSearchModule(self.web_automation, self.gui_logger)
            except Exception as init_error:
                self.log_error(f"블로그 검색 모듈 초기화 실패: {init_error}")
                return None
            
            # 블로그 검색 실행 시도
            try:
                result = blog_search_module.execute()
                
                is_success = False
                if isinstance(result, dict):
                    is_success = result.get('success', False)
                else:
                    is_success = bool(result)

                if is_success:
                    answer = blog_search_module.get_extracted_answer()
                    if answer:
                        return answer
                    else:
                        self.log_warning("블로그 검색 완료되었지만 정답을 추출하지 못했습니다")
                        return None
                else:
                    msg = result.get('message', '블로그 검색 실행 실패') if isinstance(result, dict) else '블로그 검색 실행 실패'
                    self.log_warning(msg)
                    return None
                    
            except Exception as exec_error:
                self.log_error(f"블로그 검색 실행 중 오류: {exec_error}")
                return None
                
        except Exception as e:
            self.log_error(f"블로그 검색 전체 실패: {str(e)}")
            return None

