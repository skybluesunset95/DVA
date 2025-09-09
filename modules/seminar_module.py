# -*- coding: utf-8 -*-
"""
세미나 모듈
닥터빌 라이브세미나 정보를 수집하고 관리합니다.
"""

import json
import threading
import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_module import BaseModule

# URL 상수 정의
SEMINAR_URL = "https://www.doctorville.co.kr/seminar/main"
DOCTORVILLE_BASE_URL = "https://www.doctorville.co.kr"

# CSS 선택자 상수 정의
LOADING_SELECTOR = ".list_cont"

# UI 설정 상수 정의 (설정 파일 없이 하드코딩)
WINDOW_TITLE = "닥터빌 라이브세미나 정보"
WINDOW_SIZE = "1200x800"
WINDOW_BG = '#f0f0f0'

# 세미나 데이터 필드 정의 (공통 정의)
SEMINAR_FIELDS = {
    'date': {
        'selector': '.seminar_day .date',
        'parent': True,  # 부모 컨테이너에서 찾기
        'attribute': 'text'
    },
    'day': {
        'selector': '.seminar_day .day',
        'parent': True,
        'attribute': 'text'
    },
    'time': {
        'selector': '.time',
        'parent': False,
        'attribute': 'text',
        'process': 'clean_text'  # 텍스트 정리 필요
    },
    'title': {
        'selector': '.list_tit .tit',
        'parent': False,
        'attribute': 'text'
    },
    'lecturer': {
        'selector': '.list_tit .tail',
        'parent': False,
        'attribute': 'text'
    },
    'person': {
        'selector': '.progress .person',
        'parent': False,
        'attribute': 'text'
    },
    'status': {
        'selector': '.progress .ico_box',
        'parent': False,
        'attribute': 'text'
    },
    'detail_link': {
        'selector': 'self',  # 자기 자신의 href 속성
        'parent': False,
        'attribute': 'href'
    }
}

# 버튼 설정 정의 (공통 정의)
BUTTON_CONFIGS = {
    'seminar_apply': {
        'selectors': [{'type': 'id', 'value': 'applyLiveSeminarMemberBtn'}],
        'log_search': 'BUTTON_SEARCH',
        'log_found': 'BUTTON_FOUND',
        'log_disabled': 'BUTTON_DISABLED',
        'log_click': 'BUTTON_CLICK',
        'log_not_found': 'BUTTON_NOT_FOUND',
        'log_timeout': 'BUTTON_NOT_FOUND',
        'log_error': 'BUTTON_ERROR'
    },
    'seminar_cancel': {
        'selectors': [{'type': 'id', 'value': 'cancelLiveSeminarMemberBtn'}],
        'log_search': 'CANCEL_SEARCH',
        'log_found': 'CANCEL_FOUND',
        'log_disabled': 'CANCEL_DISABLED',
        'log_click': 'CANCEL_CLICK',
        'log_not_found': 'CANCEL_NOT_FOUND',
        'log_timeout': 'CANCEL_NOT_FOUND',
        'log_error': 'CANCEL_ERROR'
    },
    'seminar_enter': {
        'selectors': [
            {'type': 'css', 'value': "a.btn_bn.btn_enter[onclick*='playOnPopup']"},
            {'type': 'xpath', 'value': "//a[contains(@class, 'btn_enter') and text()='입장하기']"},
            {'type': 'css', 'value': '.btn_bn.btn_enter'}
        ],
        'log_search': 'ENTER_SEARCH',
        'log_found': 'ENTER_FOUND',
        'log_disabled': 'ENTER_DISABLED',
        'log_click': 'ENTER_CLICK',
        'log_not_found': 'ENTER_NOT_FOUND',
        'log_timeout': 'ENTER_NOT_FOUND',
        'log_error': 'ENTER_ERROR'
    }
}

