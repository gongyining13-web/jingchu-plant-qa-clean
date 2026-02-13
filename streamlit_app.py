import streamlit as st
import os
import random
import pandas as pd
from groq import Groq

# 页面配置（必须放在最前面）
st.set_page_config(
    page_title="🌿 荆楚植物智能问答系统",
    page_icon="🌿",
    layout="wide"
)

# ----------------------
# 1. 加载你的Excel植物数据（彻底修复读取问题）
# ----------------------
@st.cache_data
def load_plant_data():
    """稳健加载Excel数据，处理各种表头问题"""
    try:
        # 读取Excel，指定header=0，确保从第1行读取表头
        df = pd.read_excel("data/荆楚植物文化图谱植物数据.xlsx", engine="openpyxl", header=0)
        
        # 调试：打印所有列名，确认读取正确
        st.write("✅ 成功读取Excel，列名如下：", df.columns.tolist())
        
        # 处理空值
        df = df.fillna("无")
        
        # 👇 用 .get() 方法读取字段，彻底避免KeyError
        df["name"]            = df.get("植物中文名", "未知")
        df["latin"]           = df.get("植物拉丁学名", "未知")
        df["family"]          = df.get("植物科", "未知")
        df["genus"]           = df.get("植物属名", "未知")
        df["distribution"]    = df.get("现代地理分布", "未知")
        df["cultural_symbol"] = df.get("文化象征", "未知")
        df["festivals"]       = df.get("节日", "未知")
        df["medicinal_value"] = df.get("药用价值", "未知")
        df["traditional_use"] = df.get("传统实用价值", "未知")
        df["ecological_significance"] = df.get("生态意义", "未知")
        
        # 转换为字典列表
        plant_list = df.to_dict("records")
        st.success(f"✅ 成功加载 {len(plant_list)} 种荆楚植物数据（来自你的Excel）")
        return plant_list
    except Exception as e:
        st.error(f"加载数据失败：{str(e)[:100]}")
        # 保底示例数据（保证页面不崩）
        return [
            {
                "name": "梅花",
                "latin": "Prunus mume",
                "family": "蔷薇科",
                "genus": "李属",
                "distribution": "湖北武汉、黄冈、襄阳等地",
                "cultural_symbol": "高洁、坚韧、不屈不挠",
                "festivals": "春节、梅花节",
                "medicinal_value": "观赏；药用（梅子）",
                "traditional_use": "观赏；食用（青梅）",
                "ecological_significance": "早春开花，为传粉昆虫提供蜜源"
            }
        ]

# ----------------------
# 2. 初始化Groq客户端
# ----------------------
@st.cache_resource
def init_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("请在Streamlit Secrets中配置GROQ_API_KEY！")
        st.stop()
    return Groq(api_key=api_key)

# ----------------------
# 3. 核心功能函数（彻底修复KeyError）
# ----------------------
def get_plant_detail(plant_name):
    """根据植物名获取详情，兼容别名和缺失字段"""
    alias_map = {
        "菊花":"菊", "梅花":"梅", "兰花":"兰", "竹子":"竹",
        "荷花":"荷", "莲花":"荷", "桂花":"桂", "牡丹花":"牡丹",
        "杜鹃花":"杜鹃", "水仙花":"水仙", "艾草":"艾", "菖蒲叶":"菖蒲"
    }
    target_name = alias_map.get(plant_name, plant_name)
    
    for plant in plant_data:
        if plant["name"] == target_name or target_name in str(plant["name"]):
            return plant
    return plant_data[0]

def generate_answer(question):
    """基于Excel数据生成回答，处理所有异常"""
    try:
        plant_names = [p["name"] for p in plant_data]
        relevant_plants = [p for p in plant_names if p in question]
        
        context = ""
        if relevant_plants:
            context = "### 荆楚植物参考数据：\n"
            for p in relevant_plants:
                detail = get_plant_detail(p)
                context += f"""
- 【{detail['name']}】
  拉丁学名：{detail['latin']}
  科属：{detail['family']} {detail['genus']}
  分布：{detail['distribution']}
  文化象征：{detail['cultural_symbol']}
  关联节日：{detail['festivals']}
"""
        
        prompt = f"""你是荆楚植物文化专家，严格根据以下参考数据回答问题：
{context}

问题：{question}
要求：简洁准确，突出荆楚地域特色，200字以内。"""
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "你是荆楚植物文化专家，回答专业简洁"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"抱歉，暂时无法回答你的问题。错误原因：{str(e)[:100]}"

# ----------------------
# 4. 初始化资源
# ----------------------
plant_data = load_plant_data()
client = init_groq()

