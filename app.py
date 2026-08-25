import streamlit as st
import pandas as pd
import google.generativeai as genai
from xhtml2pdf import pisa
import io
import os
import urllib.request

st.set_page_config(page_title="내신 출제 플랫폼", layout="wide")

# API 및 폰트 세팅
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

font_path = "NanumGothic.ttf"
if not os.path.exists(font_path):
    url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    urllib.request.urlretrieve(url, font_path)

# 공통 지문 DB
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

# [워크북 탭 코드는 어제와 동일하므로 생략 없이 그대로 유지]
with tab_workbook:
    st.subheader("📖 모의고사 워크북 검색 및 다운로드")
    col1, col2, col3, col4 = st.columns(4)
    with col1: grade_wb = st.selectbox("학년", ["고1", "고2", "고3"], index=1, key="wb_grade")
    with col2: year_wb = st.selectbox("연도", ["2026년", "2025년", "2024년", "2023년"], key="wb_year")
    with col3: month_wb = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"], key="wb_month")
    with col4:
        st.write("") 
        search_btn = st.button("🔍 자료 검색", use_container_width=True)
        
    st.markdown("---")
    if search_btn:
        st.success(f"✅ {year_wb} {month_wb} {grade_wb} 모의고사 워크북 목록을 불러왔습니다.")
        data = {
            "자료명": [f"{year_wb} {month_wb} {grade_wb} 모의고사 10단계 WORKBOOK 통합본", f"{year_wb} {month_wb} {grade_wb} 모의고사 WORKBOOK 1 지문연습", f"{year_wb} {month_wb} {grade_wb} 모의고사 WORKBOOK 2 빈칸완성"],
            "문항 수": [329, 45, 45],
            "업로드일": ["2026-08-25"] * 3
        }
        df = pd.DataFrame(data)
        df.insert(0, "선택", False)
        st.data_editor(df, column_config={"선택": st.column_config.CheckboxColumn("선택", default=False)}, disabled=["자료명", "문항 수", "업로드일"], hide_index=True, use_container_width=True)

# [변형문제 탭]
with tab_exam:
    st.subheader("🎯 1. 출제 범위 선택 (모의고사)")
    exam_col1, exam_col2, exam_col3 = st.columns(3)
    with exam_col1: exam_grade = st.selectbox("대상 학년", ["고1", "고2", "고3"], key="exam_grade_select", index=0)
    with exam_col2: exam_year = st.selectbox("모의고사 연도", ["2026년", "2025년", "2024년"], key="exam_year_select")
    with exam_col3: exam_month = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"], key="exam_month_select", index=1)
        
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
    
    if st.button("🚀 변형문제 생성 및 2단 PDF 다운로드", type="primary", use_container_width=True):
        if not selected_q_nums or not selected_types:
            st.warning("지문 번호와 문제 유형을 각각 1개 이상 선택해주세요.")
        else:
            with st.spinner("AI가 시험지를 정밀하게 디자인 중입니다..."):
                passages_text = ""
                for q in selected_q_nums:
                    text = mock_db.get(q, f"[{q} 지문 업데이트가 필요합니다]")
                    passages_text += f"[{q}]\n{text}\n\n"

                # 프롬프트 초강화 (원문자 강제)
                prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 지문으로 변형 문제를 만드세요.
[선택된 문제 유형]: {', '.join(selected_types)}
[지문 목록]: {passages_text}

