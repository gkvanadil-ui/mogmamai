import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import openai

# 1. 페이지 설정 (가장 먼저 실행)
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 큰 글씨와 명확한 칸 분리 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 20px !important; font-weight: bold !important; color: #8D6E63 !important; }
    .stTextInput input, .stTextArea textarea { font-size: 19px !important; border-radius: 12px !important; border: 2px solid #D7CCC8 !important; padding: 15px !important; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3.8em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 18px !important; }
    h1 { color: #8D6E63 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. 연결 설정
api_key = st.secrets.get("OPENAI_API_KEY")
# 따님의 시트 주소를 코드에 직접 박아넣어 에러를 방지합니다.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tz4pYbxyV8PojkzYtPz82OhiAGD2XoWVZqlTpwAebaA/edit?usp=sharing"

# 세션 상태 초기화 (영어 코드 출력 버그 방지)
for key in ['m_name', 'm_mat', 'm_per', 'm_tar', 'm_det']:
    if key not in st.session_state: st.session_state[key] = ""
if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}

# --- 3. 메인 화면: 상세 입력 ---
st.title("🌸 모그 작가님 AI 비서")
st.header("1️⃣ 작품 정보를 한 칸씩 채워주세요")

col1, col2 = st.columns(2)
with col1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name, key="in_name")
    st.session_state.m_mat = st.text_input("🧵 사용한 소재", value=st.session_state.m_mat, key="in_mat")
with col2:
    st.session_state.m_per = st.text_input("⏳ 제작 소요 기간", value=st.session_state.m_per, key="in_per")
    st.session_state.m_tar = st.text_input("🎁 추천 선물 대상", value=st.session_state.m_tar, key="in_tar")

st.session_state.m_det = st.text_area("✨ 정성 포인트와 상세 설명", value=st.session_state.m_det, height=200, key="in_det")

st.divider()

# --- 4. 기능 탭 ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진 보정법", "💬 고민 상담소", "📂 작품 창고"])

def process_ai(guide):
    if not api_key: return "API 키가 없어요🌸"
    client = openai.OpenAI(api_key=api_key)
    info = f"이름:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 기간:{st.session_state.m_per}, 대상:{st.session_state.m_tar}, 설명:{st.session_state.m_det}"
    prompt = f"작가 모그로서 {guide['name']} 판매글을 다정하게 쓰세요. ** 기호 절대 금지. [정보] {info} [지침] {guide['desc']}"
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except: return "연결 오류🌸"

with tabs[0]: # 판매글 쓰기
    c1, c2, c3 = st.columns(3)
    if c1.button("📸 인스타그램"): st.session_state.texts["인스타"] = process_ai({"name": "인스타그램", "desc": "감성 일기 스타일"})
    if c2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = process_ai({"name": "아이디어스", "desc": "정성 강조 스타일"})
    if c3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = process_ai({"name": "스마트스토어", "desc": "정보 안내 스타일"})
    
    for k in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts.get(k):
            st.text_area(f"📍 {k} 글 완성^^", value=st.session_state.texts[k], height=250, key=f"out_{k}")

with tabs[1]: # 보정 가이드
    st.info("네이버 편집기: [자동보정] / 포토(Fotor): [AI 원클릭 보정]을 사용하세요!")
    st.link_button("👉 포토(Fotor) 바로가기", "https://www.fotor.com/kr/photo-editor-app/editor/basic")

with tabs[2]: # 상담소
    st.header("💬 작가님 고민 상담소")
    if "chat_log" not in st.session_state: st.session_state.chat_log = []
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 무엇이든 물어보세요..."):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.rerun()

with tabs[3]: # 영구 창고
    st.header("📂 나의 영구 작품 창고")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # ⚠️ 여기서 SHEET_URL을 명시적으로 넣어 에러를 방지합니다.
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        
        if st.button("✨ 지금 입력한 정보 저장하기"):
            new_row = pd.DataFrame([{"name":st.session_state.m_name, "material":st.session_state.m_mat, "period":st.session_state.m_per, "target":st.session_state.m_tar, "keys":st.session_state.m_det}])
            conn.update(spreadsheet=SHEET_URL, data=pd.concat([df, new_row], ignore_index=True))
            st.success("안전하게 저장되었습니다! 🌸")
            st.rerun()
            
        st.divider()
        for i, r in df.iterrows():
            with st.expander(f"📦 {r['name']}"):
                if st.button("📥 불러오기", key=f"l_{i}"):
                    st.session_state.m_name, st.session_state.m_mat = r['name'], r['material']
                    st.session_state.m_per, st.session_state.m_tar = r['period'], r['target']
                    st.session_state.m_det = r['keys']
                    st.rerun()
    except Exception as e:
        st.warning(f"구글 시트 연동 대기 중... (공유 설정을 확인해 주세요)")
