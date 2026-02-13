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
# 1. 加载Excel植物数据
# ----------------------
@st.cache_data
def load_plant_data():
    """加载Excel格式的荆楚植物数据"""
    try:
        # 读取Excel文件（路径和你的文件一致）
        df = pd.read_excel("data/荆楚植物文化图谱植物数据.xlsx", engine="openpyxl")
        # 处理空值，避免后续报错
        df = df.fillna("无")
        
        # 统一字段名（适配你的表格结构，可根据实际字段调整）
        if "name" not in df.columns:
            df["name"] = df.get("植物名", df.get("名称", "未知"))
        if "cultural_symbol" not in df.columns:
            df["cultural_symbol"] = df.get("文化象征", df.get("象征意义", "无"))
        if "distribution" not in df.columns:
            df["distribution"] = df.get("分布", df.get("产地", "无"))
        if "family" not in df.columns:
            df["family"] = df.get("科属", df.get("科", "无"))
        if "festivals" not in df.columns:
            df["festivals"] = df.get("关联节日", df.get("节日", "无"))
        if "latin" not in df.columns:
            df["latin"] = df.get("拉丁名", df.get("学名", "无"))
        
        # 转换为字典列表，方便调用
        plant_list = df.to_dict("records")
        st.success(f"✅ 成功加载 {len(plant_list)} 种荆楚植物数据")
        return plant_list
    except FileNotFoundError:
        st.warning("⚠️ 未找到Excel数据文件，使用示例数据")
        # 示例数据（保证应用能正常运行）
        return [
            {"name": "梅花", "latin": "Prunus mume", "cultural_symbol": "高洁、坚韧、不屈不挠，是荆楚文化中代表风骨的植物", "distribution": "湖北武汉、黄冈、襄阳等地", "family": "蔷薇科", "festivals": "春节、梅花节"},
            {"name": "菊花", "latin": "Chrysanthemum × morifolium", "cultural_symbol": "长寿、高雅，重阳节赏菊是荆楚传统习俗", "distribution": "湖北荆州、宜昌等地", "family": "菊科", "festivals": "重阳节"},
            {"name": "兰花", "latin": "Cymbidium ssp.", "cultural_symbol": "君子之花，代表高洁、典雅", "distribution": "湖北神农架、恩施等山区", "family": "兰科", "festivals": "无"},
            {"name": "荷花", "latin": "Nelumbo nucifera", "cultural_symbol": "清廉、纯洁，洪湖荷花是湖北名片", "distribution": "湖北洪湖、鄂州等地", "family": "莲科", "festivals": "荷花节"},
            {"name": "桂花", "latin": "Osmanthus fragrans", "cultural_symbol": "吉祥、团圆，中秋赏桂是荆楚传统", "distribution": "湖北咸宁、武汉等地", "family": "木犀科", "festivals": "中秋节"}
        ]
    except Exception as e:
        st.error(f"加载数据失败：{str(e)[:100]}")
        # 返回保底示例数据
        return [{"name": "梅花", "latin": "Prunus mume", "cultural_symbol": "高洁、坚韧", "distribution": "湖北武汉", "family": "蔷薇科", "festivals": "春节"}]

# ----------------------
# 2. 初始化Groq客户端
# ----------------------
@st.cache_resource
def init_groq():
    """初始化Groq大模型客户端"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("请在Streamlit Secrets中配置GROQ_API_KEY！")
        st.stop()
    return Groq(api_key=api_key)

# ----------------------
# 3. 核心功能函数
# ----------------------
def get_plant_detail(plant_name):
    """根据植物名获取详情（支持别名匹配）"""
    # 别名映射（可根据你的数据扩展）
    alias_map = {
        "菊花":"菊", "梅花":"梅", "兰花":"兰", "竹子":"竹",
        "荷花":"荷", "莲花":"荷", "桂花":"桂", "牡丹花":"牡丹",
        "杜鹃花":"杜鹃", "水仙花":"水仙", "艾草":"艾", "菖蒲叶":"菖蒲"
    }
    # 匹配别名
    target_name = alias_map.get(plant_name, plant_name)
    
    # 查找对应植物数据
    for plant in plant_data:
        if plant["name"] == target_name or target_name in str(plant["name"]):
            return plant
    # 未找到时返回第一个植物数据
    return plant_data[0]

def generate_answer(question):
    """基于Excel数据+Groq生成精准回答"""
    try:
        # 提取问题中的植物名
        plant_names = [p["name"] for p in plant_data]
        relevant_plants = [p for p in plant_names if p in question]
        
        # 构建基于自有数据的提示词
        context = ""
        if relevant_plants:
            context = "### 荆楚植物参考数据：\n"
            for p in relevant_plants:
                detail = get_plant_detail(p)
                context += f"""
