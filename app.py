import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import PyPDF2
import time

# ==========================================
# 페이지 기본 설정 (Wide 모드)
# ==========================================
st.set_page_config(page_title="SDH ACADEMY 통합 출제 플랫폼", layout="wide")

# ==========================================
# 커스텀 CSS
# ==========================================
st.markdown("""
<style>
    .group-header {
        font-weight: 700;
        font-size: 1.1rem;
        color: #2C3E50;
        border-bottom: 2px solid #3498DB;
        padding-bottom: 8px;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    .sub-group-title {
        font-weight: bold;
        color: #555;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    div[data-testid="stCheckbox"] label span {
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 로컬 영구 DB 연동 엔진
# ==========================================
DB_FILE = "sdh_passages_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db_data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db_data, f, ensure_ascii=False, indent=4)

if 'passage_db' not in st.session_state:
    st.session_state.passage_db = load_db()

# ==========================================
# 체크박스 전체선택 동기화 방아쇠
# ==========================================
def toggle_all_types():
    keys = ["t_topic", "t_title", "t_purpose", "t_blank", "t_order", "t_insert", "t_imply", "t_grammar", "t_vocab", "t_essay", "t_match"]
    for k in keys:
        st.session_state[k] = st.session_state.type_all

def toggle_all_q():
    for i in range(18, 46):
        st.session_state[f"q_{i}"] = st.session_state.q_all

# ==========================================
# API 세팅
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

st.title("SDH ACADEMY 통합 출제 플랫폼 🛠️")
st.markdown("---")

tab_search, tab_db, tab_exam = st.tabs(["🔍 모의고사 검색", "🗂️ 지문 DB 관리", "🎯 세부 변형문제 제작"])

# ------------------------------------------
# 탭 1: 모의고사 검색
# ------------------------------------------
with tab_search:
    st.markdown("<div class='group-header'>📚 모의고사 DB 검색</div>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 1])
    with col1: exam_type = st.selectbox("교재 선택", ["고등 모의고사", "고등 교과서"])
    with col2: exam_year = st.selectbox("연도", ["2026년", "2025년", "2024년"])
    with col3: exam_month = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"])
    with col4: exam_grade = st.selectbox("학년", ["고1", "고2", "고3"])
    with col5: 
        st.write("")
        st.button("🔍 검색", use_container_width=True)
        
    st.markdown("---")
    st.caption("조회된 모의고사 목록")
    db_data = {
        "연도": ["2026", "2026", "2026", "2025", "2025"],
        "월": ["6월", "6월", "6월", "11월", "11월"],
        "주관": ["2026년 6월", "2026년 6월", "2026년 6월", "2025년 11월", "2025년 11월"],
        "학년": ["1학년", "2학년", "3학년", "1학년", "2학년"],
        "지문수": [28, 28, 28, 28, 28]
    }
    st.dataframe(pd.DataFrame(db_data), use_container_width=True, hide_index=True)

# ------------------------------------------
# 탭 2: 지문 DB 관리
# ------------------------------------------
with tab_db:
    st.markdown(f"##### 🗂️ 현재 선택된 출제 대상: **{exam_year} {exam_month}, {exam_grade}**")
    exam_key = f"{exam_year}_{exam_month}_{exam_grade}"
    if exam_key not in st.session_state.passage_db: st.session_state.passage_db[exam_key] = {}

    st.markdown("---")
    st.markdown("### 🚀 방법 1. 문제지 & 정답지 PDF 동시 업로드 (AI 정답 자동 반영)")
    pdf_col1, pdf_col2 = st.columns(2)
    with pdf_col1: uploaded_q_pdf = st.file_uploader("📝 문제지 PDF 업로드", type=["pdf"])
    with pdf_col2: uploaded_a_pdf = st.file_uploader("💡 정답/해설지 PDF 업로드 (선택)", type=["pdf"])
    
    if uploaded_q_pdf is not None:
        if st.button("✨ AI 정답 반영 지문 추출 및 DB 저장", type="primary", use_container_width=True):
            with st.spinner("AI가 문제를 분석하고 정답을 융합하여 순수 원문을 복원 중입니다... (약 1분 소요)"):
                try:
                    q_reader = PyPDF2.PdfReader(uploaded_q_pdf)
                    raw_q_text = ""
                    for page in q_reader.pages: raw_q_text += page.extract_text() + "\n"
                        
                    raw_a_text = ""
                    if uploaded_a_pdf is not None:
                        a_reader = PyPDF2.PdfReader(uploaded_a_pdf)
                        for page in a_reader.pages: raw_a_text += page.extract_text() + "\n"
                    else:
                        raw_a_text = "정답지가 제공되지 않았습니다. 문맥을 파악하여 최선을 다해 원문을 복원하세요."
                        
                    prompt = f"""당신은 고등학교 영어 지문 복원 전문가입니다.
제공된 [문제지 PDF 텍스트]와 [정답/해설지 PDF 텍스트]를 분석하여 18번부터 45번까지의 지문을 완벽한 '원본 텍스트'로 복원한 뒤, JSON 형태로 출력해 주세요.

[지문 복원 및 정답 반영 규칙 - 매우 엄격함]
1. 문제 발문과 하단 선택지는 절대 포함하지 마세요.
2. 빈칸 추론 문제: 빈칸을 지우고 정답 단어를 채워넣으세요.
3. 어법/어휘 문제: 정답 해설을 참고하여 틀린 단어를 고치고, 밑줄과 원문자를 지우세요.
4. 문장 삽입/글의 순서 문제: 올바른 순서대로 이어붙이고 기호를 삭제하세요.
5. JSON 키(Key)는 반드시 "18번", "19번"... 형식이어야 합니다.
6. 백틱(```) 기호나 부연 설명 없이, 오직 순수한 JSON 배열 형태의 텍스트만 출력하세요.

[문제지 텍스트]
{raw_q_text}

[정답/해설지 텍스트]
{raw_a_text}
"""
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    response = model.generate_content(prompt)
                    
                    res_text = response.text.strip()
                    res_text = res_text.replace("```json", "").replace("```", "").strip()
                    
                    extracted_data = json.loads(res_text)
                    
                    for q_num, passage in extracted_data.items():
                        st.session_state.passage_db[exam_key][q_num] = passage
                    save_db(st.session_state.passage_db)
                    st.success(f"🎉 성공! 총 {len(extracted_data)}개의 지문이 복원되어 DB에 저장되었습니다.")
                except Exception as e:
                    st.error(f"자동 추출 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    st.markdown("### ✍️ 방법 2. 개별 수동 등록 및 검수")
    db_col1, db_col2 = st.columns([1, 2.5])
    with db_col1:
        target_q = st.selectbox("수정/검수할 지문 번호", [f"{q}번" for q in range(18, 46)])
        existing_text = st.session_state.passage_db[exam_key].get(target_q, "")
        if existing_text: st.success("✅ 현재 DB에 복원된 지문이 있습니다.")
        else: st.warning("❌ 등록된 지문이 없습니다.")
            
    with db_col2:
        new_passage_text = st.text_area(f"{target_q} 지문 원문 (수동 수정 가능)", value=existing_text, height=250)
        if st.button("💾 개별 지문 수정/저장"):
            if new_passage_text.strip() == "": st.error("지문 내용을 입력해주세요.")
            else:
                st.session_state.passage_db[exam_key][target_q] = new_passage_text.strip()
                save_db(st.session_state.passage_db)
                st.success(f"{target_q} 지문이 성공적으로 수정되었습니다!")

# ------------------------------------------
# 탭 3: 세부 변형문제 제작
# ------------------------------------------
with tab_exam:
    st.markdown(f"##### 📝 출제 대상: **{exam_year} {exam_month}, {exam_grade} 모의고사**")
    
    st.markdown("<div class='group-header'>📌 1. 출제할 세부 유형 선택</div>", unsafe_allow_html=True)
    st.checkbox("✅ 전체 유형 선택", key="type_all", on_change=toggle_all_types)
    
    cat1, cat2, cat3, cat4 = st.columns(4)
    with cat1:
        st.markdown("<div class='sub-group-title'>🟢 대의 파악</div>", unsafe_allow_html=True)
        t_topic = st.checkbox("주제 추론", key="t_topic")
        t_title = st.checkbox("제목 추론", key="t_title")
        t_purpose = st.checkbox("목적/요지", key="t_purpose")
    with cat2:
        st.markdown("<div class='sub-group-title'>🟠 언어 논리</div>", unsafe_allow_html=True)
        t_blank = st.checkbox("빈칸 추론", key="t_blank")
        t_order = st.checkbox("글의 순서", key="t_order")
        t_insert = st.checkbox("문장 삽입", key="t_insert")
        t_imply = st.checkbox("함축 의미", key="t_imply")
    with cat3:
        st.markdown("<div class='sub-group-title'>🔴 어법/어휘</div>", unsafe_allow_html=True)
        t_grammar = st.checkbox("어법 추론", key="t_grammar")
        t_vocab = st.checkbox("어휘 추론", key="t_vocab")
    with cat4:
        st.markdown("<div class='sub-group-title'>🔵 서술형/기타</div>", unsafe_allow_html=True)
        t_essay = st.checkbox("서술형 영작", key="t_essay")
        t_match = st.checkbox("내용 일치/불일치", key="t_match")

    st.markdown("---")
    st.markdown("<div class='group-header'>📖 2. 모의고사 지문(번호) 선택</div>", unsafe_allow_html=True)
    st.checkbox("✅ 전체 지문 선택", key="q_all", on_change=toggle_all_q)
    
    q_cols = st.columns(10)
    for i, q_num in enumerate(range(18, 46)):
        with q_cols[i % 10]:
            st.checkbox(f"{q_num}번", key=f"q_{q_num}")

    st.markdown("---")
    
    if st.button("🚀 SDH Premium 변형문제 생성 및 인쇄", type="primary", use_container_width=True):
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
        
        if not selected_types_list:
            st.warning("출제할 세부 유형을 1개 이상 선택해주세요.")
            st.stop()
            
        if not selected_q_nums:
            st.warning("지문 번호를 1개 이상 선택해주세요.")
        else:
            exam_key = f"{exam_year}_{exam_month}_{exam_grade}"
            current_db = st.session_state.passage_db.get(exam_key, {})
            
            missing_passages = [q for q in selected_q_nums if q not in current_db or current_db[q].strip() == ""]
            
            if missing_passages:
                st.error(f"🚨 다음 지문들이 DB에 등록되지 않았습니다: {', '.join(missing_passages)}\n['🗂️ 지문 DB 관리'] 탭에서 해당 지문들을 먼저 등록해주세요!")
            else:
                total_expected_questions = len(selected_q_nums) * len(selected_types_list)
                st.info(f"💡 총 {total_expected_questions}문제 출제를 시작합니다. 무한 생성 엔진이 가동 중입니다...")
                
                # 💥 무한 출제를 위한 릴레이(Batch) 엔진 가동
                chunk_size = 3 # 한 번에 3개 지문씩 묶어서 AI에게 질문 (안정성 확보)
                all_generated_problems = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                model = genai.GenerativeModel('gemini-3.6-flash')
                
                total_chunks = (len(selected_q_nums) + chunk_size - 1) // chunk_size
                
                for i in range(0, len(selected_q_nums), chunk_size):
                    chunk_q_nums = selected_q_nums[i:i + chunk_size]
                    current_chunk_idx = (i // chunk_size) + 1
                    
                    status_text.text(f"🏃 릴레이 출제 중... (총 {total_chunks}구간 중 {current_chunk_idx}구간 생성 중)")
                    
                    passages_text = ""
                    for idx, q in enumerate(chunk_q_nums):
                        text = current_db[q]
                        passages_text += f"[지문 {q}]\n{text}\n\n"
                        
                    prompt = f"""당신은 고등학교 내신 영어 출제 전문가입니다.

[💥 핵심 출제 지침 - 가장 중요 💥]
제공된 **각각의 지문마다**, 아래 [선택된 문제 유형]에 해당하는 문제를 **빠짐없이 1개씩 모두** 출제해야 합니다.
(즉, 1개의 지문에 대해 총 {len(selected_types_list)}개의 문제가 연속으로 만들어져야 합니다.)

[선택된 문제 유형]: {', '.join(selected_types_list)}

[지문 목록]:
{passages_text}

[출력 규칙 - 매우 엄격함]
1. 부연 설명 없이, 오직 유효한 JSON 배열(Array) 형식만 출력하세요. 
2. 백틱(```)이나 마크다운 기호는 절대 사용하지 마세요.
3. JSON 키: "question", "passage", "options", "answer", "explanation"
4. "question": 문제 발문
5. "passage": 지문 내용 원문. 문단 바꿈은 <br/> 처리. 
6. "options": 선택지 리스트. ["① apple", "② banana"...]. 필요 없으면 빈 리스트 [] 반환.
7. "answer": 정답 번호
8. "explanation": 해설 텍스트.
"""
                    try:
                        response = model.generate_content(prompt)
                        raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                        chunk_problems = json.loads(raw_text)
                        all_generated_problems.extend(chunk_problems)
                    except Exception as e:
                        st.error(f"{current_chunk_idx}구간 생성 중 오류가 발생하여 건너뜁니다. (오류: {e})")
                        time.sleep(1) # 에러 시 잠시 대기
                        
                    # 진행률 업데이트
                    progress_bar.progress(current_chunk_idx / total_chunks)
                
                # 💥 릴레이 출제 완료 후 HTML 렌더링
                status_text.text("✅ 모든 문제 출제 완료! 최종 150+문제 시험지로 조립 중...")
                
                questions_html = ""
                answers_html = ""
                
                for idx, data in enumerate(all_generated_problems):
                    # 문제 번호를 전체 순서에 맞게 강제 재부여
                    q_title_original = data.get("question", "")
                    q_title_text = q_title_original.split(".", 1)[1].strip() if "." in q_title_original else q_title_original
                    q_title = f"{idx+1}. {q_title_text}"
                    
                    passage_raw = data.get("passage", "")
                    if "[박스]" in passage_raw and "[/박스]" in passage_raw:
                        inserted_box = passage_raw.split("[박스]")[1].split("[/박스]")[0]
                        main_passage = passage_raw.split("[/박스]")[1].strip()
                        passage_html = f'<div class="passage-box" style="margin-bottom: 5px;">{inserted_box}</div>'
                        passage_html += f'<div class="passage-box">{main_passage}</div>'
                    else:
                        passage_html = f'<div class="passage-box">{passage_raw}</div>'
                    
                    options_html = ""
                    options = data.get("options", [])
                    if options and len(options) > 0:
                        options_html += '<div class="options-container">'
                        for opt in options:
                            options_html += f'<div class="option-item">{opt}</div>'
                        options_html += '</div>'
                        
                    answer = data.get("answer", "")
                    explanation = data.get("explanation", "")
                    
                    questions_html += f'''
                    <div class="question-block">
                        <div class="question-title">{q_title}</div>
                        {passage_html}
                        {options_html}
                    </div>
                    '''
                    
                    answers_html += f'''
                    <div class="answer-block">
                        <b>{idx+1}번 - {answer}</b><br/>
                        <b>[해설]</b> {explanation}
                    </div>
                    '''

                header_title = f"{exam_year} {exam_month} {exam_grade} 모의고사 변형문제"
                
                html_content = f'''
                <!DOCTYPE html>
                <html lang="ko">
                <head>
                    <meta charset="utf-8">
                    <title>{header_title}</title>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700&display=swap');
                        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&display=swap');
                        
                        body {{ font-family: 'Nanum Myeongjo', serif; font-size: 9.5pt; line-height: 1.4; color: #000; max-width: 210mm; margin: 0 auto; padding: 20px; }}
                        .header-container {{ font-family: 'Noto Sans KR', sans-serif; display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 15px; }}
                        .header-title {{ font-size: 14pt; font-weight: bold; }}
                        .header-sub {{ font-size: 8.5pt; color: #555; }}
                        .two-column-layout {{ column-count: 2; column-gap: 25px; column-fill: auto; }}
                        .question-block {{ break-inside: avoid; page-break-inside: avoid; margin-bottom: 25px; text-align: justify; word-break: keep-all; }}
                        .question-title {{ font-family: 'Noto Sans KR', sans-serif; font-size: 10pt; font-weight: bold; margin-bottom: 4px; }}
                        .passage-box {{ border: 1.1px solid #000; padding: 5px 8px; margin: 3px 0; background-color: #fff; text-align: justify; word-break: keep-all; overflow-wrap: break-word; }}
                        .options-container {{ margin-top: 4px; }}
                        .option-item {{ display: inline-block; margin-right: 15px; margin-bottom: 3px; text-align: left; word-break: keep-all; }}
                        .answers-section {{ break-before: page; page-break-before: always; margin-top: 30px; }}
                        .section-title {{ font-family: 'Noto Sans KR', sans-serif; font-size: 13pt; font-weight: bold; text-align: center; border-bottom: 1px solid #000; padding-bottom: 8px; margin-bottom: 20px; }}
                        .answer-block {{ break-inside: avoid; page-break-inside: avoid; margin-bottom: 15px; text-align: justify; word-break: keep-all; }}
                        @media print {{ @page {{ margin: 15mm; }} body {{ padding: 0; }} }}
                    </style>
                </head>
                <body>
                    <div class="header-container">
                        <div class="header-title">{header_title}</div>
                        <div class="header-sub">SDH ACADEMY & Internal Exam System</div>
                    </div>
                    <div class="two-column-layout">
                        {questions_html}
                    </div>
                    <div class="answers-section">
                        <div class="section-title">정답 및 해설</div>
                        <div class="two-column-layout">
                            {answers_html}
                        </div>
                    </div>
                </body>
                </html>
                '''
                st.success(f"🎉 대성공! 총 {len(all_generated_problems)}문제가 담긴 거대한 시험지가 1개의 파일로 완벽하게 조립되었습니다.")
                st.download_button("📥 상용 서비스급 대용량 시험지 다운로드", data=html_content, file_name="SDH_Premium_Exam_Massive.html", mime="text/html")

# ==========================================
# 하단 푸터
# ==========================================
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH ACADEMY & Internal Exam System</div>", unsafe_allow_html=True)
