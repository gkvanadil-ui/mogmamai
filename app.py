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
# [섹션 A] 진실의 원천 (ID 확정 로직)
# ==========================================

found_id = None
try:
    qp = st.query_params
    val = qp.get("device_id")
    if val: found_id = val if isinstance(val, str) else val[0]
except:
    try:
        qp = st.experimental_get_query_params()
        if "device_id" in qp: found_id = qp["device_id"][0]
    except:
        pass

if found_id and "device_id" not in st.session_state:
    st.session_state["device_id"] = found_id

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
                st.experimental_set_query_params(device_id=new_id)
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
# [섹션 C] 메인 앱
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
    with st.expander("상세 오류 보기"):
        st.code(traceback.format_exc())
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
    except Exception as e:
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
    except Exception as e:
        st.toast("목록을 불러오지 못했습니다.")
        return []

def delete_work(work_id):
    if not db: return
    try:
        db.collection("works").document(f"{device_id}_{work_id}").delete()
        st.toast("작품이 삭제되었습니다.")
    except Exception as e:
        st.toast("삭제 실패: 잠시 후 다시 시도해주세요.")

# [기능] 이미지 분석 (Vision API)
def analyze_image_features(uploaded_file):
    if "OPENAI_API_KEY" not in st.secrets: return "API 키 오류"
    try:
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 핸드메이드 작품 분석가입니다. 사진의 색감, 분위기, 재질감, 시각적 특징을 3줄 이내로 간략히 요약하세요. 감탄사 생략, 핵심만 서술."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "이 작품의 시각적 특징을 분석해줘."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"(사진 분석 실패: {str(e)})"

# [기능] 글 생성 (플랫폼별 어투 강제 적용)
def generate_copy(platform, name, material, size, duration, point, img_desc):
    if "OPENAI_API_KEY" not in st.secrets: return "🚨 API 키 설정을 확인해주세요."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # 1. 공통 기본 페르소나 (모그 작가)
        base_persona = """[역할 정의]
        당신은 핸드메이드 작가 '모그(Mog)'입니다.
        기계적인 느낌 없이, 사람의 온기가 느껴지는 따뜻한 글을 씁니다.
        특수기호(*, **) 사용은 절대 금지입니다.
        """
        
        # 2. 플랫폼별 프롬프트 분기 (인스타 / 아이디어스 / 스토어)
        if platform == "인스타":
            # [인스타] 감성 일기 스타일
            specific_prompt = """
            [인스타그램 글짓기 절대 규칙]
            1. 이 글은 판매글이 아니라, 작가가 작업실에서 조용히 이야기를 건네듯 쓰는 글입니다.
            2. 문장이 완벽하지 않아도 괜찮습니다. 설명보다 '느낌'과 '분위기' 위주로 작성하세요.
            3. 정돈된 설명보다 손의 온기가 느껴지는 글이 우선입니다.
            4. 문장은 짧게 끊고, 줄바꿈을 자주 하여 여백의 미를 살려주세요.
            5. 과장된 광고 문구나 "구매하세요" 같은 직접적인 요구는 하지 마세요.
            
            [말투 가이드]
            - 1인칭 '모그' 시점 유지.
            - 말끝: ~죠? ~해요. ~랍니다. ~같아요. ~했어요. (다정하고 소박하게)
            - 감탄사는 절제하고, 차분한 독백체로 작성하세요.
            - "정성", "조물조물", "하나하나", "조금씩 다르지만" 같은 표현을 자연스럽게 사용하세요.
            
            [작성 구조]
            1. 감성적인 독백이나 날씨, 작업실 분위기로 시작 (줄바꿈 필수)
            2. 작품의 특징(소재, 느낌)을 이야기하듯 서술 (줄바꿈 필수)
            3. 하단에 사이즈/제작기간 정보를 아주 심플하게 정리
            4. 관련 해시태그 10개
            """
            system_message = base_persona + "\n" + specific_prompt

        elif platform == "아이디어스":
            # [아이디어스] 정보형 판매글 스타일 (신규 적용)
            specific_prompt = """
            [아이디어스 판매글 절대 규칙]
            1. 성격: 정보형 판매 설명 글. 구매자가 스크롤하며 정보를 빠르게 파악해야 함. 감성 마케팅이나 일기 형식이 아님.
            2. 문체: 짧고 명확한 설명체 + 차분한 친절함. 과도한 시적 표현이나 감탄사 금지.
            3. 이모지: ✔️ 📌 💓 💁‍♀️ 등 정보 강조용으로만 제한적 사용. 말끝에 ^^, ㅎㅎ 사용 절대 금지.
            4. 구성: 한 문단은 1~2줄로 짧게. 문단 사이 빈 줄 필수. 구분선(〰️) 사용하여 구획 분리.

            [작성 구조 순서 (반드시 준수)]
            1. [첫 문단] 색감/분위기 한 줄 요약 + "~파우치에요" 식의 명확한 제품 정의.
            2. [사이즈 요약] S/M 여부 언급 + "상세사이즈 하단 참고" 문구.
            3. (구분선 〰️)
            4. [포인트] 📌 이모지 사용. 활용도, 선물/데일리 추천 이유.
            5. (구분선 〰️)
            6. [컨셉] 제품 컨셉 한 줄 (질문형 허용).
            7. [작가 소개] 과장 없이 담백하게 한 문단.
            8. [소재] 겉감, 안감, 소재 특성 및 주의사항 (항목형 서술).
            9. [상세 사이즈] S/M 각각 분리, 수납 예시는 문장형으로 설명.
            10. [구성] 기본 구성 및 추가 옵션(괄호 처리).
            11. [제작/배송] 미리 제작 여부, 사이즈 변경 가능/불가 명시.
            12. [세탁] 세탁 방법 항목형 설명.

            [어투 가이드 (복사 금지, 뉘앙스만 참고)]
            "어떤 가방에도 쏙 들어가는 귀여운 사이즈의 파우치에요."
            "탄탄한 옥스포드 원단을 사용하여 흐물거리지 않습니다."
            "주문 확인 후 제작에 들어가는 핸드메이드 작품입니다."
            "세탁 시 미온수에 중성세제를 풀어 조물조물 손세탁 해주세요."
            """
            system_message = base_persona + "\n" + specific_prompt

        else:
            # [스토어] 기존 로직 유지
            store_rules = "[스토어] 💐상품명, 🌸디자인, 👜기능/특징, 📏사이즈/제작기간, 📦소재, 🧼관리법, 📍추천이유 7단락 구조 준수."
            system_message = base_persona + "\n" + store_rules

        # 사용자 입력 데이터 조합
        user_input = f"""
        [작품 기본 정보]
        - 이름: {name}
        - 소재: {material}
        - 사이즈: {size}
        - 제작기간: {duration}
        - 특징/포인트: {point}
        
        [사진에서 분석된 시각적 특징 (참고용)]
        {img_desc}
        
        [지시사항]
        1. 작가가 직접 입력한 [작품 기본 정보]가 가장 중요합니다.
        2. 사진 특징은 글의 분위기를 살리는 용도로만 자연스럽게 녹여내세요.
        3. 각 플랫폼별 정의된 말투와 구조 규칙을 100% 준수하세요.
        """
        
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content": system_message}, 
                {"role":"user","content": user_input}
            ]
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
        # 신규 필드 포함 초기화
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
            # Key 유일성 보장
            if st.button(f"{'👉' if is_active else '📦'} {label}", key=w['work_id'], use_container_width=True):
                st.session_state.current_work = w
                st.rerun()

