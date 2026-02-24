# -*- coding: utf-8 -*-
"""
배달의민족 쿠폰 자동 구매 모듈
닥터빌 포인트로 배달의민족 쿠폰을 자동 구매합니다.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_module import BaseModule

# 상수 정의
COUPON_PRICE = 9700  # 배달의민족 10,000원 쿠폰 가격 (포인트)
COUPON_VALUE = 10000  # 쿠폰 실제 가치 (원)
POINTS_PAGE_URL = "https://www.doctorville.co.kr/my/point/pointUseHistoryList"
COUPON_ORDER_URL = "https://mcircle.bizmarketb2b.com/Order/MCouponBulkOrder.aspx?guid=14152303&cate=0"
MY_PAGE_URL = "https://www.doctorville.co.kr/my/main"

class BaeminModule(BaseModule):
    def __init__(self, web_automation, gui_logger=None):
        super().__init__(web_automation, gui_logger)
    
    def get_current_points(self):
        """현재 포인트를 조회합니다."""
        try:
            from modules.points_check_module import PointsCheckModule
            points_module = PointsCheckModule(self.web_automation, self.gui_logger)
            
            if hasattr(self, 'gui_callbacks'):
                points_module.set_callbacks(self.gui_callbacks)
                if 'gui_instance' in self.gui_callbacks and self.gui_callbacks['gui_instance']:
                    points_module.gui_instance = self.gui_callbacks['gui_instance']
            
            result = points_module.get_user_info_summary()
            
            if result and 'points' in result:
                points_str = str(result['points']).replace(',', '').replace('P', '').strip()
                try:
                    return int(points_str)
                except ValueError:
                    self._log(f"⚠ 포인트 파싱 실패: {result['points']}")
                    return 0
            return 0
            
        except Exception as e:
            self._log(f"❌ 포인트 조회 중 오류: {str(e)}")
            return 0
    
    def calculate_max_coupons(self, points):
        """최대 구매 가능한 쿠폰 수를 계산합니다."""
        return points // COUPON_PRICE
    
    def get_phone_number(self):
        """마이페이지에서 휴대폰 번호를 가져옵니다 (대시 제거)."""
        try:
            driver = self.web_automation.driver
            
            self._log("📱 휴대폰 번호 조회 중...")
            driver.get(MY_PAGE_URL)
            time.sleep(1)
            
            # 휴대폰 필드 찾기: <li><strong>휴대폰</strong><span>010-XXXX-XXXX</span></li>
            phone_elements = driver.find_elements(By.XPATH, 
                "//li[strong[contains(text(),'휴대폰')]]/span")
            
            if phone_elements:
                raw_phone = phone_elements[0].text.strip()
                phone_number = raw_phone.replace('-', '')
                self._log(f"✅ 휴대폰 번호: {phone_number}")
                return phone_number
            
            self._log("❌ 휴대폰 번호를 찾을 수 없습니다")
            return None
            
        except Exception as e:
            self._log(f"❌ 휴대폰 번호 조회 오류: {str(e)}")
            return None
    
    def execute(self, quantity=1, phone_number=''):
        """배달의민족 쿠폰을 지정 수량만큼 구매합니다."""
        try:
            if not self.web_automation or not self.web_automation.driver:
                self._log("❌ 웹드라이버가 초기화되지 않았습니다. 먼저 로그인해주세요.")
                return False
            
            if not phone_number:
                self._log("❌ 받는 사람 번호가 없습니다.")
                return False
            
            driver = self.web_automation.driver
            
            self._log(f"🛵 배달의민족 쿠폰 {quantity}개 구매를 시작합니다...")
            
            # 1단계: 포인트 페이지에서 빌마켓 버튼 클릭
            self._log("📍 빌마켓으로 이동 중...")
            
            if "pointUseHistoryList" not in driver.current_url:
                driver.get(POINTS_PAGE_URL)
                time.sleep(2)
            
            driver.execute_script("openPointShop();")
            self._log("✅ 빌마켓 버튼 클릭 완료")
            
            # 2단계: 새 탭 열림 대기 → 즉시 전환
            for i in range(10):
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    self._log("📍 빌마켓 탭으로 전환")
                    break
                time.sleep(0.5)
            else:
                self._log("❌ 빌마켓 탭이 열리지 않았습니다")
                return False
            
            # 3단계: 배달의민족 쿠폰 주문 페이지로 이동
            self._log("📍 배달의민족 쿠폰 페이지로 이동 중...")
            driver.get(COUPON_ORDER_URL)
            
            for i in range(20):
                if "MCouponBulkOrder" in driver.current_url:
                    break
                time.sleep(0.5)
            else:
                self._log(f"❌ 쿠폰 페이지 로딩 실패: {driver.current_url}")
                return False
            
            self._log("✅ 쿠폰 주문 페이지 도착!")
            time.sleep(1)
            
            # 4단계: 연락처 textarea에 번호 입력 (수량만큼 줄바꿈)
            phone_lines = "\n".join([phone_number] * quantity)
            self._log(f"📱 연락처 입력 중... ({phone_number} × {quantity}개)")
            
            textarea = driver.find_element(By.ID, "rcvMobiles")
            textarea.clear()
            textarea.send_keys(phone_lines)
            
            # 5단계: 입력완료 버튼 클릭
            self._log("📋 입력완료 클릭...")
            driver.execute_script("chckMobiles();")
            time.sleep(1)
            
            # 발송 수량 확인
            try:
                cnt_element = driver.find_element(By.ID, "rcvMobileCnt")
                cnt = cnt_element.text.strip()
                self._log(f"✅ 총 발송 수량: {cnt}건")
            except:
                self._log("⚠ 발송 수량 확인 실패 (계속 진행)")
            
            # 6단계: 다음 버튼 클릭
            self._log("📍 다음 버튼 클릭...")
            driver.execute_script("document.getElementById('btnPayment').click();")
            
            # 7단계: 알림창(alert) 처리
            try:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                # 알림창 대기 (최대 5초)
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                self._log(f"🔔 알림창 확인: {alert.text}")
                alert.accept()
                self._log("✅ 알림창 확인 버튼 클릭 완료")
                time.sleep(2)
            except:
                self._log("ℹ 알림창이 나타나지 않았거나 이미 처리되었습니다.")
            
            self._log("✅ 결제 페이지 도착!")
            time.sleep(1)
            
            # 8단계: 상품금액 가져와서 포인트 입력
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, "#total_goods_price span")
                price_text = price_element.text.strip().replace(',', '')
                self._log(f"💰 상품금액: {price_text}원")
                
                point_input = driver.find_element(By.ID, "point_etc1")
                point_input.clear()
                point_input.send_keys(price_text)
                self._log(f"✅ 엠서클 포인트 {price_text}원 입력 완료")
            except Exception as e:
                self._log(f"❌ 포인트 입력 실패: {str(e)}")
                return False
            
            # 9단계: 포인트 적용 버튼 클릭
            self._log("📍 포인트 적용 클릭...")
            driver.execute_script("document.getElementById('chkMcircelPoint').click();")
            time.sleep(1)
            
            # 포인트 적용 후 알림창 처리
            try:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                self._log(f"🔔 포인트 적용 알림: {alert.text}")
                alert.accept()
            except:
                pass
            
            self._log("✅ 포인트 적용 완료")
            
            # 10단계: 동의 체크박스 클릭
            self._log("📋 동의 항목 체크 중...")
            driver.execute_script("document.getElementById('agreeFlow').click();")
            time.sleep(0.3)
            driver.execute_script("document.getElementById('chkReSale').click();")
            time.sleep(0.3)
            self._log("✅ 개인정보 제공 동의 & 재판매 금지 동의 체크 완료")
            
            return True
            
        except Exception as e:
            self._log(f"❌ 쿠폰 구매 중 오류: {str(e)}")
            return False
    
    def _log(self, message):
        """로그 메시지를 출력합니다."""
        if self.gui_logger:
            self.gui_logger(message)
