import streamlit as st
import pandas as pd
import google.generativeai as genai
from xhtml2pdf import pisa
import io
import os
import urllib.request

st.set_page_config(page_title="내신 출제 플랫폼", layout="wide")

# ==========================================
# 기본 세팅 (API 및 폰트)
# ==========================================
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

# ==========================================
# 탭 1: 워크북 제작 화면
# ==========================================
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

# ==========================================
# 탭 2: 내신 변형문제 출제 화면 (진짜 모의고사 양식)
# ==========================================
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
    
    if st.button("🚀 변형문제 생성 및 2단 PDF 다운로드", type="primary", use_container_width=True):
        if not selected_q_nums:
            st.warning("출제할 모의고사 지문 번호를 1개 이상 선택해주세요.")
        elif not selected_types:
            st.warning("문제 유형을 1개 이상 선택해주세요.")
        else:
            with st.spinner("AI가 가장 안정적인 2단 레이아웃으로 시험지를 설계하고 있습니다..."):
                passages_text = ""
                for q in selected_q_nums:
                    text = mock_db.get(q, f"[{q} 지문 업데이트가 필요합니다]")
                    passages_text += f"[{q}]\n{text}\n\n"

                prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 지문으로 선택된 문제 유형의 변형 문제를 만드세요.

[선택된 문제 유형]
{', '.join(selected_types)}

[지문 목록]
{passages_text}

[출력 규칙 및 필수 사항 - 매우 중요]
1. 절대 마크다운이나 HTML 태그를 사용하지 마세요.
2. 각 문제는 반드시 아래의 [출력 포맷 예시]와 100% 동일한 구조로 작성하세요.
3. 지문 내용은 반드시 "[박스시작]"과 "[박스끝]" 사이에 넣으세요.
4. 빈칸 밑줄은 반드시 `_____` (밑줄 5개)만 사용하세요.

[출력 포맷 예시]
[문제시작]
1. 다음 글의 목적으로 가장 적절한 것은?
[박스시작]
Dear Residents,
I am writing to you on behalf of the student council.
[박스끝]
① 선택지 1
② 선택지 2
③ 선택지 3
④ 선택지 4
⑤ 선택지 5
[정답시작]
1
[해설시작]
여기에 해설을 작성하세요.
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
                            # 텍스트 3등분
                            q_main = prob.split('[문제시작]')[1].split('[정답시작]')[0].strip()
                            ans_part = prob.split('[정답시작]')[1].split('[해설시작]')[0].strip()
                            exp_part = prob.split('[해설시작]')[1].strip()
                            
                            # 문제 번호 추출
                            q_num_text = q_main.split('\n')[0].strip()
                            
                            # 1. 문제지 파트 조립 (포장지를 모두 찢고 순수 텍스트로 나열)
                            q_html = q_main.replace('<', '&lt;').replace('>', '&gt;')
                            q_html = q_html.replace('\n', '<br/>')
                            
                            # 💥 핵심 처방: 지문 박스만 얇은 선으로 그리고, 전체를 감싸는 덩어리(div)는 완전히 제거
                            box_style = 'border: 0.5px solid black; padding: 10px; margin: 10px 0; background-color: #ffffff;'
                            q_html = q_html.replace('[박스시작]', f'<div style="{box_style}">')
                            q_html = q_html.replace('[박스끝]', '</div>')
                            
                            # 문제 덩어리를 묶지 않고 그대로 흘려보냄 (겹침 100% 차단)
                            questions_html += f"{q_html}<br/><br/><br/>"
                            
                            # 2. 해설지 파트 조립
                            a_html = exp_part.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                            answers_html += f"<b>[정답] {q_num_text} - {ans_part}</b><br/><b>[해설]</b> {a_html}<br/><br/><br/>"
                        except Exception as e:
                            continue

                    st.subheader("📝 생성된 시험지 텍스트 미리보기")
                    st.write(raw_text.replace('[박스시작]', '---지문 시작---').replace('[박스끝]', '---지문 끝---'))
                    
                    with st.spinner("겹침 현상을 원천 차단하고 PDF를 인쇄 중입니다..."):
                        
                        header_title = f"{exam_year} {exam_month} {exam_grade} 모의고사 변형문제"
                        
                        html_content = f'''
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <style>
                                @font-face {{ font-family: 'NanumGothic'; src: url('{font_path}'); }}
                                body {{ 
                                    font-family: 'NanumGothic'; 
                                    font-size: 10pt; 
                                    line-height: 1.5; 
                                    color: #000000; 
                                }}
                                @page {{
                                    size: A4 portrait; margin: 0;
                                    @frame header_frame {{ -pdf-frame-content: header_content; left: 40pt; width: 515pt; top: 30pt; height: 35pt; }}
                                    @frame col1_frame {{ left: 40pt; width: 240pt; top: 70pt; height: 720pt; }}
                                    @frame col2_frame {{ left: 315pt; width: 240pt; top: 70pt; height: 720pt; }}
                                    @frame footer_frame {{ -pdf-frame-content: footer_content; left: 40pt; width: 515pt; top: 805pt; height: 20pt; }}
                                }}
                                .header-line {{ border-bottom: 1.5px solid black; text-align: center; font-weight: bold; font-size: 12pt; padding-bottom: 5px; }}
                                .title {{ text-align: center; font-size: 14pt; font-weight: bold; border-bottom: 1.5px solid black; padding-bottom: 8px; }}
                                .footer-text {{ text-align: center; font-size: 9pt; color: gray; }}
                            </style>
                        </head>
                        <body>
                            <div id="header_content">
                                <div class="header-line">에스디에이치어학원 {header_title}</div>
                            </div>
                            <div id="footer_content">
                                <div class="footer-text">
                                    - <pdf:pagenumber /> -<br/>
                                    SDH Premium Decoding & Internal Exam System
                                </div>
                            </div>
                            
                            <!-- 1. 겹침 없이 물 흐르듯 자연스럽게 떨어지는 시험지 영역 -->
                            {questions_html}
                            
                            <!-- 2. 다음 페이지로 강제 분리 -->
                            <pdf:nextpage />
                            
                            <!-- 3. 해설지 영역 -->
                            {answers_html}
                        </body>
                        </html>
                        '''
                        pdf_file = io.BytesIO()
                        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_file)
                        
                        if pisa_status.err:
                            st.error("PDF 생성 중 오류가 발생했습니다.")
                        else:
                            st.success("✅ 오류가 완벽히 해결된 시험지 생성이 완료되었습니다!")
                            st.download_button("📥 완성된 PDF 다운로드", data=pdf_file.getvalue(), file_name="SDH_최종_실전모의고사.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH Premium Decoding & Internal Exam System</div>", unsafe_allow_html=True)