class SeminarModule(BaseModule):
    # 로그 메시지 상수
    LOG_MESSAGES = {
        'START': "🚀 라이브세미나 모듈 시작",
        'NAVIGATING': "🌐 라이브세미나 페이지로 이동 중...",
        'WAITING': "페이지 로딩 대기 중...",
        'SUCCESS': "✅ 라이브세미나 페이지 이동 완료",
        'COLLECTING': "📊 세미나 정보 수집 시작...",
        'COMPLETE': "📋 총 {count}개의 세미나 정보 수집 완료",
        'NO_DATA': "⚠ 세미나 정보를 찾을 수 없습니다.",
        'WINDOW_CREATING': "세미나 정보 창 생성 중...",
        'WINDOW_COMPLETE': "🎉 라이브세미나 모듈 실행 완료",
        'WINDOW_ERROR': "⚠ 세미나 창 표시 중 오류: {error}",
        'MODULE_ERROR': "❌ 라이브세미나 모듈 실행 실패: {error}",
        'DRIVER_ERROR': "❌ 웹드라이버가 초기화되지 않았습니다.",
        'COLLECT_ERROR': "❌ 세미나 정보 수집 실패: {error}",
        'JS_COLLECTING': "JavaScript로 세미나 정보 일괄 수집 중...",
        'JS_COMPLETE': "✅ 총 {count}개의 세미나 정보 일괄 수집 완료",
        'JS_ERROR': "❌ JavaScript 세미나 정보 수집 중 오류: {error}",
        'FALLBACK': "⚠ 기존 방식으로 재시도 중...",
        'FALLBACK_ERROR': "❌ 기존 방식 세미나 정보 수집 중 오류: {error}",
        'WINDOW_UPDATE': "현황판 업데이트 중...",
        'WINDOW_UPDATE_COMPLETE': "✅ 현황판 업데이트 완료 (총 {count}개 세미나)",
        'WINDOW_UPDATE_ERROR': "❌ 현황판 업데이트 실패: {error}",
        'BUTTON_SEARCH': "세미나 신청/입장 버튼 검색 중...",
        'BUTTON_FOUND': "세미나 버튼 요소 발견",
        'BUTTON_CLICK': "✅ '{text}' 버튼 클릭 완료",
        'BUTTON_DISABLED': "⚠ 버튼이 비활성화 상태입니다",
        'BUTTON_NOT_FOUND': "❌ 세미나 버튼을 찾을 수 없습니다 (시간 초과)",
        'BUTTON_ERROR': "❌ 세미나 버튼 클릭 실패: {error}",
        'POPUP_PROCESSING': "팝업 확인 버튼 처리 중...",
        'POPUP_COMPLETE': "✅ 팝업 확인 버튼 처리 완료",
        'POPUP_ERROR': "⚠ 팝업 확인 중 오류: {error}",
        'CANCEL_SEARCH': "세미나 신청취소 버튼 검색 중...",
        'CANCEL_FOUND': "신청취소 버튼 요소 발견",
        'CANCEL_CLICK': "✅ '{text}' 버튼 클릭 완료",
        'CANCEL_DISABLED': "⚠ 신청취소 버튼이 비활성화 상태입니다",
        'CANCEL_NOT_FOUND': "❌ 신청취소 버튼을 찾을 수 없습니다 (시간 초과)",
        'CANCEL_ERROR': "❌ 신청취소 버튼 클릭 실패: {error}",
        'CANCEL_POPUP_PROCESSING': "신청취소 확인 팝업 처리 중...",
        'CANCEL_POPUP_COMPLETE': "✅ 신청취소 확인 팝업 처리 완료",
        'CANCEL_POPUP_ERROR': "⚠ 신청취소 확인 중 오류: {error}",
        'ENTER_SEARCH': "세미나 입장하기 버튼 검색 중...",
        'ENTER_FOUND_1': "방법 1로 입장하기 버튼 발견",
        'ENTER_FOUND_2': "방법 2로 입장하기 버튼 발견",
        'ENTER_FOUND_3': "방법 3으로 입장하기 버튼 발견",
        'ENTER_NOT_FOUND': "❌ 모든 방법으로 입장하기 버튼을 찾을 수 없습니다",
        'ENTER_CLICK': "✅ '{text}' 버튼 클릭 완료",
        'ENTER_DISABLED': "⚠ 입장하기 버튼이 비활성화 상태입니다",
        'ENTER_ERROR': "❌ 입장하기 버튼 클릭 실패: {error}",
        'ENTER_POPUP_PROCESSING': "입장하기 팝업 처리 중...",
        'ENTER_POPUP_COMPLETE': "✅ 입장하기 팝업 처리 완료",
        'ENTER_POPUP_ERROR': "⚠ 입장하기 팝업 처리 중 오류: {error}",
        'PAGE_MOVING': "선택된 세미나 상세 페이지로 이동 중...",
        'PAGE_COMPLETE': "세미나 상세 페이지 로딩 완료",
        'PAGE_UPDATE': "🔄 현황판 업데이트 완료",
        'PAGE_ERROR': "❌ 세미나 페이지 이동 중 오류: {error}",
        'LINK_NOT_FOUND': "⚠ 세미나 링크를 찾을 수 없습니다",
        'DATA_INSERT_COMPLETE': "✅ 트리뷰에 데이터 삽입 완료 (총 {count}개 세미나)",
        'DATA_INSERT_ERROR': "❌ 트리뷰에 데이터 삽입 실패: {error}"
    }
    
    # 설정 값 상수
    # SEMINAR_URL = "https://www.doctorville.co.kr/seminar/main" # 이미 위에 정의됨
    # LOADING_SELECTOR = ".list_cont" # 이미 위에 정의됨
    # SETTINGS_FILE = "seminar_settings.json" # 이미 위에 정의됨
    # WINDOW_TITLE = "닥터빌 라이브세미나 정보" # 이미 위에 정의됨
    # WINDOW_SIZE = "1200x800" # 이미 위에 정의됨
    # WINDOW_BG = '#f0f0f0' # 이미 위에 정의됨
    
    # 세미나 데이터 필드 정의 (공통 정의)
    # SEMINAR_FIELDS = { # 이미 위에 정의됨
    #     'date': {
    #         'selector': '.seminar_day .date',
    #         'parent': True,  # 부모 컨테이너에서 찾기
    #         'attribute': 'text'
    #     },
    #     'day': {
    #         'selector': '.seminar_day .day',
    #         'parent': True,
    #         'attribute': 'text'
    #     },
    #     'time': {
    #         'selector': '.time',
    #         'parent': False,
    #         'attribute': 'text',
    #         'process': 'clean_text'  # 텍스트 정리 필요
    #     },
    #     'title': {
    #         'selector': '.list_tit .tit',
    #         'parent': False,
    #         'attribute': 'text'
    #     },
    #     'lecturer': {
    #         'selector': '.list_tit .tail',
    #         'parent': False,
    #         'attribute': 'text'
    #     },
    #     'person': {
    #         'selector': '.progress .person',
    #         'parent': False,
    #         'attribute': 'text'
    #     },
    #     'status': {
    #         'selector': '.progress .ico_box',
    #         'parent': False,
    #         'attribute': 'text'
    #     },
    #     'detail_link': {
    #         'selector': 'self',  # 자기 자신의 href 속성
    #         'parent': False,
    #         'attribute': 'href'
    #     }
    # }
    
    # 버튼 설정 정의 (공통 정의)
    # BUTTON_CONFIGS = { # 이미 위에 정의됨
    #     'seminar_apply': {
    #         'selectors': [{'type': 'id', 'value': 'applyLiveSeminarMemberBtn'}],
    #         'log_search': 'BUTTON_SEARCH',
    #         'log_found': 'BUTTON_FOUND',
    #         'log_disabled': 'BUTTON_DISABLED',
    #         'log_click': 'BUTTON_CLICK',
    #         'log_not_found': 'BUTTON_NOT_FOUND',
    #         'log_timeout': 'BUTTON_NOT_FOUND',
    #         'log_error': 'BUTTON_ERROR'
    #     },
    #     'seminar_cancel': {
    #         'selectors': [{'type': 'id', 'value': 'cancelLiveSeminarMemberBtn'}],
    #         'log_search': 'CANCEL_SEARCH',
    #         'log_found': 'CANCEL_FOUND',
    #         'log_disabled': 'CANCEL_DISABLED',
    #         'log_click': 'CANCEL_CLICK',
    #         'log_not_found': 'CANCEL_NOT_FOUND',
    #         'log_timeout': 'CANCEL_NOT_FOUND',
    #         'log_error': 'CANCEL_ERROR'
    #     },
    #     'seminar_enter': {
    #         'selectors': [
    #             {'type': 'css', 'value': "a.btn_bn.btn_enter[onclick*='playOnPopup']"},
    #             {'type': 'xpath', 'value': "//a[contains(@class, 'btn_enter') and text()='입장하기']"},
    #             {'type': 'css', 'value': '.btn_bn.btn_enter'}
    #         ],
    #         'log_search': 'ENTER_SEARCH',
    #         'log_found': 'ENTER_FOUND',
    #         'log_disabled': 'ENTER_DISABLED',
    #         'log_click': 'ENTER_CLICK',
    #         'log_not_found': 'ENTER_NOT_FOUND',
    #         'log_timeout': 'ENTER_NOT_FOUND',
    #         'log_error': 'ENTER_ERROR'
    #     }
    # }
    
    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
        
        # 세미나 모듈 설정
        self.settings = {
            'auto_apply': False,
            'refresh_interval': 30,
            'show_popup': True,
            'auto_enter': False,
            'timeout': 10
        }
        self.load_settings()
    
    def _log(self, message_key, **kwargs):
        """통일된 로깅 메서드 - 일반 메시지와 INFO 로그 모두 표시"""
        message = self.LOG_MESSAGES.get(message_key, message_key)
        if kwargs:
            message = message.format(**kwargs)
        
        # 기존 콜백 방식 (간단하게)
        if hasattr(self, 'gui_callbacks') and 'log_message' in self.gui_callbacks:
            self.gui_callbacks['log_message'](message)
        
        # INFO 로그로 표시 (로그 파일 + 콘솔)
        if self.gui_logger:
            self.gui_logger(message)
    
    def _navigate_to_seminar_page(self):
        """세미나 페이지로 이동하는 공통 함수"""
        try:
            if not self.web_automation.driver:
                self._log('DRIVER_ERROR')
                return False
            
            self._log('NAVIGATING')
            
            # 세미나 페이지로 이동
            self.web_automation.driver.get(SEMINAR_URL)
            
            self._log('WAITING')
            
            # 페이지 로딩 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LOADING_SELECTOR)))
            
            self._log('SUCCESS')
            self._log('COLLECTING')
            
            return True
            
        except Exception as e:
            self._log('COLLECT_ERROR', error=str(e))
            return False
    
    def _extract_seminar_data(self, item, parent_container=None):
        """세미나 데이터 추출 공통 함수"""
        seminar_data = {}
        
        for field_name, field_config in SEMINAR_FIELDS.items():
            try:
                # 셀렉터 결정
                if field_config['selector'] == 'self':
                    element = item
                elif field_config['parent'] and parent_container:
                    element = parent_container.find_element(By.CSS_SELECTOR, field_config['selector'])
                else:
                    element = item.find_element(By.CSS_SELECTOR, field_config['selector'])
                
                # 데이터 추출
                if field_config['attribute'] == 'text':
                    value = element.text.strip()
                elif field_config['attribute'] == 'href':
                    value = element.get_attribute('href')
                
                # 데이터 처리
                if field_config.get('process') == 'clean_text':
                    value = value.replace('\n', ' ').replace('  ', ' ')
                
                seminar_data[field_name] = value
                
            except NoSuchElementException:
                seminar_data[field_name] = ''
            except Exception as e:
                self._log(f'필드 {field_name} 추출 실패: {str(e)}')
                seminar_data[field_name] = ''
        
        return seminar_data
    
    def _generate_js_fields_script(self):
        """JavaScript용 필드 추출 스크립트 자동 생성"""
        js_code = """
        function extractSeminarData(item, parentContainer) {
            const data = {};
        """
        
        for field_name, field_config in SEMINAR_FIELDS.items():
            if field_config['selector'] == 'self':
                js_code += f"""
            // {field_name}
            data['{field_name}'] = item.getAttribute('href') || '';
        """
            elif field_config['parent']:
                js_code += f"""
            // {field_name}
            const {field_name}Element = parentContainer.querySelector('{field_config['selector']}');
            data['{field_name}'] = {field_name}Element ? {field_name}Element.textContent.trim() : '';
        """
            else:
                js_code += f"""
            // {field_name}
            const {field_name}Element = item.querySelector('{field_config['selector']}');
            data['{field_name}'] = {field_name}Element ? {field_name}Element.textContent.trim() : '';
        """
        
        js_code += """
            return data;
        }
        """
        
        return js_code
    
    def _insert_date_separator(self, tree, seminar):
        """날짜 구분선을 Treeview에 삽입하는 공통 함수"""
        tree.insert('', 'end', values=(
            "", f"📅 {seminar['date']} {seminar['day']}",
            "", "", "", "", "", ""
        ), tags=('date_separator',))
    
    def _insert_seminar_item(self, tree, seminar):
        """개별 세미나 항목을 Treeview에 삽입하는 공통 함수"""
        status_tag = self.get_status_tag(seminar['status'])
        
        tree.insert('', 'end', values=(
            "☐",  # 체크박스 (빈 박스)
            seminar['date'],
            seminar['day'],
            seminar['time'],
            seminar['title'],
            seminar['lecturer'],
            seminar['person'],
            seminar['status']
        ), tags=(seminar['detail_link'], status_tag))
    
    def _insert_seminar_data(self, tree, seminars, clear_existing=True):
        """Treeview에 세미나 데이터를 삽입하는 공통 함수"""
        try:
            if clear_existing:
                # 기존 데이터 삭제
                for item in tree.get_children():
                    tree.delete(item)
            
            current_date = None
            
            for seminar in seminars:
                # 날짜가 바뀌면 구분선 추가
                if current_date != seminar['date']:
                    current_date = seminar['date']
                    self._insert_date_separator(tree, seminar)
                
                # 세미나 데이터 추가
                self._insert_seminar_item(tree, seminar)
            
            self._log('DATA_INSERT_COMPLETE', count=len(seminars))
            
        except Exception as e:
            self._log('DATA_INSERT_ERROR', error=str(e))
    
    def _find_button(self, selectors):
        """여러 방법으로 버튼을 찾는 공통 함수"""
        for selector_config in selectors:
            try:
                if selector_config['type'] == 'id':
                    button = self.web_automation.driver.find_element(By.ID, selector_config['value'])
                elif selector_config['type'] == 'css':
                    button = self.web_automation.driver.find_element(By.CSS_SELECTOR, selector_config['value'])
                elif selector_config['type'] == 'xpath':
                    button = self.web_automation.driver.find_element(By.XPATH, selector_config['value'])
                else:
                    continue
                
                # 버튼을 찾았으면 즉시 반환
                return button
                
            except NoSuchElementException:
                continue
            except Exception as e:
                self._log(f"버튼 찾기 중 오류 ({selector_config['type']}: {selector_config['value']}): {str(e)}")
                continue
        
        return None
    
    def _click_button_with_fallback(self, button_config, popup_handler=None):
        """버튼 클릭 공통 함수"""
        try:
            self._log(button_config['log_search'])
            
            # 버튼 찾기 (여러 방법 지원)
            button = self._find_button(button_config['selectors'])
            
            if not button:
                self._log(button_config['log_not_found'])
                return False
            
            button_text = button.text.strip()
            self._log(f"발견된 버튼: '{button_text}'")
            
            # 버튼 활성화 확인
            if not button.is_enabled():
                self._log(button_config['log_disabled'])
                return False
            
            # 버튼 클릭
            button.click()
            self._log(button_config['log_click'], text=button_text)
            
            # 팝업 처리
            if popup_handler:
                popup_handler()
            
            return True
            
        except TimeoutException:
            self._log(button_config['log_timeout'])
            return False
        except Exception as e:
            self._log(button_config['log_error'], error=str(e))
            return False
    
    def collect_seminar_info_only(self):
        """세미나 정보만 수집 (GUI 창 표시 없음)"""
        try:
            # 공통 함수로 페이지 이동
            if not self._navigate_to_seminar_page():
                return None
            
            # 세미나 정보 수집
            seminars = self.get_seminar_info()
            
            if seminars:
                self._log('COMPLETE', count=len(seminars))
                return seminars
            else:
                self._log('NO_DATA')
                return None
                
        except Exception as e:
            self._log('COLLECT_ERROR', error=str(e))
            return None
    
    def execute(self):
        """라이브세미나 페이지로 이동하고 세미나 정보 수집 (GUI 창 포함)"""
        try:
            self._log('START')
            
            # 공통 함수로 페이지 이동
            if not self._navigate_to_seminar_page():
                return False
            
            # 세미나 정보 수집
            seminars = self.get_seminar_info()
            
            if not seminars:
                self._log('NO_DATA')
                return False
            
            self._log('COMPLETE', count=len(seminars))
            
            # 세미나 정보 창 표시
            try:
                self.show_seminar_window(seminars)
                self._log('WINDOW_COMPLETE')
                return True
            except Exception as e:
                self._log('WINDOW_ERROR', error=str(e))
                return False
                
        except Exception as e:
            self._log('MODULE_ERROR', error=str(e))
            return False
    

    
    def get_seminar_info(self):
        """세미나 정보 수집 (JavaScript 일괄 처리 최적화)"""
        try:
            self._log('JS_COLLECTING')
            
            # JavaScript에서 공통 필드 정의 사용
            fields_script = self._generate_js_fields_script()
            
            script = f"""
            {fields_script}
            
            return Array.from(document.querySelectorAll('.list_detail')).map(item => {{
                const parentContainer = item.closest('.list_cont');
                return extractSeminarData(item, parentContainer);
            }});
            """
            
            # JavaScript 실행
            seminars_data = self.web_automation.driver.execute_script(script)
            
            self._log('JS_COMPLETE', count=len(seminars_data))
            
            return seminars_data
                    
        except Exception as e:
            self._log('JS_ERROR', error=str(e))
            
            # JavaScript 실패 시 기존 방식으로 폴백
            self._log('FALLBACK')
            return self._fallback_seminar_info()
    
    def _fallback_seminar_info(self):
        """JavaScript 실패 시 기존 방식으로 세미나 정보 수집"""
        seminars = []
        
        try:
            self._log('FALLBACK')
            
            # 한 번에 모든 세미나 아이템 찾기
            all_seminar_items = self.web_automation.driver.find_elements(By.CSS_SELECTOR, ".list_detail")
            total_count = len(all_seminar_items)
            
            self._log(f"총 {total_count}개의 세미나 항목 발견")
            
            for i, item in enumerate(all_seminar_items, 1):
                try:
                    # 부모 컨테이너에서 날짜 정보 가져오기
                    parent_container = item.find_element(By.XPATH, "./ancestor::div[contains(@class, 'list_cont')]")
                    
                    # 공통 함수 사용
                    seminar_data = self._extract_seminar_data(item, parent_container)
                    seminars.append(seminar_data)
                    
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self._log('FALLBACK_ERROR', error=str(e))
        
        return seminars
    
    def get_status_tag(self, status):
        """신청상태에 따른 태그 반환"""
        status_lower = status.lower().strip()
        
        if '신청가능' in status_lower or '신청' in status_lower and '가능' in status_lower:
            return '신청가능'
        elif '신청완료' in status_lower or '완료' in status_lower:
            return '신청완료'
        elif '신청마감' in status_lower or '마감' in status_lower:
            return '신청마감'
        elif '입장' in status_lower or '입장하기' in status_lower:
            return '입장하기'
        elif '대기' in status_lower or '대기중' in status_lower:
            return '대기중'
        else:
            return '기타'
    
    def show_seminar_window(self, seminars):
        """세미나 정보를 새 창에 표시"""
        self._log('WINDOW_CREATING')
        
        # 새 창 생성
        window = tk.Toplevel()
        window.title(WINDOW_TITLE)
        window.geometry(WINDOW_SIZE)
        window.configure(bg=WINDOW_BG)
        
        # 제목
        title_label = tk.Label(window, text="📅 닥터빌 라이브세미나 정보", 
                              font=("맑은 고딕", 16, "bold"), 
                              bg=WINDOW_BG, fg='#2c3e50')
        title_label.pack(pady=10)
        
        # 설명
        desc_label = tk.Label(window, text="더블클릭하면 해당 세미나 페이지로 이동합니다", 
                             font=("맑은 고딕", 10), 
                             bg=WINDOW_BG, fg='#7f8c8d')
        desc_label.pack(pady=5)
        
        # 버튼 프레임 생성 (트리뷰 위에)
        button_frame = tk.Frame(window, bg=WINDOW_BG)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 버튼들 생성 (순서: 선택신청, 선택취소, 신청가능선택, 모두신청)
        btn_select_apply = tk.Button(button_frame, text="선택신청", 
                                    font=("맑은 고딕", 10, "bold"),
                                    bg='#6c757d', fg='white',
                                    width=10, height=1)
        btn_select_apply.pack(side=tk.LEFT, padx=3)
        
        btn_select_cancel = tk.Button(button_frame, text="선택취소", 
                                     font=("맑은 고딕", 10, "bold"),
                                     bg='#6c757d', fg='white',
                                     width=10, height=1)
        btn_select_cancel.pack(side=tk.LEFT, padx=3)
        
        btn_available_select = tk.Button(button_frame, text="신청가능선택", 
                                        font=("맑은 고딕", 10, "bold"),
                                        bg='#6c757d', fg='white',
                                        width=10, height=1)
        btn_available_select.pack(side=tk.LEFT, padx=3)
        
        btn_clear_all = tk.Button(button_frame, text="체크초기화", 
                                 font=("맑은 고딕", 10, "bold"),
                                 bg='#6c757d', fg='white',
                                 width=10, height=1)
        btn_clear_all.pack(side=tk.LEFT, padx=3)
        
        # 버튼 이벤트 연결
        btn_select_apply.config(command=lambda: self.process_checked_seminars(tree, "apply"))
        btn_select_cancel.config(command=lambda: self.process_checked_seminars(tree, "cancel"))
        btn_available_select.config(command=lambda: self.manage_checkboxes(tree, "select_available"))
        btn_clear_all.config(command=lambda: self.manage_checkboxes(tree, "clear_all"))
        
        # 프레임 생성
        main_frame = tk.Frame(window, bg=WINDOW_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 트리뷰 생성 (체크박스 컬럼 추가)
        columns = ('선택', '날짜', '요일', '시간', '강의명', '강의자', '신청인원', '신청상태')
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        # 컬럼 설정
        tree.heading('선택', text='선택')
        tree.heading('날짜', text='날짜')
        tree.heading('요일', text='요일')
        tree.heading('시간', text='시간')
        tree.heading('강의명', text='강의명')
        tree.heading('강의자', text='강의자')
        tree.heading('신청인원', text='신청인원')
        tree.heading('신청상태', text='신청상태')
        
        # 컬럼 너비 설정
        tree.column('선택', width=50, anchor='center')
        tree.column('날짜', width=80, anchor='center')
        tree.column('요일', width=80, anchor='center')
        tree.column('시간', width=100, anchor='center')
        tree.column('강의명', width=300, anchor='w')
        tree.column('강의자', width=200, anchor='w')
        tree.column('신청인원', width=100, anchor='center')
        tree.column('신청상태', width=100, anchor='center')
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 트리뷰와 스크롤바 배치
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 데이터 삽입 (날짜별 그룹화)
        self._insert_seminar_data(tree, seminars, clear_existing=False)
        
        self._log('WINDOW_COMPLETE')
        
        # 더블클릭 이벤트
        def on_double_click(event):
            try:
                # 클릭된 컬럼 확인
                column = tree.identify_column(event.x)
                
                # 체크박스 컬럼을 더블클릭한 경우는 무시
                if column == '#1':
                    return
                
                # 선택된 항목 확인
                selection = tree.selection()
                if not selection:
                    return
                
                item = selection[0]
                tags = tree.item(item, "tags")
                
                # 날짜 구분선은 클릭 불가
                if 'date_separator' in tags:
                    return
                
                # 첫 번째 태그가 링크인지 확인 (상대 경로도 허용)
                if len(tags) > 0 and tags[0]:
                    detail_link = tags[0]
                    # 상대 경로인 경우 절대 경로로 변환
                    if detail_link.startswith('/'):
                        detail_link = DOCTORVILLE_BASE_URL + detail_link
                    
                    self._log('PAGE_MOVING')
                    
                    # 현재 탭에서 열기
                    self.web_automation.driver.get(detail_link)
                    
                    self._log('PAGE_COMPLETE')
                    
                    # 세미나 상태에 따라 다른 동작 수행
                    status_tag = None
                    for tag in tags:
                        if tag in ['신청가능', '신청완료', '신청마감', '입장하기', '대기중']:
                            status_tag = tag
                            break
                    
                    if status_tag == '신청완료':
                        # 신청완료 상태면 신청취소
                        success = self.cancel_seminar()
                    elif status_tag == '입장하기':
                        # 입장하기 상태면 입장하기
                        success = self.enter_seminar()
                    else:
                        # 다른 상태면 신청/입장
                        success = self.click_seminar_button()
                    
                    if success:
                        # 처리 완료 후 잠시 대기
                        import time
                        time.sleep(0.5)
                        
                        # 현황판 업데이트
                        self.update_seminar_window(window, tree)
                        
                        self._log('PAGE_UPDATE')
                    
                    # 🔥 선택된 항목 해제 (파란색 블록 제거)
                    tree.selection_remove(item)
                    
                else:
                    self._log('LINK_NOT_FOUND')
                    # 실패한 경우에도 선택 해제
                    tree.selection_remove(item)
                        
            except Exception as e:
                self._log('PAGE_ERROR', error=str(e))
                # 예외 발생 시에도 선택 해제
                try:
                    selection = tree.selection()
                    if selection:
                        tree.selection_remove(selection[0])
                except:
                    pass
        
        tree.bind('<Double-1>', on_double_click)
        
        # 체크박스 클릭 이벤트
        def on_click(event):
            try:
                # 클릭된 항목 확인
                item = tree.identify_row(event.y)
                if not item:
                    return
                
                # 클릭된 컬럼 확인
                column = tree.identify_column(event.x)
                
                # 선택 컬럼(첫 번째 컬럼)을 클릭한 경우에만 체크박스 토글
                if column == '#1':  # 첫 번째 컬럼
                    tags = tree.item(item, "tags")
                    
                    # 날짜 구분선은 클릭 불가
                    if 'date_separator' in tags:
                        return
                    
                    # 현재 값 가져오기
                    values = list(tree.item(item, "values"))
                    
                    # 체크박스 토글
                    if values[0] == "☐":  # 빈 박스면
                        values[0] = "☑"  # 체크된 박스로
                    else:  # 체크된 박스면
                        values[0] = "☐"  # 빈 박스로
                    
                    # 값 업데이트
                    tree.item(item, values=values)
                    
            except Exception as e:
                self._log(f"❌ 체크박스 클릭 중 오류: {str(e)}")
        
        tree.bind('<Button-1>', on_click)
        
        # 상태별 색상 설정 (더 다양한 색상)
        tree.tag_configure('신청가능', background='#d5f4e6', foreground='#2e7d32')  # 연한 초록
        tree.tag_configure('신청완료', background='#fef9e7', foreground='#f39c12')  # 연한 노랑
        tree.tag_configure('신청마감', background='#fadbd8', foreground='#e74c3c')  # 연한 빨강
        tree.tag_configure('입장하기', background='#d6eaf8', foreground='#3498db')  # 연한 파랑
        tree.tag_configure('대기중', background='#f8f9fa', foreground='#6c757d')    # 연한 회색
        tree.tag_configure('기타', background='#f4f6f6', foreground='#34495e')      # 기본색
        
        # 날짜 구분선 색상 설정
        tree.tag_configure('date_separator', background='#34495e', foreground='white', font=("맑은 고딕", 10, "bold"))
        
        # 창을 화면 중앙에 배치
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
        y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
        window.geometry(f"+{x}+{y}")
        
        # 독립적인 창으로 설정 (원래 프로그램 위에 고정되지 않음)
        window.attributes('-topmost', False)
    
    def click_seminar_button(self):
        """세미나 상세 페이지에서 자동으로 버튼 클릭"""
        try:
            # 페이지 로딩 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.ID, "applyLiveSeminarMemberBtn")))
            
            # 공통 함수 사용
            return self._click_button_with_fallback(
                BUTTON_CONFIGS['seminar_apply'],
                self._handle_popup_confirmations
            )
            
        except Exception as e:
            self._log('BUTTON_ERROR', error=str(e))
            return False

    def _handle_popup_confirmations(self):
        """JavaScript로 팝업 확인 버튼들을 즉시 클릭"""
        try:
            self._log('POPUP_PROCESSING')
            
            # JavaScript로 모든 팝업 버튼 즉시 클릭
            script = """
            // 개인정보 동의 팝업
            document.querySelector('#seminarAgree .btn_confirm')?.click();
            
            // 마케팅 수신 동의 팝업  
            document.querySelector('#marketingAgree .btn_confirm')?.click();
            
            // 신청 완료 팝업
            document.querySelector('#modalType2 .btn_confirm')?.click();
            """
            
            self.web_automation.driver.execute_script(script)
            
            self._log('POPUP_COMPLETE')
                
        except Exception as e:
            self._log('POPUP_ERROR', error=str(e))

    def update_seminar_window(self, window, tree):
        """현황판 업데이트 - 새로운 세미나 정보로 트리뷰 갱신"""
        try:
            self._log('WINDOW_UPDATE')
            
            # 라이브세미나 페이지로 다시 이동
            self.web_automation.driver.get(SEMINAR_URL)
            
            # 페이지 로딩 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LOADING_SELECTOR)))
            
            # 새로운 세미나 정보 수집
            new_seminars = self.get_seminar_info()
            
            if new_seminars:
                # 기존 트리뷰 데이터 삭제
                for item in tree.get_children():
                    tree.delete(item)
                
                # 새로운 데이터 삽입
                self._insert_seminar_data(tree, new_seminars)
                
                self._log('WINDOW_UPDATE_COMPLETE', count=len(new_seminars))
            else:
                self._log("⚠ 업데이트할 세미나 정보를 찾을 수 없습니다")
                    
        except Exception as e:
            self._log('WINDOW_UPDATE_ERROR', error=str(e))

    def cancel_seminar(self):
        """세미나 신청취소"""
        try:
            # 페이지 로딩 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.ID, "cancelLiveSeminarMemberBtn")))
            
            # 공통 함수 사용
            return self._click_button_with_fallback(
                BUTTON_CONFIGS['seminar_cancel'],
                self._handle_cancel_confirmations
            )
            
        except Exception as e:
            self._log('CANCEL_ERROR', error=str(e))
            return False

    def enter_seminar(self):
        """세미나 입장하기 기능"""
        try:
            # 입장하기 버튼만 클릭
            return self._click_button_with_fallback(
                BUTTON_CONFIGS['seminar_enter'],
                None  # 팝업 처리 없음
            )
            
        except Exception as e:
            self._log('ENTER_ERROR', error=str(e))
            return False

    def _generate_seminar_id_extraction_script(self):
        """세미나 ID 추출을 위한 JavaScript 코드"""
        return """
        // 올바른 세미나 ID 추출 (여러 방법 시도)
        let seminarId = null;
        
        // 방법 1: URL에서 세미나 ID 추출
        const urlMatch = window.location.href.match(/seminarId=([^&]+)/);
        if (urlMatch) {
            seminarId = urlMatch[1];
        }
        
        // 방법 2: 페이지 내 hidden input에서 세미나 ID 추출
        if (!seminarId) {
            const hiddenInput = document.querySelector('input[name="seminarId"]');
            if (hiddenInput) {
                seminarId = hiddenInput.value;
            }
        }
        
        // 방법 3: onclick 속성에서 세미나 ID 추출
        if (!seminarId) {
            const enterButton = document.querySelector('a.btn_bn.btn_enter[onclick*="playOnPopup"]');
            if (enterButton) {
                const onclickMatch = enterButton.getAttribute('onclick').match(/playOnPopup\\(['"]([^'"]+)['"]\\)/);
                if (onclickMatch) {
                    seminarId = onclickMatch[1];
                }
            }
        }
        
        // 방법 4: 페이지 제목이나 메타데이터에서 세미나 ID 추출
        if (!seminarId) {
            const titleMatch = document.title.match(/세미나 ID[\\s:]*([0-9]+)/i);
            if (titleMatch) {
                seminarId = titleMatch[1];
            }
        }
        
        if (seminarId && typeof playOnPopup === 'function') {
            console.log('발견된 세미나 ID:', seminarId);
            playOnPopup(seminarId);
            
            // 🔥 팝업 창이 열린 후 자동 재생 처리
            console.log('팝업 창 열기 시작...');
            
            // 팝업 창이 열린 후 그 창에서 직접 실행되도록 설정
            setTimeout(() => {
                findAndHandlePopupWindow();
            }, 1000); // 1초 후 팝업 창 찾기 시작
            
        } else {
            console.error('세미나 ID를 찾을 수 없거나 playOnPopup 함수가 없습니다.');
        }
        """
    
    def _generate_popup_window_finder_script(self):
        """팝업 창을 찾는 JavaScript 코드"""
        return """
        function findAndHandlePopupWindow() {
            try {
                // 🔥 팝업 창 찾기 및 JavaScript 주입
                console.log('팝업 창 찾기 시작...');
                
                // 방법 1: window.open으로 열린 팝업 찾기
                let popupWindow = null;
                for (let i = 0; i < 10; i++) {
                    try {
                        const win = window.open('', `popup_${i}`);
                        if (win && win.location.href.includes('broadcastSeminarPopup')) {
                            popupWindow = win;
                            console.log('✅ 팝업 창 발견:', win.location.href);
                            break;
                        }
                    } catch (e) {
                        // 팝업 접근 권한이 없으면 무시
                    }
                }
                
                if (popupWindow) {
                    // 🔥 팝업 창에 JavaScript 주입
                    console.log('팝업 창에 JavaScript 주입 시작...');
                    
                    const autoplayScript = generateAutoplayScript();
                    
                    try {
                        popupWindow.eval(autoplayScript);
                        console.log('✅ 팝업 창에 JavaScript 주입 성공');
                    } catch (e) {
                        console.log('❌ 팝업 창에 JavaScript 주입 실패:', e);
                    }
                    
                } else {
                    console.log('❌ 팝업 창을 찾을 수 없습니다');
                }
                
            } catch (e) {
                console.log('❌ 팝업 창 처리 중 오류:', e);
            }
        }
        """
    
    def _generate_popup_autoplay_script(self):
        """팝업 창에서 자동 재생을 위한 JavaScript 코드"""
        return """
        function generateAutoplayScript() {
            return `
                console.log('=== 팝업 창에서 자동 재생 스크립트 시작 ===');
                console.log('현재 팝업 URL:', window.location.href);
                console.log('현재 팝업 제목:', document.title);
                
                // 3초 후 재생 시도
                setTimeout(() => {
                    attemptAutoplay('1차');
                }, 3000);
                
                // 8초 후 2차 재생 시도
                setTimeout(() => {
                    attemptAutoplay('2차');
                }, 8000);
                
                console.log('=== 팝업 창에서 자동 재생 스크립트 설정 완료 ===');
            `;
        }
        
        function attemptAutoplay(attemptType) {
            console.log(\`=== 팝업에서 \${attemptType} 자동 재생 시도 시작 ===\`);
            try {
                const iframe = document.querySelector('#playView iframe');
                console.log('iframe 요소 존재 여부:', !!iframe);
                
                if (iframe) {
                    console.log('iframe 발견! src:', iframe.src);
                    console.log('iframe 로드 상태:', iframe.contentDocument?.readyState || 'unknown');
                    
                    if (attemptType === '1차') {
                        handleFirstAttempt(iframe);
                    } else {
                        handleSecondAttempt(iframe);
                    }
                    
                } else {
                    console.log(\`❌ #playView iframe을 찾을 수 없습니다 (\${attemptType})\`);
                    console.log('현재 페이지의 모든 iframe:', document.querySelectorAll('iframe').length);
                }
                
            } catch (e) {
                console.log(\`❌ \${attemptType} 자동 재생 처리 중 오류:\`, e);
            }
            console.log(\`=== 팝업에서 \${attemptType} 자동 재생 시도 완료 ===\`);
        }
        
        function handleFirstAttempt(iframe) {
            // iframe src에 autoplay 강제 추가
            let iframeSrc = iframe.src;
            if (!iframeSrc.includes('autoplay=true')) {
                iframeSrc += (iframeSrc.includes('?') ? '&' : '?') + 'autoplay=true&muted=true';
                iframe.src = iframeSrc;
                console.log('✅ autoplay 파라미터 강제 추가 완료');
            } else {
                console.log('이미 autoplay 파라미터가 있습니다');
            }
            
            // iframe 로드 완료 후 재생 시도
            iframe.onload = function() {
                console.log('iframe onload 이벤트 발생');
                setTimeout(() => {
                    console.log('iframe 로드 후 1초 대기 완료, 재생 시도 시작');
                    try {
                        // iframe 내부 접근 시도
                        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        if (iframeDoc) {
                            console.log('✅ iframe 내부 접근 성공');
                            console.log('iframe 내부 HTML 일부:', iframeDoc.body.innerHTML.substring(0, 300));
                            
                            // 재생 버튼 찾기
                            const playButton = iframeDoc.querySelector('.vjs-play-control, .vjs-big-play-button, .play-button, .play-btn, .play, [class*="play"], button[class*="play"], .vjs-play, .vjs-play-circle');
                            if (playButton) {
                                console.log('✅ 재생 버튼 발견:', playButton.className);
                                playButton.click();
                                console.log('✅ 재생 버튼 자동 클릭 완료');
                            } else {
                                console.log('❌ 재생 버튼을 찾을 수 없습니다');
                            }
                            
                            // HTML5 video 요소 찾기
                            const videoElement = iframeDoc.querySelector('video');
                            if (videoElement) {
                                console.log('✅ HTML5 video 요소 발견');
                                try {
                                    videoElement.play();
                                    console.log('✅ HTML5 video 직접 재생 시도 완료');
                                } catch (e) {
                                    console.log('❌ HTML5 video 재생 실패:', e);
                                }
                            } else {
                                console.log('❌ HTML5 video 요소를 찾을 수 없습니다');
                            }
                            
                        } else {
                            console.log('❌ iframe 내부 접근 실패');
                        }
                    } catch (e) {
                        console.log('❌ iframe 내부 처리 중 오류:', e);
                    }
                }, 1000);
            };
            
            // iframe이 이미 로드된 경우
            if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
                console.log('iframe이 이미 로드 완료 상태입니다');
                iframe.onload();
            } else {
                console.log('iframe 로딩 대기 중...');
            }
        }
        
        function handleSecondAttempt(iframe) {
            console.log('2차 시도 - iframe 발견, 강제 재로드 시도');
            let iframeSrc = iframe.src;
            iframeSrc += '&autoplay=true&muted=true&autostart=true';
            iframe.src = iframeSrc;
            console.log('✅ iframe 강제 재로드 완료');
        }
        """
    
    def _generate_common_popup_handler_script(self):
        """공통 팝업 처리를 위한 JavaScript 코드"""
        return """
        // 기타 확인 팝업들
        document.querySelector('.popup .btn_confirm')?.click();
        document.querySelector('.btn_type1.btn_confirm')?.click();
        """

    def _handle_cancel_confirmations(self):
        """JavaScript로 신청취소 확인 팝업들을 즉시 클릭"""
        try:
            self._log('CANCEL_POPUP_PROCESSING')
            
            # JavaScript로 신청취소 확인 팝업 즉시 클릭
            script = """
            // 신청취소 확인 팝업
            document.querySelector('#modalType2 .btn_confirm')?.click();
            
            // 기타 확인 팝업들
            document.querySelector('.popup .btn_confirm')?.click();
            document.querySelector('.btn_type1.btn_confirm')?.click();
            """
            
            self.web_automation.driver.execute_script(script)
            
            self._log('CANCEL_POPUP_COMPLETE')
                
        except Exception as e:
            self._log('CANCEL_POPUP_ERROR', error=str(e))
    
    # 설정 관리 메서드들
    def load_settings(self):
        """설정 파일에서 설정을 로드합니다."""
        try:
            import json
            import os
            
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                    self.logger.info("세미나 설정을 로드했습니다.")
            else:
                self.save_settings()  # 기본 설정으로 파일 생성
                
        except Exception as e:
            self.logger.error(f"설정 로드 실패: {str(e)}")
    
    def save_settings(self):
        """현재 설정을 파일에 저장합니다."""
        try:
            import json
            
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info("세미나 설정을 저장했습니다.")
            
        except Exception as e:
            self.logger.error(f"설정 저장 실패: {str(e)}")
    
    def update_settings(self, new_settings):
        """설정을 업데이트하고 저장합니다."""
        try:
            self.settings.update(new_settings)
            self.save_settings()
            self.logger.info("세미나 설정이 업데이트되었습니다.")
            return True
            
        except Exception as e:
            self.logger.error(f"설정 업데이트 실패: {str(e)}")
            return False
    
    def get_settings(self):
        """현재 설정을 반환합니다."""
        return self.settings.copy()
    
    def get_setting(self, key, default=None):
        """특정 설정값을 반환합니다."""
        return self.settings.get(key, default)
    
    def get_checked_seminars(self, tree):
        """체크된 세미나들의 정보를 수집"""
        checked_seminars = []
        
        try:
            for item in tree.get_children():
                values = tree.item(item, "values")
                tags = tree.item(item, "tags")
                
                # 체크박스가 체크된 항목인지 확인
                if len(values) > 0 and values[0] == "☑":
                    # 날짜 구분선은 제외
                    if 'date_separator' not in tags:
                        # 세미나 정보 추출
                        seminar_info = {
                            'title': values[4] if len(values) > 4 else '',  # 강의명
                            'date': values[1] if len(values) > 1 else '',    # 날짜
                            'time': values[3] if len(values) > 3 else '',    # 시간
                            'status': values[7] if len(values) > 7 else '',  # 신청상태
                            'detail_link': tags[0] if len(tags) > 0 else '', # 상세 링크
                            'status_tag': None
                        }
                        
                        # 상태 태그 찾기
                        for tag in tags:
                            if tag in ['신청가능', '신청완료', '신청마감', '입장하기', '대기중']:
                                seminar_info['status_tag'] = tag
                                break
                        
                        checked_seminars.append(seminar_info)
            
            self._log(f"체크된 세미나 {len(checked_seminars)}개 발견")
            return checked_seminars
            
        except Exception as e:
            self._log(f"체크된 세미나 수집 중 오류: {str(e)}")
            return []
    
    def process_checked_seminars(self, tree, action_type):
        """체크된 세미나들 일괄 처리 (신청/취소)"""
        try:
            # 1. 체크된 세미나 수집
            checked_seminars = self.get_checked_seminars(tree)
            
            if not checked_seminars:
                self._log("체크된 세미나가 없습니다.")
                return
            
            # 2. 액션별 처리
            success_count = 0
            fail_count = 0
            
            for i, seminar in enumerate(checked_seminars, 1):
                try:
                    # 진행 상황 표시
                    self._log(f"[{i}/{len(checked_seminars)}] {seminar['title']} 처리 중...")
                    
                    # 상태별 처리
                    if action_type == "apply":
                        # 신청 가능한 세미나만 신청
                        if seminar['status_tag'] == '신청가능':
                            success = self._process_seminar_apply(seminar)
                        else:
                            self._log(f"⚠ {seminar['title']} - 신청 불가능한 상태 ({seminar['status_tag']})")
                            success = False
                            
                    elif action_type == "cancel":
                        # 신청 완료된 세미나만 취소
                        if seminar['status_tag'] == '신청완료':
                            success = self._process_seminar_cancel(seminar)
                        else:
                            self._log(f"⚠ {seminar['title']} - 취소 불가능한 상태 ({seminar['status_tag']})")
                            success = False
                    
                    # 결과 카운트
                    if success:
                        success_count += 1
                        self._log(f"✅ {seminar['title']} {action_type} 완료")
                    else:
                        fail_count += 1
                        self._log(f"❌ {seminar['title']} {action_type} 실패")
                    
                    # 처리 간 잠시 대기
                    time.sleep(0.5)
                    
                except Exception as e:
                    fail_count += 1
                    self._log(f"❌ {seminar['title']} 처리 중 오류: {str(e)}")
            
            # 3. 결과 요약
            self._log(f"🎉 처리 완료! 성공: {success_count}개, 실패: {fail_count}개")
            
            # 4. 현황판 업데이트
            if success_count > 0 or fail_count > 0:
                self._log("🔄 현황판 업데이트 중...")
                try:
                    # 라이브세미나 페이지로 다시 이동
                    self.web_automation.driver.get(SEMINAR_URL)
                    
                    # 페이지 로딩 대기
                    self.web_automation.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LOADING_SELECTOR)))
                    
                    # 새로운 세미나 정보 수집
                    new_seminars = self.get_seminar_info()
                    
                    if new_seminars:
                        # 기존 트리뷰 데이터 삭제
                        for item in tree.get_children():
                            tree.delete(item)
                        
                        # 새로운 데이터 삽입
                        self._insert_seminar_data(tree, new_seminars)
                        
                        self._log(f"✅ 현황판 업데이트 완료 (총 {len(new_seminars)}개 세미나)")
                    else:
                        self._log("⚠ 업데이트할 세미나 정보를 찾을 수 없습니다")
                        
                except Exception as e:
                    self._log(f"❌ 현황판 업데이트 실패: {str(e)}")
            
        except Exception as e:
            self._log(f"일괄 처리 중 오류: {str(e)}")
    
    def _process_seminar_apply(self, seminar):
        """개별 세미나 신청 처리"""
        try:
            # 세미나 상세 페이지로 이동
            detail_link = seminar['detail_link']
            if detail_link.startswith('/'):
                detail_link = DOCTORVILLE_BASE_URL + detail_link
            
            self.web_automation.driver.get(detail_link)
            
            # 페이지 로딩 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.ID, "applyLiveSeminarMemberBtn")))
            
            # 신청 버튼 클릭
            return self._click_button_with_fallback(
                BUTTON_CONFIGS['seminar_apply'],
                self._handle_popup_confirmations
            )
            
        except Exception as e:
            self._log(f"세미나 신청 처리 중 오류: {str(e)}")
            return False
    
    def _process_seminar_cancel(self, seminar):
        """개별 세미나 취소 처리"""
        try:
            # 세미나 상세 페이지로 이동
            detail_link = seminar['detail_link']
            if detail_link.startswith('/'):
                detail_link = DOCTORVILLE_BASE_URL + detail_link
            
            self.web_automation.driver.get(detail_link)
            
            # 페이지 로딩 대기
            self.web_automation.wait.until(EC.presence_of_element_located((By.ID, "cancelLiveSeminarMemberBtn")))
            
            # 취소 버튼 클릭
            return self._click_button_with_fallback(
                BUTTON_CONFIGS['seminar_cancel'],
                self._handle_cancel_confirmations
            )
            
        except Exception as e:
            self._log(f"세미나 취소 처리 중 오류: {str(e)}")
            return False
    
    def manage_checkboxes(self, tree, action_type):
        """체크박스 관리 (신청가능선택/체크초기화)"""
        try:
            processed_count = 0
            
            for item in tree.get_children():
                values = tree.item(item, "values")
                tags = tree.item(item, "tags")
                
                # 날짜 구분선은 제외
                if 'date_separator' not in tags:
                    should_process = False
                    
                    if action_type == "select_available":
                        # 신청가능 상태인지 확인
                        should_process = len(values) > 7 and '신청가능' in values[7]
                        
                    elif action_type == "clear_all":
                        # 체크된 항목인지 확인
                        should_process = len(values) > 0 and values[0] == "☑"
                    
                    if should_process:
                        new_values = list(values)
                        new_values[0] = "☑" if action_type == "select_available" else "☐"
                        tree.item(item, values=new_values)
                        processed_count += 1
            
            # 결과 로깅
            if action_type == "select_available":
                self._log(f"✅ 신청가능 세미나 {processed_count}개 체크 완료")
            else:
                self._log(f"✅ 체크된 항목 {processed_count}개 초기화 완료")
                
        except Exception as e:
            self._log(f"❌ 체크박스 관리 중 오류: {str(e)}")