[출력 규칙 - 위반 시 감점]
1. 각 문제는 반드시 [문제시작]과 [문제끝]으로 감싸세요.
2. 지문 내용은 반드시 [박스시작]과 [박스끝] 사이에 넣으세요.
3. 객관식 선택지는 예외 없이 무조건 '①, ②, ③, ④, ⑤' 기호로 시작하세요. (예: ① is scheduled)
4. 밑줄 친 부분은 반드시 <u>단어</u> 형태의 태그를 사용하세요.

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
1
[해설시작]
해설 내용
[문제끝]
'''
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    response = model.generate_content(prompt)
                    
                    raw_text = response.text.replace('```html', '').replace('```', '')
                    problems = raw_text.split('[문제끝]')
                    
                    questions_html = ""
                    answers_html = "<div class='title'>정답 및 해설</div><br/><br/>"
                    
                    for prob in problems:
                        if '[문제시작]' not in prob: continue
                        try:
                            q_main = prob.split('[문제시작]')[1].split('[정답시작]')[0].strip()
                            ans_part = prob.split('[정답시작]')[1].split('[해설시작]')[0].strip()
                            exp_part = prob.split('[해설시작]')[1].strip()
                            
                            q_num_text = q_main.split('\n')[0].strip()
                            
                            q_html = q_main.replace('<', '&lt;').replace('>', '&gt;')
                            q_html = q_html.replace('&lt;u&gt;', '<u>').replace('&lt;/u&gt;', '</u>')
                            q_html = q_html.replace('\n', '<br/>')
                            
                            # 박스 위아래 불필요한 줄바꿈 제거
                            q_html = q_html.replace('[박스시작]<br/>', '[박스시작]')
                            q_html = q_html.replace('<br/>[박스끝]', '[박스끝]')
                            
                            # 테이블 박스 치환
                            q_html = q_html.replace('[박스시작]', '<table class="passage-table"><tr><td>')
                            q_html = q_html.replace('[박스끝]', '</td></tr></table>')
                            
                            # 문제 간격(margin-bottom) 확보
                            questions_html += f"<div class='question-block'>{q_html}</div><br/><br/>"
                            
                            a_html = exp_part.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                            answers_html += f"<div class='answer-block'><b>[정답] {q_num_text} - {ans_part}</b><br/><b>[해설]</b> {a_html}</div>"
                        except:
                            continue

                    with st.spinner("헤더 침범 방지 코드를 적용하여 인쇄 중입니다..."):
                        header_title = f"{exam_year} {exam_month} {exam_grade} 모의고사 변형문제"
                        
                        html_content = f'''
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <style>
                                @font-face {{ font-family: 'NanumGothic'; src: url('{font_path}'); }}
                                body {{ font-family: 'NanumGothic'; font-size: 10pt; line-height: 1.6; color: #000000; }}
                                @page {{
                                    size: A4 portrait; margin: 0;
                                    @frame header_frame {{ -pdf-frame-content: header_content; left: 40pt; width: 515pt; top: 30pt; height: 40pt; }}
                                    /* 핵심 처방: top을 90pt로 넉넉하게 내려서 헤더와 본문 겹침 완벽 방지 */
                                    @frame col1_frame {{ left: 40pt; width: 240pt; top: 90pt; height: 690pt; }}
                                    @frame col2_frame {{ left: 315pt; width: 240pt; top: 90pt; height: 690pt; }}
                                    @frame footer_frame {{ -pdf-frame-content: footer_content; left: 40pt; width: 515pt; top: 805pt; height: 20pt; }}
                                }}
                                .header-line {{ border-bottom: 1.5px solid black; text-align: center; font-weight: bold; font-size: 12pt; padding-bottom: 5px; }}
                                .title {{ text-align: center; font-size: 14pt; font-weight: bold; border-bottom: 1.5px solid black; padding-bottom: 8px; }}
                                .footer-text {{ text-align: center; font-size: 9pt; color: gray; }}
                                
                                .passage-table {{ width: 100%; border: 1.2px solid black; margin-top: 8px; margin-bottom: 12px; }}
                                .passage-table td {{ padding: 10px; line-height: 1.5; }}
                                
                                .question-block {{ margin-bottom: 30px; text-align: left; }}
                                .answer-block {{ margin-bottom: 25px; text-align: left; }}
                            </style>
                        </head>
                        <body>
                            <div id="header_content">
                                <div class="header-line">에스디에이치어학원 {header_title}</div>
                            </div>
                            <div id="footer_content">
                                <div class="footer-text">- <pdf:pagenumber /> -<br/>SDH Premium Decoding & Internal Exam System</div>
                            </div>
                            
                            {questions_html}
                            <pdf:nextpage />
                            {answers_html}
                        </body>
                        </html>
                        '''
                        pdf_file = io.BytesIO()
                        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_file)
                        
                        if pisa_status.err:
                            st.error("PDF 생성 중 오류가 발생했습니다.")
                        else:
                            st.success("✅ 레이아웃 오류가 완벽히 수정되었습니다!")
                            st.download_button("📥 완성된 PDF 다운로드", data=pdf_file.getvalue(), file_name="SDH_최종_모의고사_수정본.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH Premium Decoding & Internal Exam System</div>", unsafe_allow_html=True)
