import streamlit as st
import random
from src.api.langchain_qa import LangChainPlantQA

# 页面配置（必须放在最前面）
st.set_page_config(
    page_title="荆楚植物智能问答系统",
    page_icon="🌿",
    layout="wide"
)

# 初始化问答系统（全局只初始化一次）
@st.cache_resource
def init_qa_system():
    """缓存问答系统实例，避免重复初始化"""
    try:
        return LangChainPlantQA()
    except Exception as e:
        st.error(f"系统初始化失败：{e}")
        st.stop()

qa = init_qa_system()
plant_list = qa.get_all_plants()

# 页面样式美化
st.markdown("""
<style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        height: 3em;
        width: 100%;
    }
    .stTextInput>div>div>input {
        height: 3em;
    }
    .sidebar .sidebar-content {
        background-color: #f0f8fb;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.title("🌿 荆楚植物智能问答系统")

# 侧边栏
with st.sidebar:
    st.markdown("### 🌱 关于系统")
    st.markdown("本系统基于荆楚植物文化知识，结合大语言模型提供智能问答服务。")
    
    st.markdown("---")
    st.markdown("### 🔧 运行状态")
    if qa.neo4j_connected:
        st.success("✅ Neo4j 数据库已连接")
    else:
        st.warning("ℹ️ 离线模式（仅使用示例数据）")
    
    st.markdown("---")
    st.markdown("### ❓ 使用示例")
    st.markdown("- 梅花在荆楚文化中的象征意义？")
    st.markdown("- 重阳节和哪些荆楚植物有关？")
    st.markdown("- 湖北哪些地方盛产兰花？")

# 主界面布局
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### ❓ 智能问答")
    user_question = st.text_input(
        "请输入你的问题（如：梅花的文化象征？）",
        placeholder="输入后点击下方按钮获取回答..."
    )
    
    # 回答按钮（带加载状态和异常处理）
    if st.button("获取回答", type="primary"):
        if not user_question.strip():
            st.warning("⚠️ 请先输入你的问题！")
        else:
            with st.spinner("🤔 正在生成回答..."):
                answer = qa.answer_question(user_question)
                st.markdown("### 📝 回答")
                st.markdown(answer)

with col2:
    st.markdown("### 🌱 今日推荐植物")
    # 随机推荐植物
    random_plant = random.choice(plant_list)
    plant_detail = qa.get_plant_detail(random_plant)
    
    # 显示植物详情卡片
    st.markdown(f"""
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px;">
        <h4 style="margin: 0; color: #2e8b57;">{random_plant}</h4>
        <p><strong>拉丁名</strong>：{plant_detail['latin']}</p>
        <p><strong>文化象征</strong>：{plant_detail['cultural_symbol']}</p>
        <p><strong>分布区域</strong>：{plant_detail['distribution']}</p>
        <p><strong>关联节日</strong>：{', '.join(plant_detail['festivals']) if plant_detail['festivals'] else '无'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 数据概览")
    st.markdown(f"**植物总数**：{len(plant_list)} 种")
    st.markdown(f"**推荐指数**：⭐⭐⭐⭐⭐")

# 页脚
st.markdown("---")
st.markdown("💡 技术支持：Streamlit + Groq + Neo4j | 数据来源：荆楚植物文化知识库")