# -*- coding: utf-8 -*-
"""
웹 자동화 기본 클래스
Chrome 웹드라이버를 설정하고 관리합니다.
"""

import sys
import os
import logging
import locale
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from webdriver_manager.chrome import ChromeDriverManager  # 로컬 chromedriver 사용으로 변경

# 브라우저 설정
BROWSER_CONFIG = {
    'headless': False,  # False: 브라우저 창 표시, True: 백그라운드 실행
    'window_size': (1200, 800),
    'implicit_wait': 2,  # 최적화: 10초 → 5초 → 2초
    'page_load_timeout': 15  # 최적화: 30초 → 15초
}

class WebAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """로거 설정"""
        # 한글 인코딩 문제 해결
        if sys.platform.startswith('win'):
            try:
                locale.setlocale(locale.LC_ALL, 'Korean_Korea.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
                except:
                    pass
        
        # 로거 설정 (콘솔 출력만)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()  # 콘솔 출력
            ]
        )
        return logging.getLogger(__name__)
    
    def setup_driver(self):
        """Chrome 웹드라이버 설정"""
        try:
            chrome_options = Options()
            
            # 브라우저 설정 적용
            if BROWSER_CONFIG['headless']:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size={},{}'.format(*BROWSER_CONFIG['window_size']))
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 다운로드 폴더 설정 (modules 폴더로)
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            modules_dir = os.path.join(current_dir, "modules")
            chrome_options.add_experimental_option("prefs", {
                "download.default_directory": modules_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            
            # 로컬 ChromeDriver 사용
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            chromedriver_path = os.path.join(current_dir, "chromedriver.exe")
            service = Service(chromedriver_path)
            
            # 웹드라이버 생성
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(BROWSER_CONFIG['implicit_wait'])
            self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
            
            # WebDriverWait 설정
            self.wait = WebDriverWait(self.driver, 5)
            
            self.logger.info("웹드라이버가 성공적으로 설정되었습니다.")
            return True
            
        except Exception as e:
            self.logger.error(f"웹드라이버 설정 실패: {str(e)}")
            return False
    
    def get_current_url(self):
        """현재 URL 반환"""
        if self.driver:
            return self.driver.current_url
        return None
    
    def get_page_title(self):
        """현재 페이지 제목 반환"""
        if self.driver:
            return self.driver.title
        return None
    
    def close_driver(self):
        """웹드라이버 종료"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("웹드라이버가 종료되었습니다.")
            except Exception as e:
                self.logger.error(f"웹드라이버 종료 실패: {str(e)}")
    

