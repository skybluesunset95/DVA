# -*- coding: utf-8 -*-
"""
세미나 모듈
닥터빌 라이브세미나 정보를 수집하고 관리합니다.
"""

import time
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_module import BaseModule
from .utils import get_status_tag

# URL 상수 정의
SEMINAR_URL = "https://www.doctorville.co.kr/seminar/main"
DOCTORVILLE_BASE_URL = "https://www.doctorville.co.kr"

# CSS 선택자 상수 정의
LOADING_SELECTOR = ".list_cont"

# 세미나 데이터 필드 정의
SEMINAR_FIELDS = {
    'date': {'selector': '.seminar_day .date', 'parent': True, 'attribute': 'text'},
    'day': {'selector': '.seminar_day .day', 'parent': True, 'attribute': 'text'},
    'time': {'selector': '.time', 'parent': False, 'attribute': 'text', 'process': 'clean_text'},
    'title': {'selector': '.list_tit .tit', 'parent': False, 'attribute': 'text'},
    'lecturer': {'selector': '.list_tit .tail', 'parent': False, 'attribute': 'text'},
    'person': {'selector': '.progress .person', 'parent': False, 'attribute': 'text'},
    'status': {'selector': '.progress .ico_box', 'parent': False, 'attribute': 'text'},
    'detail_link': {'selector': 'self', 'parent': False, 'attribute': 'href'}
}

# 버튼 설정 정의
BUTTON_CONFIGS = {
    'seminar_apply': {
        'selectors': [{'type': 'id', 'value': 'applyLiveSeminarMemberBtn'}],
        'log_search': 'BUTTON_SEARCH', 'log_found': 'BUTTON_FOUND', 'log_disabled': 'BUTTON_DISABLED',
        'log_click': 'BUTTON_CLICK', 'log_not_found': 'BUTTON_NOT_FOUND', 'log_timeout': 'BUTTON_NOT_FOUND', 'log_error': 'BUTTON_ERROR'
    },
    'seminar_cancel': {
        'selectors': [{'type': 'id', 'value': 'cancelLiveSeminarMemberBtn'}],
        'log_search': 'CANCEL_SEARCH', 'log_found': 'CANCEL_FOUND', 'log_disabled': 'CANCEL_DISABLED',
        'log_click': 'CANCEL_CLICK', 'log_not_found': 'CANCEL_NOT_FOUND', 'log_timeout': 'CANCEL_NOT_FOUND', 'log_error': 'CANCEL_ERROR'
    },
    'seminar_enter': {
        'selectors': [
            {'type': 'css', 'value': "a.btn_bn.btn_enter[onclick*='playOnPopup']"},
            {'type': 'xpath', 'value': "//a[contains(@class, 'btn_enter') and text()='입장하기']"},
            {'type': 'css', 'value': '.btn_bn.btn_enter'}
        ],
        'log_search': 'ENTER_SEARCH', 'log_found': 'ENTER_FOUND', 'log_disabled': 'ENTER_DISABLED',
        'log_click': 'ENTER_CLICK', 'log_not_found': 'ENTER_NOT_FOUND', 'log_timeout': 'ENTER_NOT_FOUND', 'log_error': 'ENTER_ERROR'
    }
}

