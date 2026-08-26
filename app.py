import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# ==========================================
# 페이지 기본 설정 (Wide 모드)
# ==========================================
st.set_page_config(page_title="SDH ACADEMY 통합 출제 플랫폼", layout="wide")

# ==========================================
# 커스텀 CSS (UI 그룹화 및 시각적 개선)
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
# API 세팅
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

# 공통 지문 DB (샘플)
mock_db = {
    "18번": "Dear Mr. Jones,\nI am writing to you on behalf of the student council...",
    "19번": "As I walked into the dark room, my heart started to beat faster...",
    "20번": "In today's fast-paced world, it is important to take time for yourself...",
    "21번": "The concept of 'social proof' dictates how we make decisions in groups...",
    "22번": "When encountering a new situation, the human brain attempts to categorize...",
    "23번": "Many ancient civilizations built their cities near major river systems...",
    "24번": "The rapid advancement of artificial intelligence has raised ethical concerns..."
}

st.title("SDH ACADEMY 통합 출제 플랫폼 🛠️")
st.markdown("---")

# ==========================================
# 메인 탭 구성
# ==========================================
tab_search, tab_exam = st.tabs(["🔍 모의고사 검색 및 워크북", "🎯 세부 변형문제 제작"])

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
# 탭 2: 세부 변형문제 제작
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
                passages_text = ""
                for idx, q in enumerate(selected_q_nums):
                    text = mock_db.get(q, f"[{q} 지문 업데이트가 필요합니다]")
                    passages_text += f"[지문 {idx+1} - {q}]\n{text}\n\n"

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

[출력 JSON 예시]
[
  {{
    "question": "1. 다음 글의 제목으로 가장 적절한 것은?",
    "passage": "In today's fast-paced world... (생략)",
    "options": ["① The importance of time", "② How to relax", "③ Why we sleep", "④ Fast-paced modern life", "⑤ Value of health"],
    "answer": "1",
    "explanation": "시간의 중요성에 대해 반복적으로 강조하고 있는 글입니다."
  }}
]
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
                                font-size: 9.5pt; /* 💥 10.5pt에서 9.5pt로 압축 (수능 표준) */
                                line-height: 1.4; /* 💥 줄 간격 1.5에서 1.4로 다이어트 */
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
                                padding-bottom: 8px; /* 💥 여백 축소 */
                                margin-bottom: 15px; /* 💥 여백 축소 */
                            }}
                            .header-title {{ font-size: 14pt; font-weight: bold; }}
                            .header-sub {{ font-size: 8.5pt; color: #555; }}
                            
                            .two-column-layout {{
                                column-count: 2;
                                column-gap: 25px; /* 💥 단 사이 간격을 좁혀서 양옆 텍스트 공간을 더 확보 */
                                column-fill: auto;
                            }}
                            .question-block {{ 
                                break-inside: avoid; 
                                page-break-inside: avoid; 
                                margin-bottom: 25px; /* 💥 문제 간 간격을 40px에서 25px로 대폭 축소 */
                                text-align: justify; 
                                word-break: keep-all; 
                            }}
                            .question-title {{
                                font-family: 'Noto Sans KR', sans-serif;
                                font-size: 10pt; /* 💥 발문 크기 약간 조절 */
                                font-weight: bold;
                                margin-bottom: 4px;
                            }}
                            .passage-box {{ 
                                border: 1.1px solid #000; 
                                padding: 5px 8px; /* 💥 박스 내부 여백을 더 타이트하게 */
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
                    st.success("✅ 오류 수정 완료! 변수들이 정상적으로 연결되었습니다.")
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
