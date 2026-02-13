import streamlit as st
import os
import random
import pandas as pd
from groq import Groq

# ------------------------------------------------------------
# 0. 页面配置（必须放在最前面）
# ------------------------------------------------------------
st.set_page_config(
    page_title="🌿 荆楚植物智能问答系统",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# 1. 别名映射表（定义在最前面，供多个函数使用）
# ------------------------------------------------------------
ALIAS_MAP = {
    "梅花": "梅", "菊花": "菊", "兰花": "兰", "竹子": "竹",
    "荷花": "荷（莲）", "莲花": "荷（莲）", "桂花": "桂", "牡丹花": "牡丹",
    "杜鹃花": "杜鹃", "水仙花": "水仙", "艾草": "艾", "菖蒲叶": "菖蒲"
}

# ------------------------------------------------------------
# 2. 加载 Excel 数据（自动定位表头行，彻底解决列名识别问题）
# ------------------------------------------------------------
@st.cache_data
def load_plant_data():
    """自动查找包含“植物中文名”的行作为表头，无论前面有多少空行/注释行"""
    try:
        excel_path = "data/荆楚植物文化图谱植物数据.xlsx"
        
        # ----- 第一步：读取前20行，定位表头行 -----
        df_preview = pd.read_excel(excel_path, engine="openpyxl", header=None, nrows=20)
        header_row_idx = None
        for idx, row in df_preview.iterrows():
            # 检查这一行是否包含“植物中文名”（转成字符串后判断）
            if row.astype(str).str.contains("植物中文名").any():
                header_row_idx = idx
                break
        
        if header_row_idx is None:
            st.error("❌ 无法在Excel中找到表头行（必须包含'植物中文名'）")
            st.stop()
        
        # ----- 第二步：以找到的行作为表头，重新读取完整数据 -----
        df = pd.read_excel(excel_path, engine="openpyxl", header=header_row_idx)
        
        # 清理列名两端的空白字符（有时会有换行符或空格）
        df.columns = df.columns.str.strip()
        
        # 过滤完全空的行
        df = df.dropna(how="all")
        df = df.fillna("无")
        
        # ----- 第三步：重映射为标准字段名 -----
        df["name"]            = df["植物中文名"]
        df["latin"]           = df["植物拉丁学名"]
        df["family"]          = df["植物科名"]
        df["genus"]           = df["植物属名"]
        df["distribution"]    = df["现代地理分布"]
        df["cultural_symbol"] = df["文化象征"]
        df["festivals"]       = df["节日"]
        df["medicinal_value"] = df["药用价值"]
        df["traditional_use"] = df["传统实用价值"]
        df["ecological_significance"] = df["生态意义"]
        
        # 转换为字典列表，只保留有效植物（名称不为“无”）
        plant_list = [p for p in df.to_dict("records") if p["name"] != "无"]
        
        st.success(f"✅ 成功加载 {len(plant_list)} 种荆楚植物数据")
        return plant_list
        
    except FileNotFoundError:
        st.error("⚠️ 未找到Excel文件！请确认 data 文件夹下有「荆楚植物文化图谱植物数据.xlsx」")
        st.stop()
    except Exception as e:
        st.error(f"❌ 数据加载失败：{str(e)[:200]}")
        st.stop()

# ------------------------------------------------------------
# 3. 初始化 Groq 客户端（缓存）
# ------------------------------------------------------------
@st.cache_resource
def init_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("❌ 未配置 GROQ_API_KEY！请在 Streamlit Secrets 中填写")
        st.stop()
    try:
        return Groq(api_key=api_key, timeout=60)
    except Exception as e:
        st.error(f"❌ Groq客户端初始化失败：{str(e)[:100]}")
        st.stop()

# ------------------------------------------------------------
# 4. 全局数据加载（必须在函数定义之后立即执行）
# ------------------------------------------------------------
plant_data = load_plant_data()
groq_client = init_groq_client()

# ------------------------------------------------------------
# 5. 辅助函数：获取植物详情（处理别名）
# ------------------------------------------------------------
def get_plant_detail(plant_name):
    """根据输入的植物名（含别名）返回对应的植物字典"""
    target_name = ALIAS_MAP.get(plant_name.strip(), plant_name.strip())
    for plant in plant_data:
        # 精确匹配，或主名包含在植物名称中（如“荷”匹配“荷（莲）”）
        if plant["name"] == target_name or target_name in plant["name"]:
            return plant
    # 未找到则返回第一个（兜底）
    return plant_data[0] if plant_data else {}

# ------------------------------------------------------------
# 6. 智能问答生成
# ------------------------------------------------------------
def generate_intelligent_answer(question):
    try:
        all_plant_names = [p["name"] for p in plant_data]
        
        # 识别问题中涉及的植物（直接匹配主名或别名）
        relevant_plants = []
        for p_name in all_plant_names:
            if p_name in question:
                relevant_plants.append(p_name)
        for alias, real_name in ALIAS_MAP.items():
            if alias in question and real_name not in relevant_plants:
                relevant_plants.append(real_name)
        
        # 构建上下文
        context = "### 荆楚植物参考数据：\n"
        if relevant_plants:
            for p_name in relevant_plants:
                plant = get_plant_detail(p_name)
                context += f"""
- 【植物名】：{plant.get('name', '未知')}
  拉丁学名：{plant.get('latin', '未知')} | 科属：{plant.get('family', '未知')} {plant.get('genus', '未知')}
  湖北分布：{plant.get('distribution', '未知')} | 文化象征：{plant.get('cultural_symbol', '未知')}
  关联节日：{plant.get('festivals', '未知')} | 药用价值：{plant.get('medicinal_value', '未知')}
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
            model="llama-3.1-8b-instant",   # Groq 免费模型
            temperature=0.1,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"💡 问答暂无法响应，错误原因：{str(e)[:80]}"

# ------------------------------------------------------------
# 7. 页面样式（纯美化，无逻辑改动）
# ------------------------------------------------------------
st.markdown("""
<style>
    * {margin: 0; padding: 0; box-sizing: border-box;}
    .main {background-color: #f5f7f9 !important; padding: 0 20px !important;}

    [data-testid="stSidebar"] {
        background-color: #2E8B57 !important;
        color: #ffffff !important;
        padding: 20px 15px !important;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] li {
        color: #ffffff !important;
        font-size: 14px !important;
    }
    [data-testid="stSidebar"] .stMetric {
        background-color: rgba(255,255,255,0.12) !important;
        border-radius: 8px;
        padding: 10px !important;
        margin: 5px 0 !important;
    }
    [data-testid="stSidebar"] .stMetric-label, [data-testid="stSidebar"] .stMetric-value {
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    .plant-card {
        background-color: #ffffff !important;
        border-radius: 10px;
        border-left: 5px solid #2E8B57 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        padding: 20px !important;
        margin: 10px 0 !important;
        width: 100% !important;
    }
    .plant-card h3 {
        color: #2E8B57 !important;
        font-size: 18px !important;
        margin-bottom: 15px !important;
        font-weight: 600 !important;
    }
    .plant-card p {
        color: #333333 !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        margin: 6px 0 !important;
    }
    .plant-card strong {
        color: #2E8B57 !important;
        font-weight: 600 !important;
        width: 120px !important;
        display: inline-block !important;
    }

    .stButton>button {
        background-color: #2E8B57 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        height: 48px !important;
        width: 100% !important;
        font-size: 15px !important;
        font-weight: 500 !important;
    }
    .stButton>button:hover {
        background-color: #1f6e43 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        height: 48px !important;
        border-radius: 8px !important;
        border: 1px solid #2E8B57 !important;
        background-color: #ffffff !important;
        color: #333333 !important;
        padding: 0 15px !important;
        font-size: 14px !important;
    }

    h1, h2, h3, h4 {color: #2E8B57 !important; margin: 10px 0 !important;}
    .stSuccess, .stError, .stWarning {
        border-radius: 8px !important;
        padding: 10px 15px !important;
        margin: 10px 0 !important;
    }

    .footer {
        color: #666666 !important;
        font-size: 13px !important;
        text-align: center !important;
        margin: 30px 0 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# 8. 页面主体布局
# ------------------------------------------------------------
st.title("🌿 荆楚植物智能问答系统")
st.markdown("##### 基于**荆楚植物文化图谱**原始数据开发 | 湖北地域专属植物文化查询")
st.markdown("---")

# --- 侧边栏 ---
with st.sidebar:
    st.markdown("### 🌱 系统说明")
    st.markdown("本系统基于荆楚植物文化图谱原始Excel数据开发，提供植物详情查询和智能文化问答。")

    st.markdown("---")
    st.markdown("### 📊 数据概览")
    total_plants = len(plant_data)
    total_families = len(set([p.get("family", "未知") for p in plant_data]))
    total_festivals = len(set([
        f for p in plant_data
        for f in p.get("festivals", "无").split("、")
        if p.get("festivals", "无") != "无"
    ]))
    total_hubei_dist = len(set([
        d for p in plant_data
        for d in p.get("distribution", "无").split("；")
        if p.get("distribution", "无") != "无"
    ]))

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("🌿 植物总数", total_plants)
        st.metric("🎉 关联节日", total_festivals)
    with col_s2:
        st.metric("🌳 科属数量", total_families)
        st.metric("📍 湖北分布区", total_hubei_dist)

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
if st.button("获取精准回答", type="primary"):
    if not user_question.strip():
        st.warning("⚠️ 请输入有效问题！")
    else:
        with st.spinner("🔍 正在检索数据..."):
            answer = generate_intelligent_answer(user_question)
            st.markdown("#### 📝 专属回答")
            st.write(answer)
st.markdown("---")

# --- 植物卡片（今日推荐 + 植物名录）---
col_card1, col_card2 = st.columns(2, gap="medium")

with col_card1:
    st.markdown("### 🌸 今日推荐植物")
    if plant_data:
        random_plant = random.choice(plant_data)
        st.markdown(f"""
        <div class="plant-card">
            <h3>{random_plant.get('name', '未知')} · 荆楚特色植物</h3>
            <p><strong>拉丁学名</strong>：{random_plant.get('latin', '未知')}</p>
            <p><strong>科属分类</strong>：{random_plant.get('family', '未知')} {random_plant.get('genus', '未知')}</p>
            <p><strong>湖北分布</strong>：{random_plant.get('distribution', '未知')}</p>
            <p><strong>文化象征</strong>：{random_plant.get('cultural_symbol', '未知')}</p>
            <p><strong>关联节日</strong>：{random_plant.get('festivals', '未知')}</p>
            <p><strong>药用价值</strong>：{random_plant.get('medicinal_value', '未知')}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 暂无有效植物数据")

with col_card2:
    st.markdown("### 📜 植物名录查询")
    if plant_data:
        plant_names_sorted = sorted([p["name"] for p in plant_data])
        selected_plant = st.selectbox(
            label="选择植物查看详细信息",
            options=plant_names_sorted,
            key="plant_selector",
            label_visibility="collapsed"
        )
        if selected_plant:
            plant_detail = get_plant_detail(selected_plant)
            st.markdown(f"""
            <div class="plant-card">
                <h3>{plant_detail.get('name', '未知')} · 详细信息</h3>
                <p><strong>拉丁学名</strong>：{plant_detail.get('latin', '未知')}</p>
                <p><strong>科属分类</strong>：{plant_detail.get('family', '未知')} {plant_detail.get('genus', '未知')}</p>
                <p><strong>湖北分布</strong>：{plant_detail.get('distribution', '未知')}</p>
                <p><strong>文化象征</strong>：{plant_detail.get('cultural_symbol', '未知')}</p>
                <p><strong>关联节日</strong>：{plant_detail.get('festivals', '未知')}</p>
                <p><strong>药用价值</strong>：{plant_detail.get('medicinal_value', '未知')}</p>
                <p><strong>传统用途</strong>：{plant_detail.get('traditional_use', '未知')}</p>
                <p><strong>生态意义</strong>：{plant_detail.get('ecological_significance', '未知')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 暂无有效植物数据")

# --- 页脚 ---
st.markdown("---")
st.markdown('<p class="footer">💡 数据来源：荆楚植物文化图谱原始Excel数据 | 技术支持：Streamlit + Groq</p>', unsafe_allow_html=True)