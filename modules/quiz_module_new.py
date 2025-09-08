# -*- coding: utf-8 -*-
"""
새로운 퀴즈풀기 모듈
닥터빌 퀴즈풀기 기능을 담당합니다.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_module import BaseModule
import time

# URL 상수 정의
MEDICINE_PAGE_URL = "https://www.doctorville.co.kr/product/medicineList"
INSTRUMENT_PAGE_URL = "https://www.doctorville.co.kr/product/instrumentList"

# CSS 선택자 상수 정의
QUIZ_CSS_SELECTOR = ".quiz_bg"
QUIZ_BANNER_BUTTON_ID = "btn_quiz_banner"
QUIZ_LAYER_POP_ID = "quizLayerPop"
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

class QuizModuleNew(BaseModule):
    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
    
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
        """요소를 찾을 수 없을 때의 공통 처리"""
        self.log_error(f"{element_name}을(를) 찾을 수 없습니다.")
        return False
    
    def handle_general_error(self, operation_name, error):
        """일반적인 오류 처리"""
        self.log_error(f"{operation_name} 실패: {str(error)}")
        return False
    
    def execute(self):
        """퀴즈풀기 실행 - 주말 퀴즈 부재 상황도 고려"""
        try:
            self.log_info("퀴즈풀기 시작...")
            
            # 1단계: 퀴즈가 있는 페이지 찾기
            quiz_page = self.find_quiz_page()
            if not quiz_page:
                self.log_warning("두 페이지 모두에 퀴즈 요소가 없습니다.")
                self.log_warning("오늘은 퀴즈가 제공되지 않습니다.")
                self._check_points_after_quiz()
                return False
            
            # 2단계: 퀴즈 팝업 열기
            if not self.open_quiz_popup():
                return False
            
            # 3단계: 블로그 검색으로 정답 얻기
            answer = self.get_answer_from_blog()
            if not answer:
                self.log_error("블로그 검색 실패로 퀴즈를 중단합니다")
                return False
            
            # 4단계: 퀴즈 풀기
            if self.solve_quiz(answer):
                self._check_points_after_quiz()
                return True
            else:
                return False
            
        except Exception as e:
            self.log_error(f"퀴즈풀기 실행 실패: {str(e)}")
            return False

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

    def try_instrument_page(self):
        """기구 페이지에서 QUIZ 요소 찾기 및 처리"""
        try:
            self.log_info("기구 페이지로 이동하여 QUIZ 요소 확인 중...")
            
            # 기구 페이지로 이동
            if not self.navigate_to_page(INSTRUMENT_PAGE_URL, "기구"):
                return False
            
            # QUIZ 요소 확인 및 처리
            if self.check_and_process_quiz_elements("기구"):
                return True
            
            self.log_warning("기구 페이지에도 QUIZ 요소를 찾을 수 없습니다.")
            return False
            
        except Exception as e:
            self.log_error(f"기구 페이지 처리 실패: {str(e)}")
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

    def check_and_process_quiz_elements(self, page_name):
        """QUIZ 요소 확인 및 처리"""
        try:
            # QUIZ 요소 즉시 확인
            if self.instant_check_quiz_elements():
                self.log_success(f"{page_name} 페이지에서 QUIZ 요소 발견")
                
                # QUIZ 요소 클릭 및 처리
                if self.click_quiz_element():
                    self.log_success(f"{page_name} 페이지에서 QUIZ 요소 클릭 완료")
                    
                    # 퀴즈 완료 후 포인트 확인
                    self.log_info("퀴즈 완료!")
                    
                    # 포인트 확인 (로그인/출석체크와 동일한 방식)
                    self._check_points_after_quiz()
                    
                    return True
            
            return False
            
        except Exception as e:
            self.log_error(f"{page_name} 페이지 QUIZ 요소 처리 실패: {str(e)}")
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

    def process_after_quiz_click(self):
        """QUIZ 요소 클릭 후 처리 로직"""
        try:
            # 블로그 검색 모듈 실행
            if self.execute_blog_search():
                self.log_success("블로그 검색 모듈 실행 완료")
                
                # 블로그 검색 완료 후 "quiz 풀고 포인트 적립" 버튼 클릭
                if self.click_quiz_button():
                    self.log_success("Quiz 풀고 포인트 적립 버튼 클릭 완료")
                    return True
                else:
                    self.log_error("Quiz 풀고 포인트 적립 버튼 클릭 실패")
                    return False
            else:
                self.log_error("블로그 검색 모듈 실행 실패")
                return False
                
        except Exception as e:
            self.log_error(f"QUIZ 클릭 후 처리 실패: {str(e)}")
            return False
    
    def execute_blog_search(self):
        """블로그 검색 모듈 실행"""
        try:
            self.log_info("블로그 검색 모듈을 실행합니다...")
            
            from modules.blog_search_module import BlogSearchModule
            
            blog_search_module = BlogSearchModule(self.web_automation, self.gui_logger)
            result = blog_search_module.execute()
            
            if result:
                # 추출된 정답 저장
                self.extracted_answer = blog_search_module.get_extracted_answer()
                self.log_success(f"블로그 검색 모듈에서 추출된 정답: {self.extracted_answer}")
            
            return result
            
        except Exception as e:
            self.log_error(f"블로그 검색 모듈 실행 실패: {str(e)}")
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

    def solve_quiz_with_extracted_answer(self):
        """추출한 정답을 사용해서 퀴즈 풀기"""
        try:
            self.log_info("추출한 정답으로 퀴즈 풀기 시작...")
            
            # 퀴즈 팝업창이 로드될 때까지 대기
            if not self.wait_for_element_presence(QUIZ_LAYER_POP_ID):
                return self.handle_element_not_found("퀴즈 팝업창")
            
            # 추출한 정답 가져오기 (blog_search_module에서 저장된 정답)
            extracted_answer = self.get_extracted_answer()
            
            if not extracted_answer:
                self.log_warning("추출된 정답을 찾을 수 없습니다.")
                return False
            
            self.log_success(f"추출된 정답: {extracted_answer}")
            
            # 퀴즈 문제 수집
            quiz_data = self.collect_quiz_info()
            
            if not quiz_data:
                self.log_error("퀴즈 정보를 수집할 수 없습니다.")
                return False
            
            # 추출한 정답으로 답안 선택
            if self.select_answers_with_extracted_answer(quiz_data, extracted_answer):
                self.log_success("답안 선택 완료")
                return True
            else:
                self.log_error("답안 선택 실패")
                return False
                
        except Exception as e:
            self.log_error(f"추출한 정답으로 퀴즈 풀기 실패: {str(e)}")
            return False

    def get_extracted_answer(self):
        """추출된 정답 가져오기"""
        if hasattr(self, 'extracted_answer') and self.extracted_answer:
            return self.extracted_answer
        else:
            self.log_warning("추출된 정답이 없습니다.")
            return None

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
            
            # 문제들 수집
            question_areas = self.web_automation.driver.find_elements(By.CSS_SELECTOR, QUESTION_AREA_SELECTOR)
            
            for i, question_area in enumerate(question_areas, 1):
                try:
                    # 문제 번호
                    question_number = question_area.find_element(By.CSS_SELECTOR, f".question{{}}".format(i)).text.strip()
                    
                    # 문제 내용
                    question_text = question_area.find_element(By.CSS_SELECTOR, QUESTION_TEXT_SELECTOR).text.strip()
                    
                    # 보기들 수집
                    choices = question_area.find_elements(By.CSS_SELECTOR, QUESTION_CHOICE_SELECTOR)
                    choice_list = []
                    
                    for choice in choices:
                        choice_text = choice.find_element(By.CSS_SELECTOR, CHOICE_LABEL_SELECTOR).text.strip()
                        choice_value = choice.find_element(By.CSS_SELECTOR, CHOICE_INPUT_SELECTOR).get_attribute("value")
                        choice_list.append(f"{choice_value}. {choice_text}")
                    
                    # choice_values 생성 (가독성을 위해 별도로 분리)
                    choice_values = []
                    for choice in choice_list:
                        if '. ' in choice:
                            choice_values.append(choice.split('. ', 1)[0])
                        else:
                            choice_values.append(choice)
                    
                    # 퀴즈 데이터에 추가
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
                    self.log_error(f"문제 {i} 수집 중 오류: {str(e)}")
                    continue
            
            return quiz_data
            
        except Exception as e:
            self.log_error(f"퀴즈 정보 수집 실패: {str(e)}")
            return None

    def select_answers_with_extracted_answer(self, quiz_data, extracted_answer):
        """추출한 정답을 사용해서 답안 자동 선택"""
        try:
            self.log_info("추출한 정답으로 답안 선택 시작...")
            self.log_info(f"추출된 정답: {extracted_answer} (길이: {len(extracted_answer)})")
            
            # 추출된 정답을 각 문제별로 분리
            answer_chars = list(extracted_answer)
            
            if len(answer_chars) != len(quiz_data['questions']):
                self.log_warning(f"정답 길이({len(answer_chars)})와 문제 개수({len(quiz_data['questions'])})가 일치하지 않습니다.")
                return False
            
            for i, question in enumerate(quiz_data['questions']):
                try:
                    question_num = question['number']
                    
                    # i번째 문제의 정답 (0부터 시작)
                    current_answer = answer_chars[i]
                    
                    self.log_info(f"문제 {question_num}: {question['question']}")
                    self.log_info(f"정답: {current_answer}")
                    
                    # 정답에 해당하는 보기 번호 찾기 (딕셔너리 매핑 사용)
                    correct_answer = ANSWER_MAPPING.get(current_answer, current_answer)
                    
                    # 숫자가 아닌 경우 처리
                    if correct_answer not in VALID_ANSWER_VALUES:
                        try:
                            correct_answer = str(int(current_answer))
                        except ValueError:
                            self.log_warning(f"정답 '{current_answer}'를 숫자로 변환할 수 없습니다.")
                            continue
                    
                    self.log_info(f"선택할 답안 번호: {correct_answer}")
                    
                    # 라디오 버튼 선택
                    radio_selector = f"input[name='an_{question_num[1:]}'][value='{correct_answer}']"
                    radio_button = self.web_automation.driver.find_element(By.CSS_SELECTOR, radio_selector)
                    radio_button.click()
                    
                    self.log_success(f"{question_num}: 답안 {correct_answer} 선택 완료")
                        
                except Exception as e:
                    self.log_error(f"문제 {question_num} 답안 선택 실패: {str(e)}")
                    continue
            
            self.log_info("답안 선택 완료 - 정답 도전 버튼을 클릭합니다")
            
            # 정답 도전 버튼 클릭
            if self.click_submit_button():
                self.log_success("정답 도전 버튼 클릭 완료")
            else:
                self.log_error("정답 도전 버튼 클릭 실패")
            
            return True
                    
        except Exception as e:
            self.log_error(f"답안 자동 선택 실패: {str(e)}")
            return False

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

    
    def _check_points_after_quiz(self):
        """퀴즈 완료 후 포인트 상태 확인 - BaseModule의 공통 메서드 사용"""
        self.check_points_after_activity()

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

    def get_answer_from_blog(self):
        """3단계: 블로그 검색으로 정답 얻기"""
        try:
            self.log_info("블로그 검색으로 정답을 찾는 중...")
            
            # 블로그 검색 시도
            answer = self.try_blog_search()
            if answer:
                self.log_success(f"블로그에서 정답 추출 완료: {answer}")
                return answer
            else:
                # 블로그 검색 실패 시 퀴즈 중단
                self.log_error("블로그 검색 실패 - 퀴즈를 중단합니다")
                return None
            
        except Exception as e:
            self.log_error(f"블로그 검색 실패: {str(e)} - 퀴즈를 중단합니다")
            return None

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
                if result:
                    answer = blog_search_module.get_extracted_answer()
                    if answer:
                        return answer
                    else:
                        self.log_warning("블로그 검색 완료되었지만 정답을 추출하지 못했습니다")
                        return None
                else:
                    self.log_warning("블로그 검색 실행 실패")
                    return None
                    
            except Exception as exec_error:
                self.log_error(f"블로그 검색 실행 중 오류: {exec_error}")
                return None
                
        except Exception as e:
            self.log_error(f"블로그 검색 전체 실패: {str(e)}")
            return None

    def solve_quiz(self, answer):
        """4단계: 퀴즈 풀기"""
        try:
            self.log_info("퀴즈를 푸는 중...")
            
            # 추출된 정답 저장 (기존 메서드들이 사용할 수 있도록)
            self.extracted_answer = answer
            
            # 퀴즈 풀기 (팝업창에서)
            if not self.solve_quiz_with_extracted_answer():
                return False
            
            self.log_success("퀴즈 풀기 완료!")
            return True
            
        except Exception as e:
            self.log_error(f"퀴즈 풀기 실패: {str(e)}")
            return False
