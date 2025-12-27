import streamlit as st
import pandas as pd
import openai
import requests
from io import StringIO

# 1. 페이지 설정 (최상단)
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 큰 글씨와 명확한 칸 분리 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 20px !important; font-weight: bold !important; color: #8D6E63 !important; }
    .stTextInput input, .stTextArea textarea { font-size: 19px !important; border-radius: 12px !important; border: 2px solid #D7CCC8 !important; padding: 15px !important; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3.8em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 19px !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")
# 구글 시트 주소 (CSV 출력 방식)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tz4pYbxyV8PojkzYtPz82OhiAGD2XoWVZqlTpwAebaA/gviz/tq?tqx=out:csv"

# 세션 상태 초기화 (데이터 증발 방지)
for key in ['m_name', 'm_mat', 'm_per', 'm_tar', 'm_det']:
    if key not in st.session_state: st.session_state[key] = ""
if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'chat_log' not in st.session_state: st.session_state.chat_log = []

# --- [함수: AI 답변 엔진] ---
def ask_mog_ai(prompt_type, user_input=""):
    if not api_key: return "API 키가 설정되지 않았어요🌸"
    client = openai.OpenAI(api_key=api_key)
    info = f"작품명:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 기간:{st.session_state.m_per}, 대상:{st.session_state.m_tar}, 설명:{st.session_state.m_det}"
    
    if prompt_type == "상담":
        system_prompt = "당신은 핸드메이드 작가 '모그'의 다정한 동료입니다. 50대 여성 작가의 말투(~이지요, ~해요)로 현실적이고 따뜻한 조언을 해주세요. 특수기호 ** 금지."
        user_content = f"고민내용: {user_input}"
    else:
        system_prompt = f"당신은 작가 모그입니다. 다정하게 {prompt_type}용 판매글을 작성하세요. 특수기호 ** 금지."
        user_content = f"작품 정보: {info} / 스타일 지침: {user_input}"

    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]
        )
        return res.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except: return "잠시 대화가 어려워요🌸"

# --- 3. 메인 화면 ---
st.title("🌸 모그 작가님 AI 비서")
st.header("1️⃣ 작품 정보를 채워주세요")

col1, col2 = st.columns(2)
with col1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 사용한 소재", value=st.session_state.m_mat)
with col2:
    st.session_state.m_per = st.text_input("⏳ 제작 소요 기간", value=st.session_state.m_per)
    st.session_state.m_tar = st.text_input("🎁 추천 선물 대상", value=st.session_state.m_tar)

st.session_state.m_det = st.text_area("✨ 정성 포인트와 상세 설명", value=st.session_state.m_det, height=180)

st.divider()

# --- 4. 기능 탭 (모든 기능 복구) ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진 보정법", "💬 고민 상담소", "📂 작품 창고"])

with tabs[0]: # 판매글 쓰기
    st.write("#### 💡 버튼을 누르면 글이 완성됩니다.")
    c1, c2, c3 = st.columns(3)
    if c1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램", "감성 일기 스타일")
    if c2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스", "정성 강조 스타일")
    if c3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어", "친절한 정보 안내")
    for k in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts.get(k):
            st.text_area(f"📍 {k} 글 완성^^", value=st.session_state.texts[k], height=250, key=f"out_{k}")

with tabs[1]: # 사진 보정 (복구 완료)
    st.header("📸 사진 보정, 이것만 기억하세요!")
    st.info("엄마! 버튼 하나로 사진이 화사해지는 방법이에요 🌸")
    st.success("**1. 네이버 스마트스토어 편집기** (가장 추천)\n- 상품 사진 올리고 [편집] - [자동보정]만 누르세요. 평소 블로그 하시던 거라 제일 쉬워요!")
    st.warning("**2. 포토(Fotor) AI 보정**\n- 아래 버튼을 눌러 사이트에 접속한 뒤 [AI 원클릭 보정]을 누르세요. 조명을 알아서 켜줍니다.")
    st.link_button("👉 포토(Fotor) 바로가기", "https://www.fotor.com/kr/photo-editor-app/editor/basic")

with tabs[2]: # 고민 상담소 (작동 보강)
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"], avatar="🌸" if m["role"]=="user" else "🕯️"): st.write(m["content"])
    
    if pr := st.chat_input("작가님, 무엇이든 말씀하셔요..."):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        with st.chat_message("user", avatar="🌸"): st.write(pr)
        with st.chat_message("assistant", avatar="🕯️"):
            answer = ask_mog_ai("상담", pr)
            st.write(answer)
            st.session_state.chat_log.append({"role": "assistant", "content": answer})
        st.rerun()

with tabs[3]: # 창고 (불러오기 기능 유지)
    st.header("📂 나의 작품 창고")
    try:
        response = requests.get(SHEET_URL)
        df = pd.read_csv(StringIO(response.text))
        st.success("창고와 연결되었습니다! 🌸")
        
        for i, r in df.iterrows():
            with st.expander(f"📦 {r.get('name', '이름 없음')}"):
                st.write(f"소재: {r.get('material', '-')}")
                if st.button("📥 불러오기", key=f"load_{i}"):
                    st.session_state.m_name = r.get('name', '')
                    st.session_state.m_mat = r.get('material', '')
                    st.session_state.m_per = r.get('period', '')
                    st.session_state.m_tar = r.get('target', '')
                    st.session_state.m_det = r.get('keys', '')
                    st.rerun()
    except: st.warning("데이터를 불러오는 중입니다... 🌸")
