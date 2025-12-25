import streamlit as st
from rembg import remove
from PIL import Image
import io

# 엄마를 위한 기본 설정
st.set_page_config(page_title="엄마의 AI 비서")

st.title("🌸 엄마 전용 AI 비서")
st.write("딸이 만든 엄마만을 위한 마법 도구예요!")

st.divider()

# 1단계: 사진 배경 지우기
st.header("📸 1. 사진 고르기")
uploaded_file = st.file_uploader("여기를 눌러서 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="엄마가 올린 사진", width=300)
    
    if st.button("✨ 배경 깨끗하게 지우기"):
        with st.spinner("AI가 고치는 중... 잠시만요!"):
            input_bytes = uploaded_file.getvalue()
            output_bytes = remove(input_bytes)
            result_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            
            white_bg = Image.new("RGBA", result_img.size, "WHITE")
            white_bg.paste(result_img, (0, 0), result_img)
            final_img = white_bg.convert("RGB")
            
            st.image(final_img, caption="완성됐어요!", width=300)
            
            buf = io.BytesIO()
            final_img.save(buf, format="JPEG")
            st.download_button("🎁 보정된 사진 저장하기", buf.getvalue(), "mom_photo.jpg", "image/jpeg")

st.divider()

# 2단계: 홍보 글 만들기
st.header("✍️ 2. 홍보 글 만들기")
p_name = st.text_input("작품 이름")
p_heart = st.text_area("엄마의 마음")

if st.button("🪄 홍보 문구 만들기"):
    if p_name and p_heart:
        txt = f"🌸 [{p_name}]\n\n{p_heart}\n\n정성을 다해 만들었습니다. 문의주세요! 😊"
        st.success("글 완성! 아래를 꾹 눌러 복사하세요.")
        st.text_area("결과", value=txt, height=200)
