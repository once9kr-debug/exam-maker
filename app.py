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

# 1. 모의고사 지문 DB (테스트용)
mock_db = {
    "18번": "Dear Mr. Jones, I am writing to you on behalf of the student council...",
    "19번": "As I walked into the dark room, my heart started to beat faster...",
    "20번": "In today's fast-paced world, it is important to take time for yourself...",
    "21번": "The concept of 'social proof' dictates how we make decisions in groups...",
    "22번": "When encountering a new situation, the human brain attempts to categorize...",
    "23번": "Many ancient civilizations built their cities near major river systems...",
    "24번": "The rapid advancement of artificial intelligence has raised ethical concerns..."
}

# 2. 출제 범위 선택 UI (전체 선택 기능 추가)
st.subheader("📚 1. 출제 범위 선택 (2026년 6월 고1 모의고사)")
select_all_q = st.checkbox("✅ **전체 지문 선택**")

selected_q_nums = []
q_cols = st.columns(10) # 10칸으로 나누어 깔끔하게 배치

for i, q_num in enumerate(range(18, 46)):
    with q_cols[i % 10]:
        # 전체 선택이 체크되면 자동으로 모두 체크되도록 설정
        if st.checkbox(f"{q_num}번", value=select_all_q):
            selected_q_nums.append(f"{q_num}번")

st.markdown("---")

# 3. 문제 유형 선택 UI (전체 선택 기능 추가)
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

            # AI 프롬프트: 2단 편집에 최적화된 HTML 구조로 답변을 강제함
            prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 모의고사 지문들을 바탕으로 선택된 문제 유형의 변형 문제를 만들어주세요.

[선택된 문제 유형]
{', '.join(selected_types)}

[지문 목록]
{passages_text}

[출력 형식 및 필수 규칙]
1. 반드시 아래의 HTML 태그 구조를 그대로 사용해서 출력할 것. (절대 마크다운이나 다른 기호를 쓰지 마세요)
2. 각 문제는 <div class="question"> 태그로 감싸주세요.

<div class="question">
  <span class="q-num">Q.</span> 다음 글을 읽고, 물음에 답하시오.<br><br>
  (여기에 영어 지문 내용 삽입)<br><br>
  ① (선택지 1)<br>
  ② (선택지 2)<br>
  ③ (선택지 3)<br>
  ④ (선택지 4)<br>
  ⑤ (선택지 5)<br><br>
  <b>[정답]</b> (정답 번호)<br>
  <b>[해설]</b> (상세한 해설)
</div>
<hr>
'''
            
            try:
                model = genai.GenerativeModel('gemini-3.6-flash')
                response = model.generate_content(prompt)
                
                # AI가 가끔 시작과 끝에 ```html 을 붙이는 것을 방지
                result_text = response.text.replace('```html', '').replace('```', '')
                
                st.subheader("생성된 시험지 미리보기")
                st.markdown(result_text, unsafe_allow_html=True)
                
                with st.spinner("실제 모의고사 형태의 2단 PDF를 굽고 있습니다..."):
                    
                    # xhtml2pdf 완벽 2단 레이아웃 CSS
                    html_content = f'''
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            @font-face {{ font-family: 'NanumGothic'; src: url('{font_path}'); }}
                            
                            /* 2단 편집을 위한 페이지 프레임 설정 */
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
                                    left: 1.5cm; width: 8.2cm; top: 2.5cm; bottom: 2.5cm;
                                }}
                                @frame col2 {{
                                    left: 11.3cm; width: 8.2cm; top: 2.5cm; bottom: 2.5cm;
                                }}
                            }}
                            
                            body {{ font-family: 'NanumGothic'; font-size: 10pt; line-height: 1.6; }}
                            .title {{ text-align: center; font-size: 15pt; font-weight: bold; border-bottom: 2px solid black; padding-bottom: 8px; margin-bottom: 10px; }}
                            .question {{ margin-bottom: 30px; -pdf-keep-with-next: false; }}
                            .q-num {{ font-weight: bold; font-size: 12pt; }}
                            hr {{ color: #dddddd; margin-bottom: 20px; }}
                        </style>
                    </head>
                    <body>
                        <div id="header_content" class="title">에스디에이치어학원 내신 변형문제</div>
                        <div id="footer_content" style="text-align: center; font-size: 9pt; color: gray;">
                            SDH Premium Decoding & Internal Exam System
                        </div>
                        
                        <!-- 여기서부터 본문 내용이 col1 -> col2 -> 다음 페이지 col1 순으로 자동 분배됩니다 -->
                        {result_text}
                        
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
