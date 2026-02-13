# streamlit_app.py（恢复 Groq 问答版）
import streamlit as st
import os
from groq import Groq

# 页面配置
st.set_page_config(page_title="荆楚植物问答", page_icon="🌿")

# 初始化 Groq 客户端（从 Secrets 读取）
@st.cache_resource
def init_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("请在 Streamlit Secrets 中配置 GROQ_API_KEY")
        st.stop()
    return Groq(api_key=api_key)

client = init_groq()

# 页面内容
st.title("🌿 荆楚植物智能问答系统（Groq 版）")

st.info("当前模式：仅使用 Groq 大模型回答，不依赖 Neo4j 数据库。")

user_question = st.text_input("输入问题（如：梅花在荆楚文化中的象征意义？）")

if st.button("获取回答", type="primary"):
    if user_question:
        with st.spinner("🤔 正在生成回答..."):
            try:
                # 调用 Groq
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "你是荆楚植物文化专家，回答简洁准确，符合荆楚地域特色。"
                        },
                        {
                            "role": "user",
                            "content": user_question
                        }
                    ],
                    model="llama3-8b-8192",
                )
                answer = chat_completion.choices[0].message.content
                st.markdown("### 📝 回答")
                st.write(answer)
            except Exception as e:
                st.error(f"回答生成失败：{e}")
    else:
        st.warning("请先输入问题！")