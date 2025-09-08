# -*- coding: utf-8 -*-
"""
블로그 검색 모듈
quiz_module_new에서 이어질 순서로 특정 웹페이지를 새 탭에서 열기
"""

import logging
import os
import json
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_module import BaseModule

class BlogSearchModule(BaseModule):
    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
        self.extracted_answer = None  # 추출된 정답 저장
    
    def get_extracted_answer(self):
        """추출된 정답 반환"""
        return self.extracted_answer
    
    def execute(self):
        """블로그 검색 페이지를 새 탭에서 열기"""
        try:
            if self.gui_logger:
                self.log_info("블로그 검색 페이지를 새 탭에서 열기 시작...")
            
            # 현재 날짜 가져오기 (예: 8월26일)
            current_date = self.get_current_date()
            
            if self.gui_logger:
                self.gui_logger(f"검색할 날짜: {current_date}")
            
            # 블로그 검색 URL 생성 (닥터빌 키워드 추가)
            blog_search_url = f"https://blog.naver.com/PostSearchList.naver?SearchText={current_date}+닥터빌&blogId=doump1004"
            
            if self.gui_logger:
                self.gui_logger(f"블로그 검색 URL: {blog_search_url}")
            
            # 새 탭에서 페이지 열기
            if self.open_in_new_tab(blog_search_url):
                if self.gui_logger:
                    self.log_info("블로그 검색 페이지를 새 탭에서 열기 완료")
                return True
            else:
                if self.gui_logger:
                    self.log_info("블로그 검색 페이지 열기 실패")
                return False
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"블로그 검색 페이지 열기 실패: {str(e)}")
            return False
    
    def get_current_date(self):
        """현재 날짜를 '8월26일' 형식으로 반환"""
        try:
            now = datetime.now()
            month = now.month
            day = now.day
            
            # 월을 한글로 변환
            month_korean = f"{month}월"
            
            # 날짜 형식 생성 (예: 8월26일)
            current_date = f"{month_korean}{day}일"
            
            if self.gui_logger:
                self.gui_logger(f"현재 날짜 변환: {now.strftime('%Y-%m-%d')} → {current_date}")
            
            return current_date
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"날짜 변환 실패: {str(e)}")
            # 기본값 반환
            return "8월26일"
    
    def open_in_new_tab(self, url):
        """새 탭에서 URL 열기"""
        try:
            if self.gui_logger:
                self.log_info("새 탭에서 페이지 열기 중...")
            
            # 현재 탭 핸들 저장
            original_window = self.web_automation.driver.current_window_handle
            
            # 새 탭 열기 (JavaScript 사용)
            self.web_automation.driver.execute_script("window.open('');")
            
            # 새 탭으로 전환
            new_window = [handle for handle in self.web_automation.driver.window_handles if handle != original_window][0]
            self.web_automation.driver.switch_to.window(new_window)
            
            if self.gui_logger:
                self.log_info("새 탭으로 전환 완료")
            
            # URL로 이동
            self.web_automation.driver.get(url)
            
            # 페이지 로딩 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            if self.gui_logger:
                self.log_info("블로그 검색 페이지 로딩 완료")
            
            # 첫 번째 게시글 클릭
            if self.click_first_post():
                if self.gui_logger:
                    self.log_info("첫 번째 게시글 클릭 완료")
            else:
                if self.gui_logger:
                    self.log_info("첫 번째 게시글 클릭 실패")
            
            # 새 탭에서 작업 완료 후 원래 탭으로 돌아가기 (선택사항)
            # self.web_automation.driver.switch_to.window(original_window)
            
            return True
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"새 탭에서 페이지 열기 실패: {str(e)}")
            return False
    
    def click_first_post(self):
        """첫 번째 게시글 클릭"""
        try:
            if self.gui_logger:
                self.log_info("첫 번째 게시글을 찾는 중...")
            
            # 검색 결과가 로드될 때까지 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".s_link")))
            
            # 첫 번째 게시글 링크 찾기
            first_post_link = self.web_automation.driver.find_element(By.CSS_SELECTOR, ".s_link")
            
            if first_post_link:
                # 링크 텍스트 확인 (디버깅용)
                link_text = first_post_link.text
                if self.gui_logger:
                    self.gui_logger(f"첫 번째 게시글 제목: {link_text}")
                
                # 현재 탭 핸들 저장 (검색 결과 페이지)
                search_tab = self.web_automation.driver.current_window_handle
                
                # 링크 클릭
                first_post_link.click()
                
                if self.gui_logger:
                    self.log_info("첫 번째 게시글 클릭 완료")
                
                # 새 탭이 열릴 때까지 잠시 대기
                import time
                time.sleep(2)
                
                # 새로 열린 탭으로 전환 (가장 최근에 열린 탭)
                all_windows = self.web_automation.driver.window_handles
                if len(all_windows) > 1:
                    # 마지막 탭(가장 최근에 열린 탭)으로 전환
                    new_tab = all_windows[-1]
                    self.web_automation.driver.switch_to.window(new_tab)
                    
                    if self.gui_logger:
                        self.gui_logger(f"새 탭으로 전환 완료 (총 {len(all_windows)}개 탭)")
                else:
                    if self.gui_logger:
                        self.log_info("새 탭이 열리지 않았습니다.")
                    return False
                
                # 새 페이지 로딩 대기
                self.web_automation.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # 현재 URL 확인 (디버깅용)
                current_url = self.web_automation.driver.current_url
                if self.gui_logger:
                    self.gui_logger(f"현재 페이지 URL: {current_url}")
                
                # 정답 추출
                if self.extract_answer():
                    if self.gui_logger:
                        self.log_info("정답 추출 완료")
                else:
                    if self.gui_logger:
                        self.log_info("정답 추출 실패")
                
                return True
            else:
                if self.gui_logger:
                    self.log_info("첫 번째 게시글 링크를 찾을 수 없습니다.")
                return False
                
        except NoSuchElementException:
            if self.gui_logger:
                self.log_info("첫 번째 게시글 링크를 찾을 수 없습니다.")
            return False
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"첫 번째 게시글 클릭 실패: {str(e)}")
            return False

    def extract_answer(self):
        """게시글 내용에서 정답 추출"""
        try:
            if self.gui_logger:
                self.log_info("게시글 내용에서 정답을 추출하는 중...")
            
            # 페이지 로딩을 위한 추가 대기
            # time.sleep(3) 제거 - 불필요한 지연 제거
            
            # 네이버 블로그는 iframe 내부에 실제 콘텐츠가 있음
            if self.gui_logger:
                self.log_info("iframe 내부에서 정답을 찾아보겠습니다...")
            
            # iframe이 있는지 확인
            iframes = self.web_automation.driver.find_elements(By.TAG_NAME, "iframe")
            if self.gui_logger:
                self.gui_logger(f"페이지에서 발견된 iframe 개수: {len(iframes)}")
            
            if len(iframes) > 0:
                # iframe이 있으면 iframe 내용을 가져오기
                if self.gui_logger:
                    self.log_info("iframe을 찾았습니다. iframe 내용을 확인합니다...")
                
                for i, iframe in enumerate(iframes):
                    try:
                        # iframe으로 전환
                        self.web_automation.driver.switch_to.frame(iframe)
                        
                        if self.gui_logger:
                            self.gui_logger(f"iframe {i+1}으로 전환했습니다.")
                        
                        # iframe 내부에서 se-component se-image 찾기
                        iframe_se_containers = self.web_automation.driver.find_elements(By.CLASS_NAME, "se-component.se-image")
                        if self.gui_logger:
                            self.gui_logger(f"iframe {i+1} 내부의 se-component se-image 개수: {len(iframe_se_containers)}")
                        
                        if len(iframe_se_containers) >= 3:
                            if self.gui_logger:
                                self.gui_logger(f"✅ iframe {i+1}에서 3개 이상의 se-component se-image를 찾았습니다!")
                            
                            # 3번째 컨테이너 안에서 se-image-resource 찾기
                            third_container = iframe_se_containers[2]
                            try:
                                # 3번째 컨테이너 안의 se-image-resource 찾기
                                third_image = third_container.find_element(By.CLASS_NAME, "se-image-resource")
                                if self.gui_logger:
                                    self.log_info("✅ 3번째 컨테이너에서 se-image-resource를 찾았습니다!")
                                    img_src = third_image.get_attribute("src")
                                    self.gui_logger(f"3번째 이미지 src: {img_src}")
                                
                                # 3번째 컨테이너 뒤의 se-text div 찾기
                                next_sibling = third_container.find_element(By.XPATH, "following-sibling::div[contains(@class, 'se-text')]")
                                
                                if next_sibling:
                                    if self.gui_logger:
                                        self.log_info("✅ 3번째 이미지 뒤에 se-text div를 찾았습니다!")
                                    
                                    # se-text div 안의 텍스트 가져오기
                                    text_content = next_sibling.text.strip()
                                    if self.gui_logger:
                                        self.gui_logger(f"📝 se-text div 내용: {text_content}")
                                    
                                    # 정답 패턴 검색
                                    answer = self.search_answer_patterns(text_content)
                                    if answer:
                                        self.extracted_answer = answer
                                        if self.gui_logger:
                                            self.gui_logger(f"🎯 정답 추출 성공!")
                                            self.gui_logger(f"   📍 위치: iframe {i+1} 내부의 3번째 se-component se-image 뒤의 se-text div")
                                            self.gui_logger(f"   📝 원본 텍스트: {text_content}")
                                            self.gui_logger(f"   ✅ 추출된 정답: {answer}")
                                        
                                        # iframe에서 빠져나오기
                                        self.web_automation.driver.switch_to.default_content()
                                        
                                        # 정답 추출 성공 후 탭 정리 및 첫 번째 탭으로 돌아가기
                                        self.cleanup_tabs_and_return()
                                        return True
                                    else:
                                        if self.gui_logger:
                                            self.log_info("❌ se-text div에서 정답 패턴을 찾을 수 없었습니다.")
                                else:
                                    if self.gui_logger:
                                        self.log_info("❌ 3번째 이미지 뒤에 se-text div를 찾을 수 없었습니다.")
                                        
                            except Exception as e:
                                if self.gui_logger:
                                    self.gui_logger(f"❌ iframe {i+1} 내부 처리 실패: {str(e)}")
                        
                        # iframe에서 빠져나오기
                        self.web_automation.driver.switch_to.default_content()
                        
                    except Exception as e:
                        if self.gui_logger:
                            self.gui_logger(f"❌ iframe {i+1} 처리 실패: {str(e)}")
                        # iframe에서 빠져나오기 시도
                        try:
                            self.web_automation.driver.switch_to.default_content()
                        except:
                            pass
            else:
                if self.gui_logger:
                    self.log_info("❌ 페이지에서 iframe을 찾을 수 없습니다.")
            
            # 정답을 찾지 못한 경우
            if self.gui_logger:
                self.log_info("❌ 모든 iframe에서 정답을 찾을 수 없었습니다.")
            
            return False
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"정답 추출 중 오류 발생: {str(e)}")
            return False



    def search_answer_patterns(self, text):
        """텍스트에서 정답 패턴 검색"""
        try:
            if self.gui_logger:
                self.gui_logger(f"🔍 정답 패턴 검색 시작...")
                self.gui_logger(f"   📝 검색할 텍스트: {text}")
            
            # "OO3 입니다!!" 같은 패턴 찾기 (간단하게)
            pattern = r'([OX\d]{3,4})\s*입니다'
            if self.gui_logger:
                self.gui_logger(f"   🎯 사용할 패턴: {pattern}")
            
            match = re.search(pattern, text)
            
            if match:
                if self.gui_logger:
                    self.gui_logger(f"   ✅ 패턴 매칭 성공!")
                    self.gui_logger(f"   📍 매칭된 전체 문자열: {match.group(0)}")
                    self.gui_logger(f"   🎯 추출된 그룹: {match.group(1)}")
                
                answer = match.group(1).strip()
                # 정답 정리 (공백, 특수문자 제거)
                original_answer = answer
                answer = re.sub(r'[\s,\.!]+', '', answer)
                
                if self.gui_logger:
                    self.gui_logger(f"   🧹 정답 정리: '{original_answer}' → '{answer}'")
                
                # 유효한 정답인지 확인 (길이 3-4글자)
                if len(answer) >= 3 and len(answer) <= 4:
                    if self.gui_logger:
                        self.gui_logger(f"   ✅ 유효한 정답 확인됨 (길이: {len(answer)})")
                        self.gui_logger(f"   🎯 최종 정답: {answer}")
                    return answer
                else:
                    if self.gui_logger:
                        self.gui_logger(f"   ❌ 찾은 값이 유효하지 않음: {answer} (길이: {len(answer)})")
                        self.gui_logger(f"   📏 요구사항: 3-4글자 (O, X, 숫자 조합)")
            else:
                if self.gui_logger:
                    self.gui_logger(f"   ❌ 패턴 매칭 실패")
                    self.gui_logger(f"   📝 텍스트에 '입니다'가 포함되어 있는지 확인: {'입니다' in text}")
            
            if self.gui_logger:
                self.gui_logger(f"   ❌ 정답 패턴을 찾을 수 없었습니다.")
            return None
            
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"   ❌ 패턴 검색 중 오류 발생: {str(e)}")
            return None

    def cleanup_tabs_and_return(self):
        """탭 정리 및 첫 번째 탭으로 돌아가기"""
        try:
            if self.gui_logger:
                self.log_info("탭을 정리하고 첫 번째 탭으로 돌아갑니다...")
            
            # 현재 열린 모든 탭 확인
            all_windows = self.web_automation.driver.window_handles
            
            if len(all_windows) >= 3:
                # 세 번째 탭(게시글 페이지) 닫기
                self.web_automation.driver.switch_to.window(all_windows[2])
                self.web_automation.driver.close()
                
                if self.gui_logger:
                    self.log_info("세 번째 탭(게시글 페이지) 닫기 완료")
                
                # 두 번째 탭(블로그 검색 페이지) 닫기
                self.web_automation.driver.switch_to.window(all_windows[1])
                self.web_automation.driver.close()
                
                if self.gui_logger:
                    self.log_info("두 번째 탭(블로그 검색 페이지) 닫기 완료")
                
                # 첫 번째 탭(닥터빌 페이지)으로 돌아가기
                self.web_automation.driver.switch_to.window(all_windows[0])
                
                if self.gui_logger:
                    self.log_info("첫 번째 탭(닥터빌 페이지)으로 돌아가기 완료")
                
                return True
            else:
                if self.gui_logger:
                    self.gui_logger(f"예상과 다른 탭 개수: {len(all_windows)}개")
                return False
                
        except Exception as e:
            if self.gui_logger:
                self.gui_logger(f"탭 정리 중 오류: {str(e)}")
            return False
