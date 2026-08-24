import streamlit as st
import google.generativeai as genai
from xhtml2pdf import pisa
import io
import os
import urllib.request

st.set_page_config(page_title="내신 변형문제 생성기", layout="wide")

# API 키 설정
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

# 한국어 폰트 세팅
font_path = "NanumGothic.ttf"
if not os.path.exists(font_path):
    url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    urllib.request.urlretrieve(url, font_path)

st.title("에스디에이치어학원 내신 출제 마법사")
st.markdown("---")

# 1. 모의고사 지문 DB
mock_db = {
    "18번": "Dear Mr. Jones, I am writing to you on behalf of the student council...",
    "19번": "As I walked into the dark room, my heart started to beat faster...",
    "20번": "In today's fast-paced world, it is important to take time for yourself...",
    "21번": "The concept of 'social proof' dictates how we make decisions in groups...",
    "22번": "When encountering a new situation, the human brain attempts to categorize...",
    "23번": "Many ancient civilizations built their cities near major river systems...",
    "24번": "The rapid advancement of artificial intelligence has raised ethical concerns..."
}

# 2. 출제 범위 선택 UI
st.subheader("📚 1. 출제 범위 선택 (2026년 6월 고1 모의고사)")
select_all_q = st.checkbox("✅ **전체 지문 선택**")

selected_q_nums = []
q_cols = st.columns(10)

for i, q_num in enumerate(range(18, 46)):
    with q_cols[i % 10]:
        if st.checkbox(f"{q_num}번", value=select_all_q):
            selected_q_nums.append(f"{q_num}번")

st.markdown("---")

# 3. 문제 유형 선택 UI
st.subheader("🎯 2. 문제 유형 선택")
select_all_types = st.checkbox("✅ **전체 유형 선택**")

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

# 4. 문제 생성 및 고급 2단 PDF 변환 로직
if st.button("문제 생성 및 PDF 다운로드", type="primary"):
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

            # 프롬프트: AI가 HTML을 쓰지 못하도록 원천 차단하고 텍스트만 받음
            prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 모의고사 지문들을 바탕으로 선택된 문제 유형의 변형 문제를 만들어주세요.

[선택된 문제 유형]
{', '.join(selected_types)}

[지문 목록]
{passages_text}

[출력 규칙 및 필수 사항] (매우 중요)
1. 절대 마크다운(```)이나 HTML 태그(table, div 등)를 사용하지 마세요. 오직 순수 텍스트만 작성하세요.
2. 각 문제가 끝날 때마다 반드시 "---문제구분선---" 이라는 텍스트를 정확하게 넣어주세요.

출력 예시:
Q1. 다음 글을 읽고...
(지문 내용)
① 번 선택지
② 번 선택지
[정답] 1
[해설] 해설 내용입니다.
---문제구분선---
Q2. 다음 중 어법상...
'''
            
            try:
                model = genai.GenerativeModel('gemini-3.6-flash')
                response = model.generate_content(prompt)
                
                # AI 답변에서 HTML 찌꺼기를 제거하고 문제별로 자르기
                raw_text = response.text.replace('```html', '').replace('```', '')
                problems = raw_text.split('---문제구분선---')
                
                st.subheader("생성된 시험지 미리보기")
                st.write(raw_text.replace('---문제구분선---', '\n\n---\n\n'))
                
                with st.spinner("실제 모의고사 형태의 2단 PDF를 굽고 있습니다..."):
                    
                    # 파이썬이 직접 안전한 HTML로 조립
                    formatted_problems_html = ""
                    for prob in problems:
                        if prob.strip():
                            # 태그 꼬임 방지를 위한 안전 처리
                            clean_text = prob.strip().replace('<', '&lt;').replace('>', '&gt;')
                            clean_text = clean_text.replace('\n', '<br>')
                            formatted_problems_html += f'<div class="question">{clean_text}</div>'
                    
                    # xhtml2pdf 완벽 2단 레이아웃 CSS (줄간격/여백 안정화)
                    html_content = f'''
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            @font-face {{ font-family: 'NanumGothic'; src: url('{font_path}'); }}
                            
                            @page {{
                                size: A4;
                                margin: 0;
                                @frame header {{
                                    -pdf-frame-content: header_content;
                                    top: 1cm; left: 1.5cm; right: 1.5cm; height: 1cm;
                                }}
                                @frame footer {{
                                    -pdf-frame-content: footer_content;
                                    bottom: 1cm; left: 1.5cm; right: 1.5cm; height: 1cm;
                                }}
                                @frame col1 {{
                                    left: 1.5cm; width: 8.5cm; top: 2.5cm; bottom: 2.5cm;
                                }}
                                @frame col2 {{
                                    left: 11cm; width: 8.5cm; top: 2.5cm; bottom: 2.5cm;
                                }}
                            }}
                            
                            body {{ 
                                font-family: 'NanumGothic'; 
                                font-size: 10pt; 
                                line-height: 1.5; 
                            }}
                            .title {{ 
                                text-align: center; 
                                font-size: 14pt; 
                                font-weight: bold; 
                                border-bottom: 1px solid black; 
                                padding-bottom: 5px; 
                            }}
                            .question {{ 
                                margin-bottom: 25px; 
                                text-align: justify;
                            }}
                        </style>
                    </head>
                    <body>
                        <div id="header_content" class="title">에스디에이치어학원 내신 변형문제</div>
                        <div id="footer_content" style="text-align: center; font-size: 9pt; color: gray;">
                            SDH Premium Decoding & Internal Exam System
                        </div>
                        
                        <!-- 조립된 문제들이 1단 -> 2단 순서로 안전하게 흘러들어갑니다 -->
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
                        st.download_button(
                            label="📥 완성된 PDF 다운로드",
                            data=pdf_file.getvalue(),
                            file_name="SDH_모의고사_변형문제.pdf",
                            mime="application/pdf"
                        )
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
