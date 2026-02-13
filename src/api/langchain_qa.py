import os
from typing import List, Optional
from langchain_neo4j import Neo4jGraph
from langchain_groq import ChatGroq
from neo4j import GraphDatabase
from dotenv import load_dotenv  # 新增：加载.env文件

# 加载本地.env文件中的环境变量（本地运行用）
load_dotenv()

# 从环境变量读取配置（优先读系统环境变量，本地读.env，云端读Streamlit Secrets）
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")  # 缺省值
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")                # 缺省值
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")     # 缺省值

class LangChainPlantQA:
    ALIAS_MAP = {
        "菊花":"菊", "梅花":"梅", "兰花":"兰", "竹子":"竹",
        "荷花":"荷", "莲花":"荷", "桂花":"桂", "牡丹花":"牡丹",
        "杜鹃花":"杜鹃", "水仙花":"水仙", "艾草":"艾", "菖蒲叶":"菖蒲"
    }

    def __init__(self):
        self.graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD
        )
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama3-8b-8192"
        )

    def get_all_plants(self) -> List[str]:
        query = "MATCH (p:Plant) RETURN p.name AS name"
        result = self.graph.query(query)
        return [row["name"] for row in result]

    def get_plant_detail(self, plant_name: str) -> Optional[dict]:
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
        return None

    def answer_question(self, question: str) -> str:
        # 简化版问答逻辑，可根据需要扩展
        return f"你问的是：{question}\n\n（当前为演示版本，完整问答功能需连接 Neo4j 数据库）"