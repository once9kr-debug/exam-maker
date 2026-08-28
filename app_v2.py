import streamlit as st
import sqlite3
import pandas as pd
import json

# ==========================================
# 1. 페이지 기본 설정 및 SDH 브랜딩
# ==========================================
st.set_page_config(page_title="SDH Premium V2 - AI 문제은행", layout="wide")

st.markdown("""
<style>
    .group-header { font-weight: 700; font-size: 1.1rem; color: #2C3E50; border-bottom: 2px solid #3498DB; padding-bottom: 8px; margin-top: 20px; margin-bottom: 15px; }
    .status-box { background-color: #E8F8F5; border-left: 5px solid #1ABC9C; padding: 15px; margin: 10px 0; border-radius: 5px; }
    .exam4you-viewer {
        column-count: 2; 
        column-gap: 40px; 
        column-rule: 1px solid #ddd;
        background-color: white;
        padding: 40px;
        border: 1px solid #ccc;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        font-family: 'Nanum Myeongjo', serif;
    }
    .question-box { break-inside: avoid; margin-bottom: 30px; }
    .q-title { font-weight: bold; color: #009688; margin-bottom: 10px; }
    .q-passage { border: 1px solid #000; padding: 10px; margin-bottom: 10px; line-height: 1.5; }
    .q-options { margin-left: 10px; line-height: 1.8; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SQLite DB 초기화 및 연결
# ==========================================
DB_NAME = "sdh_premium_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS passages (id INTEGER PRIMARY KEY AUTOINCREMENT, exam_key TEXT, q_num TEXT, passage_text TEXT, UNIQUE(exam_key, q_num))''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions_cache (id INTEGER PRIMARY KEY AUTOINCREMENT, exam_key TEXT, q_num TEXT, q_type TEXT, difficulty TEXT, question TEXT, passage TEXT, options TEXT, answer TEXT, explanation TEXT, UNIQUE(exam_key, q_num, q_type, difficulty))''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect(DB_NAME)

# ==========================================
# 3. V2 메인 UI 동선 (3단계 탭)
# ==========================================
st.markdown("<h2 style='text-align: center;'>SDH Premium Decoding V2 🛠️</h2>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚙️ Step 1. 심야 일괄 출제 (원장님용)", "🛒 Step 2. 문제 검색 및 조립 (강사용)", "📝 Step 3. 2단 웹 뷰어 & HWP 다운 (강사용)"])

# ------------------------------------------
# TAB 1: 관리자 심야 일괄 사전 출제 (Batch)
# ------------------------------------------
with tab1:
    st.markdown("<div class='group-header'>새롬캠퍼스, 보람캠퍼스 내신 대비 DB 사전 구축 (과금 최소화)</div>", unsafe_allow_html=True)
    st.info("💡 시험 범위에 해당하는 지문을 미리 AI로 대량 출제하여 DB에 쌓아둡니다. 강사들이 조회할 때는 비용이 발생하지 않습니다.")
    
    col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
    with col_b1:
        batch_exam = st.selectbox("타겟 교재", ["고등 모의고사_2026년_6월_고2", "교과서_영어1_YBM", "외부지문_Odyssey"])
    with col_b2:
        batch_target = st.selectbox("출제 범위", ["18번~45번 전체 일괄 출제", "특정 번호만 출제"])
        
    if st.button("🚀 심야 일괄 출제 가동 (DB 적재 시작)", type="primary"):
        st.success(f"[{batch_exam}] 18~45번 지문에 대한 AI 출제 워커(Worker)가 백그라운드에서 가동됩니다. (예상 소요 시간: 15분)")
        # 향후 Celery를 연동하여 백그라운드 작업으로 전환할 영역입니다.

# ------------------------------------------
# TAB 2: 강사 문제 검색 및 조립 (Zero-Cost)
# ------------------------------------------
with tab2:
    st.markdown("<div class='group-header'>문제 쇼핑 및 시험지 구성 (대기시간 0초)</div>", unsafe_allow_html=True)
    
    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        st.write("**1. 출제 범위 선택**")
        search_exam = st.selectbox("교재", ["고등 모의고사_2026년_6월_고2", "외부지문_Odyssey"], key="s_exam")
        st.write("**2. 세부 유형 선택**")
        type_blank = st.checkbox("빈칸 추론", value=True)
        type_order = st.checkbox("순서 배열", value=True)
        type_grammar = st.checkbox("어법", value=True)
        
    with col_s2:
        st.write("**3. DB 캐시 스캔 결과**")
        st.markdown("""
        <div class='status-box'>
            <b>현재 선택한 조건으로 즉시 조립 가능한 문항 수: <span style='color:red; font-size:1.2em;'>45문제</span></b><br>
            - DB 무한 캐시 사용: 45문제 (예상 대기시간: 0.1초 / 추가 AI 과금: 0원)
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🛒 선택한 문제로 시험지 조립하기", type="primary", use_container_width=True):
            st.session_state.show_viewer = True
            st.success("시험지 조립이 완료되었습니다. 'Step 3' 탭에서 확인하세요!")

# ------------------------------------------
# TAB 3: exam4you 스타일 2단 뷰어 및 HWP 다운로드
# ------------------------------------------
with tab3:
    st.markdown("<div class='group-header'>핀셋 검수 및 SDH Premium 전용 HWP 출력</div>", unsafe_allow_html=True)
    
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.button("💾 완벽한 HWP 파일 다운로드", type="primary", use_container_width=True)
    with dl_col2:
        st.button("💾 PDF 파일 다운로드", use_container_width=True)
    with dl_col3:
        st.button("📝 정답 및 해설지 다운로드", use_container_width=True)
        
    st.markdown("---")
    st.write("🔍 **웹 뷰어 미리보기 (오타 및 함정 1차 검수용)**")
    
    # exam4you 스타일 2단 뷰어 HTML Mockup
    viewer_html = """
    <div class='exam4you-viewer'>
        <div class='question-box'>
            <div class='q-title'>243. 다음 글의 밑줄 친 (A)its "future-proof" nature가 의미하는 바로 알맞은 것은?</div>
            <div class='q-passage'>
                One easily underappreciated feature of a city street or square is (A)<u>its "future-proof" nature</u>. The ancient medieval squares in places like Marrakesh and Siena are still places where stuff is sold every day, even if the stuff itself has changed over the last five hundred years. The city square is a fairly future-proof technology, as is the shopping street, even in an age of online shopping.
            </div>
            <div class='q-options'>
                ① its ability to serve new purposes across time<br>
                ② its potential to generate greater economic returns<br>
                ③ its durability in keeping its original physical structure<br>
                ④ its power to preserve historical and traditional character<br>
                ⑤ its capacity to remain useful only by resisting digital change
            </div>
            <div style='text-align: right; margin-top: 10px;'>
                <button style='background:#f0f0f0; border:1px solid #ccc; padding:2px 8px; font-size:11px;'>✏️수정</button>
                <button style='background:#f0f0f0; border:1px solid #ccc; padding:2px 8px; font-size:11px;'>🔄이 문항만 재출제</button>
            </div>
        </div>
        
        <div class='question-box'>
            <div class='q-title'>244. 다음 빈칸에 들어갈 말로 가장 적절한 것은?</div>
            <div class='q-passage'>
                The genomics revolution made it possible to see just how impactful touch is to plants on a deeper level. Peering at the genes of <i>Arabidopsis thaliana</i>, a weedy plant in the mustard family and the lab rat of the plant biology world, researchers saw that touch quietly triggered such a dramatic response in their hormones and gene expression that it could substantially inhibit their growth. Clearly, the plant was _________________ to deal with the disturbance.
            </div>
            <div class='q-options'>
                ① adjusting its internal processes<br>
                ② shifting how it allocates resources<br>
                ③ ignoring the touch completely<br>
                ④ absorbing more nutrients<br>
                ⑤ stopping all activity until the threat disappears
            </div>
            <div style='text-align: right; margin-top: 10px;'>
                <button style='background:#f0f0f0; border:1px solid #ccc; padding:2px 8px; font-size:11px;'>✏️수정</button>
                <button style='background:#f0f0f0; border:1px solid #ccc; padding:2px 8px; font-size:11px;'>🔄이 문항만 재출제</button>
            </div>
        </div>
    </div>
    """
    st.markdown(viewer_html, unsafe_allow_html=True)
