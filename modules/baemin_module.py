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
            
            # 결과 데이터 추출 (표준화된 dict 또는 기존 dict 대응)
            data = result.get('data', result) if isinstance(result, dict) else {}
            
            if data and 'points' in data:
                points_str = str(data['points']).replace(',', '').replace('P', '').strip()
                try:
                    return int(points_str)
                except ValueError:
                    self.log_warning(f"포인트 파싱 실패: {data['points']}")
                    return 0
            return 0
            
        except Exception as e:
            self.log_error(f"포인트 조회 중 오류: {str(e)}")
            return 0
    
    def calculate_max_coupons(self, points):
        """최대 구매 가능한 쿠폰 수를 계산합니다."""
        return points // COUPON_PRICE
    
    def get_phone_number(self):
        """고정된 휴대폰 번호를 반환합니다."""
        phone_number = "01075713178"
        self.log_success(f"휴대폰 번호: {phone_number}")
        return phone_number
    
    def execute(self, quantity=1, phone_number=''):
        """배달의민족 쿠폰을 지정 수량만큼 구매합니다."""
        main_window = None
        try:
            if not self.web_automation or not self.web_automation.driver:
                return self.create_result(False, "웹드라이버가 초기화되지 않았습니다. 먼저 로그인해주세요.")
            
            if not phone_number:
                return self.create_result(False, "받은 사람 번호가 없습니다.")
            
            driver = self.web_automation.driver
            main_window = driver.current_window_handle
            
            self.log_info(f"배달의민족 쿠폰 {quantity}개 구매를 시작합니다...")
            # ... (기존 로직 동일) ...
            # 생략된 부분은 위와 동일하게 유지하되, 리턴 전에 탭 정리가 필요하므로 구조를 조정합니다.
            
            # [기존 로직 진행...]
            self.log_info("빌마켓으로 이동 중...")
            
            if "pointUseHistoryList" not in driver.current_url:
                driver.get(POINTS_PAGE_URL)
                time.sleep(2)
            
            driver.execute_script("openPointShop();")
            self.log_info("빌마켓 버튼 클릭 완료")
            
            for i in range(10):
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    self.log_info("빌마켓 탭으로 전환")
                    break
                time.sleep(0.5)
            else:
                return self.create_result(False, "빌마켓 탭이 열리지 않았습니다")
            
            driver.get(COUPON_ORDER_URL)
            for i in range(20):
                if "MCouponBulkOrder" in driver.current_url:
                    break
                time.sleep(0.5)
            else:
                return self.create_result(False, f"쿠폰 페이지 로딩 실패: {driver.current_url}")
            
            self.log_success("쿠폰 주문 페이지 도착!")
            time.sleep(1)
            
            phone_lines = "\n".join([phone_number] * quantity)
            self.log_info(f"연락처 입력 중... ({phone_number} × {quantity}개)")
            
            textarea = self.find_element_safe(By.ID, "rcvMobiles")
            textarea.clear()
            textarea.send_keys(phone_lines)
            
            self.log_info("입력완료 클릭...")
            driver.execute_script("chckMobiles();")
            time.sleep(1)
            
            try:
                cnt_element = self.find_element_safe(By.ID, "rcvMobileCnt", timeout=5)
                cnt = cnt_element.text.strip()
                self.log_info(f"총 발송 수량: {cnt}건")
            except:
                pass
            
            self.log_info("다음 버튼 클릭...")
            driver.execute_script("document.getElementById('btnPayment').click();")
            
            try:
                from selenium.webdriver.support.ui import WebDriverWait
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                self.log_info(f"알림창 확인: {alert.text}")
                alert.accept()
                time.sleep(2)
            except:
                pass
            
            self.log_success("결제 페이지 도착!")
            time.sleep(1)
            
            try:
                price_element = self.find_element_safe(By.CSS_SELECTOR, "#total_goods_price span")
                price_text = price_element.text.strip().replace(',', '')
                self.log_info(f"상품금액: {price_text}원")
                
                point_input = self.find_element_safe(By.ID, "point_etc1")
                point_input.clear()
                point_input.send_keys(price_text)
                self.log_success(f"엠서클 포인트 {price_text}원 입력 완료")
            except Exception as e:
                return self.create_result(False, f"포인트 입력 실패: {str(e)}")
            
            self.log_info("포인트 적용 클릭...")
            driver.execute_script("document.getElementById('chkMcircelPoint').click();")
            time.sleep(1)
            
            try:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert_text = alert.text
                self.log_info(f"포인트 적용 알림: {alert_text}")
                
                if "포인트보다 많은 금액" in alert_text or "부족" in alert_text:
                    alert.accept()
                    return self.create_result(False, f"포인트 적용 실패: {alert_text}")
                
                alert.accept()
                self.log_success("포인트 적용 완료")
            except:
                self.log_info("알림창 없음, 진행 시도")
            
            self.log_info("동의 항목 체크 중...")
            driver.execute_script("document.getElementById('agreeFlow').click();")
            time.sleep(0.3)
            driver.execute_script("document.getElementById('chkReSale').click();")
            time.sleep(0.3)
            self.log_success("개인정보 제공 동의 & 재판매 금지 동의 체크 완료")
            
            return self.create_result(True, f"배달의민족 쿠폰 {quantity}개 구매 프로세스 완료")
            
        except Exception as e:
            error_msg = f"쿠폰 구매 중 오류: {str(e)}"
            self.log_error(error_msg)
            return self.create_result(False, error_msg)
        finally:
            # 탭 정리: 현재 창이 메인 창이 아닐 경우 닫고 메인으로 전환
            if self.web_automation and self.web_automation.driver:
                driver = self.web_automation.driver
                try:
                    if main_window and driver.current_window_handle != main_window:
                        self.log_info("빌마켓 탭을 닫고 메인 페이지로 돌아갑니다.")
                        driver.close()
                        driver.switch_to.window(main_window)
                except:
                    # 메인 창만 남은 경우 등 예외 처리
                    if len(driver.window_handles) > 0:
                        driver.switch_to.window(driver.window_handles[0])
    
