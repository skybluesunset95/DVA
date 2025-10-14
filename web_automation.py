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
from webdriver_manager.chrome import ChromeDriverManager
import shutil

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
        """Chrome 웹드라이버 설정 (로컬 우선, 실패 시 자동 업데이트)"""
        
        # 1단계: 로컬 chromedriver로 시도
        try:
            return self._try_local_chromedriver()
        except Exception as e:
            error_msg = str(e)
            
            # 버전 오류 또는 파일 없음 확인
            need_update = False
            if "This version of ChromeDriver only supports Chrome version" in error_msg:
                self.logger.warning("ChromeDriver 버전 불일치 감지 - 자동 업데이트 시작...")
                need_update = True
            elif "Unable to locate or obtain driver" in error_msg:
                self.logger.warning("ChromeDriver 파일 없음 감지 - 자동 다운로드 시작...")
                need_update = True
            
            if need_update:
                # 2단계: webdriver-manager로 최신 버전 다운로드 & 교체
                if self._update_chromedriver():
                    self.logger.info("ChromeDriver 업데이트 완료 - 재시도 중...")
                    
                    # 3단계: 업데이트된 로컬 파일로 재시도
                    try:
                        result = self._try_local_chromedriver()
                        
                        # 성공 시 백업 파일 삭제
                        if result:
                            self._cleanup_old_chromedriver()
                        
                        return result
                    except Exception as retry_error:
                        self.logger.error(f"업데이트 후 재시도 실패: {str(retry_error)}")
                        return False
            
            self.logger.error(f"웹드라이버 설정 실패: {error_msg}")
            return False
    
    def _try_local_chromedriver(self):
        """로컬 chromedriver.exe로 실행 시도"""
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(current_dir, "modules")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": modules_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        # 로컬 ChromeDriver 사용
        chromedriver_path = os.path.join(current_dir, "chromedriver.exe")
        service = Service(chromedriver_path)
        
        # 웹드라이버 생성
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(BROWSER_CONFIG['implicit_wait'])
        self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
        
        # WebDriverWait 설정
        self.wait = WebDriverWait(self.driver, 1)
        
        self.logger.info("웹드라이버가 성공적으로 설정되었습니다.")
        return True
    
    def _update_chromedriver(self):
        """webdriver-manager로 최신 chromedriver 다운로드 후 교체"""
        try:
            self.logger.info("최신 ChromeDriver 다운로드 중...")
            
            # webdriver-manager로 최신 버전 다운로드
            latest_driver_path = ChromeDriverManager().install()
            
            # 실제 chromedriver.exe 파일 찾기
            # webdriver-manager가 반환하는 경로는 디렉토리이거나 잘못된 파일일 수 있음
            driver_dir = os.path.dirname(latest_driver_path)
            actual_driver_path = None
            
            # chromedriver.exe 파일 찾기
            for root, dirs, files in os.walk(driver_dir):
                for file in files:
                    if file.lower() == "chromedriver.exe":
                        actual_driver_path = os.path.join(root, file)
                        break
                if actual_driver_path:
                    break
            
            if not actual_driver_path or not os.path.exists(actual_driver_path):
                self.logger.error("다운로드된 chromedriver.exe 파일을 찾을 수 없습니다.")
                return False
            
            # 현재 디렉토리의 chromedriver.exe 경로
            current_dir = os.path.dirname(os.path.abspath(__file__))
            local_chromedriver_path = os.path.join(current_dir, "chromedriver.exe")
            
            # 기존 파일 백업 (있으면)
            if os.path.exists(local_chromedriver_path):
                backup_path = os.path.join(current_dir, "chromedriver_old.exe")
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(local_chromedriver_path, backup_path)
                self.logger.info("기존 ChromeDriver 백업 완료")
            
            # 다운로드된 파일을 로컬로 복사
            shutil.copy2(actual_driver_path, local_chromedriver_path)
            self.logger.info(f"ChromeDriver 업데이트 완료! ({actual_driver_path})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ChromeDriver 업데이트 실패: {str(e)}")
            return False
    
    def _cleanup_old_chromedriver(self):
        """백업된 구 버전 chromedriver 삭제"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backup_path = os.path.join(current_dir, "chromedriver_old.exe")
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
                self.logger.info("구 버전 ChromeDriver 삭제 완료")
        except Exception as e:
            self.logger.warning(f"구 버전 ChromeDriver 삭제 실패 (무시 가능): {str(e)}")
    
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
    

