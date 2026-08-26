import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import PyPDF2  # PDF 처리를 위한 라이브러리 추가

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
# 로컬 영구 DB(JSON) 연동 엔진
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
# API 세팅
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

st.title("SDH ACADEMY 통합 출제 플랫폼 🛠️")
st.markdown("---")

# ==========================================
# 메인 탭 구성
# ==========================================
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
# 탭 2: 지문 DB 관리 (PDF 자동 추출 기능 추가)
# ------------------------------------------
with tab_db:
    st.markdown(f"##### 🗂️ 현재 선택된 출제 대상: **{exam_year} {exam_month}, {exam_grade}**")
    exam_key = f"{exam_year}_{exam_month}_{exam_grade}"
    
    if exam_key not in st.session_state.passage_db:
        st.session_state.passage_db[exam_key] = {}

    st.markdown("---")
    # 💥 기능 1: PDF 인공지능 자동 추출
    st.markdown("### 🚀 [추천] 방법 1. PDF 파일로 한 번에 자동 등록하기")
    st.info("평가원이나 교육청의 모의고사 PDF 파일을 업로드하면, AI가 18번~45번 지문만 쏙쏙 뽑아 DB에 자동 저장합니다.")
    
    uploaded_pdf = st.file_uploader("PDF 파일 업로드", type=["pdf"])
    
    if uploaded_pdf is not None:
        if st.button("✨ AI 자동 추출 및 DB 전체 저장", type="primary"):
            with st.spinner("AI가 PDF를 읽고 불필요한 선택지를 버린 뒤, 순수 지문만 추출하고 있습니다. (약 30~60초 소요)"):
                try:
                    # PDF 텍스트 추출
                    pdf_reader = PyPDF2.PdfReader(uploaded_pdf)
                    raw_text = ""
                    for page in pdf_reader.pages:
                        raw_text += page.extract_text() + "\n"
                        
                    # Gemini에게 지문 발췌 명령
                    prompt = f'''다음은 고등학교 영어 모의고사 PDF에서 추출한 거친 텍스트(Raw Text)입니다.
이 텍스트를 분석하여 18번부터 45번까지의 '영어 지문(Passage) 원문'만 정확하게 발췌한 뒤, JSON 형태로 출력해 주세요.

[추출 규칙 - 매우 엄격함]
1. 문제 발문("다음 글의 목적으로...", "빈칸에 들어갈 말로...")과 하단 선택지(①, ②...)는 절대 포함하지 마세요. 오직 영어 지문 본문만 추출하세요.
2. 어법/어휘 문제에 있는 밑줄이나 번호(①, ②)는 원문 그대로 유지하세요.
3. JSON 키(Key)는 반드시 "18번", "19번", ... "45번" 형식이어야 합니다. 텍스트가 없는 번호는 건너뛰세요.
4. 어떠한 인사말이나 마크다운(```json) 없이 완벽한 JSON 형식만 출력하세요.

[원문 텍스트]
{raw_text}
'''
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    response = model.generate_content(prompt)
                    
                    # JSON 파싱
                    res_text = response.text.strip()
                    if res_text.startswith("```json"): res_text = res_text[7:]
                    if res_text.startswith("```"): res_text = res_text[3:]
                    if res_text.endswith("```"): res_text = res_text[:-3]
                    
                    extracted_data = json.loads(res_text.strip())
                    
                    # DB에 업데이트
                    for q_num, passage in extracted_data.items():
                        st.session_state.passage_db[exam_key][q_num] = passage
                    save_db(st.session_state.passage_db)
                    
                    st.success(f"🎉 성공! 총 {len(extracted_data)}개의 지문이 완벽하게 추출되어 DB에 저장되었습니다.")
                except Exception as e:
                    st.error(f"자동 추출 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    
    # 기능 2: 수동 개별 등록 (기존)
    st.markdown("### ✍️ 방법 2. 개별 수동 등록 및 수정")
    db_col1, db_col2 = st.columns([1, 2.5])
    with db_col1:
        target_q = st.selectbox("수정/등록할 지문 번호", [f"{q}번" for q in range(18, 46)])
        existing_text = st.session_state.passage_db[exam_key].get(target_q, "")
        if existing_text:
            st.success("✅ 현재 DB에 등록된 지문이 있습니다.")
        else:
            st.warning("❌ 등록된 지문이 없습니다.")
            
    with db_col2:
        new_passage_text = st.text_area(f"{target_q} 지문 원문", value=existing_text, height=250)
        if st.button("💾 개별 지문 수정/저장"):
            if new_passage_text.strip() == "":
                st.error("지문 내용을 입력해주세요.")
            else:
                st.session_state.passage_db[exam_key][target_q] = new_passage_text.strip()
                save_db(st.session_state.passage_db)
                st.success(f"{target_q} 지문이 성공적으로 저장되었습니다!")

# ------------------------------------------
# 탭 3: 세부 변형문제 제작
# ------------------------------------------
with tab_exam:
    st.markdown(f"##### 📝 출제 대상: **{exam_year} {exam_month}, {exam_grade} 모의고사**")
    
    st.markdown("<div class='group-header'>📌 1. 출제할 세부 유형 선택</div>", unsafe_allow_html=True)
    type_all = st.checkbox("✅ 전체 유형 선택", key="type_all")
    
    cat1, cat2, cat3, cat4 = st.columns(4)
    with cat1:
        st.markdown("<div class='sub-group-title'>🟢 대의 파악</div>", unsafe_allow_html=True)
        t_topic = st.checkbox("주제 추론", value=type_all)
        t_title = st.checkbox("제목 추론", value=type_all)
        t_purpose = st.checkbox("목적/요지", value=type_all)
    with cat2:
        st.markdown("<div class='sub-group-title'>🟠 언어 논리</div>", unsafe_allow_html=True)
        t_blank = st.checkbox("빈칸 추론", value=type_all)
        t_order = st.checkbox("글의 순서", value=type_all)
        t_insert = st.checkbox("문장 삽입", value=type_all)
        t_imply = st.checkbox("함축 의미", value=type_all)
    with cat3:
        st.markdown("<div class='sub-group-title'>🔴 어법/어휘</div>", unsafe_allow_html=True)
        t_grammar = st.checkbox("어법 추론", value=type_all)
        t_vocab = st.checkbox("어휘 추론", value=type_all)
    with cat4:
        st.markdown("<div class='sub-group-title'>🔵 서술형/기타</div>", unsafe_allow_html=True)
        t_essay = st.checkbox("서술형 영작", value=type_all)
        t_match = st.checkbox("내용 일치/불일치", value=type_all)

    st.markdown("---")
    st.markdown("<div class='group-header'>📖 2. 모의고사 지문(번호) 선택</div>", unsafe_allow_html=True)
    q_all = st.checkbox("✅ 전체 지문 선택", key="q_all")
    
    q_cols = st.columns(10)
    for i, q_num in enumerate(range(18, 46)):
        with q_cols[i % 10]:
            st.checkbox(f"{q_num}번", value=q_all, key=f"q_{q_num}")

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
        
        final_selected_types = selected_types_list if selected_types_list else ["어법 추론"]
        
        if not selected_q_nums:
            st.warning("지문 번호를 1개 이상 선택해주세요.")
        else:
            with st.spinner("최고급 명조체 템플릿에 맞추어 문제를 출제하고 있습니다. (약 15~30초)"):
                
                exam_key = f"{exam_year}_{exam_month}_{exam_grade}"
                current_db = st.session_state.passage_db.get(exam_key, {})
                
                passages_text = ""
                missing_passages = []
                
                for idx, q in enumerate(selected_q_nums):
                    if q in current_db and current_db[q].strip() != "":
                        text = current_db[q]
                        passages_text += f"[지문 {idx+1} - {q}]\n{text}\n\n"
                    else:
                        missing_passages.append(q)
                
                if missing_passages:
                    st.error(f"🚨 다음 지문들이 DB에 등록되지 않았습니다: {', '.join(missing_passages)}\n['🗂️ 지문 DB 관리'] 탭에서 해당 지문들을 먼저 등록해주세요!")
                else:
                    prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 지문으로 변형 문제를 만드세요.
[선택된 문제 유형]: {', '.join(final_selected_types)}
[지문 목록]: {passages_text}

[출력 규칙 - 매우 엄격함]
1. 어떠한 부연 설명도 하지 말고, 오직 유효한 JSON 배열(Array) 형식만 출력하세요. 마크다운(```json)도 사용하지 마세요.
2. JSON 배열의 각 객체는 다음 키를 가져야 합니다: "question", "passage", "options", "answer", "explanation"
3. "question": 문제 발문 (예: "1. 다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?")
4. "passage": 지문 내용 원문. 문단 바꿈은 <br/>로 처리하세요. 어법/어휘 문제의 경우 지문 내에 ① <u>단어</u> 형태로 직접 번호와 밑줄을 넣으세요. 문장 삽입 문제의 경우 주어진 문장 박스도 포함해야 하니 [박스]주어진문장[/박스] 형태로 상단에 표기하세요.
5. "options": 선택지 리스트. ["① apple", "② banana", ...]. 만약 어법/어휘/문장 삽입처럼 지문 안에 이미 번호가 있어서 하단 선택지가 필요 없다면 빈 리스트 [] 를 반환하세요.
6. "answer": 정답 번호 (예: "5")
7. "explanation": 정답의 근거와 오답의 이유를 상세히 적은 해설 텍스트.
'''
                    try:
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        response = model.generate_content(prompt)
                        
                        raw_text = response.text.strip()
                        if raw_text.startswith("```json"): raw_text = raw_text[7:]
                        if raw_text.startswith("```"): raw_text = raw_text[3:]
                        if raw_text.endswith("```"): raw_text = raw_text[:-3]
                            
                        problems_data = json.loads(raw_text.strip())
                        
                        questions_html = ""
                        answers_html = ""
                        
                        for idx, data in enumerate(problems_data):
                            q_title = data.get("question", f"{idx+1}. 문제가 누락되었습니다.")
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
                                
                            q_num_only = q_title.split('.')[0] if '.' in q_title else str(idx+1)
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
                                <b>{q_num_only}번 - {answer}</b><br/>
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
                                
                                body {{ 
                                    font-family: 'Nanum Myeongjo', serif; 
                                    font-size: 9.5pt; 
                                    line-height: 1.4; 
                                    color: #000; 
                                    max-width: 210mm;
                                    margin: 0 auto;
                                    padding: 20px;
                                }}
                                .header-container {{ 
                                    font-family: 'Noto Sans KR', sans-serif; 
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: flex-end;
                                    border-bottom: 2px solid #000; 
                                    padding-bottom: 8px; 
                                    margin-bottom: 15px; 
                                }}
                                .header-title {{ font-size: 14pt; font-weight: bold; }}
                                .header-sub {{ font-size: 8.5pt; color: #555; }}
                                
                                .two-column-layout {{
                                    column-count: 2;
                                    column-gap: 25px; 
                                    column-fill: auto;
                                }}
                                .question-block {{ 
                                    break-inside: avoid; 
                                    page-break-inside: avoid; 
                                    margin-bottom: 25px; 
                                    text-align: justify; 
                                    word-break: keep-all; 
                                }}
                                .question-title {{
                                    font-family: 'Noto Sans KR', sans-serif;
                                    font-size: 10pt; 
                                    font-weight: bold;
                                    margin-bottom: 4px;
                                }}
                                .passage-box {{ 
                                    border: 1.1px solid #000; 
                                    padding: 5px 8px; 
                                    margin: 3px 0; 
                                    background-color: #fff;
                                    text-align: justify;
                                    word-break: keep-all; 
                                    overflow-wrap: break-word; 
                                }}
                                .options-container {{ margin-top: 4px; }}
                                .option-item {{
                                    display: inline-block;
                                    margin-right: 15px; 
                                    margin-bottom: 3px;
                                    text-align: left; 
                                    word-break: keep-all;
                                }}
                                .answers-section {{ 
                                    break-before: page; 
                                    page-break-before: always; 
                                    margin-top: 30px; 
                                }}
                                .section-title {{ 
                                    font-family: 'Noto Sans KR', sans-serif;
                                    font-size: 13pt; 
                                    font-weight: bold; 
                                    text-align: center; 
                                    border-bottom: 1px solid #000; 
                                    padding-bottom: 8px; 
                                    margin-bottom: 20px; 
                                }}
                                .answer-block {{ 
                                    break-inside: avoid; 
                                    page-break-inside: avoid;
                                    margin-bottom: 15px; 
                                    text-align: justify; 
                                    word-break: keep-all; 
                                }}
                                @media print {{
                                    @page {{ margin: 15mm; }}
                                    body {{ padding: 0; }}
                                }}
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
                        st.success("✅ 출제 완료! 완벽한 시험지가 조립되었습니다.")
                        st.download_button("📥 상용 서비스급 시험지 다운로드", data=html_content, file_name="SDH_Premium_Exam.html", mime="text/html")
                    except json.JSONDecodeError as e:
                        st.error("AI가 구조화된 데이터를 생성하지 못했습니다. 다시 시도해주세요.")
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")

# ==========================================
# 하단 푸터
# ==========================================
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH ACADEMY & Internal Exam System</div>", unsafe_allow_html=True)
