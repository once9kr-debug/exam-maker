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

# 공통 지문 DB (임시 샘플)
mock_db = {
    "18번": "Dear Mr. Jones, I am writing to you on behalf of the student council...",
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
        grade = st.selectbox("학년", ["고1", "고2", "고3"], index=1)
    with col2:
        year = st.selectbox("연도", ["2026년", "2025년", "2024년", "2023년"])
    with col3:
        month = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"])
    with col4:
        st.write("") 
        search_btn = st.button("🔍 자료 검색", use_container_width=True)
        
    st.markdown("---")
    
    if search_btn:
        st.success(f"✅ {year} {month} {grade} 모의고사 워크북 목록을 불러왔습니다.")
        data = {
            "자료명": [
                f"{year} {month} {grade} 모의고사 10단계 WORKBOOK 통합본",
                f"{year} {month} {grade} 모의고사 WORKBOOK 1 지문연습",
                f"{year} {month} {grade} 모의고사 WORKBOOK 2 빈칸완성",
                f"{year} {month} {grade} 모의고사 WORKBOOK 3 해석연습",
                f"{year} {month} {grade} 모의고사 WORKBOOK 4 순서배열"
            ],
            "문항 수": [329, 45, 45, 45, 45],
            "업로드일": ["2026-08-25"] * 5
        }
        df = pd.DataFrame(data)
        df.insert(0, "선택", False)
        
        edited_df = st.data_editor(
            df,
            column_config={"선택": st.column_config.CheckboxColumn("선택", default=False)},
            disabled=["자료명", "문항 수", "업로드일"],
            hide_index=True,
            use_container_width=True
        )
        if st.button("📥 선택 파일 다운로드 (테스트)", type="primary"):
            st.info("선택하신 워크북 파일이 다운로드 되었습니다!")

# ==========================================
# 탭 2: 내신 변형문제 출제 화면
# ==========================================
with tab_exam:
    st.subheader("🎯 1. 출제 범위 선택 (모의고사)")
    
    exam_col1, exam_col2, exam_col3 = st.columns(3)
    with exam_col1:
        st.selectbox("대상 학년", ["고1", "고2", "고3"], key="exam_grade", index=1)
    with exam_col2:
        st.selectbox("모의고사 연도", ["2026년", "2025년", "2024년"], key="exam_year")
    with exam_col3:
        st.selectbox("시행 월", ["3월", "6월", "9월", "11월"], key="exam_month", index=1)
        
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
            with st.spinner("AI가 SDH Premium 스타일의 시험지를 제작하고 있습니다..."):
                passages_text = ""
                for q in selected_q_nums:
                    text = mock_db.get(q, f"[{q} 지문 업데이트가 필요합니다]")
                    passages_text += f"[{q}]\n{text}\n\n"

                prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 지문으로 선택된 문제 유형의 변형 문제를 만드세요.

[선택된 문제 유형]
{', '.join(selected_types)}

[지문 목록]
{passages_text}

[출력 규칙 및 필수 사항]
1. 마크다운이나 HTML 태그를 절대 쓰지 마세요.
2. 각 문제 끝에 반드시 "---문제구분선---" 을 넣어주세요.
3. 빈칸을 만들 때 밑줄은 반드시 `_____` (밑줄 5개)만 사용하세요.
4. 선택지는 반드시 원문자(①, ②, ③, ④, ⑤)를 사용하세요.

출력 예시:
Q1. 다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?
(지문 내용)
① 선택지내용
② 선택지내용
[정답] 1
[해설] 해설내용
---문제구분선---
'''
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    response = model.generate_content(prompt)
                    
                    raw_text = response.text.replace('```html', '').replace('```', '')
                    problems = raw_text.split('---문제구분선---')
                    
                    st.subheader("📝 생성된 시험지 미리보기")
                    st.write(raw_text.replace('---문제구분선---', '\n\n---\n\n'))
                    
                    with st.spinner("2단 모의고사 포맷으로 정밀 인쇄 중입니다..."):
                        
                        # 💥 핵심 처방: 엔진이 소화 불량에 걸리지 않도록 가장 단순하고 안전한 구조로 변경
                        formatted_problems_html = ""
                        for prob in problems:
                            if prob.strip():
                                clean_text = prob.strip().replace('<', '&lt;').replace('>', '&gt;')
                                # 모든 줄바꿈을 안전한 <br/> 태그로 일괄 변경
                                clean_text = clean_text.replace('\n', '<br/>')
                                clean_text = clean_text.replace('[정답]', '<br/><br/><b>[정답]</b>')
                                clean_text = clean_text.replace('[해설]', '<br/><b>[해설]</b>')
                                
                                formatted_problems_html += f'<div class="question">{clean_text}</div><br/>'
                        
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
                                    word-wrap: break-word; 
                                    -pdf-word-wrap: CJK;
                                }}
                                @page {{
                                    size: A4 portrait; margin: 0;
                                    @frame header_frame {{ -pdf-frame-content: header_content; left: 40pt; width: 515pt; top: 30pt; height: 30pt; }}
                                    @frame col1_frame {{ left: 40pt; width: 245pt; top: 75pt; height: 715pt; }}
                                    @frame col2_frame {{ left: 310pt; width: 245pt; top: 75pt; height: 715pt; }}
                                    @frame footer_frame {{ -pdf-frame-content: footer_content; left: 40pt; width: 515pt; top: 800pt; height: 20pt; }}
                                }}
                                .title {{ text-align: center; font-size: 14pt; font-weight: bold; border-bottom: 1.5px solid black; padding-bottom: 8px; }}
                                .footer-text {{ text-align: center; font-size: 9pt; color: gray; }}
                                .question {{ margin-bottom: 25px; text-align: justify; }}
                            </style>
                        </head>
                        <body>
                            <div id="header_content"><div class="title">에스디에이치어학원 모의고사 변형문제</div></div>
                            <div id="footer_content"><div class="footer-text">SDH Premium Decoding & Internal Exam System</div></div>
                            {formatted_problems_html}
                        </body>
                        </html>
                        '''
                        pdf_file = io.BytesIO()
                        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_file)
                        
                        if pisa_status.err:
                            st.error("PDF 생성 중 오류가 발생했습니다.")
                        else:
                            st.success("✅ 학원 전용 시험지 생성이 완료되었습니다!")
                            st.download_button("📥 완성된 PDF 다운로드", data=pdf_file.getvalue(), file_name="SDH_모의고사_변형문제.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH Premium Decoding & Internal Exam System</div>", unsafe_allow_html=True)
