import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io

# 1. 앱 기본 설정
st.set_page_config(page_title="엄마의 명품 보정 & 상세페이지")

st.title("✨ 작가님 전용 명품 보정 도구")
st.write("사진은 화사하게, 글은 꼼꼼하게 완성해드려요.")

st.divider()

# 2. 사진 보정 기능 (배경 잡티 완화 + 색감)
st.header("📸 1. 사진 보정하기")
uploaded_file = st.file_uploader("보정할 작품 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    # 보정 옵션 (사용자 친화적인 명칭)
    smooth = st.slider("✨ 배경 잡티 지우기 (부드럽게)", 0, 5, 1)
    bright = st.slider("☀️ 밝기 조절 (화사하게)", 0.5, 2.0, 1.1)
    sharp = st.slider("🔍 선명도 조절 (디테일 살리기)", 0.5, 3.0, 1.5)
    color = st.slider("🌈 색감 조절 (생생하게)", 0.5, 2.0, 1.2)

    if st.button("🚀 보정 적용 및 미리보기"):
        # 보정 프로세스
        enhancer = ImageEnhance.Brightness(img)
        edited = enhancer.enhance(bright)
        
        enhancer = ImageEnhance.Color(edited)
        edited = enhancer.enhance(color)
        
        for _ in range(smooth):
            edited = edited.filter(ImageFilter.SMOOTH_MORE)
            
        enhancer = ImageEnhance.Sharpness(edited)
        edited = enhancer.enhance(sharp)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("보정 전")
            st.image(img, use_container_width=True)
        with col2:
            st.write("보정 후")
            st.image(edited, use_container_width=True)
        
        buf = io.BytesIO()
        edited.save(buf, format="JPEG", quality=95)
        st.download_button(
            label="📥 보정된 사진 저장하기",
            data=buf.getvalue(),
            file_name="refined_product.jpg",
            mime="image/jpeg"
        )

st.divider()

# 3. 항목별 상세 설명 제작 (요청하신 분류 적용)
st.header("✍️ 2. 상세페이지 글쓰기")
st.write("각 항목을 채워주시면 정돈된 판매글로 만들어드려요.")

p_name = st.text_input("📦 작품 이름", placeholder="예: 봄날의 린넨 파우치")
p_desc = st.text_area("📝 작품 설명", placeholder="어떤 마음으로 만드셨는지 적어주세요.")
p_size = st.text_input("📏 사이즈", placeholder="예: 가로 20cm x 세로 15cm")
p_material = st.text_input("🧵 재질", placeholder="예: 순면 100%, 린넨")
p_usage = st.text_area("💡 사용법 및 주의사항", placeholder="예: 가벼운 손세탁을 권장합니다.")
p_process = st.text_area("🛠️ 작업 과정", placeholder="예: 원단 세척부터 바느질까지 100% 수작업으로 진행됩니다.")

if st.button("🪄 전문 판매글 완성하기"):
    if p_name:
        full_text = f"""
🌸 **[{p_name}]**

---

**[작품 설명]**
{p_desc}

**[재질]**
{p_material}

**[사이즈]**
{p_size}

**[작업 과정]**
{p_process}

**[사용법 및 주의사항]**
{p_usage}

---
* 정성을 다해 직접 만듭니다. 궁금한 점은 언제든 편하게 문의주세요! 😊
"""
        st.success("상세페이지 문구가 완성되었습니다!")
        st.text_area("아래 내용을 꾹 눌러 복사해서 사용하세요", value=full_text, height=450)
    else:
        st.warning("작품 이름을 먼저 입력해주세요!")
