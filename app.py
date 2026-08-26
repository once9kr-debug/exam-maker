import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import time
import PyPDF2
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import concurrent.futures

# ==========================================
# 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="SDH ACADEMY 통합 출제 플랫폼", layout="wide")

st.markdown("""
<style>
    .group-header { font-weight: 700; font-size: 1.1rem; color: #2C3E50; border-bottom: 2px solid #3498DB; padding-bottom: 8px; margin-top: 20px; margin-bottom: 15px; }
    div[data-testid="stCheckbox"] label span { font-size: 0.95rem; }
    .status-box { background-color: #E8F8F5; border-left: 5px solid #1ABC9C; padding: 15px; margin: 10px 0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 워드(.docx) 파일 생성 엔진
# ==========================================
def create_word_file(problems_list, header_title):
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.5); section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.6); section.right_margin = Inches(0.6)

    title = doc.add_heading(header_title, level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for idx, data in enumerate(problems_list):
        q_title_text = data.get('question', '문제 누락').split('.', 1)[-1].strip() if '.' in data.get('question', '') else data.get('question', '')
        q_title = f"{idx+1}. {q_title_text}"
        p_q = doc.add_paragraph()
        p_q.add_run(q_title).bold = True

        passage_raw = data.get("passage", "").replace("<br/>", "\n").replace("<br>", "\n")
        
        if "[박스]" in passage_raw and "[/박스]" in passage_raw:
            try:
                inserted_box = passage_raw.split("[박스]")[1].split("[/박스]")[0]
                main_passage = passage_raw.split("[/박스]")[1].strip()
                p_box = doc.add_paragraph()
                p_box.add_run(f"[{inserted_box}]").italic = True
                p_box.paragraph_format.left_indent = Inches(0.2)
                p_box.paragraph_format.right_indent = Inches(0.2)
                doc.add_paragraph(main_passage)
            except: doc.add_paragraph(passage_raw)
        else: doc.add_paragraph(passage_raw)

        options = data.get("options", [])
        if options: doc.add_paragraph("  ".join(options))
        doc.add_paragraph("")

    doc.add_page_break()
    doc.add_heading("정답 및 해설", level=1)
    for idx, data in enumerate(problems_list):
        p_ans = doc.add_paragraph()
        p_ans.add_run(f"{idx+1}번 - {data.get('answer', '')}").bold = True
        doc.add_paragraph(f"[해설] {data.get('explanation', '')}")
        doc.add_paragraph("")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 💥 파이썬 1차 기계적 필터링 규칙 (15종 유형 반영)
# ==========================================
def rule_based_check(task_type, prob_data):
    required_keys = ["question", "passage", "options", "answer", "explanation"]
    if not all(k in prob_data for k in required_keys): return False, "JSON 결함"
    passage = prob_data.get("passage", "")
    if task_type in ["어법", "어휘", "흐름(과 무관한 문장)"] and "①" not in passage: return False, "지문 내 원문자(①) 누락"
    if task_type == "삽입" and "[박스]" not in passage: return False, "주어진 문장 [박스] 누락"
    if task_type == "순서" and len(prob_data.get("options", [])) < 3: return False, "순서 배열 선택지 부족"
    return True, "통과"

# ==========================================
# 💥 초고속 청크 생성 (15종 유형 프롬프트 반영)
# ==========================================
def process_chunk(chunk, exam_key, passage_db, model):
    prompt = "당신은 고등학교 내신 영어 출제 전문가입니다. 다음 [출제 목록]에 맞게 출제하세요.\n\n"
    for idx, task in enumerate(chunk):
        passage_text = passage_db[exam_key][task['q_num']]
        prompt += f"요청 {idx+1}. 지문: {task['q_num']}, 유형: {task['q_type']}\n원문: {passage_text}\n\n"
    
    prompt += """[💥 출력 규칙 및 자가 검수 💥]
1. 오직 순수 JSON 배열만 출력하세요. (마크다운 ```json 금지)
2. 키: "question", "passage", "options", "answer", "explanation" 포함.
3. 순서 문제: options에 ['① (A)-(C)-(B)', ...] 포함.
4. 어법/어휘/흐름 문제: 지문(passage) 안에 밑줄이나 번호(①, ②)가 이미 포함된 경우, options는 반드시 빈 리스트 [] 반환.
5. 서술형 문제: <조건> 텍스트는 passage 맨 밑에 추가.
6. 삽입 문제: 맨 앞에 [박스]주어진문장[/박스] 표기.
[필수] 답변을 출력하기 직전, 위 6가지 규칙을 모두 완벽하게 지켰는지 스스로 검증한 후 결과물만 반환하세요."""

    for attempt in range(2): 
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            probs = json.loads(raw_text)
            
            valid_probs = []
            for idx, prob in enumerate(probs):
                if idx < len(chunk):
                    is_ok, msg = rule_based_check(chunk[idx]['q_type'], prob)
                    if not is_ok: raise ValueError(msg)
                    valid_probs.append(prob)
            return chunk, valid_probs, True
        except Exception as e:
            time.sleep(1.5)
            
    failed_probs = [{"question": "[⚠️검수 실패] 수동 확인 요망", "passage": "생성 오류", "options": [], "answer": "1", "explanation": "재시도 요망"} for _ in chunk]
    return chunk, failed_probs, False

# ==========================================
# DB 및 세션 관리
# ==========================================
DB_FILE = "sdh_passages_db.json"
CACHE_FILE = "sdh_problems_cache_db.json"

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

if 'passage_db' not in st.session_state: st.session_state.passage_db = load_json(DB_FILE)
if 'problem_cache' not in st.session_state: st.session_state.problem_cache = load_json(CACHE_FILE)
if 'exam_queue' not in st.session_state: st.session_state.exam_queue = []
if 'generated_files' not in st.session_state: st.session_state.generated_files = []
if 'part_counter' not in st.session_state: st.session_state.part_counter = 1
if 'total_tasks' not in st.session_state: st.session_state.total_tasks = 0

# 💥 15종 전체 선택 콜백 업데이트
def toggle_all_types():
    keys = ["t_purpose", "t_mood", "t_claim", "t_main_idea", "t_topic", "t_title", "t_match", 
            "t_grammar", "t_vocab", "t_blank", "t_flow", "t_order", "t_insert", "t_summary", "t_essay"]
    for k in keys: st.session_state[k] = st.session_state.type_all

def toggle_all_q():
    for i in range(18, 46): st.session_state[f"q_{i}"] = st.session_state.q_all

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다.")
    st.stop()

# ==========================================
# 💥 좌측 사이드바 (메뉴 및 전역 설정)
# ==========================================
st.sidebar.markdown("### ⚙️ 출제 기본 설정")
exam_type = st.sidebar.selectbox("교재 선택", ["고등 모의고사", "고등 교과서"])
exam_year = st.sidebar.selectbox("연도", ["2026년", "2025년", "2024년"])
exam_month = st.sidebar.selectbox("시행 월", ["3월", "6월", "9월", "11월"])
exam_grade = st.sidebar.selectbox("학년", ["고1", "고2", "고3"])

exam_key = f"{exam_year}_{exam_month}_{exam_grade}"
if exam_key not in st.session_state.passage_db: st.session_state.passage_db[exam_key] = {}

st.sidebar.markdown("---")
menu = st.sidebar.radio("📌 메뉴 이동", ["🔍 모의고사 검색", "🎯 변형문제 제작", "🗂️ 지문 DB 관리"])

st.title("SDH ACADEMY 통합 출제 플랫폼 🛠️")
st.markdown("---")

# ==========================================
# 메인 화면 로직 분기
# ==========================================

# ------------------------------------------
# 메뉴 1: 모의고사 검색
# ------------------------------------------
if menu == "🔍 모의고사 검색":
    st.markdown("<div class='group-header'>📚 모의고사 DB 검색</div>", unsafe_allow_html=True)
    st.caption("현재 설정된 조건에 맞는 모의고사 목록입니다.")
    
    db_data = {
        "연도": ["2026", "2026", "2026", "2025", "2025"],
        "월": ["6월", "6월", "6월", "11월", "11월"],
        "주관": ["2026년 6월", "2026년 6월", "2026년 6월", "2025년 11월", "2025년 11월"],
        "학년": ["1학년", "2학년", "3학년", "1학년", "2학년"],
        "지문수": [28, 28, 28, 28, 28]
    }
    st.dataframe(pd.DataFrame(db_data), use_container_width=True, hide_index=True)

# ------------------------------------------
# 메뉴 2: 변형문제 제작 (15종 유형 플랫 전개)
# ------------------------------------------
elif menu == "🎯 변형문제 제작":
    st.markdown(f"##### 📝 출제 대상: **{exam_year} {exam_month}, {exam_grade} 모의고사**")
    
    st.markdown("<div class='group-header'>📌 1. 출제할 세부 유형 선택</div>", unsafe_allow_html=True)
    st.checkbox("✅ 전체 유형 선택", key="type_all", on_change=toggle_all_types)
    st.write("") # 간격 띄우기
    
    # 💥 그룹 해제 및 15종 수평 나열
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        t_purpose = st.checkbox("목적", key="t_purpose")
        t_mood = st.checkbox("심경/분위기", key="t_mood")
        t_claim = st.checkbox("주장", key="t_claim")
    with col2:
        t_main_idea = st.checkbox("요지", key="t_main_idea")
        t_topic = st.checkbox("주제", key="t_topic")
        t_title = st.checkbox("제목", key="t_title")
    with col3:
        t_match = st.checkbox("일치/불일치", key="t_match")
        t_grammar = st.checkbox("어법", key="t_grammar")
        t_vocab = st.checkbox("어휘", key="t_vocab")
    with col4:
        t_blank = st.checkbox("빈칸", key="t_blank")
        t_flow = st.checkbox("흐름(무관한 문장)", key="t_flow")
        t_order = st.checkbox("순서", key="t_order")
    with col5:
        t_insert = st.checkbox("삽입", key="t_insert")
        t_summary = st.checkbox("요약", key="t_summary")
        t_essay = st.checkbox("서술형", key="t_essay")

    st.markdown("---")
    st.markdown("<div class='group-header'>📖 2. 모의고사 지문(번호) 선택</div>", unsafe_allow_html=True)
    st.checkbox("✅ 전체 지문 선택", key="q_all", on_change=toggle_all_q)
    
    q_cols = st.columns(10)
    for i, q_num in enumerate(range(18, 46)):
        with q_cols[i % 10]: st.checkbox(f"{q_num}번", key=f"q_{q_num}")

    st.markdown("---")
    st.markdown("<div class='group-header'>⚙️ 3. 분할 출제 설정 및 대기열 생성</div>", unsafe_allow_html=True)
    split_size = st.number_input("파일 1개당 출제할 문제 수 (기본: 150)", min_value=10, max_value=500, value=150, step=10)
    
    if st.button("🛒 1단계: 출제 대기열(Queue) 생성하기", type="secondary", use_container_width=True):
        selected_q_nums = [f"{num}번" for num in range(18, 46) if st.session_state.get(f"q_{num}")]
        
        # 💥 15종 리스트 매핑
        selected_types_list = []
        if t_purpose: selected_types_list.append("목적")
        if t_mood: selected_types_list.append("심경/분위기")
        if t_claim: selected_types_list.append("주장")
        if t_main_idea: selected_types_list.append("요지")
        if t_topic: selected_types_list.append("주제")
        if t_title: selected_types_list.append("제목")
        if t_match: selected_types_list.append("일치/불일치")
        if t_grammar: selected_types_list.append("어법")
        if t_vocab: selected_types_list.append("어휘")
        if t_blank: selected_types_list.append("빈칸")
        if t_flow: selected_types_list.append("흐름(과 무관한 문장)")
        if t_order: selected_types_list.append("순서")
        if t_insert: selected_types_list.append("삽입")
        if t_summary: selected_types_list.append("요약")
        if t_essay: selected_types_list.append("서술형")

        if not selected_types_list or not selected_q_nums:
            st.warning("유형과 지문을 최소 1개 이상 선택해주세요.")
        else:
            current_db = st.session_state.passage_db.get(exam_key, {})
            missing_passages = [q for q in selected_q_nums if q not in current_db or current_db[q].strip() == ""]
            
            if missing_passages:
                st.error(f"🚨 다음 지문이 DB에 없습니다: {', '.join(missing_passages)}\n['지문 DB 관리'] 탭에서 먼저 저장해주세요.")
            else:
                new_queue = [{"q_num": q, "q_type": t} for q in selected_q_nums for t in selected_types_list]
                st.session_state.exam_queue = new_queue
                st.session_state.total_tasks = len(new_queue)
                st.session_state.generated_files = [] 
                st.session_state.part_counter = 1
                st.rerun()

    if st.session_state.total_tasks > 0:
        remain_tasks = len(st.session_state.exam_queue)
        st.markdown(f"<div class='status-box'><b>📊 현재 출제 현황:</b> 총 {st.session_state.total_tasks}문제 중 <b>{remain_tasks}문제 남음</b></div>", unsafe_allow_html=True)
        
        if st.session_state.generated_files:
            st.markdown("### 📥 완성된 시험지 다운로드")
            for file_info in st.session_state.generated_files:
                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    st.download_button(
                        label=f"🌐 Part {file_info['part']} 인쇄용 HTML 다운로드", data=file_info['html'], 
                        file_name=f"SDH_Premium_Part_{file_info['part']}.html", mime="text/html",
                        key=f"dl_html_{file_info['part']}", use_container_width=True
                    )
                with dl_col2:
                    st.download_button(
                        label=f"📝 Part {file_info['part']} 편집용 Word 다운로드", data=file_info['word'], 
                        file_name=f"SDH_Premium_Part_{file_info['part']}.docx", 
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_word_{file_info['part']}", use_container_width=True
                    )
            st.markdown("---")
        
        if remain_tasks > 0:
            target_amount = min(split_size, remain_tasks)
            if st.button(f"🚀 2단계: Part {st.session_state.part_counter} 초고속 출제 시작 ({target_amount}문제)", type="primary", use_container_width=True):
                
                current_batch = st.session_state.exam_queue[:target_amount]
                cached_results = {}
                tasks_to_process = []
                
                for task in current_batch:
                    cache_key = f"{exam_key}_{task['q_num']}_{task['q_type']}"
                    if cache_key in st.session_state.problem_cache:
                        cached_results[cache_key] = st.session_state.problem_cache[cache_key]
                    else: tasks_to_process.append(task)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                model = genai.GenerativeModel('gemini-3.6-flash')
                
                if tasks_to_process:
                    chunk_size = 2 
                    chunks = [tasks_to_process[i:i + chunk_size] for i in range(0, len(tasks_to_process), chunk_size)]
                    total_chunks = len(chunks)
                    completed_chunks = 0
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                        future_to_chunk = {executor.submit(process_chunk, c, exam_key, st.session_state.passage_db, model): c for c in chunks}
                        
                        for future in concurrent.futures.as_completed(future_to_chunk):
                            chunk_info, probs, success = future.result()
                            for idx, task in enumerate(chunk_info):
                                if idx < len(probs):
                                    cache_key = f"{exam_key}_{task['q_num']}_{task['q_type']}"
                                    st.session_state.problem_cache[cache_key] = probs[idx]
                                    cached_results[cache_key] = probs[idx]
                                    
                            completed_chunks += 1
                            progress = min(1.0, completed_chunks / total_chunks)
                            progress_bar.progress(progress)
                            status_text.text(f"⚡ 초고속 병렬 출제 중... (총 {total_chunks}구간 중 {completed_chunks}구간 완료)")
                    
                    save_json(CACHE_FILE, st.session_state.problem_cache)
                
                status_text.text(f"✅ Part {st.session_state.part_counter} 초고속 출제 완료! 렌더링 중...")
                
                all_generated_problems = [cached_results[f"{exam_key}_{task['q_num']}_{task['q_type']}"] for task in current_batch if f"{exam_key}_{task['q_num']}_{task['q_type']}" in cached_results]
                
                questions_html = ""
                answers_html = ""
                
                for idx, data in enumerate(all_generated_problems):
                    q_title = f"{idx+1}. {data.get('question', '문제 누락').split('.', 1)[-1].strip() if '.' in data.get('question', '') else data.get('question', '')}"
                    passage_raw = data.get("passage", "")
                    if "[박스]" in passage_raw and "[/박스]" in passage_raw:
                        inserted_box = passage_raw.split("[박스]")[1].split("[/박스]")[0]
                        main_passage = passage_raw.split("[/박스]")[1].strip()
                        passage_html = f'<div class="inserted-box">{inserted_box}</div><div class="passage-box">{main_passage}</div>'
                    else: passage_html = f'<div class="passage-box">{passage_raw}</div>'
                    
                    options_html = ""
                    options = data.get("options", [])
                    if options:
                        options_html += '<div class="options-container">'
                        for opt in options: options_html += f'<div class="option-item">{opt}</div>'
                        options_html += '</div>'
                        
                    questions_html += f'<div class="question-block"><div class="question-title">{q_title}</div>{passage_html}{options_html}</div>'
                    answers_html += f'<div class="answer-block"><b>{idx+1}번 - {data.get("answer", "")}</b><br/><b>[해설]</b> {data.get("explanation", "")}</div>'

                header_title = f"{exam_year} {exam_month} {exam_grade} 모의고사 변형문제 (Part {st.session_state.part_counter})"
                
                html_content = f'''
                <!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><title>{header_title}</title>
                <style>
                    @import url('[https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700&display=swap](https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700&display=swap)');
                    @import url('[https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&display=swap](https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&display=swap)');
                    body {{ font-family: 'Nanum Myeongjo', serif; font-size: 9.8pt; letter-spacing: -0.3px; line-height: 1.35; color: #000; max-width: 210mm; margin: 0 auto; padding: 20px; }}
                    .header-container {{ font-family: 'Noto Sans KR', sans-serif; display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 20px; }}
                    .header-title {{ font-size: 14pt; font-weight: bold; }}
                    .header-sub {{ font-size: 8.5pt; color: #555; }}
                    .two-column-layout {{ column-count: 2; column-gap: 25px; column-fill: auto; }}
                    .question-block {{ break-inside: avoid; page-break-inside: avoid; margin-bottom: 30px; text-align: left; word-break: keep-all; }}
                    .question-title {{ font-family: 'Noto Sans KR', sans-serif; font-size: 10.5pt; font-weight: bold; margin-bottom: 5px; }}
                    .passage-box {{ border: 1.2px solid #000; padding: 8px 10px; margin: 5px 0; background-color: #fff; text-align: justify; word-break: normal; overflow-wrap: break-word; }}
                    .inserted-box {{ border: 1.5px solid #555; padding: 7px; margin-bottom: 8px; text-align: justify; word-break: normal; background-color: #f9f9f9; }}
                    .options-container {{ margin-top: 8px; }} .option-item {{ display: inline-block; margin-right: 15px; margin-bottom: 4px; }}
                    .answers-section {{ break-before: page; page-break-before: always; margin-top: 30px; }}
                    .section-title {{ font-family: 'Noto Sans KR', sans-serif; font-size: 13pt; font-weight: bold; text-align: center; border-bottom: 1px solid #000; padding-bottom: 8px; margin-bottom: 20px; }}
                    .answer-block {{ break-inside: avoid; page-break-inside: avoid; margin-bottom: 15px; text-align: justify; word-break: keep-all; }}
                    @media print {{ @page {{ margin: 12mm; }} body {{ padding: 0; }} }}
                </style></head><body>
                <div class="header-container"><div class="header-title">{header_title}</div><div class="header-sub">SDH Premium Decoding</div></div>
                <div class="two-column-layout">{questions_html}</div>
                <div class="answers-section"><div class="section-title">정답 및 해설</div><div class="two-column-layout">{answers_html}</div></div>
                </body></html>'''
                
                word_buffer = create_word_file(all_generated_problems, header_title)
                
                st.session_state.generated_files.append({
                    "part": st.session_state.part_counter,
                    "count": len(all_generated_problems),
                    "html": html_content,
                    "word": word_buffer.getvalue()
                })
                
                st.session_state.exam_queue = st.session_state.exam_queue[target_amount:]
                st.session_state.part_counter += 1
                st.rerun() 
        else:
            st.success("🎉 모든 대기열의 문제가 출제 완료되었습니다!")

# ------------------------------------------
# 메뉴 3: 지문 DB 관리
# ------------------------------------------
elif menu == "🗂️ 지문 DB 관리":
    st.markdown(f"##### 🗂️ 현재 선택된 출제 대상: **{exam_year} {exam_month}, {exam_grade}**")
    
    st.markdown("### 🚀 방법 1. 문제지 & 정답지 PDF 동시 업로드")
    pdf_col1, pdf_col2 = st.columns(2)
    with pdf_col1: uploaded_q_pdf = st.file_uploader("📝 문제지 PDF 업로드", type=["pdf"])
    with pdf_col2: uploaded_a_pdf = st.file_uploader("💡 정답/해설지 PDF 업로드 (선택)", type=["pdf"])
    
    if uploaded_q_pdf is not None:
        if st.button("✨ AI 정답 반영 지문 추출 및 DB 저장", type="primary"):
            with st.spinner("순수 원문을 복원 중입니다..."):
                try:
                    q_reader = PyPDF2.PdfReader(uploaded_q_pdf)
                    raw_q_text = "".join([page.extract_text() + "\n" for page in q_reader.pages])
                    raw_a_text = "".join([page.extract_text() + "\n" for page in PyPDF2.PdfReader(uploaded_a_pdf).pages]) if uploaded_a_pdf else "정답지 없음."
                    prompt = f"""고등학교 영어 지문 복원 전문가로서, 아래 텍스트에서 18~45번 지문을 복원해 JSON 형태로 출력하세요. 발문과 선택지는 지우고, 빈칸과 어법 오류는 정답을 반영해 완벽한 원문으로 만드세요. 밑줄과 번호 기호도 모두 삭제하세요.\n[문제지]\n{raw_q_text}\n\n[정답지]\n{raw_a_text}"""
                    response = genai.GenerativeModel('gemini-3.6-flash').generate_content(prompt)
                    res_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                    for q_num, passage in json.loads(res_text).items(): st.session_state.passage_db[exam_key][q_num] = passage
                    save_json(DB_FILE, st.session_state.passage_db)
                    st.success("🎉 DB 저장 완료!")
                except Exception as e: st.error(f"오류: {e}")
                
    st.markdown("---")
    st.markdown("### ✍️ 방법 2. 개별 수동 등록 및 검수")
    db_col1, db_col2 = st.columns([1, 2.5])
    with db_col1:
        target_q = st.selectbox("수정/검수할 지문 번호", [f"{q}번" for q in range(18, 46)])
        existing_text = st.session_state.passage_db.get(exam_key, {}).get(target_q, "")
        if existing_text: st.success("✅ 현재 DB에 복원된 지문이 있습니다.")
        else: st.warning("❌ 등록된 지문이 없습니다.")
            
    with db_col2:
        new_passage_text = st.text_area(f"{target_q} 지문 원문 (수동 수정 가능)", value=existing_text, height=250)
        if st.button("💾 개별 지문 수정/저장"):
            if new_passage_text.strip() == "": st.error("지문 내용을 입력해주세요.")
            else:
                st.session_state.passage_db[exam_key][target_q] = new_passage_text.strip()
                save_json(DB_FILE, st.session_state.passage_db)
                st.success(f"{target_q} 지문이 성공적으로 수정되었습니다!")

# ==========================================
# 하단 푸터
# ==========================================
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH Premium Decoding & Internal Exam System</div>", unsafe_allow_html=True)
