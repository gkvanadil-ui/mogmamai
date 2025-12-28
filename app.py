import streamlit as st
import openai
from PIL import Image
import io
import base64
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_google_auth import Authenticate

# 1. 로그인 설정 (최상단)
auth = Authenticate(
    secret_key=st.secrets.get("AUTH_SECRET_KEY", "mog_secret_123"),
    client_id=st.secrets.get("GOOGLE_CLIENT_ID"),
    client_secret=st.secrets.get("GOOGLE_CLIENT_SECRET"),
    redirect_uri=st.secrets.get("REDIRECT_URI"),
    cookie_name="mom_ai_login"
)

# 🔑 로그인 체크 (UI 그리기 전에 먼저 실행)
auth.check_authentification()

# --- 로그인 안 됐을 때 보여줄 화면 ---
if not st.session_state.get('connected'):
    st.set_page_config(page_title="모그 AI 비서 - 로그인", page_icon="🔒")
    st.markdown("<h1 style='text-align: center; color: #8D6E63;'>🌸 모그 작가님 AI 비서 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 20px;'>작가님, 안전한 기록 저장을 위해 로그인이 필요해요^^</p>", unsafe_allow_html=True)
    
    # 중앙 정렬을 위한 컬럼 배치
    _, col, _ = st.columns([1, 2, 1])
    with col:
        auth.login() # 👈 여기서 구글 로그인 버튼이 뜹니다.
    st.stop() # 🛑 로그인 안 되면 여기서 코드 실행 중단 (본문 절대 안 뜸)

# --- [로그인 성공 후 실행되는 본문] ---

# 2. 본문 페이지 설정 및 스타일
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# Firebase 초기화 (로그인 후 1회만)
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase 설정 에러: {e}")

db = firestore.client()
user_id = st.session_state['user_info'].get('email', 'mom_mog_01')

# UI 스타일 적용 (따님 원본 100%)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 24px !important; font-weight: bold !important; color: #5D4037 !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 30px; font-weight: 800; }
    .stTextInput input, .stTextArea textarea { font-size: 22px !important; border-radius: 15px !important; border: 2px solid #E0D4CC !important; padding: 20px !important; background-color: #FFFFFF !important; }
    .stButton>button { width: 100%; border-radius: 20px; height: 4.5em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 22px !important; transition: 0.3s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stButton>button:hover { background-color: #6D4C41 !important; transform: translateY(-2px); }
    .result-card { background-color: #FFFFFF; padding: 30px; border-radius: 25px; border-left: 10px solid #D7CCC8; box-shadow: 0 10px 20px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] button { font-size: 26px !important; font-weight: bold !important; padding: 15px 30px; }
    </style>
    """, unsafe_allow_html=True)

# 💾 데이터 연동 함수
def save_data(uid, data): db.collection("users").document(uid).set(data)
def load_data(uid):
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None

# 데이터 로드
if 'init_done' not in st.session_state:
    saved = load_data(user_id)
    if saved: st.session_state.update(saved)
    else: st.session_state.update({'texts': {"인스타": "", "아이디어스": "", "스토어": ""}, 'chat_log': [], 'm_name': '', 'm_mat': '', 'm_per': '', 'm_size': '', 'm_det': '', 'img_analysis': ''})
    st.session_state.init_done = True

# --- 이하 따님 설계 글쓰기 로직 및 화면 구성 (동일) ---
st.sidebar.write(f"🌸 접속: {user_id}")
if st.sidebar.button("로그아웃"): auth.logout()

st.title("🌸 모그 작가님 AI 비서 🌸")
# (생략된 기존 UI 코드 부분은 아까와 동일하게 유지하세요)
