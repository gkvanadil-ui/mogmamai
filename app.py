import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="모그(Mog) AI 스튜디오", layout="wide")

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.sidebar.header("⚙️ AI 설정")
    api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")
else:
    st.sidebar.success("✅ 모그 AI 비서 연결됨")

st.title("🕯️ 모그(Mog) 작가 전용 AI 비서")
st.write("'세상에 단 하나뿐인 온기'를 전하는 작가님의 콘텐츠 제작실입니다.")

st.divider()

# --- [공통 입력 구역] ---
with st.expander("📦 작업할 작품 정보 입력", expanded=True):
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        name = st.text_input("제품명", placeholder="예: 앤과 푸우 보스턴백")
        keys = st.text_area("특징/스토리", placeholder="예: 여행을 꿈꾸며 만든 단 하나뿐인 패치워크")
    with col_in2:
        mat = st.text_input("소재/사이즈", placeholder="예: 유럽 리넨, 가죽 손잡이, 30x40cm")
        process = st.text_area("제작 디테일", placeholder="예: 손바느질 자국, 정성스러운 안감 처리")

# --- [중요] 탭 선언 (이 부분이 에러의 원인이었습니다) ---
tabs = st.tabs(["✍️ 글쓰기 센터", "🎨 이미지 & 상세페이지", "📱 영상 제작 팁"])

# --- [Tab 1: 글쓰기 센터] ---
with tabs[0]:
    st.subheader("매체별 맞춤 판매글")
    sub_tabs = st.tabs(["인스타그램", "아이디어스", "스마트스토어"])
    
    def generate_moog_text(platform, prompt_extra):
        if not api_key or not name:
            st.warning("상단의 작품 정보를 먼저 입력해주세요.")
            return
        client = openai.OpenAI(api_key=api_key)
        full_prompt = f"""당신은 브랜드 '모그'의 작가 본인입니다. [{platform}] 판매글을 작성하세요.
        - 별표(**) 금지, 다정한 말투(~이지요, ~했답니다), 본론(인사)부터 시작.
        - 제품:{name}, 특징:{keys}, 소재:{mat}, 디테일:{process}
        - {prompt_extra}"""
        with st.spinner("작가님의 목소리를 담는 중..."):
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
            st.text_area(f"{platform} 결과", value=res.choices[0].message.content.replace("**", ""), height=450)

    with sub_tabs[0]:
        if st.button("🪄 인스타용 생성"): generate_moog_text("인스타그램", "짧고 감성적으로, 해시태그 포함.")
    with sub_tabs[1]:
        if st.button("🪄 아이디어스용 생성"): generate_moog_text("아이디어스", "모바일 가독성을 위해 한 줄에 한 문장씩 줄바꿈 필수.")
    with sub_tabs[2]:
        if st.button("🪄 스마트스토어용 생성"): generate_moog_text("스마트스토어", "구분선과 이모지를 사용하여 친절하게 정리.")

# --- [Tab 2: 이미지 & 상세페이지] ---
with tabs[1]:
    col_img1, col_img2 = st.columns([1, 1.2])
    
    with col_img1:
        st.subheader("📸 사진 자동 보정")
        uploaded_files = st.file_uploader("보정할 사진 선택", type=["jpg", "png"], accept_multiple_files=True)
        if uploaded_files and api_key and st.button("🚀 사진 일괄 보정"):
            client = openai.OpenAI(api_key=api_key)
            cols = st.columns(2)
            for idx, file in enumerate(uploaded_files):
                img_bytes = file.getvalue()
                encoded = base64.b64encode(img_bytes).decode('utf-8')
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [{"type": "text", "text": "화사한 보정 수치 JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}]}],
                    response_format={"type": "json_object"}
                )
                vals = json.loads(res.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageEnhance.Brightness(img).enhance(vals.get('b', 1.1))
                img = ImageEnhance.Color(img).enhance(vals.get('c', 1.1))
                with cols[idx % 2]:
                    st.image(img, use_container_width=True)

    with col_img2:
        st.subheader("🎨 캔바(Canva) 상세페이지 제작")
        
        # 따님이 만든 캔바 템플릿 주소를 아래 주소 대신 넣어주세요!
        canva_url = "https://www.canva.com/" 
        st.link_button("✨ 모그 전용 캔바 작업실 열기", canva_url, use_container_width=True)
        
        st.divider()
        
        if st.button("🪄 캔바 대량 제작용 데이터 만들기"):
            if not name:
                st.warning("상단의 작품 정보를 먼저 입력해주세요.")
            else:
                client = openai.OpenAI(api_key=api_key)
                prompt = f"""
                브랜드 '모그'의 {name} 상세페이지 5장을 기획하세요.
                반드시 아래 구조의 JSON 배열로만 답변하세요.
                [
                  {{"순서": "1", "메인문구": "문구", "설명": "설명", "사진구도": "제안"}}
                ]
                별표(**) 금지, 다정한 말투.
                """
                with st.spinner("캔바 레시피 생성 중..."):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={ "type": "json_object" }
                    )
                    data = json.loads(response.choices[0].message.content)
                    # 데이터 키값 추출 시 유연성 확보
                    first_key = list(data.keys())[0]
                    df = pd.DataFrame(data[first_key])
                    
                    st.table(df)
                    
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 캔바 업로드용 파일(.csv) 받기",
                        data=csv,
                        file_name=f"moog_canva_{name}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

# --- [Tab 3: 영상 제작 팁] ---
with tabs[2]:
    st.subheader("📱 에픽(EPIK) 앱으로 영상 완성하기")
    st.info("""
    **따님이 추천하는 초간편 영상 제작법:**
    1. **에픽(EPIK) 앱** 실행 -> 하단 **[템플릿]** 클릭
    2. **'핸드메이드'** 혹은 **'감성'** 검색 후 마음에 드는 디자인 선택
    3. 보정한 사진들을 넣기만 하면 음악과 효과가 자동으로 붙습니다!
    
    💡 자막이 고민될 땐 '글쓰기 센터'에서 만든 문구를 복사해서 쓰세요.
    """)
