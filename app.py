import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io

# 1. 앱 페이지 설정
st.set_page_config(page_title="엄마의 명품 비서 (최종판)", layout="wide")

st.title("🕯️ 엄마작가님 전용 명품 비서")
st.write("사진은 일괄 보정하고, 키워드만으로 정성 가득한 판매글을 완성하세요!")

st.divider()

# --- 1. 사진 일괄 보정 섹션 ---
st.header("📸 1. 사진 한 번에 보정하기")
uploaded_files = st.file_uploader("사진을 여러 장 선택하세요 (최대 10장)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    st.subheader("🎨 보정 강도 설정")
    col1, col2, col3 = st.columns(3)
    with col1:
        bright = st.select_slider("☀️ 화사함", options=["기본", "밝게", "매우 밝게"], value="밝게")
    with col2:
        sharp = st.select_slider("🔍 선명함", options=["자연스럽게", "선명하게", "또렷하게"], value="선명하게")
    with col3:
        smooth = st.select_slider("✨ 잡티 제거", options=["없음", "약하게", "강하게"], value="약하게")

    b_val = {"기본": 1.0, "밝게": 1.2, "매우 밝게": 1.4}[bright]
    s_val = {"자연스럽게": 1.0, "선명하게": 1.5, "또렷하게": 2.0}[sharp]
    m_val = {"없음": 0, "약하게": 1, "강하게": 2}[smooth]

    if st.button("🚀 모든 사진 일괄 보정하기"):
        cols = st.columns(len(uploaded_files))
        for idx, file in enumerate(uploaded_files):
            img = Image.open(file)
            edited = ImageEnhance.Brightness(img).enhance(b_val)
            edited = ImageEnhance.Color(edited).enhance(1.1)
            for _ in range(m_val):
                edited = edited.filter(ImageFilter.SMOOTH_MORE)
            edited = ImageEnhance.Sharpness(edited).enhance(s_val)
            
            with cols[idx]:
                st.image(edited, caption=f"보정본 {idx+1}", use_container_width=True)
                buf = io.BytesIO()
                edited.save(buf, format="JPEG", quality=95)
                st.download_button(f"📥 저장 {idx+1}", buf.getvalue(), f"photo_{idx+1}.jpg", "image/jpeg")

st.divider()

# --- 2. 스마트 문장 완성 글쓰기 ---
st.header("✍️ 2. 스마트 상세페이지 만들기")
st.write("단어만 툭툭 던져주세요. 제가 예쁜 문장으로 다듬어 드릴게요.")

with st.expander("내용 입력하기 (클릭)", expanded=True):
    p_name = st.text_input("📦 작품 이름", placeholder="예: 봄날 린넨 파우치")
    p_keys = st.text_input("🔑 핵심 키워드", placeholder="예: 핸드메이드, 가벼움, 튼튼함, 넉넉함")
    
    col_a, col_b = st.columns(2)
    with col_a:
        p_size = st.text_input("📏 사이즈", placeholder="예: 가로 20 세로 15")
        p_mat = st.text_input("🧵 재질", placeholder="예: 순면 100%")
    with col_b:
        p_use = st.text_input("💡 사용법", placeholder="예: 찬물 손세탁 권장")
        p_work = st.text_input("🛠️ 작업 과정", placeholder="예: 원단 세척부터 바느질까지 직접 작업")

if st.button("🪄 자연스러운 문장으로 만들기"):
    if p_name and p_keys:
        # 자연스러운 문장 변환 로직
        keywords = [k.strip() for k in p_keys.split(",")]
        
        # 문장 구성 예시: "이 작품은 핸드메이드라 정성이 가득하고 가벼움이 특징이에요. 또한 튼튼함까지 신경 써서 만들었습니다."
        if len(keywords) >= 3:
            keyword_intro = f"이 작품은 **{keywords[0]}**(이)라 정성이 가득하고, **{keywords[1]}**(이)가 특징이에요. 또한 **{keywords[2]}**까지 세심하게 신경 써서 만들었습니다."
        else:
            keyword_intro = f"**{p_keys}** 하나하나에 작가의 진심을 듬뿍 담아 제작했습니다."

        full_text = f"""
🌸 **{p_name}**

안녕하세요, 정성을 다해 만드는 작가입니다. 😊
오늘 소개해드릴 **{p_name}**은(는) 제가 직접 고른 좋은 재료로 오랜 시간 공들여 완성한 작품이에요.

{keyword_intro}

---

**[상세 정보]**
• **소재**: {p_mat if p_mat else '엄선한 고급 소재'}
• **사이즈**: {p_size if p_size else '상세 문의 부탁드려요'}
• **제작 과정**: {p_work if p_work else '한 땀 한 땀 정성을 담은 수작업'}

**[사용 및 관리]**
• {p_use if p_use else '소중한 작품이니 살살 다뤄주시면 오래 사용하실 수 있어요.'}

---
직접 눈으로 확인하고 맞춤법까지 꼼꼼히 체크해 보내드립니다. 
작가인 저의 마음이 잘 전달되길 바라며, 오늘도 행복한 하루 보내세요. 감사합니다! 🌸
        """
        st.success("자연스러운 판매글이 완성되었습니다!")
        st.text_area("결과 (복사해서 사용하세요)", value=full_text, height=450)
    else:
        st.warning("작품 이름과 키워드를 입력해 주세요!")
