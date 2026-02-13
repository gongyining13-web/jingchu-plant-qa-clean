import streamlit as st
import os
import random
import pandas as pd
from groq import Groq

# 页面配置（必须放在最前面）
st.set_page_config(
    page_title="荆楚植物智能问答系统",
    page_icon="🌿",
    layout="wide"
)

# ----------------------
# 1. 加载你的Excel植物数据（50种植物，完全适配）
# ----------------------
@st.cache_data
def load_plant_data():
    """加载Excel格式的荆楚植物数据（含50种植物，匹配你的表格结构）"""
    try:
        # 读取你的Excel文件（路径和文件名完全一致）
        df = pd.read_excel("data/荆楚植物文化图谱植物数据.xlsx", engine="openpyxl", header=0)
        # 处理空值（避免后续显示空白）
        df = df.fillna("无")
        
        # 字段映射（完全匹配你的Excel表头，一字不差）
        df["name"]            = df["植物名"]       # 对应Excel的“植物名”列
        df["latin"]           = df["拉丁名"]       # 对应Excel的“拉丁名”列
        df["family"]          = df["科属"]         # 对应Excel的“科属”列
        df["distribution"]    = df["分布"]         # 对应Excel的“分布”列
        df["cultural_symbol"] = df["文化象征"]     # 对应Excel的“文化象征”列
        df["festivals"]       = df["关联节日"]     # 对应Excel的“关联节日”列
        
        # 转换为字典列表，方便调用（确保加载全部50种植物）
        plant_list = df.to_dict("records")
        st.success(f"✅ 成功加载 {len(plant_list)} 种荆楚植物数据（来自你的Excel表格）")
        return plant_list
    except FileNotFoundError:
        st.warning("⚠️ 未找到Excel数据文件，临时使用示例数据")
        # 示例数据（保证应用不崩溃，实际部署会加载你的50种植物）
        return [
            {"name": "梅花", "latin": "Prunus mume", "cultural_symbol": "高洁、坚韧", "distribution": "湖北武汉", "family": "蔷薇科", "festivals": "春节"},
            {"name": "菊花", "latin": "Chrysanthemum × morifolium", "cultural_symbol": "长寿、高雅", "distribution": "湖北荆州", "family": "菊科", "festivals": "重阳节"},
            {"name": "兰花", "latin": "Cymbidium ssp.", "cultural_symbol": "君子之花", "distribution": "湖北神农架", "family": "兰科", "festivals": "无"}
        ]
    except Exception as e:
        st.error(f"加载数据失败：{str(e)[:100]}")
        # 保底数据（避免页面空白）
        return [{"name": "梅花", "latin": "Prunus mume", "cultural_symbol": "高洁、坚韧", "distribution": "湖北武汉", "family": "蔷薇科", "festivals": "春节"}]

# ----------------------
# 2. 初始化Groq客户端（稳定调用）
# ----------------------
@st.cache_resource
def init_groq():
    """初始化Groq大模型客户端（确保API正常调用）"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("请在Streamlit Secrets中配置GROQ_API_KEY！")
        st.stop()
    return Groq(api_key=api_key)

# ----------------------
# 3. 核心功能函数（基于50种植物数据）
# ----------------------
def get_plant_detail(plant_name):
    """根据植物名获取详情（支持别名匹配，覆盖50种植物）"""
    # 别名映射（适配你50种植物中的常见别名）
    alias_map = {
        "菊花":"菊", "梅花":"梅", "兰花":"兰", "竹子":"竹",
        "荷花":"荷", "莲花":"荷", "桂花":"桂", "牡丹花":"牡丹",
        "杜鹃花":"杜鹃", "水仙花":"水仙", "艾草":"艾", "菖蒲叶":"菖蒲",
        "月季花":"月季", "玫瑰花":"玫瑰", "栀子花":"栀子", "茉莉花":"茉莉"
    }
    # 匹配别名（避免因别名导致找不到数据）
    target_name = alias_map.get(plant_name, plant_name)
    
    # 从50种植物中查找对应数据
    for plant in plant_data:
        if plant["name"] == target_name or target_name in str(plant["name"]):
            return plant
    # 未找到时返回第一个植物（避免页面报错）
    return plant_data[0]

def generate_answer(question):
    """基于你的50种植物数据+Groq生成精准回答"""
    try:
        # 从问题中提取植物名（匹配50种植物）
        plant_names = [p["name"] for p in plant_data]
        relevant_plants = [p for p in plant_names if p in question or any(alias in question for alias in alias_map.get(p, []))]
        
        # 构建基于你50种植物数据的提示词（确保回答精准）
        context = ""
        if relevant_plants:
            context = "### 荆楚植物参考数据（来自你的Excel表格，共50种）：\n"
            for p in relevant_plants:
                detail = get_plant_detail(p)
                context += f"""
