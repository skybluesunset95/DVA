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
def open_survey_problem_manager(parent_window, gui_logger=None, initial_question=None, initial_category=None):
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
    
    # 초기값 설정
    if initial_question:
        question_entry.insert("1.0", initial_question)
    if initial_category:
        category_entry.insert(0, initial_category)
    
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
                if not initial_question:
                    messagebox.showinfo("성공", "문제가 추가되었습니다.")
                if gui_logger:
                    category_str = f" [{category}]" if category else ""
                    gui_logger(f"✅ 퀴즈 추가: {question[:30]}...{category_str} → {answer}")
                
                # 자동으로 열린 창이면 추가 후 파기하고 리턴
                if initial_question:
                    popup.destroy()
                    return
            else:
                messagebox.showerror("오류", "문제 추가에 실패했습니다.")
                return
        
        selection = cat_listbox.curselection()
        current_cat = cat_listbox.get(selection[0]) if selection else "전체"
        clear_inputs()
        refresh_list(current_cat)
    
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
    
    # 리스트 영역 상위 프레임 (사이드바 + 리스트)
    content_frame = tk.Frame(popup, bg='#f0f0f0')
    content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

    # 카테고리 사이드바
    sidebar = tk.Frame(content_frame, width=150, bg='#ffffff', relief='solid', borderwidth=1)
    sidebar.pack(side='left', fill='y', padx=(0, 5))
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="📁 카테고리", font=("맑은 고딕", 10, "bold"), bg='#ffffff').pack(pady=(10, 5))
    
    cat_listbox = tk.Listbox(sidebar, font=("맑은 고딕", 10), bd=0, highlightthickness=0, selectmode='single', bg='#ffffff')
    cat_listbox.pack(fill='both', expand=True, padx=5, pady=5)
    
    # 리스트 영역 프레임
    list_frame = tk.Frame(content_frame, bg='#ffffff', relief='solid', borderwidth=1)
    list_frame.pack(side='left', fill='both', expand=True)
    
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
    
    # original_q를 보이지 않는 컬럼으로 추가 (순서 조절 및 원본 데이터 유지용)
    tree = ttk.Treeview(
        tree_frame,
        columns=('category', 'question', 'answer', 'original_q'),
        displaycolumns=('category', 'question', 'answer'),
        height=12,
        yscrollcommand=scrollbar.set
    )
    scrollbar.config(command=tree.yview)
    
    tree.column('#0', width=0, stretch='no')
    tree.column('category', anchor='center', width=100)
    tree.column('question', anchor='w', width=500)
    tree.column('answer', anchor='center', width=80)
    tree.column('original_q', width=0, stretch='no')
    
    tree.heading('#0', text='', anchor='w')
    tree.heading('category', text='카테고리', anchor='center')
    tree.heading('question', text='문제 (순서 조절: 드래그)', anchor='w')
    tree.heading('answer', text='정답', anchor='center')
    
    tree.pack(fill='both', expand=True)

    def on_category_select(event):
        selection = cat_listbox.curselection()
        if selection:
            cat = cat_listbox.get(selection[0])
            refresh_list(cat)

    cat_listbox.bind('<<ListboxSelect>>', on_category_select)
    
    def on_tree_select(event):
        """리스트에서 항목을 선택했을 때 입력 필드에 채웁니다."""
        selected = tree.selection()
        if not selected:
            return
        
        # 선택된 항목의 데이터 가져오기 (인덱스 3에 원본 문제 저장됨)
        item = selected[0]
        item_data = tree.item(item)
        original_question = item_data['values'][3]
        
        # 전체 문제 목록에서 데이터 가져오기
        quiz_data = problem_manager.get_all_quizzes().get(original_question)
        if quiz_data:
            if isinstance(quiz_data, dict):
                answer = quiz_data.get("answer", "")
                category = quiz_data.get("category", "")
            else:
                answer = quiz_data
                category = ""
            
            # 입력 필드에 채우기
            question_entry.delete("1.0", "end")
            question_entry.insert("1.0", original_question)
            answer_entry.delete(0, "end")
            answer_entry.insert(0, answer)
            category_entry.delete(0, "end")
            category_entry.insert(0, category)
            
            # 수정 모드 활성화
            edit_mode["active"] = True
            edit_mode["original_question"] = original_question
            
            update_button_states()
    
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
    
    def refresh_categories():
        """카테고리 목록을 바에서 새로고침합니다."""
        current_selection = cat_listbox.curselection()
        selected_cat = cat_listbox.get(current_selection[0]) if current_selection else "전체"
        
        cat_listbox.delete(0, "end")
        cat_listbox.insert("end", "전체")
        
        # 유니크 카테고리 추출
        categories = set()
        for quiz_data in problem_manager.get_all_quizzes().values():
            if isinstance(quiz_data, dict):
                cat = quiz_data.get("category", "")
                if cat:
                    categories.add(cat)
        
        for cat in sorted(list(categories)):
            cat_listbox.insert("end", cat)
            
        # 기존 선택 유지
        idx = 0
        for i in range(cat_listbox.size()):
            if cat_listbox.get(i) == selected_cat:
                idx = i
                break
        cat_listbox.select_set(idx)
        cat_listbox.see(idx)

    def refresh_list(selected_category="전체"):
        """목록을 새로고침합니다."""
        for item in tree.get_children():
            tree.delete(item)
        
        quizzes = problem_manager.get_all_quizzes()
        for idx, (question, quiz_data) in enumerate(quizzes.items()):
            # 새로운 형식과 구형식 모두 지원
            if isinstance(quiz_data, dict):
                answer = quiz_data.get("answer", "")
                category = quiz_data.get("category", "")
            else:
                answer = quiz_data
                category = ""
            
            # 카테고리 필터링
            if selected_category != "전체" and category != selected_category:
                continue
            
            # 표시는 요약본, 실제 데이터는 original_q 컬럼에 유지
            display_question = question[:100] + "..." if len(question) > 100 else question
            tree.insert('', 'end', values=(category, display_question, answer, question))
        
        refresh_categories()
    
    def save_order():
        """트리뷰의 현재 순서대로 json 파일을 다시 저장합니다."""
        # 전체 보기일 때만 순서 조절 가능 (다른 카테고리가 섞여있으면 보존이 어려움)
        selection = cat_listbox.curselection()
        if selection and cat_listbox.get(selection[0]) != "전체":
            return
            
        new_answers = {}
        all_quizzes = problem_manager.get_all_quizzes()
        
        for item in tree.get_children():
            original_q = tree.item(item)['values'][3]
            if original_q in all_quizzes:
                new_answers[original_q] = all_quizzes[original_q]
        
        # 순서가 보장되는 딕셔너리로 교체 후 저장
        problem_manager.quiz_answers = new_answers
        problem_manager.save_quizzes()
        if gui_logger:
            gui_logger("↔️ 문제 순서가 변경되어 저장되었습니다.")

    # 드래그 앤 드롭 구현
    def on_drag_start(event):
        item = tree.identify_row(event.y)
        if item:
            tree.drag_item = item

    def on_drag_stop(event):
        target_item = tree.identify_row(event.y)
        source_item = getattr(tree, 'drag_item', None)
        
        if source_item and target_item and source_item != target_item:
            # 타겟 위치 확인 (위에 놓는지 아래에 놓는지)
            target_idx = tree.index(target_item)
            tree.move(source_item, '', target_idx)
            save_order()
        
        tree.drag_item = None

    # 전체 보기일 때만 드래그 앤 드롭 바인딩
    tree.bind("<Button-1>", on_drag_start, add="+")
    tree.bind("<ButtonRelease-1>", on_drag_stop, add="+")
    
    def delete_selected():
        """선택된 문제를 삭제합니다."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("경고", "삭제할 문제를 선택하세요.")
            return
        
        item = selected[0]
        original_question = tree.item(item)['values'][3]
        
        if messagebox.askyesno("확인", f"다음 문제를 삭제하시겠습니까?\n{original_question[:50]}..."):
            if problem_manager.delete_quiz(original_question):
                messagebox.showinfo("성공", "문제가 삭제되었습니다.")
                selection = cat_listbox.curselection()
                current_cat = cat_listbox.get(selection[0]) if selection else "전체"
                clear_inputs()  # 입력 필드 초기화
                refresh_list(current_cat)
                if gui_logger:
                    gui_logger(f"🗑️ 퀴즈 삭제: {original_question[:30]}...")
            else:
                messagebox.showerror("오류", "문제 삭제에 실패했습니다.")
    
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
