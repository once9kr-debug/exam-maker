import streamlit as st
import sqlite3
import pandas as pd
import json
import docx
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from io import BytesIO
import google.generativeai as genai # AI 엔진 라이브러리 추가

# ==========================================
# 1. 페이지 설정 및 세션 상태 초기화
# ==========================================
st.set_page_config(page_title="SDH STUDIO", layout="wide", initial_sidebar_state="expanded")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "current_page" not in st.session_state: st.session_state.current_page = "list"

if "f_grade" not in st.session_state: st.session_state.f_grade = "고2"
if "f_year" not in st.session_state: st.session_state.f_year = "2026"
if "f_month" not in st.session_state: st.session_state.f_month = "6월"

# ==========================================
# CSS 스타일링
# ==========================================
st.markdown("""
<style>
    .sdh-logo { font-size: 24px; font-weight: 900; color: #2C3E50; margin-bottom: 20px; text-align: center; border: 1px solid #2C3E50; padding: 20px 0;}
    .disabled-menu { background-color: #D5D8DC; color: #5D6D7E; padding: 15px; text-align: center; border: 1px solid #ABB2B9; margin-bottom: 5px; }
    .active-menu { background-color: #F8F9F9; color: #2C3E50; padding: 15px; text-align: center; border: 1px solid #2C3E50; font-weight: bold; margin-bottom: 5px; }
    .filter-box { border: 1px solid #5D6D7E; border-radius: 10px; padding: 20px; margin-bottom: 30px; }
    .filter-label { font-size: 16px; font-weight: bold; text-align: center; padding: 5px; border: 1px solid #5D6D7E; }
    .tbl-header { background-color: #4A90E2; color: white; text-align: center; padding: 8px; font-weight: bold; font-size: 16px; border: 1px solid #fff;}
    .tbl-cell { text-align: center; padding: 12px 5px; font-size: 15px; background-color: #EBF5FB; border-bottom: 1px solid #fff;}
    .tbl-cell-alt { text-align: center; padding: 12px 5px; font-size: 15px; background-color: #D6EAF8; border-bottom: 1px solid #fff;}
    .exam4you-viewer { column-count: 2; column-gap: 40px; column-rule: 1px solid #ddd; background-color: white; padding: 40px; border: 1px solid #ccc; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); font-family: 'Nanum Myeongjo', serif; }
    .question-box { break-inside: avoid; margin-bottom: 30px; }
    .q-title { font-weight: bold; color: #009688; margin-bottom: 10px; }
    .q-passage { border: 1px solid #000; padding: 10px; margin-bottom: 10px; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SQLite DB 헬퍼
# ==========================================
DB_NAME = "sdh_premium_v2.db"
def get_db_connection(): return sqlite3.connect(DB_NAME)

# ==========================================
# 3. 로그인 화면
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<div style='max-width: 400px; margin: 100px auto;'>", unsafe_allow_html=True)
    st.markdown("<div class='sdh-logo'>SDH STUDIO<br><span style='font-size:14px; font-weight:normal;'>(로그인)</span></div>", unsafe_allow_html=True)
    user_id = st.text_input("ID")
    user_pw = st.text_input("PW", type="password")
    if st.button("로그인", use_container_width=True, type="primary"):
        if user_id == "admin" and user_pw == "1234":
            st.session_state.logged_in, st.session_state.is_admin = True, True
            st.rerun()
        elif user_id == "teacher" and user_pw == "1234":
            st.session_state.logged_in, st.session_state.is_admin = True, False
            st.rerun()
        else: st.error("ID 또는 PW가 일치하지 않습니다.")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 4. 메인 화면 (로그인 성공 시)
# ==========================================
else:
    # --- 사이드바 메뉴 ---
    with st.sidebar:
        st.markdown("<div class='sdh-logo'>SDH STUDIO<br><span style='font-size:14px; font-weight:normal;'>(로고)</span></div>", unsafe_allow_html=True)
        if st.button("모의고사", use_container_width=True): 
            st.session_state.current_page = "list"
            st.rerun()
        st.markdown("<div class='disabled-menu'>외부지문</div>", unsafe_allow_html=True)
        st.markdown("<div class='disabled-menu'>교과서</div>", unsafe_allow_html=True)
        
        if st.session_state.is_admin:
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            if st.button("⚙️ 관리자 모드 (일괄출제)", use_container_width=True, type="primary"):
                st.session_state.current_page = "admin"
                st.rerun()
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("로그아웃"):
            st.session_state.logged_in, st.session_state.is_admin = False, False
            st.rerun()

    # --- 화면 1: 모의고사 리스트 (기존과 동일) ---
    if st.session_state.current_page == "list":
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        # 학년, 연도, 월 필터 (UI 간소화 적용)
        st.write("📌 필터 선택: 고2 | 2026년 | 6월")
        if st.button("출제 (다음 단계로)", type="primary", use_container_width=True):
            st.session_state.current_page = "select"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.write("🗂️ **DB 업로드 내역**")
        db_history = [{"no": 1, "grade": "2", "year": "2026", "month": "6", "date": "2026-08-29"}]
        st.dataframe(pd.DataFrame(db_history), use_container_width=True, hide_index=True)

    # --- 화면 2: 문제 출제 (조건 선택) ---
    elif st.session_state.current_page == "select":
        st.subheader("모의고사 출제 옵션 선택")
        st.checkbox("빈칸 추론", value=True)
        st.checkbox("18번 (목적)", value=True)
        if st.button("📖 선택 문제 보기 (DB 캐시 스캔)", type="primary"):
            st.session_state.current_page = "viewer"
            st.rerun()

    # --- 화면 3: 웹 뷰어 및 출력 ---
    elif st.session_state.current_page == "viewer":
        st.subheader("미리보기 및 HWP 다운로드")
        if st.button("📥 HWP/Docx 다운로드", type="primary"): st.success("다운로드 완료!")
        st.markdown("<div class='exam4you-viewer'>여기에 DB에서 꺼낸 문제가 출력됩니다.</div>", unsafe_allow_html=True)

    # --- 화면 4: 관리자 모드 (AI 심야 일괄 출제) ---
    elif st.session_state.current_page == "admin":
        st.subheader("⚙️ 관리자 모드 - AI 심야 일괄 출제 엔진")
        st.info("원장님, 이곳에서 Gemini API 키를 넣고 18~45번 지문 일괄 출제를 돌리면 DB에 영구 저장됩니다.")
        
        api_key = st.text_input("🔑 Gemini API Key 입력", type="password")
        exam_target = st.selectbox("출제 대상 지문", ["고2 2026년 6월 18번 더미 지문"])
        
        if st.button("🚀 AI 출제 가동 (DB 적재 시작)", type="primary"):
            if not api_key:
                st.error("API Key를 입력해주세요!")
            else:
                with st.spinner("AI가 지문을 분석하고 빈칸 추론 문제를 생성하는 중입니다... (약 5초 소요)"):
                    try:
                        # 1. Gemini 엔진 세팅 (최신 빠르고 저렴한 1.5 flash 모델 사용)
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        
                        dummy_passage = "Dear Residents, I am Trixie Mitchell, the director of the Riverside Community Center..."
                        
                        # 2. AI에게 내릴 강력한 족쇄 프롬프트 (JSON 강제)
                        prompt = f"""
                        당신은 한국의 고등학교 영어 내신 출제 전문가입니다.
                        다음 지문을 읽고, '빈칸 추론' 문제 1개를 만들어주세요.
                        반드시 아래 JSON 형식으로만 출력해야 합니다.
                        {{
                            "q_type": "빈칸 추론",
                            "difficulty": "중",
                            "question": "다음 글의 빈칸에 들어갈 말로 가장 적절한 것은?",
                            "passage": "빈칸이 뚫린 지문 내용",
                            "options": ["보기1", "보기2", "보기3", "보기4", "보기5"],
                            "answer": "정답번호(1~5)",
                            "explanation": "정답인 이유 해설"
                        }}
                        지문: {dummy_passage}
                        """
                        
                        # 3. AI 호출
                        response = model.generate_content(prompt)
                        result_text = response.text.replace('```json', '').replace('```', '').strip()
                        ai_data = json.loads(result_text)
                        
                        # 4. 생성된 데이터를 SQLite DB에 저장 (무한 캐싱)
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("""INSERT OR IGNORE INTO questions_cache 
                                     (exam_key, q_num, q_type, difficulty, question, passage, options, answer, explanation) 
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                  ("2026_6_고2", "18번", ai_data["q_type"], ai_data["difficulty"], ai_data["question"], 
                                   ai_data["passage"], json.dumps(ai_data["options"]), ai_data["answer"], ai_data["explanation"]))
                        conn.commit()
                        conn.close()
                        
                        st.success("✅ AI 출제 및 DB 저장이 완벽하게 완료되었습니다! 이제 강사들은 이 문제를 0초 만에 무료로 뽑아 쓸 수 있습니다.")
                        st.json(ai_data) # AI가 만든 결과물 화면에 확인용으로 출력
                        
                    except Exception as e:
                        st.error(f"출제 중 오류가 발생했습니다: {e}")
