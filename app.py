import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import openai

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 칸 분리 및 글씨 크기 최적화 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    
    /* 입력창 라벨 */
    label p { font-size: 20px !important; font-weight: bold !important; color: #8D6E63 !important; }
    
    /* 입력창 내부 */
    .stTextInput input, .stTextArea textarea { font-size: 18px !important; border-radius: 12px !important; border: 2px solid #D7CCC8 !important; padding: 15px !important; }
    
    /* 버튼 */
    .stButton>button { width: 100%; border-radius: 15px; height: 3.5em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 18px !important; }
    
    h1 { color: #8D6E63 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 데이터 및 연결
api_key = st.secrets.get("OPENAI_API_KEY")
# 구글 시트 연결 (에러 방지를 위해 try-except 추가)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("구글 시트 연결 설정을 확인해주세요!")

# 세션 상태 초기화 (이름 겹침 방지)
if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'm_name' not in st.session_state: st.session_state.m_name = ""
if 'm_mat' not in st.session_state: st.session_state.m_mat = ""
if 'm_per' not in st.session_state: st.session_state.m_per = ""
if 'm_tar' not in st.session_state: st.session_state.m_tar = ""
if 'm_det' not in st.session_state: st.session_state.m_det = ""

# --- 3. 메인 화면: 상세 입력 (칸 확실히 분리) ---
st.title("🌸 모그 작가님 AI 비서")
st.header("1️⃣ 작품 정보를 입력해주세요")

col1, col2 = st.columns(2)
with col1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name, placeholder="예: 빈티지 튤립 파우치")
    st.session_state.m_mat = st.text_input("🧵 사용한 소재", value=st.session_state.m_mat, placeholder="예: 순면사, 린넨")
with col2:
    st.session_state.m_per = st.text_input("⏳ 제작 소요 기간", value=st.session_state.m_per, placeholder="예: 3일 이내")
    st.session_state.m_tar = st.text_input("🎁 추천 선물 대상", value=st.session_state.m_tar, placeholder="예: 친구 생일")

st.session_state.m_det = st.text_area("✨ 정성 포인트와 상세 설명", value=st.session_state.m_det, height=150, placeholder="작가님의 정성을 담아 적어주세요.")

st.divider()

# --- 4. 기능 탭 ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진 보정법", "💬 고민 상담소", "📂 작품 창고"])

def process_ai(guide):
    if not api_key: return "API 키가 없어요🌸"
    client = openai.OpenAI(api_key=api_key)
    info = f"이름:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 기간:{st.session_state.m_per}, 대상:{st.session_state.m_tar}, 설명:{st.session_state.m_det}"
    prompt = f"당신은 작가 모그입니다. 다정하게 {guide['name']} 판매글을 작성하세요. 특수기호 ** 금지. [정보] {info} [지침] {guide['desc']}"
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except: return "연결 오류🌸"

with tabs[0]:
    st.write("#### 💡 버튼을 누르면 글이 완성됩니다.")
    c1, c2, c3 = st.columns(3)
    if c1.button("📸 인스타그램"): st.session_state.texts["인스타"] = process_ai({"name": "인스타그램", "desc": "감성 일기 스타일"})
    if c2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = process_ai({"name": "아이디어스", "desc": "정성 강조 스타일"})
    if c3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = process_ai({"name": "스마트스토어", "desc": "정보 안내 스타일"})
    for k in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts.get(k):
            st.info(f"📍 {k} 글이 완성되었어요^^")
            st.text_area(f"{k} 내용", value=st.session_state.texts[k], height=200, key=f"t_{k}")

with tabs[1]:
    st.markdown("### 📸 사진 보정법")
    st.success("네이버 편집기: [자동보정] 클릭! / 포토(Fotor): [AI 원클릭 보정] 클릭!")

with tabs[2]:
    st.header("💬 고민 상담소")
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"], avatar="🌸" if m["role"]=="user" else "🕯️"): st.write(m["content"])
    if pr := st.chat_input("작가님, 무엇이든 물어보세요..."):
        st.session_state.chat_history.append({"role": "user", "content": pr})
        st.rerun()

with tabs[3]:
    st.header("📂 나의 작품 창고")
    try:
        df = conn.read(ttl=0)
        if st.button("✨ 지금 정보 저장하기"):
            new_row = pd.DataFrame([{"name":st.session_state.m_name, "material":st.session_state.m_mat, "period":st.session_state.m_per, "target":st.session_state.m_tar, "keys":st.session_state.m_det}])
            conn.update(data=pd.concat([df, new_row], ignore_index=True))
            st.success("저장 완료! 🌸")
        st.divider()
        for i, r in df.iterrows():
            with st.expander(f"📦 {r['name']}"):
                if st.button("📥 불러오기", key=f"l_{i}"):
                    st.session_state.m_name, st.session_state.m_mat = r['name'], r['material']
                    st.session_state.m_per, st.session_state.m_tar = r['period'], r['target']
                    st.session_state.m_det = r['keys']
                    st.rerun()
    except: st.warning("구글 시트 설정을 확인해주세요!")
