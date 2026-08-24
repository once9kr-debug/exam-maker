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

# 한국어 폰트 자동 다운로드
font_path = "NanumGothic.ttf"
if not os.path.exists(font_path):
    url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    urllib.request.urlretrieve(url, font_path)

st.title("에스디에이치어학원 내신 출제 마법사")
st.markdown("---")

# 1. 모의고사 지문 데이터베이스 (향후 전체 지문으로 확장 필요)
mock_db = {
    "18번": "Dear Mr. Jones, I am writing to you on behalf of the student council... (18번 원문 텍스트)",
    "19번": "As I walked into the dark room, my heart started to beat faster... (19번 원문 텍스트)",
    "20번": "In today's fast-paced world, it is important to take time for yourself... (20번 원문 텍스트)"
}

# 2. 출제 범위 (모의고사 번호) 선택 UI
st.subheader("📚 1. 출제 범위 선택 (2026년 6월 고1 모의고사)")
selected_q_nums = []
q_cols = st.columns(8) # 화면을 8칸으로 나눔

# 18번부터 25번까지만 예시로 체크박스 생성
for i, q_num in enumerate(range(18, 26)):
    col_idx = i % 8
    with q_cols[col_idx]:
        if st.checkbox(f"{q_num}번"):
            selected_q_nums.append(f"{q_num}번")

st.markdown("---")

# 3. 문제 유형 선택 UI (체크박스 다중 선택)
st.subheader("🎯 2. 문제 유형 선택")
selected_types = []

type_col1, type_col2, type_col3, type_col4 = st.columns(4)
with type_col1:
    if st.checkbox("어법 추론"): selected_types.append("어법 추론")
    if st.checkbox("어휘 추론"): selected_types.append("어휘 추론")
with type_col2:
    if st.checkbox("빈칸 추론"): selected_types.append("빈칸 추론")
    if st.checkbox("함축 의미"): selected_types.append("함축 의미")
with type_col3:
    if st.checkbox("글의 순서"): selected_types.append("글의 순서")
    if st.checkbox("문장 삽입"): selected_types.append("문장 삽입")
with type_col4:
    if st.checkbox("서술형 영작"): selected_types.append("서술형 영작")
    if st.checkbox("주제/제목"): selected_types.append("주제/제목")

st.markdown("---")

# 4. 문제 생성 및 PDF 변환 로직
if st.button("문제 생성 및 PDF 다운로드", type="primary"):
    if not selected_q_nums:
        st.warning("출제할 모의고사 지문 번호를 선택해주세요.")
    elif not selected_types:
        st.warning("문제 유형을 1개 이상 선택해주세요.")
    else:
        with st.spinner("AI가 학원 전용 시험지를 제작하고 있습니다..."):
            
            # 선택된 번호의 원문 텍스트들을 하나로 모으기
            passages_text = ""
            for q in selected_q_nums:
                # DB에 지문이 있으면 가져오고, 없으면 안내문 삽입
                text = mock_db.get(q, f"[{q} 원문 업데이트 필요]")
                passages_text += f"[{q} 지문]\n{text}\n\n"

            # AI에게 내릴 복합 명령어 (프롬프트)
            prompt = f'''다음 제공된 모의고사 지문들을 바탕으로, 선택된 문제 유형들에 해당하는 고등학교 내신 변형 문제를 만들어주세요.

[선택된 문제 유형]
{', '.join(selected_types)}

[지문 목록]
{passages_text}

[출력 형식]
각 지문당 선택된 유형의 문제를 1개씩 만들어주세요.
문제 번호를 매기고, 문제 내용, 객관식 선택지(서술형 제외), 정답, 그리고 상세한 해설을 포함해주세요.
'''
            
            try:
                model = genai.GenerativeModel('gemini-3.6-flash')
                response = model.generate_content(prompt)
                result_text = response.text
                
                st.subheader("생성된 시험지 미리보기")
                st.write(result_text)
                
                with st.spinner("PDF를 디자인하고 있습니다..."):
                    formatted_text = result_text.replace('\n', '<br>')
                    
                    html_content = f'''
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            @font-face {{ font-family: 'NanumGothic'; src: url('{font_path}'); }}
                            body {{ font-family: 'NanumGothic'; line-height: 1.6; font-size: 13px; }}
                            h1 {{ color: #1a237e; text-align: center; border-bottom: 2px solid #1a237e; padding-bottom: 10px; }}
                            .content {{ margin-top: 20px; column-count: 2; column-gap: 30px; }}
                            .footer {{ text-align: center; margin-top: 40px; font-size: 11px; color: #7f8c8d; }}
                        </style>
                    </head>
                    <body>
                        <h1>에스디에이치어학원 모의고사 변형문제</h1>
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
                            label="📥 완성된 PDF 다운로드",
                            data=pdf_file.getvalue(),
                            file_name="SDH_변형문제.pdf",
                            mime="application/pdf"
                        )
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