- 【{detail['name']}】
  拉丁名：{detail['latin']}
  文化象征：{detail['cultural_symbol']}
  分布区域：{detail['distribution']}
  科属：{detail['family']}
  关联节日：{detail['festivals']}
"""
        
        # 最终提示词
        prompt = f"""你是专业的荆楚植物文化研究员，请严格根据以下参考数据回答问题（仅用中文）：
{context}

如果参考数据中无相关信息，基于荆楚地域文化常识回答，禁止编造数据。

问题：{question}
要求：
1. 回答简洁准确，突出荆楚地域特色；
2. 语言通俗易懂，避免专业术语；
3. 字数控制在200字以内。"""
        
        # 调用Groq生成回答
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "你是荆楚植物文化专家，回答专业、简洁、有地域特色"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",  # 可用的最新模型
            temperature=0.2  # 降低随机性，保证回答精准
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
# 5. 页面样式与布局
# ----------------------
# 自定义样式美化
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
    /* 植物卡片样式 */
    .plant-card {
        background-color: #f0f8fb;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #2E8B57;
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
</style>
""", unsafe_allow_html=True)

# 页面标题
st.title("🌿 荆楚植物智能问答系统")
st.markdown("##### 📚 基于真实荆楚植物Excel数据的智能问答助手")

# 侧边栏
with st.sidebar:
    st.markdown("### 🌱 关于系统")
    st.markdown("本系统基于**荆楚植物文化Excel数据** + 大语言模型，提供精准的植物文化问答服务。")
    
    st.markdown("---")
    st.markdown("### 📊 数据概览")
    # 统计核心数据
    total_plants = len(plant_data)
    total_families = len(set([p["family"] for p in plant_data]))
    # 统计关联节日
    total_festivals = 0
    for p in plant_data:
        if p["festivals"] != "无" and p["festivals"] != "":
            total_festivals += len(str(p["festivals"]).split("、"))
    
    # 展示统计指标
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("植物总数", total_plants)
        st.metric("关联节日数", total_festivals)
    with col_s2:
        st.metric("科属数量", total_families)
    
    st.markdown("---")
    st.markdown("### ❓ 提问示例")
    st.markdown("- 梅花在荆楚文化中的象征意义？")
    st.markdown("- 重阳节和哪些荆楚植物有关？")
    st.markdown("- 湖北哪些地方盛产荷花？")

# 主界面双列布局
col1, col2 = st.columns([2, 1])

# 左侧：智能问答区域
with col1:
    st.markdown("### ❓ 智能问答")
    user_question = st.text_input(
        label="请输入你的问题",
        placeholder="例如：梅花的文化象征？湖北哪些地方产桂花？",
        key="user_question"
    )
    
    # 回答按钮逻辑
    if st.button("获取专业回答", type="primary"):
        if user_question.strip():
            with st.spinner("🤔 正在检索数据并生成回答..."):
                answer = generate_answer(user_question)
                st.markdown("### 📝 回答")
                st.write(answer)
        else:
            st.warning("⚠️ 请先输入你的问题！")

# 右侧：植物推荐与名录区域
with col2:
    st.markdown("### 🌺 今日推荐植物")
    # 随机推荐一种植物
    random_plant = random.choice(plant_data)
    st.markdown(f"""
    <div class="plant-card">
        <h4 style="margin:0; color:#2E8B57;">{random_plant['name']}</h4>
        <p><strong>拉丁名</strong>：{random_plant['latin']}</p>
        <p><strong>文化象征</strong>：{random_plant['cultural_symbol']}</p>
        <p><strong>分布区域</strong>：{random_plant['distribution']}</p>
        <p><strong>关联节日</strong>：{random_plant['festivals']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📜 植物名录查询")
    # 植物名录下拉选择
    plant_names = [p["name"] for p in plant_data]
    selected_plant = st.selectbox("选择查看植物详情", options=plant_names, key="plant_selector")
    
    # 展示选中植物的详情
    if selected_plant:
        detail = get_plant_detail(selected_plant)
        st.markdown(f"""
        <div class="plant-card">
            <h4 style="margin:0; color:#2E8B57;">{detail['name']} 详细信息</h4>
            <p><strong>科属</strong>：{detail['family']}</p>
            <p><strong>地理分布</strong>：{detail['distribution']}</p>
            <p><strong>文化象征</strong>：{detail['cultural_symbol']}</p>
            <p><strong>关联节日</strong>：{detail['festivals']}</p>
        </div>
        """, unsafe_allow_html=True)

# 页脚信息
st.markdown("---")
st.markdown("💡 数据来源：荆楚植物文化Excel数据表 | 技术支持：Streamlit + Groq | 后续可直接更新Excel文件同步数据")