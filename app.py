import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime
import traceback # 상세 에러 출력을 위해 추가

# 1. 페이지 설정
st.set_page_config(page_title="모그 작가님 AI 비서", layout="wide", page_icon="🌸")

# ==========================================
# [섹션 A] 진실의 원천(Source of Truth) 확립
# ==========================================
# 지침: 앱 시작 시점에 ID와 진입 플래그를 무조건 확정한다.

# 1. URL 파라미터 안전하게 읽기 (읽기 전용)
found_id = None
try:
    # 최신 Streamlit
    qp = st.query_params
    val = qp.get("device_id")
    if val: found_id = val if isinstance(val, str) else val[0]
except:
    try:
        # 구버전
        qp = st.experimental_get_query_params()
        if "device_id" in qp: found_id = qp["device_id"][0]
    except:
        pass

# 2. Session State 초기화 (device_id가 없으면 즉시 생성)
if "device_id" not in st.session_state:
    if found_id:
        st.session_state["device_id"] = found_id # URL에서 복구
    else:
        st.session_state["device_id"] = f"mog_{str(uuid.uuid4())[:8]}" # 신규 생성

# 3. 진입 플래그 초기화
if "entered" not in st.session_state:
    # URL에 ID가 있었으면 이미 진입한 것으로 간주할 수도 있으나,
    # 명확한 테스트를 위해 버튼 클릭을 유도하려면 False로 둡니다.
    # (여기서는 루프 방지를 위해 버튼 클릭을 강제합니다)
    st.session_state["entered"] = False

# 편의를 위한 로컬 변수 (이후 로직은 이것만 씀)
device_id = st.session_state["device_id"]

# ==========================================
# [섹션 B] 화면 분기 (Start Screen vs Main App)
# ==========================================

