import os
from typing import List, Optional
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# 加载环境变量（本地开发用）
load_dotenv()

# 从环境变量读取配置
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

class LangChainPlantQA:
    """荆楚植物问答核心类（兼容离线模式）"""
    ALIAS_MAP = {
        "菊花":"菊", "梅花":"梅", "兰花":"兰", "竹子":"竹",
        "荷花":"荷", "莲花":"荷", "桂花":"桂", "牡丹花":"牡丹",
        "杜鹃花":"杜鹃", "水仙花":"水仙", "艾草":"艾", "菖蒲叶":"菖蒲"
    }

    def __init__(self):
        # 初始化 Groq 大模型（必须项）
        if not GROQ_API_KEY:
            raise ValueError("请配置 GROQ_API_KEY 环境变量！")
        
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama3-8b-8192",
            temperature=0.1  # 降低随机性，回答更稳定
        )
        
        # 初始化 Neo4j（可选，失败不影响基础功能）
        self.graph = None
        self.neo4j_connected = False
        
        if all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
            try:
                from langchain_neo4j import Neo4jGraph
                self.graph = Neo4jGraph(
                    url=NEO4J_URI,
                    username=NEO4J_USER,
                    password=NEO4J_PASSWORD
                )
                self.neo4j_connected = True
                print("✅ Neo4j 数据库连接成功")
            except Exception as e:
                print(f"⚠️ Neo4j 连接失败（离线模式）：{str(e)}")
        else:
            print("ℹ️ Neo4j 配置不全，使用离线模式")

    def get_all_plants(self) -> List[str]:
        """获取植物列表（离线返回示例数据）"""
        if self.neo4j_connected:
            try:
                query = "MATCH (p:Plant) RETURN p.name AS name"
                result = self.graph.query(query)
                return [row["name"] for row in result]
            except Exception:
                pass
        # 离线模式返回示例植物列表
        return ["梅花", "菊花", "兰花", "竹子", "荷花", "桂花", "牡丹"]

    def get_plant_detail(self, plant_name: str) -> Optional[dict]:
        """获取植物详情（离线返回示例数据）"""
        # 别名映射
        plant_name = self.ALIAS_MAP.get(plant_name, plant_name)
        
        if self.neo4j_connected:
            try:
                query = """
                MATCH (p:Plant {name: $name})
                OPTIONAL MATCH (p)-[:HAS_FAMILY]->(f:Family)
                OPTIONAL MATCH (p)-[:ASSOCIATED_WITH]->(fe:Festival)
                RETURN p.name AS name, p.latin AS latin, 
                       p.cultural_symbol AS cultural_symbol, 
                       p.distribution AS distribution,
                       f.name AS family,
                       collect(DISTINCT fe.name) AS festivals
                """
                result = self.graph.query(query, {"name": plant_name})
                if result:
                    return result[0]
            except Exception:
                pass
        
        # 离线模式返回示例详情
        demo_details = {
            "梅花": {
                "name": "梅花",
                "latin": "Prunus mume",
                "cultural_symbol": "高洁、坚韧、不屈不挠，是荆楚文化中代表风骨的植物",
                "distribution": "湖北武汉、黄冈、襄阳等地广泛种植",
                "family": "蔷薇科",
                "festivals": ["春节", "梅花节"]
            },
            "菊花": {
                "name": "菊花",
                "latin": "Chrysanthemum × morifolium",
                "cultural_symbol": "长寿、高雅，重阳节赏菊是荆楚传统习俗",
                "distribution": "湖北荆州、宜昌等地",
                "family": "菊科",
                "festivals": ["重阳节"]
            },
            "兰花": {
                "name": "兰花",
                "latin": "Cymbidium ssp.",
                "cultural_symbol": "君子之花，代表高洁、典雅",
                "distribution": "湖北神农架、恩施等山区",
                "family": "兰科",
                "festivals": []
            }
        }
        return demo_details.get(plant_name, demo_details["梅花"])

    def answer_question(self, question: str) -> str:
        """生成回答（带完整异常处理）"""
        try:
            # 构建提示词
            if self.neo4j_connected:
                # 从 Neo4j 检索相关信息
                plant_names = self.get_all_plants()
                relevant_plants = [p for p in plant_names if p in question]
                
                if relevant_plants:
                    context = ""
                    for plant in relevant_plants:
                        detail = self.get_plant_detail(plant)
                        context += f"\n【{plant}】\n拉丁名：{detail['latin']}\n文化象征：{detail['cultural_symbol']}\n分布：{detail['distribution']}\n"
                    prompt = f"""你是荆楚植物文化专家，请根据以下资料回答问题（仅用中文）：
{context}

问题：{question}
要求：回答简洁准确，符合荆楚地域文化特色，不要编造信息。"""
                else:
                    prompt = f"你是荆楚植物文化专家，请回答以下问题（仅用中文）：{question}"
            else:
                prompt = f"""你是荆楚植物文化专家，请回答以下问题（仅用中文）：
{question}
要求：回答简洁准确，符合荆楚地域文化特色，基于常见的荆楚植物知识回答。"""
            
            # 调用 LLM 生成回答
            response = self.llm.invoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            # 捕获所有异常，返回友好提示
            error_msg = f"抱歉，暂时无法回答你的问题。错误原因：{str(e)[:100]}"
            return error_msg