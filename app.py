import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import openai

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI/UX: 입력창이 절대 깨지지 않는 스타일 설정 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FCF9F6;
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 입력창 라벨 글씨 크기 */
    .stMarkdown p { font-size: 18px !important; font-weight: bold; color: #8D6E63; }

    /* 모든 입력창 가로 100% 및 글씨 확대 */
    .stTextInput input, .stTextArea textarea, .stSelectbox div {
        font-size: 19px !important;
        border-radius: 12px !important;
        border: 2px solid #D7CCC8 !important;
        padding: 12px !important;
    }

    /* 제목 스타일 */
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 30px; }
    h2 { color: #A1887F !important; border-bottom: 2px solid #D7CCC8; padding-bottom: 10px; }

    /* 버튼 스타일 */
    .stButton>button {
        width: 100%; border-radius: 15px; height: 3.8em;
        background-color: #8D6E63 !important; color: white !important;
        font-weight: bold; font-size: 18px !important; border: none;
    }

    /* 탭 메뉴 크게 */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 20px !important; font-weight: bold !important; height: 60px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 연결 설정
api_key = st.secrets.get("OPENAI_API_KEY")
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 데이터 초기화
if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'refined' not in st.session_state: st.session_state.refined = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- [복구된 상세 입력 섹션] ---
st.title("🌸 모그 작가님 AI 비서 (상세 입력 버전)")

st.header("1️⃣ 작품의 상세 정보를 알려주세요")

# 엄마가 쓰기 편하게 칸을 큼직하게 나누었습니다.
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("📦 작품 이름", value=st.session_state.get('name', ''), placeholder="예: 빈티지 튤립 파우치")
    material = st.text_input("🧵 사용한 소재", value=st.session_state.get('material', ''), placeholder="예: 순면사, 린넨 안감")
with col2:
    period = st.text_input("⏳ 제작 소요 기간", value=st.session_state.get('period', ''), placeholder="예: 주문 후 3일 이내")
    target = st.text_input("🎁 추천 선물 대상", value=st.session_state.get('target', ''), placeholder="예: 생일 선물, 나를 위한 작은 사치")

keys = st.text_area("✨ 정성 포인트와 상세 설명", value=st.session_state.get('keys', ''), placeholder="작가님의 정성이 들어간 부분을 자세히 적어주세요.", height=150)

# 입력값 세션 저장
st.session_state.name = name
st.session_state.material = material
st.session_state.period = period
st.session_state.target = target
st.session_state.keys = keys

st.divider()

# --- [함수 정의] ---
def process_mog_ai(guide):
    if not api_key: return "API 키를 확인해주세요🌸"
    client = openai.OpenAI(api_key=api_key)
    # 복구된 상세 정보를 모두 프롬프트에 담습니다.
    info = f"작품명:{name}, 소재:{material}, 기간:{period}, 대상:{target}, 특징:{keys}"
    prompt = f"당신은 작가 모그입니다. 다음 정보를 바탕으로 {guide['name']} 판매글을 작성하세요. 말투는 50대 여성의 다정함이 묻어나야 하며, {guide['desc']}를 지키세요. 특수기호 ** 금지.\n[정보] {info}"
    
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except: return "잠시 연결이 끊겼어요🌸"

# --- [2구역: 탭 기능] ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진 보정법", "💬 고민 상담소", "📂 작품 창고"])

with tabs[0]: # 판매글 쓰기
    st.write("#### 💡 버튼을 눌러 글을 완성하세요.")
    c1, c2, c3 = st.columns(3)
    if c1.button("📸 인스타그램", key="in"): st.session_state.texts["인스타"] = process_mog_ai({"name": "인스타그램", "desc": "감성 일기 스타일, 해시태그 포함"})
    if c2.button("🎨 아이디어스", key="id"): st.session_state.texts["아이디어스"] = process_mog_ai({"name": "아이디어스", "desc": "정성 강조 스타일"})
    if c3.button("🛍️ 스토어", key="st"): st.session_state.texts["스토어"] = process_mog_ai({"name": "스마트스토어", "desc": "정보 안내 스타일"})

    for k in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts.get(k):
            st.info(f"📍 {k} 글이 완성되었어요^^")
            st.text_area(f"{k} 내용", value=st.session_state.texts[k], height=250, key=f"t_{k}")

with tabs[1]: # 보정법
    st.markdown("### 📸 사진 보정, 이것만 기억하세요!")
    st.success("**네이버 편집기**: [편집] - [자동보정] 클릭! (가장 추천)")
    st.info("**포토(Fotor)**: [AI 원클릭 보정] 클릭!")
    st.link_button("👉 포토(Fotor) 바로가기", "https://www.fotor.com/kr/photo-editor-app/editor/basic")

with tabs[2]: # 상담소
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"], avatar="🌸" if m["role"]=="user" else "🕯️"): st.write(m["content"])
    if pr := st.chat_input("작가님, 무엇이든 물어보세요..."):
        st.session_state.chat_history.append({"role": "user", "content": pr})
        with st.chat_message("user", avatar="🌸"): st.write(pr)
        with st.chat_message("assistant", avatar="🕯️"):
            ans = process_mog_ai({"name": "상담소", "desc": f"현실적 조언 질문: {pr}"})
            st.write(ans)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()

with tabs[3]: # 창고
    st.header("📂 나의 영구 작품 창고")
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    if st.button("✨ 구글 시트에 저장"):
        new_row = pd.DataFrame([{"name":name, "material":material, "period":period, "target":target, "keys":keys}])
        conn.update(data=pd.concat([df, new_row], ignore_index=True))
        st.success("저장되었습니다! 🌸")
    st.divider()
    for i, r in df.iterrows():
        with st.expander(f"📦 {r['name']}"):
            st.write(f"소재: {r['material']} | 기간: {r['period']}")
            if st.button("📥 불러오기", key=f"l_{i}"):
                st.session_state.name, st.session_state.material = r['name'], r['material']
                st.session_state.period, st.session_state.target = r['period'], r['target']
                st.session_state.keys = r['keys']
                st.rerun()
