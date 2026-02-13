# -*- coding: utf-8 -*-
"""
설문 문제 관리 모듈
퀴즈 문제와 정답을 관리합니다.
"""

import json
import os
from pathlib import Path


class SurveyProblemManager:
    """설문 퀴즈 문제와 정답을 관리하는 클래스"""
    
    def __init__(self, quiz_file="survey_quizzes.json"):
        """
        초기화
        
        Args:
            quiz_file: 퀴즈 정보를 저장할 JSON 파일 경로
        """
        self.quiz_file = quiz_file
        self.quiz_answers = {}
        self.load_quizzes()
    
    def load_quizzes(self):
        """퀴즈 정보를 파일에서 로드합니다."""
        try:
            if os.path.exists(self.quiz_file):
                with open(self.quiz_file, 'r', encoding='utf-8') as f:
                    self.quiz_answers = json.load(f)
            else:
                self.quiz_answers = {}
        except Exception as e:
            print(f"퀴즈 로드 실패: {str(e)}")
            self.quiz_answers = {}
    
    def save_quizzes(self):
        """퀴즈 정보를 파일에 저장합니다."""
        try:
            with open(self.quiz_file, 'w', encoding='utf-8') as f:
                json.dump(self.quiz_answers, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"퀴즈 저장 실패: {str(e)}")
            return False
    
    def add_quiz(self, question: str, answer: str, category: str = ""):
        """
        새로운 퀴즈를 추가합니다.
        
        Args:
            question: 문제 텍스트
            answer: 정답 (예: "1", "2", "O", "X" 등)
            category: 카테고리 (예: "제미다파", "글리벤클라마이드" 등)
        
        Returns:
            성공 여부
        """
        if not question or not answer:
            return False
        
        # 문제 제목 정규화 (특수문자 제거)
        normalized_question = self._normalize_question(question)
        
        # 새로운 형식: {문제: {answer: "정답", category: "카테고리"}}
        self.quiz_answers[normalized_question] = {
            "answer": answer,
            "category": category if category else ""
        }
        return self.save_quizzes()
    
    def update_quiz(self, question: str, answer: str):
        """
        기존 퀴즈를 수정합니다.
        
        Args:
            question: 문제 텍스트
            answer: 새로운 정답
        
        Returns:
            성공 여부
        """
        if question not in self.quiz_answers:
            return False
        
        self.quiz_answers[question] = answer
        return self.save_quizzes()
    
    def delete_quiz(self, question: str):
        """
        퀴즈를 삭제합니다.
        
        Args:
            question: 문제 텍스트
        
        Returns:
            성공 여부
        """
        if question not in self.quiz_answers:
            return False
        
        del self.quiz_answers[question]
        return self.save_quizzes()
    
    def get_answer(self, question: str):
        """
        특정 문제의 정답을 가져옵니다.
        저장된 문제가 설문의 문제에 포함되어 있으면 해당 정답을 반환합니다.
        
        Args:
            question: 문제 텍스트 (설문에서 긁어온 전체 문제 + 선택지)
        
        Returns:
            정답 (없으면 None)
        """
        # 문제 제목 정규화 후 조회
        normalized_question = self._normalize_question(question)
        
        # 1. 완전 일치 먼저 시도
        if normalized_question in self.quiz_answers:
            quiz_data = self.quiz_answers[normalized_question]
            # 새로운 형식 처리
            if isinstance(quiz_data, dict):
                return quiz_data.get("answer")
            # 호환성: 구형식 처리
            else:
                return quiz_data
        
        # 2. 부분 일치: 저장된 문제가 추출된 문제에 포함되어 있는지 확인
        for saved_question, quiz_data in self.quiz_answers.items():
            # 저장된 문제(정규화됨)가 추출된 문제에 포함되어 있는지 확인
            if saved_question in normalized_question:
                if isinstance(quiz_data, dict):
                    return quiz_data.get("answer")
                else:
                    return quiz_data
        
        # 3. 역방향 확인: 추출된 문제의 일부가 저장된 문제에 포함되어 있는지
        # (추출된 문제가 너무 길 경우 대비)
        for saved_question, quiz_data in self.quiz_answers.items():
            # 최소 20자 이상 일치하면 부분 일치로 간주
            common_length = len(saved_question)
            if common_length > 20 and saved_question[:20] in normalized_question:
                if isinstance(quiz_data, dict):
                    return quiz_data.get("answer")
                else:
                    return quiz_data
        
        return None
    
    def get_question_details(self, question: str):
        """
        특정 문제의 전체 정보(정답 + 카테고리)를 가져옵니다.
        
        Args:
            question: 문제 텍스트
        
        Returns:
            {"answer": "...", "category": "..."} 딕셔너리 또는 None
        """
        normalized_question = self._normalize_question(question)
        
        # 1. 완전 일치
        if normalized_question in self.quiz_answers:
            quiz_data = self.quiz_answers[normalized_question]
            if isinstance(quiz_data, dict):
                return quiz_data
            else:
                return {"answer": quiz_data, "category": ""}
        
        # 2. 부분 일치
        for saved_question, quiz_data in self.quiz_answers.items():
            if saved_question in normalized_question:
                if isinstance(quiz_data, dict):
                    return quiz_data
                else:
                    return {"answer": quiz_data, "category": ""}
        
        # 3. 역방향 확인
        for saved_question, quiz_data in self.quiz_answers.items():
            common_length = len(saved_question)
            if common_length > 20 and saved_question[:20] in normalized_question:
                if isinstance(quiz_data, dict):
                    return quiz_data
                else:
                    return {"answer": quiz_data, "category": ""}
    
    def _normalize_question(self, question: str) -> str:
        """
        문제 제목을 정규화합니다.
        [퀴즈] 태그와 후행 특수문자(*, ?, 등)를 제거합니다.
        
        Args:
            question: 원본 문제 텍스트
        
        Returns:
            정규화된 문제 텍스트
        """
        import re
        
        # [퀴즈] 태그 제거
        cleaned = question.replace("[퀴즈]", "").strip()
        
        # 후행 특수문자 제거 (*, ?, 숫자 옆의 특수문자 등)
        # 문제 끝의 *, ?, 공백 제거
        cleaned = re.sub(r'[\*\?]+\s*$', '', cleaned).strip()
        
        # 여러 개의 공백을 단일 공백으로 정규화
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    def get_all_quizzes(self):
        """
        모든 퀴즈를 가져옵니다.
        
        Returns:
            {문제: 정답} 딕셔너리
        """
        return self.quiz_answers.copy()
    
    def has_quiz(self, question: str):
        """
        해당 문제가 존재하는지 확인합니다.
        
        Args:
            question: 문제 텍스트
        
        Returns:
            존재 여부
        """
        return question in self.quiz_answers
    
    def clear_all(self):
        """모든 퀴즈를 삭제합니다."""
        self.quiz_answers = {}
        return self.save_quizzes()


