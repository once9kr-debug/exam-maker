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

# ==========================================
# 페이지 기본 설정 (Wide 모드)
# ==========================================
st.set_page_config(page_title="SDH ACADEMY 통합 출제 플랫폼", layout="wide")

# ==========================================
# 🎨 커스텀 CSS
# ==========================================
st.markdown("""
<style>
    .group-header { font-weight: 700; font-size: 1.1rem; color: #2C3E50; border-bottom: 2px solid #3498DB; padding-bottom: 8px; margin-top: 20px; margin-bottom: 15px; }
    .sub-group-title { font-weight: bold; color: #555; margin-top: 15px; margin-bottom: 5px; }
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
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.6)
        section.right_margin = Inches(0.6)

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
            except:
                doc.add_paragraph(passage_raw)
        else:
            doc.add_paragraph(passage_raw)

        options = data.get("options", [])
        if options:
            doc.add_paragraph("  ".join(options))
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
# 로컬 영구 DB 및 스마트 캐시 연동
# ==========================================
DB_FILE = "sdh_passages_db.json"
CACHE_FILE = "sdh_problems_cache_db.json"

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'passage_db' not in st.session_state: st.session_state.passage_db = load_json(DB_FILE)
if 'problem_cache' not in st.session_state: st.session_state.problem_cache = load_json(CACHE_FILE)

# ==========================================
# 세션 상태 관리
# ==========================================
if 'exam_queue' not in st.session_state: st.session_state.exam_queue = []
if 'generated_files' not in st.session_state: st.session_state.generated_files = []
if 'part_counter' not in st.session_state: st.session_state.part_counter = 1
if 'total_tasks' not in st.session_state: st.session_state.total_tasks = 0

def toggle_all_types():
    keys = ["t_topic", "t_title", "t_purpose", "t_blank", "t_order", "t_insert", "t_imply", "t_grammar", "t_vocab", "t_essay", "t_match"]
    for k in keys: st.session_state[k] = st.session_state.type_all

def toggle_all_q():
    for i in range(18, 46): st.session_state[f"q_{i}"] = st.session_state.q_all

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다.")
    st.stop()

st.title("SDH ACADEMY 통합 출제 플랫폼 🛠️")
st.markdown("---")

tab_search, tab_db, tab_exam = st.tabs(["🔍 모의고사 검색", "🗂️ 지문 DB 관리", "🎯 세부 변형문제 제작"])

with tab_search:
    st.markdown("<div class='group-header'>📚 모의고사 DB 검색</div>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 1])
    with col1: exam_type = st.selectbox("교재 선택", ["고등 모의고사", "고등 교과서"])
    with col2: exam_year = st.selectbox("연도", ["2026년", "2025년", "2024년"])
    with col3: exam_month = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"])
    with col4: exam_grade = st.selectbox("학년", ["고1", "고2", "고3"])
    with col5: st.write(""); st.button("🔍 검색", use_container_width=True)

with tab_db:
    st.markdown(f"##### 🗂️ 현재 선택된 출제 대상: **{exam_year} {exam_month}, {exam_grade}**")
    exam_key = f"{exam_year}_{exam_month}_{exam_grade}"
    if exam_key not in st.session_state.passage_db: st.session_state.passage_db[exam_key] = {}

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

with tab_exam:
    st.markdown(f"##### 📝 출제 대상: **{exam_year} {exam_month}, {exam_grade} 모의고사**")
    st.checkbox("✅ 전체 유형 선택", key="type_all", on_change=toggle_all_types)
    
    cat1, cat2, cat3, cat4 = st.columns(4)
    with cat1:
        st.markdown("<div class='sub-group-title'>🟢 대의 파악</div>", unsafe_allow_html=True)
        t_topic = st.checkbox("주제 추론", key="t_topic"); t_title = st.checkbox("제목 추론", key="t_title"); t_purpose = st.checkbox("목적/요지", key="t_purpose")
    with cat2:
        st.markdown("<div class='sub-group-title'>🟠 언어 논리</div>", unsafe_allow_html=True)
        t_blank = st.checkbox("빈칸 추론", key="t_blank"); t_order = st.checkbox("글의 순서", key="t_order"); t_insert = st.checkbox("문장 삽입", key="t_insert"); t_imply = st.checkbox("함축 의미", key="t_imply")
    with cat3:
        st.markdown("<div class='sub-group-title'>🔴 어법/어휘</div>", unsafe_allow_html=True)
        t_grammar = st.checkbox("어법 추론", key="t_grammar"); t_vocab = st.checkbox("어휘 추론", key="t_vocab")
    with cat4:
        st.markdown("<div class='sub-group-title'>🔵 서술형/기타</div>", unsafe_allow_html=True)
        t_essay = st.checkbox("서술형 영작", key="t_essay"); t_match = st.checkbox("내용 일치/불일치", key="t_match")

    st.markdown("---")
    st.checkbox("✅ 전체 지문 선택", key="q_all", on_change=toggle_all_q)
    
    q_cols = st.columns(10)
    for i, q_num in enumerate(range(18, 46)):
        with q_cols[i % 10]: st.checkbox(f"{q_num}번", key=f"q_{q_num}")

    st.markdown("---")
    split_size = st.number_input("파일 1개당 출제할 문제 수 (기본: 150)", min_value=10, max_value=500, value=150, step=10)
    
    if st.button("🛒 1단계: 출제 대기열(Queue) 생성하기", type="secondary", use_container_width=True):
        selected_q_nums = [f"{num}번" for num in range(18, 46) if st.session_state.get(f"q_{num}")]
        selected_types_list = []
        if t_topic: selected_types_list.append("주제 추론")
        if t_title: selected_types_list.append("제목 추론")
        if t_purpose: selected_types_list.append("목적/요지")
        if t_blank: selected_types_list.append("빈칸 추론")
        if t_order: selected_types_list.append("글의 순서")
        if t_insert: selected_types_list.append("문장 삽입")
        if t_imply: selected_types_list.append("함축 의미")
        if t_grammar: selected_types_list.append("어법 추론")
        if t_vocab: selected_types_list.append("어휘 추론")
        if t_essay: selected_types_list.append("서술형 영작")
        if t_match: selected_types_list.append("내용 일치/불일치")

        if not selected_types_list or not selected_q_nums:
            st.warning("유형과 지문을 최소 1개 이상 선택해주세요.")
        else:
            exam_key = f"{exam_year}_{exam_month}_{exam_grade}"
            current_db = st.session_state.passage_db.get(exam_key, {})
            missing_passages = [q for q in selected_q_nums if q not in current_db or current_db[q].strip() == ""]
            
            if missing_passages:
                st.error(f"🚨 다음 지문이 DB에 없습니다: {', '.join(missing_passages)}")
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
                        label=f"🌐 Part {file_info['part']} 인쇄용 HTML 다운로드", 
                        data=file_info['html'], 
                        file_name=f"SDH_Premium_Part_{file_info['part']}.html", 
                        mime="text/html",
                        key=f"dl_html_{file_info['part']}",
                        use_container_width=True
                    )
                with dl_col2:
                    st.download_button(
                        label=f"📝 Part {file_info['part']} 편집용 Word 다운로드", 
                        data=file_info['word'], 
                        file_name=f"SDH_Premium_Part_{file_info['part']}.docx", 
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_word_{file_info['part']}",
                        use_container_width=True
                    )
            st.markdown("---")
        
        if remain_tasks > 0:
            target_amount = min(split_size, remain_tasks)
            if st.button(f"🚀 2단계: Part {st.session_state.part_counter} 출제 시작 ({target_amount}문제)", type="primary", use_container_width=True):
                
                current_batch = st.session_state.exam_queue[:target_amount]
                exam_key = f"{exam_year}_{exam_month}_{exam_grade}"
                
                cached_results = {}
                tasks_to_generate = []
                
                for task in current_batch:
                    cache_key = f"{exam_key}_{task['q_num']}_{task['q_type']}"
                    if cache_key in st.session_state.problem_cache:
                        cached_results[cache_key] = st.session_state.problem_cache[cache_key]
                    else:
                        tasks_to_generate.append(task)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                model = genai.GenerativeModel('gemini-3.6-flash')
                
                if tasks_to_generate:
                    chunk_size = 3 
                    total_chunks = (len(tasks_to_generate) + chunk_size - 1) // chunk_size
                    
                    for i in range(0, len(tasks_to_generate), chunk_size):
                        chunk = tasks_to_generate[i:i + chunk_size]
                        current_chunk_idx = (i // chunk_size) + 1
                        status_text.text(f"🏃 Part {st.session_state.part_counter} AI 생성 중... (총 {total_chunks}구간 중 {current_chunk_idx}구간 진행)")
                        
                        prompt = "당신은 고등학교 내신 영어 출제 전문가입니다. 다음 지시된 [출제 목록]에 맞게 문제를 출제하세요.\n\n[출제 목록]\n"
                        for idx, task in enumerate(chunk):
                            passage_text = st.session_state.passage_db[exam_key][task['q_num']]
                            prompt += f"요청 {idx+1}. 지문 번호: {task['q_num']}, 출제해야 할 문제 유형: {task['q_type']}\n원문: {passage_text}\n\n"
                            
                        prompt += """[💥 디테일 출력 규칙 - 매우 엄격함 💥]
1. 부연 설명이나 마크다운(```json 등) 없이 순수 JSON 배열만 출력하세요.
2. 키: "question", "passage", "options", "answer", "explanation"
3. 글의 순서 문제: options에 반드시 ['① (A) - (C) - (B)', '② (B) - (A) - (C)', ...] 형태로 원문자 기호를 포함하세요.
4. 어법/어휘/문장삽입 문제: 지문(passage) 안에 밑줄이나 번호(①, ②)가 이미 포함된 경우, options는 반드시 빈 리스트 [] 를 반환하여 중복을 방지하세요.
5. 서술형 영작 문제: <조건> 텍스트는 발문(question)에 넣지 말고, 지문(passage) 텍스트 맨 마지막에 줄바꿈(<br/><br/>) 후 추가하세요.
6. 문장 삽입 문제: 주어진 문장은 반드시 [박스]주어진 문장[/박스] 형태로 지문 맨 앞에 표기하세요.
"""
                        try:
                            response = model.generate_content(prompt)
                            raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                            chunk_problems = json.loads(raw_text)
                            
                            for idx, task in enumerate(chunk):
                                if idx < len(chunk_problems):
                                    cache_key = f"{exam_key}_{task['q_num']}_{task['q_type']}"
                                    st.session_state.problem_cache[cache_key] = chunk_problems[idx]
                                    cached_results[cache_key] = chunk_problems[idx]
                        except Exception as e:
                            time.sleep(1)
                            
                        progress_bar.progress(current_chunk_idx / total_chunks)
                    
                    save_json(CACHE_FILE, st.session_state.problem_cache)
                
                status_text.text(f"✅ Part {st.session_state.part_counter} 출제 완료! 시험지 렌더링 중...")
                
                all_generated_problems = []
                for task in current_batch:
                    cache_key = f"{exam_key}_{task['q_num']}_{task['q_type']}"
                    if cache_key in cached_results:
                        all_generated_problems.append(cached_results[cache_key])
                
                questions_html = ""
                answers_html = ""
                
                for idx, data in enumerate(all_generated_problems):
                    q_title = f"{idx+1}. {data.get('question', '문제 누락').split('.', 1)[-1].strip() if '.' in data.get('question', '') else data.get('question', '')}"
                    passage_raw = data.get("passage", "")
                    
                    if "[박스]" in passage_raw and "[/박스]" in passage_raw:
                        inserted_box = passage_raw.split("[박스]")[1].split("[/박스]")[0]
                        main_passage = passage_raw.split("[/박스]")[1].strip()
                        passage_html = f'<div class="inserted-box">{inserted_box}</div><div class="passage-box">{main_passage}</div>'
                    else:
                        passage_html = f'<div class="passage-box">{passage_raw}</div>'
                    
                    options_html = ""
                    options = data.get("options", [])
                    if options:
                        options_html += '<div class="options-container">'
                        for opt in options: options_html += f'<div class="option-item">{opt}</div>'
                        options_html += '</div>'
                        
                    questions_html += f'<div class="question-block"><div class="question-title">{q_title}</div>{passage_html}{options_html}</div>'
                    answers_html += f'<div class="answer-block"><b>{idx+1}번 - {data.get("answer", "")}</b><br/><b>[해설]</b> {data.get("explanation", "")}</div>'

                header_title = f"{exam_year} {exam_month} {exam_grade} 모의고사 변형문제 (Part {st.session_state.part_counter})"
                
                # 💥 3. CSS 초정밀 튜닝: 양쪽 정렬(justify) 적용 및 단어 찢어짐 방지(word-break: normal)
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
                    
                    /* 💥 핵심: 양쪽 정렬(justify) 유지하되 영문 띄어쓰기 보호(word-break: normal) */
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

# ==========================================
# 하단 푸터
# ==========================================
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH ACADEMY & Internal Exam System</div>", unsafe_allow_html=True)
