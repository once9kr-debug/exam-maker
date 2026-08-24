import streamlit as st
import google.generativeai as genai
import pdfkit

st.set_page_config(page_title="내신 변형문제 생성기", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

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
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            result_text = response.text
            
            st.subheader("생성된 문제")
            st.write(result_text)
            
            with st.spinner("PDF를 생성하고 있습니다..."):
                html_content = f'''
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: sans-serif; line-height: 1.6; margin: 40px; }}
                        h1 {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
                        .container {{ column-count: 2; column-gap: 40px; }}
                        .content {{ white-space: pre-wrap; font-size: 14px; }}
                        .footer {{ text-align: center; margin-top: 50px; font-size: 12px; color: #7f8c8d; }}
                    </style>
                </head>
                <body>
                    <h1>에스디에이치어학원 변형문제</h1>
                    <div class="container">
                        <div class="content">{result_text}</div>
                    </div>
                    <div class="footer">SDH Premium Decoding & Internal Exam System</div>
                </body>
                </html>
                '''
                try:
                    pdf_bytes = pdfkit.from_string(html_content, False, options={'encoding': 'UTF-8'})
                    st.download_button(label="📥 PDF 다운로드", data=pdf_bytes, file_name="변형문제.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"PDF 변환 에러 (wkhtmltopdf 설치 확인 필요): {e}")
