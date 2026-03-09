# -*- coding: utf-8 -*-
import os
import sys
import getpass

def setup():
    print("\n" + "="*50)
    print(" 닥터빌 계정 정보 설정을 시작합니다.")
    print("="*50 + "\n")

    # 1. 계정 별칭 입력
    account_name = input("▶ 계정 별칭을 입력하세요 (예: 계정1, 홍길동): ").strip()
    if not account_name:
        account_name = "Account1"

    # 2. 이메일 ID 입력
    username = input("▶ 닥터빌 로그인 이메일(ID)을 입력하세요: ").strip()
    
    # 3. 비밀번호 입력 (화면에 보이지 않음)
    password = getpass.getpass("▶ 닥터빌 로그인 비밀번호를 입력하세요 (입력 시 화면에 표시되지 않습니다): ").strip()

    # 4. 배치 파일 내용 생성 (UTF-8)
    bat_content = f"""@echo off
chcp 65001 >nul 2>&1
set ACCOUNT_NAME={account_name}
set ACCOUNT_USERNAME={username}
set ACCOUNT_PASSWORD={password}
start /min "" pythonw main.py
"""

    bat_file_name = f"{account_name}_닥터빌.bat"
    
    try:
        # 윈도우 CMD 호환을 위해 UTF-8 (BOM 없음)으로 저장
        with open(bat_file_name, "w", encoding="utf-8") as f:
            f.write(bat_content)
        
        print(f"\n✅ '{bat_file_name}' 파일이 성공적으로 생성되었습니다!")
        print(f"👉 이제 이 파일을 더블클릭하여 프로그램을 시작하세요.\n")
    except Exception as e:
        print(f"\n❌ 파일 생성 중 오류 발생: {e}")
        input("엔터 키를 눌러 종료하세요...")

if __name__ == "__main__":
    setup()
