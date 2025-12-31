import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime
import traceback
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 작가님 AI 비서", layout="wide", page_icon="🌸")

# ==========================================
# [섹션 A] 진실의 원천 (ID 확정 및 유지 로직)
# ==========================================

# 1. URL 파라미터 확인 (읽기)
found_id = None
try:
    qp = st.query_params
    val = qp.get("device_id")
    if val: found_id = val if isinstance(val, str) else val[0]
except:
    pass

# 2. Session State <-> URL 동기화 (새로고침 방어 핵심)
if found_id:
    # URL에 있으면 세션에 저장
    if "device_id" not in st.session_state:
        st.session_state["device_id"] = found_id
elif "device_id" in st.session_state:
    # 세션에만 있으면 URL에 복구 (새로고침 대비)
    try:
        st.query_params["device_id"] = st.session_state["device_id"]
    except:
        pass

# ==========================================
# [섹션 B] 화면 분기 (device_id 유무 기준)
# ==========================================

if "device_id" not in st.session_state:
    st.markdown("""
    <div style='text-align: center; padding-top: 50px; padding-bottom: 30px;'>
        <h1 style='color: #FF4B4B;'>🌸 모그 작가님 AI 비서</h1>
        <p style='font-size: 1.1em; color: #666;'>
            환영합니다, 작가님.<br>
            아래 버튼을 눌러 작업을 시작해주세요.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 작가님, 여기를 눌러 시작해주세요", use_container_width=True, type="primary"):
            new_id = f"mog_{str(uuid.uuid4())[:8]}"
            st.session_state["device_id"] = new_id
            try:
                st.query_params["device_id"] = new_id
            except:
                pass
            st.rerun()
    
    st.markdown("""
    <div style='text-align: center; margin-top: 40px; font-size: 0.85em; color: #999;'>
        * 버튼을 누르면 작가님만의 고유 주소가 생성됩니다.<br>
        * 주소를 <b>즐겨찾기</b> 해두시면 언제든 이어서 작성하실 수 있어요.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# [섹션 C] 메인 앱 준비
# ==========================================

device_id = st.session_state["device_id"]

# 1. Firebase 연결
db = None
try:
    if not firebase_admin._apps:
        if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
            raise ValueError("Secrets 설정을 확인해주세요.")
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error("🚨 서버와 연결할 수 없습니다.")
    st.stop()

# 2. 데이터 처리 함수들
def save_to_db(work_id, data):
    if not db: return
    try:
        doc_ref = db.collection("works").document(f"{device_id}_{work_id}")
        doc_ref.set({
            "device_id": device_id,
            "work_id": work_id,
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
            **data
        })
    except:
        st.toast("⚠️ 저장 중에 문제가 생겼어요.")

def load_works():
    if not db: return []
    try:
        docs = db.collection("works").where("device_id", "==", device_id).stream()
        return sorted(
            [doc.to_dict() for doc in docs], 
            key=lambda x: x.get('updated_at', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)), 
            reverse=True
        )
    except:
        st.toast("목록을 불러오지 못했습니다.")
        return []

def delete_work(work_id):
    if not db: return
    try:
        db.collection("works").document(f"{device_id}_{work_id}").delete()
        st.toast("작품이 삭제되었습니다.")
    except:
        st.toast("삭제 실패: 잠시 후 다시 시도해주세요.")

