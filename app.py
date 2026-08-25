import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="내신 출제 플랫폼", layout="wide")

# ==========================================
# 기본 세팅 (API)
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

# 공통 지문 DB (임시 샘플)
mock_db = {
    "18번": "Dear Mr. Jones,\nI am writing to you on behalf of the student council...",
    "19번": "As I walked into the dark room, my heart started to beat faster...",
    "20번": "In today's fast-paced world, it is important to take time for yourself...",
    "21번": "The concept of 'social proof' dictates how we make decisions in groups...",
    "22번": "When encountering a new situation, the human brain attempts to categorize...",
    "23번": "Many ancient civilizations built their cities near major river systems...",
    "24번": "The rapid advancement of artificial intelligence has raised ethical concerns..."
}

st.title("에스디에이치어학원 통합 출제 플랫폼 🛠️")
st.markdown("---")

tab_workbook, tab_exam = st.tabs(["📚 워크북 제작", "🎯 내신 변형문제 제작"])

with tab_workbook:
    st.subheader("📖 모의고사 워크북 검색 및 다운로드")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        grade_wb = st.selectbox("학년", ["고1", "고2", "고3"], index=1, key="wb_grade")
    with col2:
        year_wb = st.selectbox("연도", ["2026년", "2025년", "2024년", "2023년"], key="wb_year")
    with col3:
        month_wb = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"], key="wb_month")
    with col4:
        st.write("") 
        search_btn = st.button("🔍 자료 검색", use_container_width=True)
        
    st.markdown("---")
    
    if search_btn:
        st.success(f"✅ {year_wb} {month_wb} {grade_wb} 모의고사 워크북 목록을 불러왔습니다.")
        data = {
            "자료명": [
                f"{year_wb} {month_wb} {grade_wb} 모의고사 10단계 WORKBOOK 통합본",
                f"{year_wb} {month_wb} {grade_wb} 모의고사 WORKBOOK 1 지문연습",
                f"{year_wb} {month_wb} {grade_wb} 모의고사 WORKBOOK 2 빈칸완성"
            ],
            "문항 수": [329, 45, 45],
            "업로드일": ["2026-08-25"] * 3
        }
        df = pd.DataFrame(data)
        df.insert(0, "선택", False)
        st.data_editor(df, column_config={"선택": st.column_config.CheckboxColumn("선택", default=False)}, disabled=["자료명", "문항 수", "업로드일"], hide_index=True, use_container_width=True)

with tab_exam:
    st.subheader("🎯 1. 출제 범위 선택 (모의고사)")
    
    exam_col1, exam_col2, exam_col3 = st.columns(3)
    with exam_col1:
        exam_grade = st.selectbox("대상 학년", ["고1", "고2", "고3"], key="exam_grade_select", index=0)
    with exam_col2:
        exam_year = st.selectbox("모의고사 연도", ["2026년", "2025년", "2024년"], key="exam_year_select")
    with exam_col3:
        exam_month = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"], key="exam_month_select", index=1)
        
    st.write("")
    select_all_q = st.checkbox("✅ **전체 지문 선택**", key="exam_all_q")
    selected_q_nums = []
    q_cols = st.columns(10)
    for i, q_num in enumerate(range(18, 46)):
        with q_cols[i % 10]:
            if st.checkbox(f"{q_num}번", value=select_all_q, key=f"q_{q_num}"):
                selected_q_nums.append(f"{q_num}번")

    st.markdown("---")
    
    st.subheader("🎯 2. 문제 유형 선택")
    select_all_types = st.checkbox("✅ **전체 유형 선택**", key="exam_all_types")
    selected_types = []
    type_col1, type_col2, type_col3, type_col4 = st.columns(4)

    with type_col1:
        if st.checkbox("어법 추론", value=select_all_types): selected_types.append("어법 추론")
        if st.checkbox("어휘 추론", value=select_all_types): selected_types.append("어휘 추론")
    with type_col2:
        if st.checkbox("빈칸 추론", value=select_all_types): selected_types.append("빈칸 추론")
        if st.checkbox("함축 의미", value=select_all_types): selected_types.append("함축 의미")
    with type_col3:
        if st.checkbox("글의 순서", value=select_all_types): selected_types.append("글의 순서")
        if st.checkbox("문장 삽입", value=select_all_types): selected_types.append("문장 삽입")
    with type_col4:
        if st.checkbox("서술형 영작", value=select_all_types): selected_types.append("서술형 영작")
        if st.checkbox("주제/제목", value=select_all_types): selected_types.append("주제/제목")

    st.markdown("---")
    
    if st.button("🚀 변형문제 생성 및 인쇄용 웹 문서(HTML) 다운로드", type="primary", use_container_width=True):
        if not selected_q_nums or not selected_types:
            st.warning("지문 번호와 문제 유형을 각각 1개 이상 선택해주세요.")
        else:
            with st.spinner("AI가 가장 자연스러운 레이아웃으로 시험지를 조립하고 있습니다..."):
                passages_text = ""
                for q in selected_q_nums:
                    text = mock_db.get(q, f"[{q} 지문 업데이트가 필요합니다]")
                    passages_text += f"[{q}]\n{text}\n\n"

                prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 지문으로 변형 문제를 만드세요.
