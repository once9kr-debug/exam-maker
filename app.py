import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# ==========================================
# 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="SDH ACADEMY 통합 출제 플랫폼", layout="wide")

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

tab_workbook, tab_exam = st.tabs(["📚 워크북 제작", "🎯 변형문제 제작"])

with tab_workbook:
    st.subheader("📖 모의고사 워크북 제작")
    st.info("워크북 제작 기능은 준비 중입니다.")

with tab_exam:
    st.subheader("🎯 1. 출제 범위 선택 (모의고사)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        exam_grade = st.selectbox("대상 학년", ["고1", "고2", "고3"])
    with col2:
        exam_year = st.selectbox("모의고사 연도", ["2026년", "2025년", "2024년"])
    with col3:
        exam_month = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"])
        
    st.write("")
    st.checkbox("✅ 전체 지문 선택", key="select_all_q")
    
    q_cols = st.columns(10)
    for i, q_num in enumerate(range(18, 46)):
        with q_cols[i % 10]:
            st.checkbox(f"{q_num}번", key=f"q_{q_num}")

    st.markdown("---")
    st.subheader("🎯 2. 문제 유형 선택")
    st.checkbox("✅ 전체 유형 선택", key="select_all_types")
    
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1:
        st.checkbox("어법 추론", key="type_1")
        st.checkbox("어휘 추론", key="type_2")
    with t_col2:
        st.checkbox("빈칸 추론", key="type_3")
        st.checkbox("함축 의미", key="type_4")
    with t_col3:
        st.checkbox("글의 순서", key="type_5")
        st.checkbox("문장 삽입", key="type_6")
    with t_col4:
        st.checkbox("서술형 영작", key="type_7")
        st.checkbox("주제/제목", key="type_8")

    st.markdown("---")
    
    # ------------------------------------------
    # 💥 JSON 데이터 기반 파이썬 자체 렌더링 로직
    # ------------------------------------------
    if st.button("🚀 고급 인쇄용 변형문제 생성 (JSON 아키텍처)", type="primary", use_container_width=True):
        
        selected_q_nums = [f"{num}번" for num in range(18, 46) if st.session_state.get(f"q_{num}")]
        
        # 하드코딩된 테스트 유형 (향후 세션 스테이트 연동)
        final_selected_types = ["어법 추론", "빈칸 추론", "주제/제목", "문장 삽입"]
        
        if not selected_q_nums:
            st.warning("지문 번호를 1개 이상 선택해주세요.")
        else:
            with st.spinner("데이터 분리 엔진 가동 중... AI가 구조화된 데이터를 추출하고 있습니다. (약 15초)"):
                
                passages_text = ""
                for idx, q in enumerate(selected_q_nums):
                    text = mock_db.get(q, f"[{q} 지문 업데이트가 필요합니다]")
                    passages_text += f"[지문 {idx+1} - {q}]\n{text}\n\n"

                # 💥 AI에게 HTML 디자인을 금지하고 오직 순수 JSON 데이터만 요구하는 마스터 프롬프트
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
  }},
  {{
    "question": "2. 다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?",
    "passage": "Dear Mr. Jones,<br/>I am writing to you... ① <u>to be</u>...",
    "options": [],
    "answer": "5",
    "explanation": "look forward to의 to는 전치사이므로 동명사 hearing이 와야 합니다."
  }}
]
'''
                try:
                    # 1. AI API 호출
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    response = model.generate_content(prompt)
                    
                    # 2. JSON 파싱 및 데이터 정제
                    raw_text = response.text.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                        
                    problems_data = json.loads(raw_text.strip())
                    
                    # 3. 파이썬을 이용한 완벽한 렌더링 (디자인 통제)
                    questions_html = ""
                    answers_html = ""
                    
                    for idx, data in enumerate(problems_data):
                        # 문제 제목
                        q_title = data.get("question", f"{idx+1}. 문제가 누락되었습니다.")
                        # 지문 렌더링 (삽입 문제용 이중 박스 처리 로직 포함)
                        passage_raw = data.get("passage", "")
                        if "[박스]" in passage_raw and "[/박스]" in passage_raw:
                            inserted_box = passage_raw.split("[박스]")[1].split("[/박스]")[0]
                            main_passage = passage_raw.split("[/박스]")[1].strip()
                            passage_html = f'<div class="passage-box" style="margin-bottom: 8px;">{inserted_box}</div>'
                            passage_html += f'<div class="passage-box">{main_passage}</div>'
                        else:
                            passage_html = f'<div class="passage-box">{passage_raw}</div>'
                        
                        # 지능형 선택지 렌더링 (길이에 따라 유동적으로 가로 배열)
                        options_html = ""
                        options = data.get("options", [])
                        if options and len(options) > 0:
                            options_html += '<div class="options-container">'
                            for opt in options:
                                options_html += f'<div class="option-item">{opt}</div>'
                            options_html += '</div>'
                            
                        # 해설지 렌더링 (너른터 스타일의 한 문단 압축형)
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
                            <b>{q_num_only}번 - {answer}</b> <b>[해설]</b> {explanation}
                        </div>
                        '''

                    # 4. 최종 HTML/CSS 병합 (명조체/바탕체 적용)
                    header_title = f"{exam_year} {exam_month} {exam_grade} 모의고사 변형문제"
                    
                    html_content = f'''
                    <!DOCTYPE html>
                    <html lang="ko">
                    <head>
                        <meta charset="utf-8">
                        <title>{header_title}</title>
                        <style>
                            /* 상용 모의고사 전용 명조체 적용 */
                            @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700&display=swap');
                            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&display=swap');
                            
                            body {{ 
                                font-family: 'Nanum Myeongjo', serif; /* 본문 명조체 */
                                font-size: 10.5pt; 
                                line-height: 1.5; 
                                color: #000; 
                                max-width: 210mm;
                                margin: 0 auto;
                                padding: 20px;
                            }}
                            
                            .header-container {{ 
                                font-family: 'Noto Sans KR', sans-serif; /* 제목만 고딕체 */
                                display: flex;
                                justify-content: space-between;
                                align-items: flex-end;
                                border-bottom: 2px solid #000; 
                                padding-bottom: 10px; 
                                margin-bottom: 25px; 
                            }}
                            .header-title {{ font-size: 15pt; font-weight: bold; }}
                            .header-sub {{ font-size: 9pt; color: #555; }}
                            
                            .two-column-layout {{
                                column-count: 2;
                                column-gap: 35px;
                                column-fill: auto;
                            }}
                            
                            .question-block {{ 
                                break-inside: avoid; 
                                page-break-inside: avoid; 
                                margin-bottom: 45px; 
                                text-align: justify; 
                                word-break: keep-all; 
                            }}
                            
                            .question-title {{
                                font-family: 'Noto Sans KR', sans-serif;
                                font-weight: bold;
                                margin-bottom: 6px;
                            }}
                            
                            .passage-box {{ 
                                border: 1px solid #000; 
                                padding: 10px 12px; 
                                margin: 3px 0; 
                                background-color: #fff;
                                text-align: justify;
                                word-break: keep-all; 
                                overflow-wrap: break-word; 
                            }}
                            
                            /* 지능적 선택지 가로 배열 로직 */
                            .options-container {{
                                display: flex;
                                flex-wrap: wrap;
                                margin-top: 5px;
                            }}
                            .option-item {{
                                margin-right: 18px; /* 가로 여백 */
                                text-align: left; 
                                word-break: keep-all;
                            }}
                            
                            .answers-section {{ 
                                break-before: page; 
                                page-break-before: always; 
                                margin-top: 50px; 
                            }}
                            
                            .section-title {{ 
                                font-family: 'Noto Sans KR', sans-serif;
                                font-size: 14pt; 
                                font-weight: bold; 
                                text-align: center; 
                                border-bottom: 1px solid #000; 
                                padding-bottom: 10px; 
                                margin-bottom: 25px; 
                            }}
                            
                            /* 해설지 압축 포맷 */
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
                            <div class="header-sub">SDH ACADEMY Internal Exam System</div>
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
                    
                    st.success("✅ [JSON 데이터 모델링 완료] 너른터급 퀄리티의 시험지가 조립되었습니다!")
                    st.download_button("📥 상용 서비스급 고급 시험지 다운로드", data=html_content, file_name="SDH_Premium_Exam.html", mime="text/html")
                except json.JSONDecodeError as e:
                    st.error("AI가 구조화된 데이터(JSON)를 완벽하게 생성하지 못했습니다. 다시 시도해주세요.")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

# ==========================================
# 하단 푸터
# ==========================================
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH ACADEMY Internal Exam System</div>", unsafe_allow_html=True)