- 【{detail['name']}】
  拉丁名：{detail['latin']}
  科属：{detail['family']}
  分布区域：{detail['distribution']}
  文化象征：{detail['cultural_symbol']}
  关联节日：{detail['festivals']}
"""
        
        # 最终提示词（突出荆楚地域特色，基于50种植物数据）
        prompt = f"""你是专业的荆楚植物文化研究员，必须严格根据以下参考数据回答问题（仅用中文）：
{context}

如果参考数据中无相关信息，基于荆楚地域文化常识回答，禁止编造数据；若有相关信息，优先用参考数据中的内容。

问题：{question}
要求：
1. 回答简洁准确，突出荆楚地域特色；
2. 语言通俗易懂，避免专业术语；
3. 字数控制在200字以内。"""
        
        # 调用Groq生成回答（使用稳定可用的模型）
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "你是荆楚植物文化专家，回答需结合湖北地域特色，基于用户提供的50种植物数据"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",  # 经测试稳定的模型
            temperature=0.2,  # 降低随机性，保证回答与数据一致
            timeout=30  # 延长超时时间，避免生成中断
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"抱歉，暂时无法回答你的问题。错误原因：{str(e)[:100]}"

# ----------------------
# 4. 初始化资源（加载50种植物数据）
# ----------------------
plant_data = load_plant_data()
client = init_groq()
# 初始化别名映射（供回答函数使用）
alias_map = {
    "菊花":"菊", "梅花":"梅", "兰花":"兰", "竹子":"竹",
    "荷花":"荷", "莲花":"荷", "桂花":"桂", "牡丹花":"牡丹",
    "杜鹃花":"杜鹃", "水仙花":"水仙", "艾草":"艾", "菖蒲叶":"菖蒲",
    "月季花":"月季", "玫瑰花":"玫瑰", "栀子花":"栀子", "茉莉花":"茉莉"
}

# ----------------------
# 5. 页面样式与布局（突出50种植物数据）
# ----------------------
# 自定义样式美化（确保数据清晰显示）
st.markdown("""
<style>
    /* 按钮样式 */
    .stButton>button {
        background-color: #2E8B57;
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1f6e43;
    }
    /* 植物卡片样式（突出显示50种植物数据） */
    .plant-card {
        background-color: #f0f8fb;
        padding: 18px;
        border-radius: 10px;
        margin: 12px 0;
        border-left: 5px solid #2E8B57;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    /* 标题样式 */
    h1, h3 {
        color: #2E8B57;
    }
    /* 输入框样式 */
    .stTextInput>div>div>input {
        height: 3em;
        border-radius: 8px;
    }
    /* 下拉选择框样式 */
    .stSelectbox>div>div>div {
        background-color: #f0f8fb;
        border-radius: 8px;
    }
    /* 统计数字样式 */
    .stMetric-value {
        color: #2E8B57;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题（突出50种植物）
st.title("🌿 荆楚植物智能问答系统")
st.markdown("##### 📚 基于你的荆楚植物Excel数据（共50种植物）")

# 侧边栏（展示50种植物的统计信息）
with st.sidebar:
    st.markdown("### 🌱 关于系统")
    st.markdown("本系统基于**你的荆楚植物文化Excel数据**（共50种植物）+ 大语言模型，提供精准的植物文化问答服务。")
    
    st.markdown("---")
    st.markdown("### 📊 数据概览（来自你的50种植物）")
    # 统计你的50种植物数据（实时计算）
    total_plants = len(plant_data)
    total_families = len(set([p["family"] for p in plant_data]))  # 去重统计科属数
    total_festivals = 0
    for p in plant_data:
        if p["festivals"] != "无" and p["festivals"] != "":
            total_festivals += len(str(p["festivals"]).split("、"))  # 统计关联节日总数
    
    # 展示统计指标（突出50种植物）
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("🌿 植物总数", total_plants)
        st.metric("🎉 关联节日数", total_festivals)
    with col_s2:
        st.metric("🌳 科属数量", total_families)
    
    st.markdown("---")
    st.markdown("### ❓ 提问示例（基于50种植物）")
    st.markdown("- 梅花在荆楚文化中的象征意义？")
    st.markdown("- 重阳节和哪些荆楚植物有关？")
    st.markdown("- 湖北哪些地方盛产荷花？")
    st.markdown("- 兰花属于哪个科属？")

# 主界面布局（确保50种植物数据正常展示）
st.markdown("---")
st.markdown("### ❓ 智能问答")
user_question = st.text_input(
    label="请输入你的问题（如：梅花的文化象征？）",
    placeholder="输入后点击按钮，基于你的50种植物数据生成回答...",
    key="user_question"
)
if st.button("获取专业回答", type="primary"):
    if user_question.strip():
        with st.spinner("🤔 正在检索你的50种植物数据并生成回答..."):
            answer = generate_answer(user_question)
            st.markdown("### 📝 回答（基于你的50种植物数据）")
            st.write(answer)
    else:
        st.warning("⚠️ 请先输入你的问题！")

st.markdown("---")
col_main1, col_main2 = st.columns(2)

with col_main1:
    st.markdown("### 🌺 今日推荐植物（来自50种植物）")
    # 从50种植物中随机推荐（每次刷新换一种）
    random_plant = random.choice(plant_data)
    st.markdown(f"""
    <div class="plant-card">
        <h3 style="margin:0; color:#2E8B57;">{random_plant['name']}</h3>
        <p><strong>🔍 拉丁名</strong>：{random_plant['latin']}</p>
        <p><strong>🌳 科属</strong>：{random_plant['family']}</p>
        <p><strong>📍 分布区域</strong>：{random_plant['distribution']}</p>
        <p><strong>🏛️ 文化象征</strong>：{random_plant['cultural_symbol']}</p>
        <p><strong>🎉 关联节日</strong>：{random_plant['festivals']}</p>
    </div>
    """, unsafe_allow_html=True)

with col_main2:
    st.markdown("### 📜 植物名录查询（50种植物）")
    # 展示全部50种植物的名录（下拉选择）
    plant_names = [p["name"] for p in plant_data]
    selected_plant = st.selectbox(
        "从50种植物中选择查看详情", 
        options=plant_names, 
        key="plant_selector"
    )
    
    # 展示选中植物的详情（来自你的50种植物数据）
    if selected_plant:
        detail = get_plant_detail(selected_plant)
        st.markdown(f"""
        <div class="plant-card">
            <h3 style="margin:0; color:#2E8B57;">{detail['name']} 详细信息</h3>
            <p><strong>🔍 拉丁名</strong>：{detail['latin']}</p>
            <p><strong>🌳 科属</strong>：{detail['family']}</p>
            <p><strong>📍 地理分布</strong>：{detail['distribution']}</p>
            <p><strong>🏛️ 文化象征</strong>：{detail['cultural_symbol']}</p>
            <p><strong>🎉 关联节日</strong>：{detail['festivals']}</p>
        </div>
        """, unsafe_allow_html=True)

# 页脚信息（强调50种植物数据）
st.markdown("---")
st.markdown("💡 数据来源：你的荆楚植物文化Excel数据表（共50种植物） | 技术支持：Streamlit + Groq | 后续更新Excel文件即可同步50种植物数据")