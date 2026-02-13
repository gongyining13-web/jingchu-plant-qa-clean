# streamlit_app.py
import streamlit as st

st.set_page_config(page_title="荆楚植物问答", page_icon="🌿")
st.title("🌿 荆楚植物智能问答系统（极简版）")

st.info("当前为极简演示模式，用于验证部署环境。")

user_input = st.text_input("输入问题（如：梅花的象征意义？）")
if st.button("获取回答"):
    if user_input:
        st.success(f"你问的是：{user_input}")
        st.write("（演示模式：实际回答功能需连接 Groq API）")
    else:
        st.warning("请先输入问题")