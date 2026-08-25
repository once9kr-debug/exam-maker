import streamlit as st
import pandas as pd
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

st.set_page_config(page_title="내신 출제 플랫폼", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

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
    
    # 💥 워드 파일용 밑줄 변환 함수
    def add_formatted_paragraph(doc_or_cell, text):
        p = doc_or_cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        
        # <u> 태그를 워드의 실제 밑줄(Underline)로 변환하는 정밀 로직
        parts = text.split('<u>')
        for i, part in enumerate(parts):
            if i == 0:
                p.add_run(part)
            else:
                subparts = part.split('</u>')
                if len(subparts) == 2:
                    u_run = p.add_run(subparts[0])
                    u_run.underline = True
                    p.add_run(subparts[1])
                else:
                    p.add_run(part)

    if st.button("🚀 변형문제 생성 및 편집용 워드(.docx) 다운로드", type="primary", use_container_width=True):
        if not selected_q_nums or not selected_types:
            st.warning("지문 번호와 문제 유형을 각각 1개 이상 선택해주세요.")
        else:
            with st.spinner("선생님들이 편집하기 가장 편한 워드 파일 형식으로 문제를 제작 중입니다..."):
                passages_text = ""
                for q in selected_q_nums:
                    text = mock_db.get(q, f"[{q} 지문 업데이트가 필요합니다]")
                    passages_text += f"[{q}]\n{text}\n\n"

                prompt = f'''당신은 고등학교 내신 영어 출제 전문가입니다. 제공된 지문으로 변형 문제를 만드세요.
[선택된 문제 유형]: {', '.join(selected_types)}
[지문 목록]: {passages_text}

[출력 규칙]
1. 각 문제는 반드시 [문제시작]과 [문제끝]으로 감싸세요.
2. 지문 내용(삽입 문장 등)은 반드시 [박스시작]과 [박스끝] 사이에 넣으세요.
3. 객관식 선택지는 무조건 '①, ②, ③, ④, ⑤' 기호로 시작하세요.
4. 밑줄 친 부분은 반드시 <u>단어</u> 형태의 태그를 사용하세요. 빈칸은 밑줄 5개(_____)로 표시하세요.
5. [정답시작] 아래에는 오직 '정답 번호' 또는 '서술형 정답'만 적으세요.

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
해설 작성.
[문제끝]
'''
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    response = model.generate_content(prompt)
                    raw_text = response.text.replace('```html', '').replace('```', '')
                    problems = raw_text.split('[문제끝]')
                    
                    # 💥 워드 문서 객체 생성
                    doc = Document()
                    
                    # 헤더 스타일
                    header_title = f"에스디에이치어학원 {exam_year} {exam_month} {exam_grade} 모의고사 변형문제"
                    h = doc.add_heading(header_title, level=1)
                    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    
                    sub = doc.add_paragraph("SDH Premium Decoding & Internal Exam System")
                    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    doc.add_paragraph("_" * 60) # 구분선
                    
                    answers_data = []
                    
                    for prob in problems:
                        if '[문제시작]' not in prob: continue
                        try:
                            q_main = prob.split('[문제시작]')[1].split('[정답시작]')[0].strip()
                            ans_part = prob.split('[정답시작]')[1].split('[해설시작]')[0].strip()
                            exp_part = prob.split('[해설시작]')[1].strip()
                            
                            first_line = q_main.split('\n')[0].strip()
                            q_num = first_line.split('.')[0] if '.' in first_line else "★"
                            
                            # 중복 선택지 제거 로직
                            last_end = q_main.rfind('[박스끝]')
                            if last_end != -1:
                                main_part = q_main[:last_end + len('[박스끝]')]
                                options_part = q_main[last_end + len('[박스끝]'):].strip()
                                
                                if '①' in main_part and '②' in main_part:
                                    options_part = ""
                                
                                # 문제 본문 (박스 전)
                                pre_box = main_part.split('[박스시작]')[0].strip()
                                if pre_box:
                                    add_formatted_paragraph(doc, pre_box)
                                
                                # 💥 워드 표(Table) 기능을 이용한 지문 박스 생성
                                box_content = main_part.split('[박스시작]')[1].split('[박스끝]')[0].strip()
                                table = doc.add_table(rows=1, cols=1)
                                table.style = 'Table Grid'
                                cell = table.cell(0, 0)
                                for line in box_content.split('\n'):
                                    add_formatted_paragraph(cell, line)
                                
                                doc.add_paragraph("") # 박스와 선택지 사이 여백
                                
                                # 선택지 출력
                                if options_part:
                                    for opt_line in options_part.split('\n'):
                                        if opt_line.strip():
                                            doc.add_paragraph(opt_line.strip())
                            else:
                                for line in q_main.split('\n'):
                                    add_formatted_paragraph(doc, line)
                            
                            doc.add_paragraph("\n") # 문제 사이 여백
                            answers_data.append((q_num, ans_part, exp_part))
                            
                        except Exception as e:
                            continue
                            
                    # 정답 및 해설 페이지 강제 넘김
                    doc.add_page_break()
                    ans_title = doc.add_heading("정답 및 해설", level=2)
                    ans_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    doc.add_paragraph("_" * 60)
                    
                    for q_num, ans, exp in answers_data:
                        ans_p = doc.add_paragraph()
                        ans_p.add_run(f"{q_num}. [정답] {ans}").bold = True
                        
                        exp_p = doc.add_paragraph()
                        exp_p.add_run("[해설] ").bold = True
                        exp_p.add_run(exp)
                        doc.add_paragraph("")
                    
                    # 워드 파일을 메모리에 저장하여 다운로드 버튼에 연결
                    word_file = io.BytesIO()
                    doc.save(word_file)
                    word_file.seek(0)
                    
                    st.success("✅ 선생님들이 수정하기 편한 워드 파일이 완성되었습니다!")
                    st.download_button(
                        label="📥 편집용 워드 파일(.docx) 다운로드",
                        data=word_file,
                        file_name="SDH_실전모의고사_편집용.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH Premium Decoding & Internal Exam System</div>", unsafe_allow_html=True)
