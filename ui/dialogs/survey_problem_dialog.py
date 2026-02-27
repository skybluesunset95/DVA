# -*- coding: utf-8 -*-
"""
설문 문제 관리 팝업 대화상자
"""
import tkinter as tk
from modules.survey_problem import SurveyProblemManager

def open_survey_problem_manager(parent_window, gui_logger=None, initial_question=None, initial_category=None):
    """
    설문 문제 관리 팝업 창을 엽니다.
    (이전 modules.survey_problem에서 이전됨)
    """
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
    
    def refresh_categories():
        """카테고리 목록을 바에서 새로고침합니다."""
        current_selection = cat_listbox.curselection()
        selected_cat = cat_listbox.get(current_selection[0]) if current_selection else "전체"
        
        cat_listbox.delete(0, "end")
        cat_listbox.insert("end", "전체")
        
        categories = set()
        for quiz_data in problem_manager.get_all_quizzes().values():
            if isinstance(quiz_data, dict):
                cat = quiz_data.get("category", "")
                if cat:
                    categories.add(cat)
        
        for cat in sorted(list(categories)):
            cat_listbox.insert("end", cat)
            
        idx = 0
        for i in range(cat_listbox.size()):
            if cat_listbox.get(i) == selected_cat:
                idx = i
                break
        cat_listbox.select_set(idx)

    def refresh_list(selected_category="전체"):
        """목록을 새로고침합니다."""
        for item in tree.get_children():
            tree.delete(item)
        
        quizzes = problem_manager.get_all_quizzes()
        for idx, (question, quiz_data) in enumerate(quizzes.items()):
            if isinstance(quiz_data, dict):
                answer = quiz_data.get("answer", "")
                category = quiz_data.get("category", "")
            else:
                answer = quiz_data
                category = ""
            
            if selected_category != "전체" and category != selected_category:
                continue
            
            display_question = question[:100] + "..." if len(question) > 100 else question
            tree.insert('', 'end', values=(category, display_question, answer, question))
        
        refresh_categories()

    def update_button_states():
        if edit_mode["active"]:
            action_button.config(text="📝 수정", bg='#3498db')
            cancel_button.pack(side='left', padx=5)
        else:
            action_button.config(text="➕ 추가", bg='#27ae60')
            cancel_button.pack_forget()

    def on_tree_select(event):
        selected = tree.selection()
        if not selected:
            return
        
        item = selected[0]
        item_data = tree.item(item)
        original_question = item_data['values'][3]
        
        quiz_data = problem_manager.get_all_quizzes().get(original_question)
        if quiz_data:
            if isinstance(quiz_data, dict):
                answer = quiz_data.get("answer", "")
                category = quiz_data.get("category", "")
            else:
                answer = quiz_data
                category = ""
            
            question_entry.delete("1.0", "end")
            question_entry.insert("1.0", original_question)
            answer_entry.delete(0, "end")
            answer_entry.insert(0, answer)
            category_entry.delete(0, "end")
            category_entry.insert(0, category)
            
            edit_mode["active"] = True
            edit_mode["original_question"] = original_question
            update_button_states()

    tree.bind('<<TreeviewSelect>>', on_tree_select)
    cat_listbox.bind('<<ListboxSelect>>', lambda e: refresh_list(cat_listbox.get(cat_listbox.curselection()[0]) if cat_listbox.curselection() else "전체"))

    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("경고", "삭제할 문제를 선택하세요.")
            return
        
        item = selected[0]
        original_question = tree.item(item)['values'][3]
        
        if messagebox.askyesno("확인", f"다음 문제를 삭제하시겠습니까?\n{original_question[:50]}..."):
            if problem_manager.delete_quiz(original_question):
                refresh_list()
                clear_inputs()

    delete_button = tk.Button(button_frame, text="🗑️ 삭제", bg='#e74c3c', fg='white', command=delete_selected, padx=20)
    delete_button.pack(side='left', padx=5)

    close_button = tk.Button(popup, text="닫기", bg='#3498db', fg='white', command=popup.destroy, padx=30)
    close_button.pack(pady=10)

    refresh_list()
