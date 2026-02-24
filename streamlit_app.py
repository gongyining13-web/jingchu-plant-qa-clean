import streamlit as st
import os
import random
from src.api.free_qa_system import PlantQASystem, LangChainPlantQA
from groq import Groq

# ------------------------------------------------------------
# 0. 页面配置
# ------------------------------------------------------------
st.set_page_config(
    page_title="🌿 荆楚植物智能问答系统 (Neo4j版)",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- 注入 PWA Manifest ----------
st.markdown('<link rel="manifest" href="/static/manifest.json">', unsafe_allow_html=True)

# ------------------------------------------------------------
# 1. 初始化 Neo4j 连接（从环境变量读取）
# ------------------------------------------------------------
@st.cache_resource
def init_traditional_qa():
    """初始化传统 PlantQASystem"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, password]):
        st.error("❌ 未配置 Neo4j 环境变量！请在 Streamlit Secrets 中设置 NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        st.stop()
    return PlantQASystem(uri=uri, user=user, password=password)

@st.cache_resource
def init_langchain_qa():
    """初始化 LangChainPlantQA"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not all([uri, user, password, groq_api_key]):
        st.error("❌ 未配置 Neo4j 或 Groq 环境变量！请在 Streamlit Secrets 中设置 NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, GROQ_API_KEY")
        st.stop()
    return LangChainPlantQA(uri=uri, user=user, password=password, groq_api_key=groq_api_key)

# 初始化两个问答系统
qa = init_traditional_qa()          # 传统系统，保持变量名以兼容后续代码
qa_langchain = init_langchain_qa()  # LangChain 系统
plant_names = qa.plant_names        # 从传统系统获取植物列表

# ------------------------------------------------------------
# 2. 别名映射表
# ------------------------------------------------------------
ALIAS_MAP = {
    "梅花": "梅", "菊花": "菊", "兰花": "兰", "竹子": "竹",
    "荷花": "荷（莲）", "莲花": "荷（莲）", "桂花": "桂", "牡丹花": "牡丹",
    "杜鹃花": "杜鹃", "水仙花": "水仙", "艾草": "艾", "菖蒲叶": "菖蒲"
}

# ------------------------------------------------------------
# 3. 获取植物详情（封装 qa.get_plant_detail，使用传统系统）
# ------------------------------------------------------------
def get_plant_detail(plant_name):
    target_name = ALIAS_MAP.get(plant_name.strip(), plant_name.strip())
    detail = qa.get_plant_detail(target_name)
    if detail:
        return detail
    # 尝试直接用原名再查一次
    if target_name != plant_name.strip():
        detail = qa.get_plant_detail(plant_name.strip())
        if detail:
            return detail
    # 返回空结构（避免出错）
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

# ------------------------------------------------------------
# 4. 智能问答生成（传统模式使用此函数）
# ------------------------------------------------------------
@st.cache_resource
def init_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("❌ 未配置 GROQ_API_KEY！请在 Streamlit Secrets 中填写")
        st.stop()
    return Groq(api_key=api_key, timeout=60)

groq_client = init_groq_client()

def generate_intelligent_answer(question):
    """传统模式：基于检索 + Groq 生成回答"""
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
                plant = qa.get_plant_detail(p_name)   # 使用传统系统获取详情
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

# ------------------------------------------------------------
# 5. 页面样式（请从原 Excel 版本的 streamlit_app.py 中复制你的完整 CSS 代码）
# ------------------------------------------------------------
st.markdown("""
<style>
    /* ===== 请将你原来的 CSS 样式粘贴在此处 ===== */
    /* 例如： */
    * {margin: 0; padding: 0; box-sizing: border-box;}
    .main {background-color: #f5f7f9 !important; padding: 0 20px !important;}
    /* ... 其他样式 ... */
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# 6. 页面主体布局
# ------------------------------------------------------------
st.title("🌿 荆楚植物智能问答系统 (Neo4j 实时版)")
st.markdown("##### 基于 **Neo4j 实时数据库** 开发 | 数据可动态更新")
st.markdown("---")

# --- 侧边栏 ---
with st.sidebar:
    st.markdown("### 🌱 系统说明")
    st.markdown("本版连接 Neo4j 数据库，数据实时读取，支持动态更新。")

    st.markdown("---")
    st.markdown("### 📊 数据概览")
    st.metric("🌿 植物总数", len(plant_names))

    st.markdown("---")
    st.markdown("### ❓ 提问示例")
    st.markdown("- 梅在荆楚文化中的象征意义？")
    st.markdown("- 重阳节和哪些湖北植物有关？")
    st.markdown("- 荷（莲）在湖北的分布区域？")

# --- 智能问答区域 ---
st.markdown("### 🧠 智能文化问答")
user_question = st.text_input(
    label="请输入你的问题",
    placeholder="例如：桂的文化象征和湖北分布？",
    key="user_question",
    label_visibility="collapsed"
)

# 添加模式选择
qa_mode = st.radio(
    "选择问答模式",
    options=["传统规则", "智能LangChain"],
    index=0,
    horizontal=True
)

if st.button("获取精准回答", type="primary"):
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
st.markdown("---")

# --- 植物卡片 ---
col_card1, col_card2 = st.columns(2, gap="medium")

with col_card1:
    st.markdown("### 🌸 今日推荐植物")
    if plant_names:
        random_name = random.choice(plant_names)
        plant = qa.get_plant_detail(random_name)   # 使用传统系统获取详情
        if plant:
            festivals = "、".join(plant.get("festivals", [])) if plant.get("festivals") else "无"
            medicinal = "、".join(plant.get("medicinal", [])) if plant.get("medicinal") else "无"
            st.markdown(f"""
            <div class="plant-card">
                <h3>{plant.get('name', '未知')} · 荆楚特色植物</h3>
                <p><strong>拉丁学名</strong>：{plant.get('latin', '未知')}</p>
                <p><strong>科属分类</strong>：{plant.get('family', '未知')} {plant.get('genus', '未知')}</p>
                <p><strong>湖北分布</strong>：{plant.get('distribution', '暂无分布信息')}</p>
                <p><strong>文化象征</strong>：{plant.get('cultural_symbol', '暂无文化象征')}</p>
                <p><strong>关联节日</strong>：{festivals}</p>
                <p><strong>药用价值</strong>：{medicinal}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 暂无有效植物数据")

with col_card2:
    st.markdown("### 📜 植物名录查询")
    if plant_names:
        plant_names_sorted = sorted(plant_names)
        selected_plant = st.selectbox(
            label="选择植物查看详细信息",
            options=plant_names_sorted,
            key="plant_selector",
            label_visibility="collapsed"
        )
        if selected_plant:
            plant = qa.get_plant_detail(selected_plant)   # 使用传统系统获取详情
            if plant:
                festivals = "、".join(plant.get("festivals", [])) if plant.get("festivals") else "无"
                medicinal = "、".join(plant.get("medicinal", [])) if plant.get("medicinal") else "无"
                st.markdown(f"""
                <div class="plant-card">
                    <h3>{plant.get('name', '未知')} · 详细信息</h3>
                    <p><strong>拉丁学名</strong>：{plant.get('latin', '未知')}</p>
                    <p><strong>科属分类</strong>：{plant.get('family', '未知')} {plant.get('genus', '未知')}</p>
                    <p><strong>湖北分布</strong>：{plant.get('distribution', '暂无分布信息')}</p>
                    <p><strong>文化象征</strong>：{plant.get('cultural_symbol', '暂无文化象征')}</p>
                    <p><strong>关联节日</strong>：{festivals}</p>
                    <p><strong>药用价值</strong>：{medicinal}</p>
                    <p><strong>民俗用途</strong>：{plant.get('folk_use', '暂无民俗用途')}</p>
                    <p><strong>生态意义</strong>：{plant.get('ecological', '暂无生态意义')}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 暂无有效植物数据")

# --- 页脚 ---
st.markdown("---")
st.markdown('<p class="footer">💡 数据来源：Neo4j 实时数据库 | 技术支持：Streamlit + Groq + Neo4j</p>', unsafe_allow_html=True)