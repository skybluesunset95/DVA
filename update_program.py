#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
닥터빌 프로그램 자동 업데이트 도구
GitHub에서 최신 파일들을 다운로드하여 프로그램을 업데이트합니다.
개인 파일들(.bat, .exe, .ini, .log, .json)은 보존합니다.
"""

import os
import sys
import shutil
import requests
import zipfile
import json
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
from datetime import datetime
import threading

class UpdateGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("닥터빌 업데이트")
        self.root.geometry("400x200")
        self.progress_window = None
        
    def show_update_dialog(self):
        """업데이트 확인 팝업"""
        result = messagebox.askyesno(
            "업데이트 확인", 
            "닥터빌 프로그램을 최신 버전으로 업데이트하시겠습니까?"
        )
        return result
    
    def show_progress(self):
        """업데이트 진행 중 창"""
        self.progress_window = tk.Toplevel()
        self.progress_window.title("업데이트 중")
        self.progress_window.geometry("300x100")
        self.progress_window.resizable(False, False)
        
        # 중앙에 배치
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        tk.Label(self.progress_window, text="업데이트 중입니다...", font=("맑은 고딕", 12)).pack(pady=20)
        
        # 프로그레스 바
        self.progress = ttk.Progressbar(self.progress_window, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill='x')
        self.progress.start()
        
        self.progress_window.update()
    
    def close_progress(self):
        """진행 중 창 닫기"""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
    
    def show_complete(self, success):
        """완료 메시지"""
        if success:
            messagebox.showinfo("완료", "업데이트가 완료되었습니다!")
        else:
            messagebox.showerror("실패", "업데이트에 실패했습니다.")
    
    def run(self):
        """GUI 실행"""
        self.root.withdraw()  # 메인 창 숨기기
        
        # 업데이트 확인
        if self.show_update_dialog():
            # 진행 중 창 표시
            self.show_progress()
            
            # 백그라운드에서 업데이트 실행
            updater = DoctorBillUpdater()
            success = updater.run_update()
            
            # 진행 중 창 닫기
            self.close_progress()
            
            # 완료 메시지
            self.show_complete(success)
        
        self.root.destroy()

class DoctorBillUpdater:
    def __init__(self):
        # update_program.py가 있는 폴더를 기준으로 설정
        self.current_dir = Path(__file__).parent
        self.backup_dir = self.current_dir / "backup_temp"
        self.github_repo = "https://api.github.com/repos/skybluesunset95/DVA"
        self.github_download = "https://github.com/skybluesunset95/DVA/archive/main.zip"
        
        # 보존할 파일 확장자들
        self.preserve_extensions = ['.bat', '.exe', '.ini', '.log', '.json', '.txt']
        
        # 업데이트할 파일/폴더들
        self.update_targets = [
            'main_GUI.pyw',
            'main_task_manager.py', 
            'web_automation.py',
            'modules/',
            'requirements.txt',
            'README.md'
        ]
    
    def print_status(self, message):
        """상태 메시지 출력"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def create_backup(self):
        """현재 파일들을 백업"""
        self.print_status("백업 생성 중...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir()
        
        # 모든 파일을 백업
        for item in self.current_dir.iterdir():
            if item.is_file() and item.name != "update_program.py":
                shutil.copy2(item, self.backup_dir / item.name)
            elif item.is_dir() and item.name not in ["backup_temp", "__pycache__"]:
                shutil.copytree(item, self.backup_dir / item.name)
        
        self.print_status("백업 완료")
    
    def download_latest_version(self):
        """GitHub에서 최신 버전 다운로드"""
        self.print_status("최신 버전 다운로드 중...")
        
        try:
            response = requests.get(self.github_download, timeout=30)
            response.raise_for_status()
            
            zip_path = self.current_dir / "latest_version.zip"
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            self.print_status("다운로드 완료")
            return zip_path
            
        except requests.RequestException as e:
            self.print_status(f"다운로드 실패: {e}")
            return None
    
    def extract_and_update(self, zip_path):
        """압축 파일을 해제하고 업데이트"""
        self.print_status("파일 업데이트 중...")
        
        extract_dir = self.current_dir / "temp_extract"
        
        try:
            # 압축 해제
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 압축 파일 내부의 실제 폴더 찾기 (보통 DVA-main 형태)
            extracted_folder = None
            for item in extract_dir.iterdir():
                if item.is_dir() and "DVA" in item.name:
                    extracted_folder = item
                    break
            
            if not extracted_folder:
                self.print_status("압축 파일 구조를 찾을 수 없습니다")
                return False
            
            # 파일 업데이트
            updated_count = 0
            for target in self.update_targets:
                source_path = extracted_folder / target
                dest_path = self.current_dir / target
                
                if source_path.exists():
                    if source_path.is_file():
                        # 개인 파일이 아닌 경우에만 업데이트
                        if not self.should_preserve_file(dest_path):
                            shutil.copy2(source_path, dest_path)
                            updated_count += 1
                            self.print_status(f"업데이트: {target}")
                    elif source_path.is_dir():
                        # 폴더의 경우 개인 파일 제외하고 업데이트
                        self.update_folder(source_path, dest_path)
                        updated_count += 1
                        self.print_status(f"폴더 업데이트: {target}")
            
            self.print_status(f"총 {updated_count}개 파일/폴더 업데이트 완료")
            return True
            
        except Exception as e:
            self.print_status(f"업데이트 실패: {e}")
            return False
        finally:
            # 임시 파일들 정리
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            if zip_path.exists():
                zip_path.unlink()
    
    def should_preserve_file(self, file_path):
        """파일을 보존해야 하는지 확인"""
        if not file_path.exists():
            return False
        
        # 확장자로 판단
        if file_path.suffix.lower() in self.preserve_extensions:
            return True
        
        # 특정 파일명으로 판단
        preserve_names = ['chromedriver', 'config', 'settings']
        if any(name in file_path.name.lower() for name in preserve_names):
            return True
        
        return False
    
    def update_folder(self, source_folder, dest_folder):
        """폴더 업데이트 (개인 파일 보존)"""
        if not dest_folder.exists():
            dest_folder.mkdir(parents=True)
        
        for item in source_folder.iterdir():
            dest_item = dest_folder / item.name
            
            if item.is_file():
                if not self.should_preserve_file(dest_item):
                    shutil.copy2(item, dest_item)
            elif item.is_dir():
                self.update_folder(item, dest_item)
    
    def restore_backup(self):
        """백업에서 복원"""
        self.print_status("백업에서 복원 중...")
        
        try:
            for item in self.backup_dir.iterdir():
                dest_path = self.current_dir / item.name
                
                if item.is_file():
                    shutil.copy2(item, dest_path)
                elif item.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(item, dest_path)
            
            self.print_status("복원 완료")
            return True
            
        except Exception as e:
            self.print_status(f"복원 실패: {e}")
            return False
    
    def cleanup(self):
        """임시 파일들 정리"""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
    
    def run_update(self):
        """업데이트 실행"""
        self.print_status("닥터빌 프로그램 업데이트를 시작합니다...")
        
        try:
            # 1. 백업 생성
            self.create_backup()
            
            # 2. 최신 버전 다운로드
            zip_path = self.download_latest_version()
            if not zip_path:
                return False
            
            # 3. 파일 업데이트
            success = self.extract_and_update(zip_path)
            
            if success:
                self.print_status("업데이트가 성공적으로 완료되었습니다!")
                self.print_status("백업 파일은 5초 후 자동으로 삭제됩니다...")
                
                # 5초 후 백업 삭제
                import time
                time.sleep(5)
                self.cleanup()
                
                return True
            else:
                self.print_status("업데이트 실패. 백업에서 복원합니다...")
                self.restore_backup()
                return False
                
        except Exception as e:
            self.print_status(f"업데이트 중 오류 발생: {e}")
            self.print_status("백업에서 복원합니다...")
            self.restore_backup()
            return False

def main():
    """메인 함수"""
    try:
        # GUI 업데이트 도구 실행
        gui = UpdateGUI()
        gui.run()
    except Exception as e:
        # 오류 발생 시 메시지 박스로 표시
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("오류", f"업데이트 중 오류가 발생했습니다:\n{str(e)}")
        root.destroy()

if __name__ == "__main__":
    main()