# GUI를 위한 팝업 창
def open_survey_problem_manager(parent_window, gui_logger=None):
    """
    설문 문제 관리 팝업 창을 엽니다.
    
    Args:
        parent_window: 부모 창 (tkinter.Tk)
        gui_logger: 로깅 함수
    """
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    problem_manager = SurveyProblemManager()
    
    # 팝업 창 생성
    popup = tk.Toplevel(parent_window)
    popup.title("📝 설문 문제 관리")
    popup.geometry("900x600")
    popup.minsize(800, 500)
    popup.grab_set()
    
    # 제목
    title_label = tk.Label(
        popup,
        text="🎯 설문 퀴즈 문제 답안 관리",
        font=("맑은 고딕", 14, "bold"),
        bg='#f0f0f0',
        fg='#2c3e50'
    )
    title_label.pack(pady=(10, 5), padx=10)
    
    # 설명
    desc_label = tk.Label(
        popup,
        text="[퀴즈] 표시가 있는 문제의 답을 입력하세요. (예: 1, 2, O, X 등)",
        font=("맑은 고딕", 10),
        bg='#f0f0f0',
        fg='#7f8c8d'
    )
    desc_label.pack(padx=10)
    
    # 입력 영역 프레임
    input_frame = tk.Frame(popup, bg='#ffffff', relief='solid', borderwidth=1)
    input_frame.pack(fill='x', padx=10, pady=10)
    
    # 문제 입력
    tk.Label(input_frame, text="문제:", font=("맑은 고딕", 10), bg='#ffffff').pack(anchor='w', padx=10, pady=(10, 2))
    
    question_entry = tk.Text(
        input_frame,
        height=3,
        width=80,
        font=("맑은 고딕", 10),
        wrap='word'
    )
    question_entry.pack(padx=10, pady=(0, 10), fill='x', expand=True)
    
    # 정답 입력
    tk.Label(input_frame, text="정답:", font=("맑은 고딕", 10), bg='#ffffff').pack(anchor='w', padx=10, pady=(0, 2))
    
    answer_entry = tk.Entry(
        input_frame,
        font=("맑은 고딕", 10),
        width=40
    )
    answer_entry.pack(anchor='w', padx=10, pady=(0, 10))
    
    # 카테고리 입력
    tk.Label(input_frame, text="카테고리 (예: 제미다파, 글리벤클라마이드):", font=("맑은 고딕", 10), bg='#ffffff').pack(anchor='w', padx=10, pady=(0, 2))
    
    category_entry = tk.Entry(
        input_frame,
        font=("맑은 고딕", 10),
        width=40
    )
    category_entry.pack(anchor='w', padx=10, pady=(0, 10))
    
    # 버튼 프레임
    button_frame = tk.Frame(input_frame, bg='#ffffff')
    button_frame.pack(fill='x', padx=10, pady=(0, 10))
    
    # 수정 모드를 추적하는 변수
    edit_mode = {"active": False, "original_question": ""}
    
    def clear_inputs():
        """입력 필드를 초기화합니다."""
        question_entry.delete("1.0", "end")
        answer_entry.delete(0, "end")
        category_entry.delete(0, "end")
        edit_mode["active"] = False
        edit_mode["original_question"] = ""
        update_button_states()
    
    def add_or_update_quiz():
        """새 문제를 추가하거나 기존 문제를 수정합니다."""
        question = question_entry.get("1.0", "end").strip()
        answer = answer_entry.get().strip()
        category = category_entry.get().strip()
        
        if not question or not answer:
            messagebox.showwarning("경고", "문제와 정답을 모두 입력하세요.")
            return
        
        if edit_mode["active"]:
            # 수정 모드
            old_question = edit_mode["original_question"]
            problem_manager.delete_quiz(old_question)
            problem_manager.add_quiz(question, answer, category)
            messagebox.showinfo("성공", "문제가 수정되었습니다.")
            if gui_logger:
                category_str = f" [{category}]" if category else ""
                gui_logger(f"✏️ 퀴즈 수정: {question[:30]}...{category_str} → {answer}")
        else:
            # 추가 모드
            if problem_manager.add_quiz(question, answer, category):
                messagebox.showinfo("성공", "문제가 추가되었습니다.")
                if gui_logger:
                    category_str = f" [{category}]" if category else ""
                    gui_logger(f"✅ 퀴즈 추가: {question[:30]}...{category_str} → {answer}")
            else:
                messagebox.showerror("오류", "문제 추가에 실패했습니다.")
                return
        
        clear_inputs()
        refresh_list()
    
    # 추가/수정 버튼 (동적으로 텍스트 변경)
    action_button = tk.Button(
        button_frame,
        text="➕ 추가",
        font=("맑은 고딕", 10, "bold"),
        bg='#27ae60',
        fg='white',
        command=add_or_update_quiz,
        padx=20
    )
    action_button.pack(side='left', padx=(0, 5))
    
    # 취소 버튼 (수정 중에만 보임)
    cancel_button = tk.Button(
        button_frame,
        text="✖️ 취소",
        font=("맑은 고딕", 10, "bold"),
        bg='#95a5a6',
        fg='white',
        command=clear_inputs,
        padx=20
    )
    cancel_button.pack(side='left', padx=5)
    cancel_button.pack_forget()  # 처음엔 숨김
    
    # 리스트 영역 프레임
    list_frame = tk.Frame(popup, bg='#ffffff', relief='solid', borderwidth=1)
    list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    # 리스트 제목
    list_title = tk.Label(
        list_frame,
        text="📋 등록된 문제 목록 (수정하려면 선택)",
        font=("맑은 고딕", 11, "bold"),
        bg='#ffffff',
        fg='#2c3e50'
    )
    list_title.pack(anchor='w', padx=10, pady=(10, 5))
    
    # 스크롤바와 트리뷰
    tree_frame = tk.Frame(list_frame, bg='#ffffff')
    tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    scrollbar = ttk.Scrollbar(tree_frame)
    scrollbar.pack(side='right', fill='y')
    
    tree = ttk.Treeview(
        tree_frame,
        columns=('category', 'question', 'answer'),
        height=12,
        yscrollcommand=scrollbar.set
    )
    scrollbar.config(command=tree.yview)
    
    tree.column('#0', width=0, stretch='no')
    tree.column('category', anchor='center', width=100)
    tree.column('question', anchor='w', width=600)
    tree.column('answer', anchor='center', width=80)
    
    tree.heading('#0', text='', anchor='w')
    tree.heading('category', text='카테고리', anchor='center')
    tree.heading('question', text='문제', anchor='w')
    tree.heading('answer', text='정답', anchor='center')
    
    tree.pack(fill='both', expand=True)
    
    def on_tree_select(event):
        """리스트에서 항목을 선택했을 때 입력 필드에 채웁니다."""
        selected = tree.selection()
        if not selected:
            return
        
        # 선택된 항목의 데이터 가져오기
        item = selected[0]
        item_data = tree.item(item)
        category = item_data['values'][0]
        question_display = item_data['values'][1]
        answer = item_data['values'][2]
        
        # 전체 문제 목록에서 원본 문제 찾기
        for original_question, quiz_data in problem_manager.get_all_quizzes().items():
            # 새로운 형식과 구형식 모두 지원
            if isinstance(quiz_data, dict):
                original_answer = quiz_data.get("answer", "")
                original_category = quiz_data.get("category", "")
            else:
                original_answer = quiz_data
                original_category = ""
            
            if original_question[:60] + ("..." if len(original_question) > 60 else "") == question_display or original_question == question_display:
                # 입력 필드에 채우기
                question_entry.delete("1.0", "end")
                question_entry.insert("1.0", original_question)
                answer_entry.delete(0, "end")
                answer_entry.insert(0, original_answer)
                category_entry.delete(0, "end")
                category_entry.insert(0, original_category)
                
                # 수정 모드 활성화
                edit_mode["active"] = True
                edit_mode["original_question"] = original_question
                
                update_button_states()
                break
    
    def update_button_states():
        """버튼 상태를 업데이트합니다."""
        if edit_mode["active"]:
            action_button.config(text="📝 수정", bg='#3498db')
            cancel_button.pack(side='left', padx=5)
        else:
            action_button.config(text="➕ 추가", bg='#27ae60')
            cancel_button.pack_forget()
    
    # 리스트 선택 이벤트 연결
    tree.bind('<<TreeviewSelect>>', on_tree_select)
    
    def refresh_list():
        """목록을 새로고침합니다."""
        for item in tree.get_children():
            tree.delete(item)
        
        for idx, (question, quiz_data) in enumerate(problem_manager.get_all_quizzes().items()):
            # 문제는 최대 60글자까지만 표시 (카테고리 컬럼 추가로 너비 조정)
            display_question = question[:60] + "..." if len(question) > 60 else question
            
            # 새로운 형식과 구형식 모두 지원
            if isinstance(quiz_data, dict):
                answer = quiz_data.get("answer", "")
                category = quiz_data.get("category", "")
            else:
                answer = quiz_data
                category = ""
            
            tree.insert('', 'end', text=str(idx+1), values=(category, display_question, answer))
    
    def delete_selected():
        """선택된 문제를 삭제합니다."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("경고", "삭제할 문제를 선택하세요.")
            return
        
        # 선택된 항목의 인덱스 구하기
        item = selected[0]
        question_display = tree.item(item)['values'][1]  # 인덱스 1로 수정 (0은 카테고리)
        
        # 전체 문제에서 매칭되는 문제 찾기
        for question, quiz_data in problem_manager.get_all_quizzes().items():
            if question[:60] + ("..." if len(question) > 60 else "") == question_display or question == question_display:
                if messagebox.askyesno("확인", f"다음 문제를 삭제하시겠습니까?\n{question[:50]}..."):
                    if problem_manager.delete_quiz(question):
                        messagebox.showinfo("성공", "문제가 삭제되었습니다.")
                        clear_inputs()  # 입력 필드 초기화
                        refresh_list()
                        if gui_logger:
                            gui_logger(f"🗑️ 퀴즈 삭제: {question[:30]}...")
                    else:
                        messagebox.showerror("오류", "문제 삭제에 실패했습니다.")
                break
    
    delete_button = tk.Button(
        button_frame,
        text="🗑️ 삭제",
        font=("맑은 고딕", 10, "bold"),
        bg='#e74c3c',
        fg='white',
        command=delete_selected,
        padx=20
    )
    delete_button.pack(side='left', padx=5)
    
    def clear_all():
        """모든 문제를 삭제합니다."""
        if messagebox.askyesno("확인", "정말로 모든 문제를 삭제하시겠습니까?\n(되돌릴 수 없습니다)"):
            if problem_manager.clear_all():
                messagebox.showinfo("성공", "모든 문제가 삭제되었습니다.")
                clear_inputs()  # 입력 필드 초기화
                refresh_list()
                if gui_logger:
                    gui_logger("🗑️ 모든 퀴즈 삭제됨")
            else:
                messagebox.showerror("오류", "삭제에 실패했습니다.")
    
    clear_button = tk.Button(
        button_frame,
        text="🗑️ 전체 삭제",
        font=("맑은 고딕", 10, "bold"),
        bg='#95a5a6',
        fg='white',
        command=clear_all,
        padx=20
    )
    clear_button.pack(side='left', padx=5)
    
    # 하단 버튼
    bottom_frame = tk.Frame(popup, bg='#f0f0f0')
    bottom_frame.pack(fill='x', padx=10, pady=(0, 10))
    
    close_button = tk.Button(
        bottom_frame,
        text="닫기",
        font=("맑은 고딕", 10, "bold"),
        bg='#3498db',
        fg='white',
        command=popup.destroy,
        padx=30
    )
    close_button.pack(side='right')
    
    # 초기 목록 로드
    refresh_list()


if __name__ == "__main__":
    # 테스트 코드
    manager = SurveyProblemManager()
    
    # 샘플 데이터 추가
    manager.add_quiz("DPP-4와 SGLT-2i 병용의 이점은?", "3")
    manager.add_quiz("바이트 프로틴 관련 문제", "O")
    
    # 목록 출력
    print("저장된 퀴즈:")
    for question, answer in manager.get_all_quizzes().items():
        print(f"Q: {question} → A: {answer}")
