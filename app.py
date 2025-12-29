import streamlit as st
import openai
import base64
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_google_auth import Authenticate
import json
import os

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- 🔐 구글 로그인 설정 (TypeError 완벽 방어) ---
# Secrets 정보를 기반으로 라이브러리가 요구하는 JSON 파일을 생성합니다.
client_secrets = {
    "web": {
        "client_id": st.secrets["GOOGLE_CLIENT_ID"],
        "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": [st.secrets["REDIRECT_URI"]]
    }
}

with open("client_secrets.json", "w") as f:
    json.dump(client_secrets, f)

# 🚨 에러 원인인 Authenticate 부분을 인자 이름(Keyword)을 명시하여 수정했습니다.
try:
    auth = Authenticate(
        client_secrets_file="client_secrets.json",
        cookie_name="mom_ai_login_cookie",
        cookie_key=st.secrets["AUTH_SECRET_KEY"],
        cookie_expiry_days=30
    )
except TypeError:
    # 혹시라도 인자 이름이 다른 구버전일 경우를 대비한 2차 방어
    auth = Authenticate(
        secret_key=st.secrets["AUTH_SECRET_KEY"],
        google_client_id=st.secrets["GOOGLE_CLIENT_ID"],
        google_client_secret=st.secrets["GOOGLE_CLIENT_SECRET"],
        redirect_uri=st.secrets["REDIRECT_URI"],
        cookie_name="mom_ai_login_cookie"
    )

# 🔑 로그인 체크
auth.check_authentification()

if not st.session_state.get('connected'):
    st.markdown("<h1 style='text-align: center; color: #8D6E63;'>🌸 모그 작가님 AI 비서 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 20px;'>작가님, 안전한 기록 저장을 위해 로그인이 필요해요^^</p>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        auth.login()
    st.stop()

# --- 🔑 로그인 성공 후 본문 ---
user_id = st.session_state['user_info'].get('email', 'mom_mog_01')

# Firebase 초기화
if not firebase_admin._apps:
    try:
        # Streamlit Secrets에 저장된 Firebase 딕셔너리를 그대로 사용합니다.
        cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase 초기화 에러: {e}")

db = firestore.client()
api_key = st.secrets["OPENAI_API_KEY"]

# --- ✨ 따님 설계 UI/AI 로직 ---
st.markdown("""
    <style>
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 30px; font-weight: 800; }
    .result-card { background-color: #FFFFFF; padding: 30px; border-radius: 25px; border-left: 10px solid #D7CCC8; box-shadow: 0 10px 20px rgba(0,0,0,0.05); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    base_style = "[절대 규칙: 1인칭 작가 시점] 당신은 작가 '모그(Mog)' 본인입니다. 말투: ~이지요^^, ~해요 등 다정하게. 특수기호(*, **) 금지."
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램] 감성 문구로 시작해 제작 일기와 정보를 연결해줘."
    elif platform == "아이디어스":
        system_p = f"{base_style} [🎨 아이디어스] 💡상세설명, 🍀Add info., 🔉안내, 👍🏻작가보증 포맷 엄수."
    elif platform == "스마트스토어":
        system_p = f"{base_style} [🛍️ 스마트스토어] 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천 엄수."
    else:
        system_p = f"{base_style} [💬 고민 상담소] 다정하게 공감하며 답변해줘."

    info = f"작품:{st.session_state.get('m_name','')}, 소재:{st.session_state.get('m_mat','')}, 포인트:{st.session_state.get('m_det','')}"
    content = f"수정요청: {feedback}\n기존: {user_in}" if feedback else f"정보: {info} / {user_in}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 화면 구성 ---
st.sidebar.title("🌸 작가님 정보")
st.sidebar.write(f"접속: {user_id}")
if st.sidebar.button("로그아웃"):
    auth.logout()

st.title("🌸 모그 작가님 AI 비서 🌸")

if 'texts' not in st.session_state:
    st.session_state.update({'texts': {"인스타": "", "아이디어스": "", "스토어": ""}, 'chat_log': [], 'm_name': '', 'm_mat': '', 'm_det': ''})

with st.container():
    st.header("📝 작품 정보 입력")
    st.session_state.m_name = st.text_input("📦 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.m_mat)
    st.session_state.m_det = st.text_area("✨ 포인트", value=st.session_state.m_det, height=120)

st.divider()
tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]:
    b1, b2, b3 = st.columns(3)
    if b1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if b2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if b3.button("🛍️ 스마트스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for p_name, key in [("인스타그램", "인스타"), ("아이디어스", "아이디어스"), ("스마트스토어", "스토어")]:
        if st.session_state.texts[key]:
            st.markdown(f"---")
            st.markdown(f"### ✨ 완성된 {p_name} 글")
            st.markdown(f'<div class="result-card">{st.session_state.texts[key].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

with tabs[1]:
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님 고민을 말해주세요^^"):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
