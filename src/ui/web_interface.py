import streamlit as st
import sys
import os
import random

# 修正模块导入路径：把 src/api 加入 Python 搜索路径
current_dir = os.path.dirname(__file__)  # 当前文件所在目录：src/ui
src_dir = os.path.abspath(os.path.join(current_dir, ".."))  # 上级目录：src
sys.path.append(os.path.join(src_dir, "api"))  # 加入 src/api 目录

# 现在可以正常导入
from langchain_qa import LangChainPlantQA

# 初始化问答系统
@st.cache_resource
def get_qa_system():
    return LangChainPlantQA()

qa = get_qa_system()

# --- 页面配置与主题 ---
st.set_page_config(
    page_title="荆楚植物文化图谱（智能版）",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS，优化视觉效果
st.markdown("""
<style>
    :root {
        --primary-color: #2E8B57; /* 主色调：明快的绿色 */
        --background-color: #F5F5F5; /* 背景色：浅灰 */
        --text-color: #333333; /* 文本色：深灰 */
        --card-color: #FFFFFF; /* 卡片色：白色 */
        --accent-color: #FF6347; /* 强调色：珊瑚红 */
    }
    body {
        color: var(--text-color);
        background-color: var(--background-color);
    }
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #236b44;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .sidebar .stExpander {
        background-color: var(--card-color);
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .main .stCard {
        background-color: var(--card-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .highlight {
        background-color: #E8F5E9;
        padding: 10px;
        border-left: 4px solid var(--primary-color);
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏：折叠式植物详情 ---
st.sidebar.title("🌿 荆楚植物图谱")
plant_list = qa.plant_names
selected_plant = st.sidebar.selectbox("选择植物查看详情", plant_list)

# 折叠框：默认收起，点击展开
with st.sidebar.expander(f"📖 {selected_plant} 详情", expanded=False):
    if selected_plant:
        detail = qa.get_plant_detail(selected_plant)
        if detail:
            st.markdown(f"**拉丁名**：{detail['latin']}")
            st.markdown(f"**科**：{detail['family']}")
            st.markdown(f"**属**：{detail['genus']}")
            st.markdown(f"**分布**：{detail['distribution']}")
            
            # 使用不同颜色区分信息块
            st.markdown(f"🪴 **民俗用途**：{detail['folk_use']}", unsafe_allow_html=True)
            st.markdown(f"🌍 **生态意义**：{detail['ecological']}", unsafe_allow_html=True)
            st.markdown(f"🎨 **文化象征**：{detail['cultural_symbol']}", unsafe_allow_html=True)
            
            if detail['symbols']:
                st.markdown("💡 **象征意义**：" + "、".join(detail['symbols']))
            if detail['medicinal']:
                st.markdown("💊 **药用价值**：" + "、".join(detail['medicinal']))
            if detail['literature']:
                st.markdown("📜 **文献记载**：" + "、".join(detail['literature']))
            if detail['festivals']:
                st.markdown("🎉 **关联节日**：" + "、".join(detail['festivals']))

# --- 主页面：双栏布局 + 更多交互 ---
st.title("🤖 荆楚植物智能问答")
st.markdown("探索荆楚大地上的植物文化，解锁它们背后的故事与智慧。")

# 主页面分为两栏
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 智能问答")
    st.markdown("你可以问我关于荆楚植物的文化、分布、药用价值等问题。")
    
    # 热门问题快捷按钮
    st.markdown("#### 热门问题：")
    hot_questions = [
        "兰有什么文化象征？",
        "菖蒲在端午节有什么用途？",
        "哪些植物有药用价值？",
        "湖北有哪些特色水生植物？"
    ]
    cols = st.columns(4)
    for i, q in enumerate(hot_questions):
        with cols[i]:
            if st.button(q, key=f"hot_{i}"):
                st.session_state.user_question = q

    # 问答输入框
    user_question = st.text_input(
        "或者输入你的问题：",
        value=st.session_state.get("user_question", ""),
        placeholder="例如：荆楚地区最具代表性的植物是什么？"
    )
    
    if st.button("获取答案", key="answer_btn") and user_question:
        with st.spinner("正在思考..."):
            answer = qa.answer(user_question)
            st.markdown(answer, unsafe_allow_html=True)

with col2:
    st.markdown("### 🌱 今日推荐")
    # 随机推荐一种植物
    random_plant = random.choice(plant_list)
    random_detail = qa.get_plant_detail(random_plant)
    
    st.markdown(f"#### {random_plant}")
    st.markdown(f"**拉丁名**：{random_detail['latin']}")
    st.markdown(f"**文化象征**：{random_detail['cultural_symbol']}")
    st.markdown(f"**分布**：{random_detail['distribution']}")
    
    st.markdown("---")
    st.markdown("### 📊 数据概览")
    st.markdown(f"**植物总数**：{len(plant_list)} 种")
    st.markdown(f"**科属数量**：{len(set([qa.get_plant_detail(p)['family'] for p in plant_list]))} 科")
    st.markdown(f"**关联节日**：{len(set([f for p in plant_list for f in qa.get_plant_detail(p)['festivals']]))} 个")

# --- 页脚 ---
st.markdown("---")
st.markdown("💡 数据来源：荆楚植物文化图谱数据库 | 技术支持：LangChain + Neo4j + Streamlit")