# ----------------------
# 5. 页面样式与布局（彻底修复所有UI问题）
# ----------------------
st.markdown("""
<style>
    /* 按钮样式 */
    .stButton>button {
        background-color: #2E8B57 !important;
        color: #ffffff !important;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        border: none !important;
    }
    .stButton>button:hover {
        background-color: #1f6e43 !important;
    }

    /* 植物卡片样式（彻底修复KeyError） */
    .plant-card {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        border-left: 5px solid #2E8B57 !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        color: #1a1a1a !important;
    }
    .plant-card h3 {
        color: #2E8B57 !important;
        font-size: 1.3em !important;
        margin-bottom: 10px !important;
    }
    .plant-card p {
        color: #1a1a1a !important;
        font-size: 1em !important;
        line-height: 1.5 !important;
        margin: 5px 0 !important;
    }
    .plant-card strong {
        color: #2E8B57 !important;
    }

    /* 侧边栏样式（彻底修复颜色和统计） */
    [data-testid="stSidebar"] {
        background-color: #2E8B57 !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stMetric {
        background-color: rgba(255,255,255,0.1) !important;
        padding: 10px;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] .stMetric-label {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stMetric-value {
        color: #ffffff !important;
        font-size: 1.5em !important;
        font-weight: bold !important;
    }

    /* 标题样式 */
    h1, h2, h3, h4 {
        color: #2E8B57 !important;
    }

    /* 输入框/下拉框样式 */
    .stTextInput>div>div>input {
        height: 3em;
        border-radius: 8px;
        color: #1a1a1a !important;
        background-color: #f8f9fa !important;
        border: 1px solid #2E8B57 !important;
    }
    .stSelectbox>div>div>div {
        background-color: #f8f9fa !important;
        border-radius: 8px;
        color: #1a1a1a !important;
        border: 1px solid #2E8B57 !important;
    }

    /* 全局样式 */
    .main {
        background-color: #f8f9fa !important;
    }
    body {
        color: #1a1a1a !important;
    }

    /* 提示框样式 */
    .stSuccess, .stWarning, .stError {
        border-radius: 8px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.title("🌿 荆楚植物智能问答系统")
st.markdown("##### 基于你的荆楚植物Excel数据（共50种植物）")

# 侧边栏（统计正确，无KeyError）
with st.sidebar:
    st.markdown("### 🌱 关于系统")
    st.markdown("本系统基于你的荆楚植物文化Excel数据（50种植物）+ 大语言模型，提供精准问答服务。")
    
    st.markdown("---")
    st.markdown("### 📊 数据概览（来自你的Excel）")
    # 统计数据（实时计算，确保正确）
    total_plants = len(plant_data)
    total_families = len(set([p["family"] for p in plant_data]))
    total_festivals = 0
    for p in plant_data:
        if p["festivals"] != "无" and p["festivals"] != "":
            total_festivals += len(str(p["festivals"]).split("、"))
    
    # 展示统计指标
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("🌿 植物总数", total_plants)
        st.metric("🎉 关联节日数", total_festivals)
    with col_s2:
        st.metric("🌳 科数量", total_families)
    
    st.markdown("---")
    st.markdown("### 提问示例")
    st.markdown("- 梅花在荆楚文化中的象征意义？")
    st.markdown("- 重阳节和哪些荆楚植物有关？")
    st.markdown("- 湖北哪些地方盛产荷花？")

# 主界面布局（彻底修复所有报错）
st.markdown("---")
st.markdown("### 智能问答")
user_question = st.text_input(
    label="请输入你的问题（如：梅花的文化象征？）",
    placeholder="输入后点击按钮，基于你的50种植物数据生成回答...",
    key="user_question"
)
if st.button("获取专业回答", type="primary"):
    if user_question.strip():
        with st.spinner("正在检索你的50种植物数据并生成回答..."):
            answer = generate_answer(user_question)
            st.markdown("### 回答（基于你的50种植物数据）")
            st.write(answer)
    else:
        st.warning("请先输入你的问题！")

st.markdown("---")
col_main1, col_main2 = st.columns(2)

with col_main1:
    st.markdown("### 🌺 今日推荐植物")
    # 从50种植物中随机推荐
    random_plant = random.choice(plant_data)
    # 👇 这里用 .get() 方法，彻底避免 KeyError
    st.markdown(f"""
    <div class="plant-card">
        <h3>{random_plant.get('name', '未知植物')}</h3>
        <p><strong>🔍 拉丁学名</strong>：{random_plant.get('latin', '无')}</p>
        <p><strong>🌳 科属</strong>：{random_plant.get('family', '无')} {random_plant.get('genus', '无')}</p>
        <p><strong>📍 现代地理分布</strong>：{random_plant.get('distribution', '无')}</p>
        <p><strong>🏛️ 文化象征</strong>：{random_plant.get('cultural_symbol', '无')}</p>
        <p><strong>🎉 关联节日</strong>：{random_plant.get('festivals', '无')}</p>
        <p><strong>💊 药用价值</strong>：{random_plant.get('medicinal_value', '无')}</p>
    </div>
    """, unsafe_allow_html=True)

with col_main2:
    st.markdown("### 📜 植物名录查询")
    # 展示全部50种植物的名录
    plant_names = [p["name"] for p in plant_data]
    selected_plant = st.selectbox(
        "从50种植物中选择查看详情", 
        options=plant_names, 
        key="plant_selector"
    )
    
    # 展示选中植物的详情（彻底修复KeyError）
    if selected_plant:
        detail = get_plant_detail(selected_plant)
        st.markdown(f"""
        <div class="plant-card">
            <h3>{detail.get('name', '未知植物')} 详细信息</h3>
            <p><strong>🔍 拉丁学名</strong>：{detail.get('latin', '无')}</p>
            <p><strong>🌳 科属</strong>：{detail.get('family', '无')} {detail.get('genus', '无')}</p>
            <p><strong>📍 现代地理分布</strong>：{detail.get('distribution', '无')}</p>
            <p><strong>🏛️ 文化象征</strong>：{detail.get('cultural_symbol', '无')}</p>
            <p><strong>🎉 关联节日</strong>：{detail.get('festivals', '无')}</p>
            <p><strong>💊 药用价值</strong>：{detail.get('medicinal_value', '无')}</p>
            <p><strong>🛠️ 传统实用价值</strong>：{detail.get('traditional_use', '无')}</p>
            <p><strong>🌍 生态意义</strong>：{detail.get('ecological_significance', '无')}</p>
        </div>
        """, unsafe_allow_html=True)

# 页脚信息
st.markdown("---")
st.markdown("💡 数据来源：你的荆楚植物文化Excel数据表（共50种植物） | 技术支持：Streamlit + Groq | 后续更新Excel文件即可同步数据")