[선택된 문제 유형]: {', '.join(selected_types)}
[지문 목록]: {passages_text}

[출력 규칙 - 매우 엄격함]
1. 각 문제는 반드시 [문제시작]과 [문제끝]으로 감싸세요.
2. 지문 내용(삽입 문장 포함)은 반드시 [박스시작]과 [박스끝] 사이에 넣으세요.
3. 객관식 선택지는 예외 없이 무조건 '①, ②, ③, ④, ⑤' 기호로 시작하세요.
4. 밑줄 친 부분은 반드시 <u>단어</u> 형태의 HTML 태그를 사용하세요. 빈칸은 밑줄 5개(_____)로 표시하세요.
5. [정답시작] 아래에는 오직 '정답 번호(숫자)' 또는 '서술형 정답'만 간결하게 적으세요.

[출력 포맷 예시]
[문제시작]
1. 다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?
[박스시작]
Dear Residents,
I am <u>pleased</u> to invite you.
[박스끝]
① pleased
② collecting
③ donating
④ condition
⑤ while
[정답시작]
4
[해설시작]
여기에 해설을 작성하세요.
[문제끝]
'''
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    response = model.generate_content(prompt)
                    
                    raw_text = response.text.replace('```html', '').replace('```', '')
                    problems = raw_text.split('[문제끝]')
                    
                    valid_q_htmls = []
                    valid_a_htmls = []
                    
                    for prob in problems:
                        if '[문제시작]' not in prob: continue
                        try:
                            q_main = prob.split('[문제시작]')[1].split('[정답시작]')[0].strip()
                            ans_part = prob.split('[정답시작]')[1].split('[해설시작]')[0].strip()
                            exp_part = prob.split('[해설시작]')[1].strip()
                            
                            first_line = q_main.split('\n')[0].strip()
                            q_num = first_line.split('.')[0] if '.' in first_line else "★"
                            
                            # 중복 선택지 제거 로직
                            last_box_end_idx = q_main.rfind('[박스끝]')
                            if last_box_end_idx != -1:
                                text_before_options = q_main[:last_box_end_idx]
                                if '①' in text_before_options and '②' in text_before_options:
                                    q_main = q_main[:last_box_end_idx + len('[박스끝]')]
                            
                            # 태그 보호 로직
                            q_main_escaped = q_main.replace('<', '&lt;').replace('>', '&gt;')
                            q_main_escaped = q_main_escaped.replace('&lt;u&gt;', '<u>').replace('&lt;/u&gt;', '</u>')
                            q_main_escaped = q_main_escaped.replace('&lt;U&gt;', '<u>').replace('&lt;/U&gt;', '</u>')
                            
                            # 옵션 분리 및 HTML 조립
                            if '[박스끝]' in q_main_escaped:
                                pre_box = q_main_escaped.split('[박스시작]')[0].strip()
                                box_content = q_main_escaped.split('[박스시작]')[1].split('[박스끝]')[0].strip()
                                options_content = q_main_escaped.split('[박스끝]')[1].strip()
                                
                                pre_box_html = pre_box.replace('\n', '<br/>')
                                box_content_html = box_content.replace('\n', '<br/>')
                                options_content_html = options_content.replace('\n', '<br/>')
                                
                                q_html = f"{pre_box_html}"
                                q_html += f'<div class="passage-box">{box_content_html}</div>'
                                if options_content_html:
                                    # 💥 수정 포인트: 선택지 전용 클래스 적용 (왼쪽 정렬을 위함)
                                    q_html += f'<div class="options-text">{options_content_html}</div>'
                            else:
                                q_html = q_main_escaped.replace('\n', '<br/>')
                            
                            valid_q_htmls.append(f"<div class='question-block'>{q_html}</div>")
                            
                            a_html = exp_part.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                            valid_a_htmls.append(f"<div class='answer-block'><b>{q_num}. [정답] {ans_part}</b><br/><b>[해설]</b> {a_html}</div>")
                        except Exception as e:
                            continue

                    # 💥 수정 포인트: 억지로 4개씩 끊지 않고 통으로 묶어서 브라우저 자연 흐름에 맡김
                    questions_final_html = '<div class="two-column-layout">' + "".join(valid_q_htmls) + '</div>'
                    answers_final_html = '<div class="two-column-layout">' + "".join(valid_a_htmls) + '</div>'

                    header_title = f"{exam_year} {exam_month} {exam_grade} 모의고사 변형문제"
                    
                    html_content = f'''
                    <!DOCTYPE html>
                    <html lang="ko">
                    <head>
                        <meta charset="utf-8">
                        <title>{header_title}</title>
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
                            body {{ 
                                font-family: 'Noto Sans KR', sans-serif; 
                                font-size: 10.5pt; 
                                line-height: 1.5; 
                                color: #000; 
                                max-width: 210mm;
                                margin: 0 auto;
                                padding: 20px;
                            }}
                            
                            .header-container {{ 
                                text-align: center;
                                border-bottom: 2px solid #000; 
                                padding-bottom: 15px; 
                                margin-bottom: 25px; 
                            }}
                            .header-title {{ font-size: 16pt; font-weight: bold; margin-bottom: 5px; }}
                            .header-sub {{ font-size: 10pt; color: #555; }}
                            
                            .two-column-layout {{
                                column-count: 2;
                                column-gap: 30px;
                            }}
                            
                            .question-block {{ 
                                break-inside: avoid; 
                                page-break-inside: avoid; 
                                margin-bottom: 55px; /* 💥 수정 포인트: 문제 간격 대폭 확대 */
                                text-align: justify; 
                                word-break: keep-all; 
                            }}
                            
                            .passage-box {{ 
                                border: 1.2px solid #000; 
                                padding: 10px 12px; 
                                margin: 5px 0; 
                                background-color: #fff;
                                text-align: justify;
                                word-break: break-all;
                            }}
                            
                            .options-text {{
                                margin-top: 5px;
                                text-align: left; /* 💥 수정 포인트: 선택지는 왼쪽 정렬 고정 (자간 벌어짐 방지) */
                                word-break: keep-all;
                            }}
                            
                            .answers-section {{ 
                                break-before: page; 
                                page-break-before: always; 
                                margin-top: 50px; 
                            }}
                            .section-title {{ 
                                font-size: 15pt; 
                                font-weight: bold; 
                                text-align: center; 
                                border-bottom: 1px solid #000; 
                                padding-bottom: 10px; 
                                margin-bottom: 25px; 
                            }}
                            .answer-block {{ 
                                break-inside: avoid; 
                                page-break-inside: avoid;
                                margin-bottom: 35px; 
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
                            <div class="header-title">에스디에이치어학원 {header_title}</div>
                            <div class="header-sub">SDH Premium Decoding & Internal Exam System</div>
                        </div>
                        
                        <!-- 💥 물 흐르듯 자연스럽게 2단으로 넘어가는 시험지 -->
                        {questions_final_html}
                        
                        <div class="answers-section">
                            <div class="section-title">정답 및 해설</div>
                            <!-- 해설지도 자연스러운 2단 흐름 유지 -->
                            {answers_final_html}
                        </div>
                    </body>
                    </html>
                    '''
                    
                    st.success("✅ 간격 조정 및 자연스러운 페이지 배치 로직이 완벽하게 적용되었습니다!")
                    st.download_button("📥 인쇄용 웹 문서(HTML) 다운로드", data=html_content, file_name="SDH_실전모의고사_레이아웃최적화.html", mime="text/html")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH Premium Decoding & Internal Exam System</div>", unsafe_allow_html=True)
