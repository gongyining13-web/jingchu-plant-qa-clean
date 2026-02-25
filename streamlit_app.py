import streamlit as st
import os
import random
from src.api.free_qa_system import PlantQASystem, LangChainPlantQA
from groq import Groq

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="草木集 · 古风植物图鉴",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- 注入 PWA Manifest ----------
st.markdown('<link rel="manifest" href="/static/manifest.json">', unsafe_allow_html=True)

# ---------- 自定义古风 CSS（浅色高对比度） ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;500&display=swap');
    @import url('https://cdn.bootcdn.net/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css');

    /* 全局 */
    .main {
        background-color: #fffaf5;  /* 暖白浅色 */
        padding: 2rem !important;
    }
    h1, h2, h3, h4 {
        font-family: 'Ma Shan Zheng', cursive;
        color: #4a3e35;  /* 深褐色 */
        font-weight: 500;
    }
    p, div, span, li {
        color: #3e332b;   /* 深色文字 */
    }
    /* 侧边栏 */
    section[data-testid="stSidebar"] {
        background: #ffffff;  /* 纯白背景 */
        border-right: 1px solid #e0d6cc;
        padding: 1.5rem 0.5rem;
    }
    /* 侧边栏按钮 */
    .stButton > button {
        font-family: 'Noto Serif SC', serif;
        font-size: 16px;
        color: #4a3e35 !important;
        background: transparent !important;
        border: none !important;
        padding: 12px 20px !important;
        border-radius: 12px !important;
        margin: 4px 0 !important;
        text-align: left !important;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.3s ease;
        width: 100%;
        cursor: pointer;
    }
    .stButton > button:hover {
        background: #f5eee8 !important;
    }
    .stButton > button:focus {
        box-shadow: none !important;
    }
    /* 标题 */
    .page-title {
        font-family: 'Ma Shan Zheng', cursive;
        font-size: 32px;
        color: #4a3e35;
        margin-bottom: 24px;
        letter-spacing: 2px;
        position: relative;
        padding-bottom: 10px;
    }
    .page-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 2px;
        background: #d9c5ad;
    }
    /* 搜索框 */
    .search-box {
        max-width: 500px;
        position: relative;
        margin-bottom: 30px;
    }
    .search-input {
        width: 100%;
        padding: 14px 20px 14px 45px;
        border: 1px solid #d9c5ad;
        border-radius: 16px;
        background: #ffffff;
        font-size: 16px;
        color: #3e332b;
        outline: none;
        transition: all 0.3s ease;
        font-family: 'Noto Serif SC', serif;
    }
    .search-input:focus {
        border-color: #b8a58c;
        box-shadow: 0 0 0 3px rgba(184, 165, 140, 0.2);
    }
    .search-input::placeholder {
        color: #a39282;
    }
    .search-icon {
        position: absolute;
        left: 18px;
        top: 50%;
        transform: translateY(-50%);
        color: #a39282;
        font-size: 18px;
    }
    /* 卡片网格 */
    .plant-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 25px;
        margin: 20px 0;
    }
    .plant-card {
        background: #ffffff;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 3px 10px rgba(0,0,0,0.03);
        transition: all 0.3s ease;
        border: 1px solid #ede3d8;
        cursor: pointer;
    }
    .plant-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.05);
        border-color: #d9c5ad;
    }
    .plant-img {
        width: 100%;
        height: 160px;
        background: linear-gradient(145deg, #f5f0ea, #e9e0d7);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        color: #7a6a5a;
    }
    .plant-info {
        padding: 18px;
    }
    .plant-name {
        font-size: 18px;
        color: #4a3e35;
        margin-bottom: 8px;
        font-weight: 500;
        font-family: 'Ma Shan Zheng', cursive;
    }
    .plant-desc {
        font-size: 13px;
        color: #6b5b4e;
        line-height: 1.6;
        margin-bottom: 12px;
        font-family: 'Noto Serif SC', serif;
    }
    /* 收藏按钮 */
    .collect-btn {
        background: #f0e8dd;
        border: none;
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 14px;
        color: #4a3e35;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: 'Noto Serif SC', serif;
        width: 100%;
        justify-content: center;
    }
    .collect-btn:hover {
        background: #e9d9c2;
    }
    .collect-btn.active {
        background: #d9c5ad;
        color: #fff;
    }
    /* 问答容器 */
    .qa-container {
        background: #ffffff;
        border-radius: 18px;
        padding: 2rem;
        border: 1px solid #ede3d8;
        max-width: 900px;
        margin: 0 auto;
    }
    /* 弹窗 */
    div[data-testid="stDialog"] {
        background-color: #ffffff !important;
        border: 1px solid #ede3d8 !important;
        border-radius: 20px !important;
        padding: 1rem !important;
    }
    /* 滚动条 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f5efe5;
    }
    ::-webkit-scrollbar-thumb {
        background: #d9c5ad;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #c8b79e;
    }
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    /* 按钮重置 */
    .stButton > button {
        background: transparent;
        border: none;
        color: inherit;
    }
</style>
""", unsafe_allow_html=True)

# ---------- 初始化数据 ----------
@st.cache_resource
def init_traditional_qa():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, password]):
        st.error("❌ 未配置 Neo4j 环境变量！请在 Streamlit Secrets 中设置 NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        st.stop()
    return PlantQASystem(uri=uri, user=user, password=password)

@st.cache_resource
def init_langchain_qa():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not all([uri, user, password, groq_api_key]):
        st.error("❌ 未配置 Neo4j 或 Groq 环境变量！")
        st.stop()
    return LangChainPlantQA(uri=uri, user=user, password=password, groq_api_key=groq_api_key)

qa = init_traditional_qa()
qa_langchain = init_langchain_qa()
plant_names = qa.plant_names

# ---------- 别名映射表 ----------
ALIAS_MAP = {
    "梅花": "梅", "菊花": "菊", "兰花": "兰", "竹子": "竹",
    "荷花": "荷（莲）", "莲花": "荷（莲）", "桂花": "桂", "牡丹花": "牡丹",
    "杜鹃花": "杜鹃", "水仙花": "水仙", "艾草": "艾", "菖蒲叶": "菖蒲"
}

# ---------- 获取植物详情 ----------
def get_plant_detail(plant_name):
    target_name = ALIAS_MAP.get(plant_name.strip(), plant_name.strip())
    detail = qa.get_plant_detail(target_name)
    if detail:
        return detail
    if target_name != plant_name.strip():
        detail = qa.get_plant_detail(plant_name.strip())
        if detail:
            return detail
    return {
        "name": plant_name,
        "latin": "未知",
        "family": "未知",
        "genus": "未知",
        "distribution": "暂无分布信息",
        "cultural_symbol": "暂无文化象征",
        "folk_use": "暂无民俗用途",
        "ecological": "暂无生态意义",
        "medicinal": [],
        "literature": [],
        "festivals": []
    }

# ---------- Groq 客户端初始化 ----------
@st.cache_resource
def init_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("❌ 未配置 GROQ_API_KEY！")
        st.stop()
    return Groq(api_key=api_key, timeout=60)

groq_client = init_groq_client()

# ---------- 传统规则问答函数 ----------
def generate_intelligent_answer(question):
    try:
        relevant_plants = []
        for name in plant_names:
            if name in question:
                relevant_plants.append(name)
        for alias, real_name in ALIAS_MAP.items():
            if alias in question and real_name not in relevant_plants:
                relevant_plants.append(real_name)

        context = "### 荆楚植物参考数据（实时查询自 Neo4j）：\n"
        if relevant_plants:
            for p_name in relevant_plants:
                plant = qa.get_plant_detail(p_name)
                if plant:
                    festivals = "、".join(plant.get("festivals", [])) if plant.get("festivals") else "无"
                    medicinal = "、".join(plant.get("medicinal", [])) if plant.get("medicinal") else "无"
                    context += f"""
- 【植物名】：{plant.get('name', '未知')}
  拉丁学名：{plant.get('latin', '未知')} | 科属：{plant.get('family', '未知')} {plant.get('genus', '未知')}
  湖北分布：{plant.get('distribution', '暂无分布信息')}
  文化象征：{plant.get('cultural_symbol', '暂无文化象征')}
  关联节日：{festivals}
  药用价值：{medicinal}
"""
        else:
            context += "未匹配到具体植物，将基于荆楚植物文化常识回答。"

        prompt = f"""
你是荆楚植物文化研究员，仅围绕湖北地域植物作答：
1. 有数据时100%基于数据，无数据时基于常识，不编造；
2. 突出湖北/荆楚特色，语言通俗易懂，150字以内。

参考数据：
{context}

用户问题：{question}
"""
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"💡 问答暂无法响应，错误原因：{str(e)[:80]}"

# ---------- 会话状态初始化 ----------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "collected_plants" not in st.session_state:
    st.session_state.collected_plants = []
if "selected_plant" not in st.session_state:
    st.session_state.selected_plant = None
if "show_detail" not in st.session_state:
    st.session_state.show_detail = False

# ---------- 侧边栏导航 ----------
with st.sidebar:
    st.markdown('<div style="font-family:Ma Shan Zheng; font-size:28px; color:#4a3e35; text-align:center; margin-bottom:20px;">草木集</div>', unsafe_allow_html=True)

    pages = {
        "home": "🌱 今日推荐",
        "collect": "❤️ 我的收藏",
        "qa": "💬 智能问答",
        "user": "👤 个人中心"
    }
    for key, label in pages.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = key
            st.rerun()

# ---------- 主内容区域 ----------
st.markdown(f'<div class="page-title">{pages[st.session_state.current_page].split(" ")[1]}</div>', unsafe_allow_html=True)

# 搜索框（仅首页显示）
if st.session_state.current_page == "home":
    st.markdown("""
    <div class="search-box">
        <i class="fa fa-search search-icon"></i>
        <input class="search-input" type="text" placeholder="搜索草木名称…">
    </div>
    """, unsafe_allow_html=True)

# ---------- 首页：植物卡片网格 ----------
if st.session_state.current_page == "home":
    filtered_plants = plant_names
    # 使用 columns 手动构建网格，每行4列
    cols = st.columns(4)
    for i, name in enumerate(filtered_plants):
        detail = get_plant_detail(name)
        with cols[i % 4]:
            # 卡片容器
            card_key = f"card_{name}"
            is_collected = any(p["name"] == name for p in st.session_state.collected_plants)

            # 卡片主体（点击触发详情）
            if st.button(
                label=f"**{name}**  \n*{detail.get('latin', '')}*  \n{detail.get('family', '')} · {detail.get('genus', '')}  \n{detail.get('cultural_symbol', '')[:30]}…",
                key=card_key,
                use_container_width=True
            ):
                st.session_state.selected_plant = name
                st.session_state.show_detail = True
                st.rerun()

            # 收藏按钮
            btn_icon = "❤️" if is_collected else "🤍"
            if st.button(btn_icon, key=f"collect_{name}", help="收藏"):
                if is_collected:
                    st.session_state.collected_plants = [p for p in st.session_state.collected_plants if p["name"] != name]
                else:
                    st.session_state.collected_plants.append({
                        "name": name,
                        "latin": detail.get("latin", ""),
                        "family": detail.get("family", ""),
                        "genus": detail.get("genus", ""),
                        "desc": detail.get("cultural_symbol", "")[:50]
                    })
                st.rerun()

# ---------- 收藏页 ----------
elif st.session_state.current_page == "collect":
    if not st.session_state.collected_plants:
        st.markdown('<div style="color:#6b5b4e; text-align:center; padding:40px;">暂无收藏，快去首页收藏心仪的草木吧～</div>', unsafe_allow_html=True)
    else:
        cols = st.columns(4)
        for i, plant in enumerate(st.session_state.collected_plants):
            with cols[i % 4]:
                if st.button(
                    label=f"**{plant['name']}**  \n{plant['desc']}",
                    key=f"collect_card_{plant['name']}",
                    use_container_width=True
                ):
                    st.session_state.selected_plant = plant["name"]
                    st.session_state.show_detail = True
                    st.rerun()
                if st.button("❤️ 取消收藏", key=f"uncollect_{plant['name']}", use_container_width=True):
                    st.session_state.collected_plants = [p for p in st.session_state.collected_plants if p["name"] != plant["name"]]
                    st.rerun()

# ---------- 问答页 ----------
elif st.session_state.current_page == "qa":
    st.markdown('<div class="qa-container">', unsafe_allow_html=True)
    st.markdown("### 🧠 智能文化问答")
    user_question = st.text_input(
        label="请输入你的问题",
        placeholder="例如：桂的文化象征和湖北分布？",
        key="user_question",
        label_visibility="collapsed"
    )
    qa_mode = st.radio(
        "选择问答模式",
        options=["传统规则", "智能LangChain"],
        index=0,
        horizontal=True
    )
    if st.button("获取精准回答", type="primary", use_container_width=True):
        if not user_question.strip():
            st.warning("⚠️ 请输入有效问题！")
        else:
            with st.spinner("🔍 正在检索数据..."):
                if qa_mode == "传统规则":
                    answer = generate_intelligent_answer(user_question)
                else:
                    answer = qa_langchain.answer(user_question)
                st.markdown("#### 📝 专属回答")
                st.write(answer)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- 个人中心页 ----------
elif st.session_state.current_page == "user":
    st.markdown(f"""
    <div style="background:#ffffff; padding:30px; border-radius:18px; border:1px solid #ede3d8;">
        <h3 style="font-family:'Ma Shan Zheng',cursive; color:#4a3e35;">个人中心</h3>
        <div style="display:flex; align-items:center; gap:20px; margin-top:20px;">
            <div style="width:80px; height:80px; border-radius:50%; background:#f0e8dd; display:flex; align-items:center; justify-content:center; font-size:32px; color:#4a3e35;">
                <i class="fa fa-user"></i>
            </div>
            <div>
                <p style="font-size:18px; color:#4a3e35; font-weight:500;">草木知音</p>
                <p style="color:#6b5b4e;">与草木为伴，享自然之美</p>
                <p style="color:#6b5b4e;">已收藏：<span style="font-weight:500;">{len(st.session_state.collected_plants)}</span> 种草木</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- 详情弹窗 ----------
if st.session_state.show_detail and st.session_state.selected_plant:
    plant = st.session_state.selected_plant
    detail = get_plant_detail(plant)
    with st.dialog(f"## {detail.get('name', '')}"):
        st.markdown(f"*{detail.get('latin', '')}*")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**科**：{detail.get('family', '')}")
            st.markdown(f"**属**：{detail.get('genus', '')}")
            st.markdown(f"**分布**：{detail.get('distribution', '')}")
        with col2:
            st.markdown(f"**文化象征**：{detail.get('cultural_symbol', '')}")
            st.markdown(f"**民俗用途**：{detail.get('folk_use', '')}")
            st.markdown(f"**药用价值**：{', '.join(detail.get('medicinal', [])) if detail.get('medicinal') else '无'}")
        if st.button("关闭"):
            st.session_state.show_detail = False
            st.rerun()