class SeminarModule(BaseModule):
    # 로그 메시지 상수
    LOG_MESSAGES = {
        'START': "라이브세미나 모듈 시작",
        'NAVIGATING': "라이브세미나 페이지로 이동 중...",
        'WAITING': "페이지 로딩 대기 중...",
        'SUCCESS': "라이브세미나 페이지 이동 완료",
        'COLLECTING': "세미나 정보 수집 시작...",
        'COMPLETE': "총 {count}개의 세미나 정보 수집 완료",
        'NO_DATA': "세미나 정보를 찾을 수 없습니다.",
        'COLLECT_ERROR': "세미나 정보 수집 실패: {error}",
        'JS_COLLECTING': "JavaScript로 세미나 정보 일괄 수집 중...",
        'JS_COMPLETE': "총 {count}개의 세미나 정보 일괄 수집 완료",
        'JS_ERROR': "JavaScript 세미나 정보 수집 중 오류: {error}",
        'BUTTON_SEARCH': "세미나 신청/입장 버튼 검색 중...",
        'BUTTON_CLICK': "'{text}' 버튼 클릭 완료",
        'BUTTON_DISABLED': "버튼이 비활성화 상태입니다",
        'BUTTON_NOT_FOUND': "세미나 버튼을 찾을 수 없습니다",
        'BUTTON_ERROR': "세미나 버튼 클릭 실패: {error}",
        'POPUP_PROCESSING': "팝업 처리 중...",
        'POPUP_COMPLETE': "팝업 처리 완료",
        'CANCEL_SEARCH': "신청취소 버튼 검색 중...",
        'ENTER_SEARCH': "입장하기 버튼 검색 중...",
        'ENTER_ERROR': "입장하기 실패: {error}",
        'PAGE_MOVING': "세미나 페이지로 이동 중..."
    }

    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
        self.settings = {
            'auto_apply': False,
            'refresh_interval': 30,
            'timeout': 10
        }
    
    def _log(self, message_key, **kwargs):
        message = self.LOG_MESSAGES.get(message_key, message_key)
        if kwargs:
            message = message.format(**kwargs)
            
        if 'ERROR' in message_key or 'FAIL' in message_key:
            self.log_error(message)
        elif 'SUCCESS' in message_key or 'COMPLETE' in message_key:
            self.log_success(message)
        elif 'WARNING' in message_key or 'NO_DATA' in message_key:
            self.log_warning(message)
        else:
            self.log_info(message)
    
    def navigate_to_seminar_main(self):
        """세미나 메인 페이지로 이동"""
        try:
            self.web_automation.driver.get(SEMINAR_URL)
            self.web_automation.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LOADING_SELECTOR)))
            return True
        except Exception as e:
            self._log('COLLECT_ERROR', error=str(e))
            return False

    def get_seminar_list(self):
        """세미나 목록 데이터 가져오기"""
        if not self.navigate_to_seminar_main():
            return []
        return self._collect_with_js()

    def _collect_with_js(self):
        try:
            fields_script = self._generate_js_fields_script()
            script = f"""
            {fields_script}
            return Array.from(document.querySelectorAll('.list_detail')).map(item => {{
                const parentContainer = item.closest('.list_cont');
                return extractSeminarData(item, parentContainer);
            }});
            """
            return self.web_automation.driver.execute_script(script)
        except Exception as e:
            self._log('JS_ERROR', error=str(e))
            return self._fallback_collect()

    def _fallback_collect(self):
        seminars = []
        try:
            items = self.web_automation.driver.find_elements(By.CSS_SELECTOR, ".list_detail")
            for item in items:
                try:
                    parent = item.find_element(By.XPATH, "./ancestor::div[contains(@class, 'list_cont')]")
                    seminars.append(self._extract_seminar_data(item, parent))
                except: continue
        except: pass
        return seminars

    def _extract_seminar_data(self, item, parent):
        data = {}
        for name, config in SEMINAR_FIELDS.items():
            try:
                elem = item if config['selector'] == 'self' else \
                       (parent.find_element(By.CSS_SELECTOR, config['selector']) if config['parent'] else \
                        item.find_element(By.CSS_SELECTOR, config['selector']))
                val = elem.text.strip() if config['attribute'] == 'text' else elem.get_attribute('href')
                if config.get('process') == 'clean_text': val = val.replace('\n', ' ').replace('  ', ' ')
                data[name] = val
            except: data[name] = ''
        return data

    def _generate_js_fields_script(self):
        js = "function extractSeminarData(item, parentContainer) { const data = {};"
        for name, config in SEMINAR_FIELDS.items():
            if config['selector'] == 'self':
                js += f"data['{name}'] = item.getAttribute('href') || '';"
            elif config['parent']:
                js += f"const e{name} = parentContainer.querySelector('{config['selector']}'); data['{name}'] = e{name} ? e{name}.textContent.trim() : '';"
            else:
                js += f"const e{name} = item.querySelector('{config['selector']}'); data['{name}'] = e{name} ? e{name}.textContent.trim() : '';"
        js += "return data; }"
        return js

    def _click_button_with_fallback(self, config, popup_handler=None):
        try:
            button = None
            for sel in config['selectors']:
                try:
                    if sel['type'] == 'id': button = self.web_automation.driver.find_element(By.ID, sel['value'])
                    elif sel['type'] == 'css': button = self.web_automation.driver.find_element(By.CSS_SELECTOR, sel['value'])
                    elif sel['type'] == 'xpath': button = self.web_automation.driver.find_element(By.XPATH, sel['value'])
                    if button: break
                except: continue
            
            if not button or not button.is_enabled(): return False
            
            button.click()
            if popup_handler: popup_handler()
            return True
        except: return False

    def handle_seminar_action(self, detail_link, status_tag):
        """특정 세미나에 대한 액션 수행 (신청/취소/입장)"""
        try:
            # 절대 경로 보장
            if detail_link.startswith('/'):
                detail_link = DOCTORVILLE_BASE_URL + detail_link
            
            self.web_automation.driver.get(detail_link)
            
            if status_tag == '신청완료':
                return self.cancel_seminar()
            elif status_tag == '입장하기':
                return self.enter_seminar()
            else:
                return self.apply_seminar()
        except: return False

    def apply_seminar(self):
        try:
            self.web_automation.wait.until(EC.presence_of_element_located((By.ID, "applyLiveSeminarMemberBtn")))
            return self._click_button_with_fallback(BUTTON_CONFIGS['seminar_apply'], self._handle_popup_confirmations)
        except: return False

    def cancel_seminar(self):
        try:
            self.web_automation.wait.until(EC.presence_of_element_located((By.ID, "cancelLiveSeminarMemberBtn")))
            return self._click_button_with_fallback(BUTTON_CONFIGS['seminar_cancel'], self._handle_cancel_confirmations)
        except: return False

    def enter_seminar(self):
        return self._click_button_with_fallback(BUTTON_CONFIGS['seminar_enter'])

    def _handle_popup_confirmations(self):
        script = """
        document.querySelector('#seminarAgree .btn_confirm')?.click();
        document.querySelector('#marketingAgree .btn_confirm')?.click();
        document.querySelector('#modalType2 .btn_confirm')?.click();
        """
        self.web_automation.driver.execute_script(script)

    def _handle_cancel_confirmations(self):
        script = "document.querySelector('#modalType2 .btn_confirm')?.click();"
        self.web_automation.driver.execute_script(script)

    def execute(self):
        """세미나 정보 수집 실행"""
        try:
            seminars = self.get_seminar_list()
            if seminars:
                return self.create_result(True, f"세미나 {len(seminars)}개 수집 완료", {"seminars": seminars, "count": len(seminars)})
            else:
                return self.create_result(True, "진행 중인 세미나가 없습니다", {"seminars": [], "count": 0})
        except Exception as e:
            error_msg = f"세미나 정보 수집 실패: {str(e)}"
            self.log_error(error_msg)
            return self.create_result(False, error_msg)