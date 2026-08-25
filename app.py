import streamlit as st
import pandas as pd
import google.generativeai as genai
from xhtml2pdf import pisa
import io
import os
import urllib.request

st.set_page_config(page_title="내신 출제 플랫폼", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

font_path = "NanumGothic.ttf"
if not os.path.exists(font_path):
    urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf", font_path)

mock_db = {
    "18번": "Dear Mr. Jones,\nI am writing to you on behalf of the student council...",
    "19번": "As I walked into the dark room, my heart started to beat faster...",
    "20번": "In today's fast-paced world, it is important to take time for yourself...",
    "21번": "The concept of 'social proof' dictates how we make decisions in groups..."
}

st.title("에스디에이치어학원 통합 출제 플랫폼 🛠️")
st.markdown("---")

tab_workbook, tab_exam = st.tabs(["📚 워크북 제작", "🎯 내신 변형문제 제작"])

with tab_workbook:
    st.subheader("📖 모의고사 워크북 (개발 중)")

with tab_exam:
    st.subheader("🎯 1. 출제 범위 선택")
    exam_col1, exam_col2, exam_col3 = st.columns(3)
    with exam_col1: exam_grade = st.selectbox("대상 학년", ["고1", "고2", "고3"], index=0)
    with exam_col2: exam_year = st.selectbox("모의고사 연도", ["2026년", "2025년", "2024년"])
    with exam_col3: exam_month = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"], index=1)
        
    st.write("")
    selected_q_nums = []
    q_cols = st.columns(10)
    for i, q_num in enumerate(range(18, 22)):
        with q_cols[i % 10]:
            if st.checkbox(f"{q_num}번"): selected_q_nums.append(f"{q_num}번")

    st.markdown("---")
    st.subheader("🎯 2. 문제 유형 선택")
    selected_types = []
    type_col1, type_col2 = st.columns(2)
    with type_col1:
        if st.checkbox("어법 추론"): selected_types.append("어법 추론")
    with type_col2:
        if st.checkbox("빈칸 추론"): selected_types.append("빈칸 추론")

    st.markdown("---")
    
    if st.button("🚀 변형문제 생성 및 2단 PDF 다운로드", type="primary", use_container_width=True):
        if not selected_q_nums or not selected_types:
            st.warning("지문 번호와 문제 유형을 선택해주세요.")
        else:
            with st.spinner("가장 안전한 레이아웃으로 시험지를 인쇄 중입니다..."):
                passages_text = ""
                for q in selected_q_nums:
                    text = mock_db.get(q, f"[{q} 지문 업데이트가 필요합니다]")
                    passages_text += f"[{q}]\n{text}\n\n"

                prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 지문으로 변형 문제를 만드세요.
[선택된 문제 유형]: {', '.join(selected_types)}
[지문 목록]: {passages_text}

[출력 규칙]
1. 각 문제는 [문제시작]과 [문제끝]으로 감싸세요.
2. 지문 내용은 반드시 [박스시작]과 [박스끝] 사이에 넣으세요.
3. 선택지는 무조건 '①, ②, ③, ④, ⑤' 기호로 시작하세요.
4. 밑줄 친 부분은 반드시 <u>단어</u> 형태의 HTML 태그를 사용하세요.

[출력 포맷 예시]
[문제시작]
1. 다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?
[박스시작]
Dear Residents,
I am <u>pleased</u> to invite you.
[박스끝]
① pleased
② collecting
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
                            
                            q_html = q_html.replace('[박스시작]<br/>', '[박스시작]').replace('<br/>[박스끝]', '[박스끝]')
                            
                            # 엔진 에러를 막기 위해 table을 버리고 가장 단순한 div 박스로 변경
                            q_html = q_html.replace('[박스시작]', '<div class="simple-box">')
                            q_html = q_html.replace('[박스끝]', '</div>')
                            
                            questions_html += f"<div class='question-block'>{q_html}</div>"
                            
                            a_html = exp_part.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                            answers_html += f"<div class='answer-block'><b>[정답] {q_num_text} - {ans_part}</b><br/><b>[해설]</b> {a_html}</div>"
                        except:
                            continue

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
                                @frame col1_frame {{ left: 40pt; width: 240pt; top: 90pt; height: 690pt; }}
                                @frame col2_frame {{ left: 315pt; width: 240pt; top: 90pt; height: 690pt; }}
                                @frame footer_frame {{ -pdf-frame-content: footer_content; left: 40pt; width: 515pt; top: 805pt; height: 20pt; }}
                            }}
                            .header-line {{ border-bottom: 1.5px solid black; text-align: center; font-weight: bold; font-size: 12pt; padding-bottom: 5px; }}
                            .title {{ text-align: center; font-size: 14pt; font-weight: bold; border-bottom: 1.5px solid black; padding-bottom: 8px; }}
                            .footer-text {{ text-align: center; font-size: 9pt; color: gray; }}
                            
                            /* 에러 유발 요소를 전부 제거한 순수 테두리 박스 */
                            .simple-box {{ border: 1px solid black; padding: 10px; margin-top: 5px; margin-bottom: 10px; }}
                            .question-block {{ margin-bottom: 30px; text-align: left; }}
                            .answer-block {{ margin-bottom: 25px; text-align: left; }}
                        </style>
                    </head>
                    <body>
                        <div id="header_content"><div class="header-line">에스디에이치어학원 {header_title}</div></div>
                        <div id="footer_content"><div class="footer-text">- <pdf:pagenumber /> -<br/>SDH Premium Decoding & Internal Exam System</div></div>
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
                        st.download_button("📥 완성된 PDF 다운로드", data=pdf_file.getvalue(), file_name="SDH_최종_모의고사_수정본.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
