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

# 한국어 폰트 자동 다운로드 (PDF 한글 깨짐 방지)
font_path = "NanumGothic.ttf"
if not os.path.exists(font_path):
    url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    urllib.request.urlretrieve(url, font_path)

st.title("에스디에이치어학원 내신 변형문제 자동 생성기")

passage = st.text_area("지문을 입력하세요 (영어 원문):", height=200)
q_type = st.selectbox("문제 유형 선택:", ["어법 추론", "빈칸 추론", "글의 순서 배열", "문장 삽입"])

if st.button("문제 생성 및 PDF 다운로드"):
    if not passage.strip():
        st.warning("지문을 입력해주세요.")
    else:
        with st.spinner("AI가 문제를 생성하고 있습니다..."):
            prompt = f'''다음 영어 지문을 바탕으로 고등학교 내신 스타일의 '{q_type}' 문제를 1개 만들어주세요.
[문제]
(문제 내용 및 선택지)
[정답]
(정답 번호)
[해설]
(상세한 해설)

지문: {passage}'''
            
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(prompt)
                result_text = response.text
                
                st.subheader("생성된 문제")
                st.write(result_text)
                
                with st.spinner("PDF를 디자인하고 있습니다..."):
                    # 줄바꿈 문자를 HTML 태그로 변환
                    formatted_text = result_text.replace('\n', '<br>')
                    
                    # xhtml2pdf용 HTML/CSS 템플릿
                    html_content = f'''
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            @font-face {{
                                font-family: 'NanumGothic';
                                src: url('{font_path}');
                            }}
                            body {{
                                font-family: 'NanumGothic';
                                line-height: 1.6;
                                font-size: 14px;
                            }}
                            h1 {{
                                color: #2c3e50;
                                text-align: center;
                                border-bottom: 2px solid #2c3e50;
                                padding-bottom: 10px;
                            }}
                            .content {{
                                margin-top: 20px;
                            }}
                            .footer {{
                                text-align: center;
                                margin-top: 40px;
                                font-size: 11px;
                                color: #7f8c8d;
                            }}
                        </style>
                    </head>
                    <body>
                        <h1>에스디에이치어학원 변형문제</h1>
                        <div class="content">{formatted_text}</div>
                        <div class="footer">SDH Premium Decoding & Internal Exam System</div>
                    </body>
                    </html>
                    '''
                    
                    pdf_file = io.BytesIO()
                    pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_file)
                    
                    if pisa_status.err:
                        st.error("PDF 생성 중 오류가 발생했습니다.")
                    else:
                        st.download_button(
                            label="📥 PDF 다운로드",
                            data=pdf_file.getvalue(),
                            file_name="변형문제.pdf",
                            mime="application/pdf"
                        )
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
