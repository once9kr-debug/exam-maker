import streamlit as st
import pandas as pd

# ==========================================
# 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="SDH ACADEMY 통합 출제 플랫폼", layout="wide")

st.title("SDH ACADEMY 통합 출제 플랫폼 🛠️")
st.markdown("---")

# ==========================================
# 메인 탭 구성
# ==========================================
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
        st.checkbox("어법 추론")
        st.checkbox("어휘 추론")
    with t_col2:
        st.checkbox("빈칸 추론")
        st.checkbox("함축 의미")
    with t_col3:
        st.checkbox("글의 순서")
        st.checkbox("문장 삽입")
    with t_col4:
        st.checkbox("서술형 영작")
        st.checkbox("주제/제목")

    st.markdown("---")
    
    # ------------------------------------------
    # 실행 버튼 (수능 포맷 레이아웃 테스트 로직)
    # ------------------------------------------
    if st.button("🚀 출력 레이아웃 테스트 (임시 데이터로 문서 생성)", type="primary", use_container_width=True):
        with st.spinner("수능 포맷에 맞춘 완벽한 2단 문서를 조립하고 있습니다..."):
            
            # 💥 수정 포인트: 가짜 데이터(Dummy)도 완벽한 수능 양식(지문 내 번호 포함)으로 변경
            dummy_response = '''
[문제시작]
1. 다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?
[박스시작]
Dear Mr. Jones,
I am writing to you on behalf of the student council. We would love to invite you ① <u>to be</u> one of our guest judges for the event. Your extensive background makes your evaluation deeply ② <u>valuable</u> to our students. The event will take place on Friday, October 20th. We would be honored to ③ <u>have</u> you join us. Please let us know ④ <u>if</u> you are able to attend. We look forward to ⑤ <u>hear</u> from you soon.
[박스끝]
[정답시작]
5
[해설시작]
look forward to의 to는 전치사이므로 동명사 hearing이 와야 합니다.
[문제끝]

[문제시작]
2. 글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?
[박스시작]
However, this reliance on familiar categories can also create cognitive biases.
[박스끝]
[박스시작]
When encountering a new situation, the human brain attempts to categorize the information based on prior experiences. ( ① ) This cognitive process helps us process complex data quickly. ( ② ) By comparing novel stimuli to existing mental schemas, the brain can make rapid predictions. ( ③ ) When we force a unique experience into an ill-fitting category, we risk ignoring subtle nuances. ( ④ ) Therefore, while mental categorization is essential for efficiency, remaining open to new perspectives is equally crucial. ( ⑤ )
[박스끝]
[정답시작]
3
[해설시작]
However로 시작하는 역접 문장이므로 장단점이 전환되는 3번 위치가 가장 적절합니다.
[문제끝]

[문제시작]
3. 다음 글의 빈칸에 들어갈 말로 가장 적절한 것은?
[박스시작]
In today's fast-paced world, it is important to take time for yourself. Constant connectivity and packed schedules often leave us feeling overwhelmed and exhausted. Pausing your daily routine allows your mind to rest, process information, and regain balance. Therefore, setting aside moments for self-care is not a luxury, but an essential component of _________________.
[박스끝]
① ignoring all daily work responsibilities
② maintaining a healthy and sustainable life
③ building a larger network of business partners
④ competing successfully against your coworkers
⑤ adapting to rapidly changing digital technologies
[정답시작]
2
[해설시작]
자기 관리를 위한 시간을 갖는 것은 건강하고 지속 가능한 삶을 유지하는 데 필수적이라는 내용입니다.
[문제끝]
'''
            
            # 파이썬 파싱 로직 
            problems = dummy_response.strip().split('[문제끝]')
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
                    
                    # 태그 보호
                    q_main_escaped = q_main.replace('<', '&lt;').replace('>', '&gt;')
                    q_main_escaped = q_main_escaped.replace('&lt;u&gt;', '<u>').replace('&lt;/u&gt;', '</u>')
                    
                    # 지문과 선택지 분리 (선택지가 없으면 빈 문자열로 처리됨)
                    last_end = q_main_escaped.rfind('[박스끝]')
                    if last_end != -1:
                        main_part = q_main_escaped[:last_end + len('[박스끝]')]
                        options_part = q_main_escaped[last_end + len('[박스끝]'):].strip()
                        
                        # 지문 내 ①, ② 존재 시 선택지 완벽 제거 (수능 포맷 대응)
                        if '①' in main_part and '②' in main_part:
                            options_part = ""
                            
                        # 박스 치환
                        main_part = main_part.replace('\n', '<br/>')
                        main_part = main_part.replace('[박스시작]<br/>', '[박스시작]').replace('<br/>[박스끝]', '[박스끝]')
                        main_part = main_part.replace('[박스시작]', '<div class="passage-box">')
                        main_part = main_part.replace('[박스끝]', '</div>')
                        
                        options_html = options_part.replace('\n', '<br/>')
                        
                        q_html = main_part
                        if options_html:
                            q_html += f'<div class="options-text">{options_html}</div>'
                    else:
                        q_html = q_main_escaped.replace('\n', '<br/>')
                    
                    valid_q_htmls.append(f"<div class='question-block'>{q_html}</div>")
                    
                    a_html = exp_part.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                    valid_a_htmls.append(f"<div class='answer-block'><b>{q_num}. [정답] {ans_part}</b><br/><b>[해설]</b> {a_html}</div>")
                except Exception as e:
                    continue

            # Flexbox 조립
            questions_final_html = '<div class="flex-container">' + "".join(valid_q_htmls) + '</div>'
            answers_final_html = '<div class="flex-container">' + "".join(valid_a_htmls) + '</div>'
            
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
                    
                    .flex-container {{
                        display: flex;
                        flex-wrap: wrap;
                        justify-content: space-between;
                    }}
                    .question-block {{ 
                        width: 48%; 
                        break-inside: avoid; 
                        page-break-inside: avoid; 
                        margin-bottom: 45px; 
                        text-align: justify; 
                        word-break: keep-all; 
                    }}
                    
                    /* 💥 수정 포인트: 박스 상하 여백을 대폭 줄여서 다중 박스가 밀착되도록 처리 */
                    .passage-box {{ 
                        border: 1.2px solid #000; 
                        padding: 10px 12px; 
                        margin: 3px 0; /* 여백 축소 */
                        background-color: #fff;
                        text-align: justify;
                        word-break: break-all;
                    }}
                    
                    .options-text {{
                        margin-top: 5px;
                        text-align: left; 
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
                        width: 48%;
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
                    <div class="header-sub">SDH ACADEMY Internal Exam System</div>
                </div>
                
                {questions_final_html}
                
                <div class="answers-section">
                    <div class="section-title">정답 및 해설</div>
                    {answers_final_html}
                </div>
            </body>
            </html>
            '''
            
            st.success("✅ 수능 포맷(지문 내 번호) 및 다중 박스 밀착 디자인이 완벽히 준비되었습니다!")
            st.download_button("📥 인쇄용 레이아웃 테스트 문서 다운로드", data=html_content, file_name="SDH_Layout_Test_CSAT.html", mime="text/html")

# ==========================================
# 하단 푸터
# ==========================================
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH ACADEMY Internal Exam System</div>", unsafe_allow_html=True)
