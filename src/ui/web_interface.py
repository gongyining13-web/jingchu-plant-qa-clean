import streamlit as st
import random
from src.api.langchain_qa import LangChainPlantQA  # 这里改成绝对导入

# 初始化问答系统
qa = LangChainPlantQA()
plant_list = qa.get_all_plants()

st.title("🌿 荆楚植物智能问答系统")

# 侧边栏
with st.sidebar:
    st.markdown("### 🌱 关于")
    st.markdown("本系统基于荆楚植物文化图谱数据库，结合大语言模型提供智能问答服务。")
    st.markdown("---")
    st.markdown("### 🔍 功能")
    st.markdown("- 植物信息查询")
    st.markdown("- 文化象征解读")
    st.markdown("- 关联节日推荐")

# 主界面
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### ❓ 智能问答")
    user_question = st.text_input("输入你的问题（如：梅花的文化象征？）")
    if st.button("获取回答"):
        if user_question:
            answer = qa.answer_question(user_question)
            st.markdown(answer, unsafe_allow_html=True)

with col2:
    st.markdown("### 🌱 今日推荐")
    # 随机推荐一种植物
    random_plant = random.choice(plant_list)
    random_detail = qa.get_plant_detail(random_plant)

    st.markdown(f"#### {random_plant}")
    st.markdown(f"**拉丁名**: {random_detail['latin']}")
    st.markdown(f"**文化象征**: {random_detail['cultural_symbol']}")
    st.markdown(f"**分布**: {random_detail['distribution']}")

    st.markdown("---")
    st.markdown("### 📊 数据概览")
    st.markdown(f"**植物总数**: {len(plant_list)} 种")
    st.markdown(f"**科属数量**: {len(set([qa.get_plant_detail(p)['family'] for p in plant_list]))} 个")
    st.markdown(f"**关联节日**: {len(set([f for p in plant_list for f in qa.get_plant_detail(p)['festivals']]))} 个")

# --- 页脚 ---
st.markdown("---")
st.markdown("💡 数据来源：荆楚植物文化图谱数据库 | 技术支持：LangChain + Neo4j + Streamlit")