# [기능] 이미지 분석
def analyze_image_features(uploaded_file):
    if "OPENAI_API_KEY" not in st.secrets: return "API 키 오류"
    try:
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 핸드메이드 작품 분석가입니다. 사진의 색감, 분위기, 재질감, 시각적 특징을 3줄 이내로 간략히 요약하세요. 감탄사 생략, 핵심만 서술."},
                {"role": "user", "content": [{"type": "text", "text": "이 작품의 시각적 특징을 분석해줘."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"(사진 분석 실패: {str(e)})"

# [기능] 글 생성 (수정 요청 반영 + AI 흔적 제거)
def generate_copy(platform, name, material, size, duration, point, img_desc, feedback=None):
    if "OPENAI_API_KEY" not in st.secrets: return "🚨 API 키 설정을 확인해주세요."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # 기본 페르소나
        base_persona = """[역할] 당신은 핸드메이드 작가 '모그(Mog)'입니다. AI가 쓴 티가 나지 않도록 자연스러운 한국어를 구사하세요.
        [절대 금지] '**', '[ ]', '구조:', '단락:' 같은 메타 설명 문구 절대 출력 금지. 오직 결과물 텍스트만 출력."""
        
        # 플랫폼별 프롬프트
        if platform == "인스타":
            system_message = """
            [인스타 규칙] 100% 감성 독백형 에세이. 판매/상업 키워드 금지. 줄바꿈 자주.
            말끝: ~죠?, ~해요, ~랍니다, ~같아요. (다정하고 소박하게)
            구조: 도입(날씨/기분) -> 본문(감정/손맛) -> 정보(녹여서) -> 여운 남는 마무리 -> 해시태그.
            """
        elif platform == "아이디어스":
            system_message = """
            [아이디어스 규칙] 정보형 판매글. 감성/일기체 금지.
            말끝: ~에요, ~입니다. (친절한 설명체)
            구조(순서엄수): 1.요약(색감/분위기) 2.사이즈요약 3.〰️ 4.포인트(📌) 5.➖ 6.컨셉 7.작가소개 8.소재 9.상세사이즈 10.구성 11.제작/배송 12.세탁.
            """
        else:
            system_message = """
            [스토어 규칙] 신뢰감 있는 정보 전달. 3인칭 설명체(~입니다, ~있어요).
            구조: 1.제품요약 2.디자인/핏 3.스타일링 4.추천대상 5.소재 6.사이즈 7.촬영안내.
            """

        # 사용자 데이터
        user_input = f"""
        [Data] Name: {name}, Material: {material}, Size: {size}, Duration: {duration}, Point: {point}, Image Feature: {img_desc}
        """

        # [수정 요청 로직] 피드백이 있으면 프롬프트 강화
        if feedback:
            user_input += f"""
            \n[🚨 수정 요청사항]
            사용자가 현재 결과물이 마음에 들지 않아 수정을 요청했습니다.
            기존 내용을 바탕으로 아래 요청사항을 반영하여 '처음부터 다시' 작성하세요.
            요청: "{feedback}"
            """
        else:
            user_input += "\n[지시] 작가 입력 정보 최우선. 플랫폼별 어투/구조 100% 준수."

        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content": base_persona + "\n" + system_message}, 
                {"role":"user","content": user_input}
            ]
        )
        
        # [후처리] AI 흔적 강제 제거 (지시서 1번 항목)
        clean_text = res.choices[0].message.content
        clean_text = clean_text.replace("**", "").replace("[", "").replace("]", "")
        # 추가적인 메타 텍스트 제거 시도
        lines = clean_text.split('\n')
        filtered_lines = [line for line in lines if not line.strip().startswith(("구조:", "지시사항:", "단락"))]
        return "\n".join(filtered_lines).strip()

    except Exception as e: return f"AI 오류: {str(e)}"

# [숨김] 고민상담소 함수 (코드는 유지, UI 미노출)
def ask_consultant(history):
    pass 

# ==========================================
# [섹션 D] UI 레이아웃 구성
# ==========================================

# 1. 데이터 로드 및 복구 (새로고침 시 데이터 유지 핵심)
if 'current_work' not in st.session_state: st.session_state.current_work = None
my_works = load_works()

# [복구 로직] 세션에 작품이 없는데 DB에는 있다면, 가장 최신 작품 자동 선택
if st.session_state.current_work is None and my_works:
    st.session_state.current_work = my_works[0]

# 2. 사이드바
with st.sidebar:
    st.title("📂 내 작품 목록")
    if st.button("➕ 새 작품 만들기", use_container_width=True, type="primary"):
        uid = str(uuid.uuid4())
        empty = {"name": "", "material": "", "size": "", "duration": "", "point": "", "image_analysis": "", "texts": {}}
        st.session_state.current_work = {"work_id": uid, **empty}
        save_to_db(uid, empty)
        st.rerun()
    
    st.divider()
    
    if not my_works:
        st.caption("목록이 비어있습니다.")
    else:
        for w in my_works:
            label = w.get('name') or "(이름 없는 작품)"
            is_active = st.session_state.current_work and st.session_state.current_work['work_id'] == w['work_id']
            if st.button(f"{'👉' if is_active else '📦'} {label}", key=w['work_id'], use_container_width=True):
                st.session_state.current_work = w
                st.rerun()

st.title("🌸 모그 작가님 AI 비서")

# 3. 메인 화면 (상단 탭 제거 -> 즉시 렌더링)
if not st.session_state.current_work:
    st.info("👈 왼쪽 사이드바의 [➕ 새 작품 만들기] 버튼을 눌러주세요!")
    st.stop()

curr = st.session_state.current_work
wid = curr['work_id']

# 데이터 로드
c_name = curr.get('name', '')
c_mat = curr.get('material', '')
c_size = curr.get('size', '')
c_dur = curr.get('duration', '')
c_point = curr.get('point', '')
c_img_anl = curr.get('image_analysis', '')

c1, c2 = st.columns(2)

with c1:
    st.subheader("📝 기본 정보 입력")
    nn = st.text_input("작품 이름", value=c_name, key=f"input_name_{wid}")
    
    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        nm = st.text_input("소재", value=c_mat, key=f"input_mat_{wid}")
    with col_sub2:
        ns = st.text_input("사이즈 (예: 20x30cm)", value=c_size, key=f"input_size_{wid}")
        
    nd = st.text_input("제작 소요 기간 (예: 3일)", value=c_dur, key=f"input_dur_{wid}")
    np = st.text_area("특징 / 포인트 (작가님 생각)", value=c_point, height=100, key=f"input_point_{wid}")

    st.markdown("---")
    st.subheader("📸 사진 보조 (선택)")
    
    uploaded_img = st.file_uploader("작품 사진을 올리면 AI가 특징을 읽어줍니다", type=['png', 'jpg', 'jpeg'], key=f"uploader_{wid}")
    
    if uploaded_img:
        if st.button("✨ 이 사진 특징 분석하기", key=f"btn_anal_{wid}"):
            with st.spinner("사진을 꼼꼼히 보고 있어요..."):
                analysis_result = analyze_image_features(uploaded_img)
                c_img_anl = analysis_result
                curr.update({'image_analysis': c_img_anl})
                save_to_db(wid, curr)
                st.session_state[f"input_img_anl_{wid}"] = analysis_result
                st.rerun()

    n_img_anl = st.text_area("AI가 분석한 사진 특징 (수정 가능)", value=c_img_anl, height=80, key=f"input_img_anl_{wid}", placeholder="사진을 올리고 분석 버튼을 누르면 채워집니다.")

    # 자동 저장
    if (nn!=c_name or nm!=c_mat or ns!=c_size or nd!=c_dur or np!=c_point or n_img_anl!=c_img_anl):
        curr.update({'name': nn, 'material': nm, 'size': ns, 'duration': nd, 'point': np, 'image_analysis': n_img_anl})
        save_to_db(wid, curr)

    st.caption("모든 내용은 자동으로 저장됩니다.")
    
    if st.button("🗑️ 이 작품 삭제", key=f"btn_del_{wid}"):
        delete_work(wid)
        st.session_state.current_work = None
        st.rerun()

with c2:
    st.subheader("✨ 글쓰기")
    # 상단바 제거하고 바로 플랫폼 탭 표시
    sub_tabs = st.tabs(["인스타", "아이디어스", "스토어"])
    texts = curr.get('texts', {})
    
    def render_platform_ui(tab, platform_key, platform_name):
        with tab:
            # 1. 글 짓기 버튼
            if st.button(f"{platform_name} 글 짓기 (처음 생성)", key=f"btn_gen_{platform_key}_{wid}", type="primary"):
                if not nn: st.toast("작품 이름을 먼저 입력해주세요! 😅")
                else:
                    with st.spinner(f"모그 작가님 말투로 {platform_name} 글을 쓰는 중..."):
                        res = generate_copy(platform_name, nn, nm, ns, nd, np, n_img_anl)
                        texts[platform_key] = res
                        curr['texts'] = texts
                        save_to_db(wid, curr)
                        st.session_state[f"result_{platform_key}_{wid}"] = res
                        st.rerun()
            
            # 2. 결과물 출력
            current_text = texts.get(platform_key, "")
            st.text_area("결과물", value=current_text, height=500, key=f"result_{platform_key}_{wid}")
            
            # 3. [신규] 수정 요청 UI (결과물이 있을 때만 노출)
            if current_text:
                with st.container():
                    st.markdown("---")
                    st.caption(f"🔧 맘에 안 드시나요? 수정 사항을 적어주세요.")
                    col_feed, col_btn = st.columns([3, 1])
                    with col_feed:
                        feedback = st.text_input(f"{platform_name} 수정 요청사항", placeholder="예: 말투를 더 부드럽게 해줘, 너무 기니까 줄여줘", key=f"feed_{platform_key}_{wid}", label_visibility="collapsed")
                    with col_btn:
                        if st.button("다시 쓰기", key=f"btn_regen_{platform_key}_{wid}"):
                            if not feedback:
                                st.toast("수정 요청사항을 입력해주세요!")
                            else:
                                with st.spinner(f"요청하신 대로 '{feedback}' 반영해서 다시 쓰는 중..."):
                                    # 피드백 반영해서 재생성
                                    res = generate_copy(platform_name, nn, nm, ns, nd, np, n_img_anl, feedback=feedback)
                                    texts[platform_key] = res
                                    curr['texts'] = texts
                                    save_to_db(wid, curr)
                                    st.session_state[f"result_{platform_key}_{wid}"] = res
                                    st.rerun()

    render_platform_ui(sub_tabs[0], "insta", "인스타")
    render_platform_ui(sub_tabs[1], "idus", "아이디어스")
    render_platform_ui(sub_tabs[2], "store", "스토어")