st.title("🌸 모그 작가님 AI 비서")

if not st.session_state.current_work:
    if my_works:
        st.session_state.current_work = my_works[0]
        st.rerun()
    else:
        st.info("👈 왼쪽 사이드바의 [➕ 새 작품 만들기] 버튼을 눌러주세요!")
        st.stop()

curr = st.session_state.current_work
wid = curr['work_id']

# 데이터 안전 조회
c_name = curr.get('name', '')
c_mat = curr.get('material', '')
c_size = curr.get('size', '')
c_dur = curr.get('duration', '')
c_point = curr.get('point', '')
c_img_anl = curr.get('image_analysis', '')

c1, c2 = st.columns(2)

with c1:
    st.subheader("📝 기본 정보 입력")
    
    # [입력 필드] 모든 위젯에 고유 Key 부여
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
    
    # 사진 업로더
    uploaded_img = st.file_uploader("작품 사진을 올리면 AI가 특징을 읽어줍니다", type=['png', 'jpg', 'jpeg'], key=f"uploader_{wid}")
    
    # 사진 분석 버튼
    if uploaded_img:
        if st.button("✨ 이 사진 특징 분석하기", key=f"btn_anal_{wid}"):
            with st.spinner("사진을 꼼꼼히 보고 있어요..."):
                analysis_result = analyze_image_features(uploaded_img)
                c_img_anl = analysis_result
                curr.update({'image_analysis': c_img_anl})
                save_to_db(wid, curr)
                st.rerun()

    # 분석 결과 표시
    n_img_anl = st.text_area("AI가 분석한 사진 특징 (수정 가능)", value=c_img_anl, height=80, key=f"input_img_anl_{wid}", placeholder="사진을 올리고 분석 버튼을 누르면 채워집니다.")

    # 저장 로직
    if (nn!=c_name or nm!=c_mat or ns!=c_size or nd!=c_dur or np!=c_point or n_img_anl!=c_img_anl):
        curr.update({
            'name': nn, 'material': nm, 'size': ns, 'duration': nd, 
            'point': np, 'image_analysis': n_img_anl
        })
        save_to_db(wid, curr)

    st.caption("모든 내용은 자동으로 저장됩니다.")
    
    if st.button("🗑️ 이 작품 삭제", key=f"btn_del_{wid}"):
        delete_work(wid)
        st.session_state.current_work = None
        st.rerun()

with c2:
    st.subheader("✨ 글쓰기")
    tabs = st.tabs(["인스타", "아이디어스", "스토어"])
    texts = curr.get('texts', {})
    
    def render_tab(tab, platform_key, platform_name):
        with tab:
            # 생성 버튼
            if st.button(f"{platform_name} 글 짓기", key=f"btn_gen_{platform_key}_{wid}"):
                if not nn: st.toast("작품 이름을 먼저 입력해주세요! 😅")
                else:
                    with st.spinner(f"모그 작가님 말투로 {platform_name} 글을 쓰는 중..."):
                        # 모든 필드 정보를 AI에게 전달
                        res = generate_copy(platform_name, nn, nm, ns, nd, np, n_img_anl)
                        texts[platform_key] = res
                        curr['texts'] = texts
                        save_to_db(wid, curr)
                        st.rerun()
            
            # 결과 표시 (Key 충돌 방지 적용)
            st.text_area("결과물", value=texts.get(platform_key,""), height=500, key=f"result_{platform_key}_{wid}")

    render_tab(tabs[0], "insta", "인스타")
    render_tab(tabs[1], "idus", "아이디어스")
    render_tab(tabs[2], "store", "스토어")