# 지침: 'entered' 플래그가 False면 무조건 시작 화면
if not st.session_state["entered"]:
    # --- 시작 화면 (디버그 UI 포함) ---
    st.markdown("""
    <div style='text-align: center; padding-top: 50px;'>
        <h1 style='color: #FF4B4B;'>🌸 모그 작가님 AI 비서</h1>
        <p>환영합니다. 아래 버튼을 눌러주세요.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # [강제 지시] 디버그 정보 가시화
    with st.expander("🛠️ 시스템 상태 확인 (디버그)", expanded=True):
        st.write(f"DEBUG: 현재 device_id(Session) = `{st.session_state.get('device_id')}`")
        st.write(f"DEBUG: 감지된 URL 파라미터 = `{found_id}`")
        st.write(f"DEBUG: 진입 플래그(entered) = `{st.session_state.get('entered')}`")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # [강제 지시] 버튼 클릭 로직
        if st.button("🚀 작가님, 여기를 눌러 시작해주세요", use_container_width=True, type="primary"):
            # 1. 진입 플래그 확정 (루프 탈출의 핵심)
            st.session_state["entered"] = True
            
            # 2. 클릭 확인 UI 노출
            st.success("DEBUG: Start button clicked! 이동 중...")
            
            # 3. URL 업데이트 (보조 수단, 오직 experimental 사용)
            try:
                st.experimental_set_query_params(device_id=device_id)
            except Exception as e:
                st.warning(f"URL 설정 중 경고(무시 가능): {e}")
            
            # 4. 재실행
            st.rerun()
    
    # 버튼이 눌리지 않았을 때만 멈춤
    st.stop()

# ==========================================
# [섹션 C] 메인 앱 (여기 왔다는 건 entered=True라는 뜻)
# ==========================================

# [강제 지시] 메인 진입 마커
st.success("DEBUG: Entered main app successfully")
st.caption(f"현재 접속 ID: {device_id}")

# 1. Firebase 연결 (예외 절대 숨기지 않음)
db = None
try:
    if not firebase_admin._apps:
        if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
            raise ValueError("Secrets에 'FIREBASE_SERVICE_ACCOUNT'가 없습니다.")
        
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error("🚨 Firebase 연결 실패 (이 에러가 보이면 서버 설정 문제임)")
    st.code(traceback.format_exc()) # 상세 에러 출력
    st.stop() # 더 이상 진행 불가

# 2. 데이터 처리 함수 (예외 노출)
def save_to_db(work_id, data):
    if not db: return
    try:
        doc_ref = db.collection("works").document(f"{device_id}_{work_id}")
        doc_ref.set({
            "device_id": device_id,
            "work_id": work_id,
            "updated_at": datetime.datetime.now(),
            **data
        })
    except Exception as e:
        st.error(f"저장 중 오류 발생: {e}")

def load_works():
    if not db: return []
    try:
        docs = db.collection("works").where("device_id", "==", device_id).stream()
        return sorted([doc.to_dict() for doc in docs], key=lambda x: x.get('updated_at', datetime.datetime.min), reverse=True)
    except Exception as e:
        st.error(f"목록 불러오기 실패: {e}")
        st.code(traceback.format_exc())
        return []

def delete_work(work_id):
    if not db: return
    try:
        db.collection("works").document(f"{device_id}_{work_id}").delete()
    except Exception as e:
        st.error(f"삭제 실패: {e}")

def generate_copy(platform, name, material, point):
    if "OPENAI_API_KEY" not in st.secrets: return "🚨 API 키가 없습니다."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        base = "[규칙: 1인칭 '모그' 작가 시점] 말투: ~이지요^^, ~해요. 특수기호(*, **) 금지."
        prompts = {
            "인스타": f"{base} [인스타] 감성, 일기투, 해시태그.",
            "아이디어스": f"{base} [아이디어스] 💡상세, 🍀Info, 🔉안내, 👍🏻보증 4단락.",
            "스토어": f"{base} [스토어] 💐이름, 🌸디자인, 👜기능, 📏사이즈, 📦소재, 🧼관리, 📍추천 7단락."
        }
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":prompts.get(platform, base)}, {"role":"user","content":f"이름:{name}, 소재:{material}, 특징:{point}"}]
        )
        return res.choices[0].message.content.replace("**", "").strip()
    except Exception as e: return f"AI 오류: {str(e)}"

# 3. UI 렌더링
if 'current_work' not in st.session_state: st.session_state.current_work = None
my_works = load_works()

with st.sidebar:
    st.title("📂 내 작품 목록")
    if st.button("➕ 새 작품 만들기", use_container_width=True, type="primary"):
        uid = str(uuid.uuid4())
        empty = {"name": "", "material": "", "point": "", "texts": {}}
        st.session_state.current_work = {"work_id": uid, **empty}
        save_to_db(uid, empty)
        st.rerun()
    st.divider()
    if not my_works: st.caption("저장된 작품이 없습니다.")
    for w in my_works:
        if st.button(f"📦 {w.get('name') or '이름 없음'}", key=w['work_id'], use_container_width=True):
            st.session_state.current_work = w
            st.rerun()

st.title("🌸 모그 작가님 AI 비서")

if not st.session_state.current_work:
    if my_works:
        st.session_state.current_work = my_works[0]
        st.rerun()
    else:
        st.info("👈 왼쪽 [➕ 새 작품 만들기] 버튼을 눌러주세요!")
        st.stop()

curr = st.session_state.current_work
c1, c2 = st.columns(2)

with c1:
    st.subheader("📝 정보 입력")
    nn = st.text_input("작품 이름", curr.get('name',''))
    nm = st.text_input("소재", curr.get('material',''))
    np = st.text_area("특징", curr.get('point',''), height=150)
    
    if nn!=curr.get('name') or nm!=curr.get('material') or np!=curr.get('point'):
        curr.update({'name':nn, 'material':nm, 'point':np})
        save_to_db(curr['work_id'], curr)
    st.caption("자동 저장됨")
    
    if st.button("🗑️ 삭제"):
        delete_work(curr['work_id'])
        st.session_state.current_work = None
        st.rerun()

with c2:
    st.subheader("✨ 글쓰기")
    tabs = st.tabs(["인스타", "아이디어스", "스토어"])
    texts = curr.get('texts', {})
    for i, (k, n) in enumerate([("insta","인스타"), ("idus","아이디어스"), ("store","스토어")]):
        with tabs[i]:
            if st.button(f"{n} 생성", key=f"b_{k}"):
                if not nn: st.warning("이름 입력 필요")
                else:
                    with st.spinner("작성 중..."):
                        texts[k] = generate_copy(k, nn, nm, np)
                        curr['texts'] = texts
                        save_to_db(curr['work_id'], curr)
                        st.rerun()
            st.text_area("결과", texts.get(k,""), height=400)
